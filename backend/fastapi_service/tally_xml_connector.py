"""
SIZH CA – Tally XML Connector
================================
Builds Tally-compliant XML envelopes and sends them to Tally's
built-in HTTP XML Server (port 9000 by default).

Architecture:
─────────────
  Django DB (TallyVoucher)
       │
       ▼
  tally_xml_connector.py
       │  build_voucher_xml()   → Generates <ENVELOPE> XML per voucher
       │  build_batch_xml()     → Wraps multiple vouchers in one envelope
       │  send_to_tally()       → HTTP POST to Tally XML Server
       ▼
  Tally ERP/Prime (http://localhost:9000)

Tally XML Server accepts POST requests at its configured port.
Request body = XML envelope.  Response = XML with success/failure.
"""

import os
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Optional
from xml.dom.minidom import parseString

import httpx


# ── Configuration ────────────────────────────────────────────────────────────

TALLY_URL = os.getenv("TALLY_URL", "http://localhost:9000")


# ═══════════════════════════════════════════════════════════════════════════════
# XML GENERATION
# ═══════════════════════════════════════════════════════════════════════════════


def _fmt_date(d) -> str:
    """Format a date/datetime to Tally's YYYYMMDD format."""
    if isinstance(d, datetime):
        d = d.date()
    if isinstance(d, date):
        return d.strftime("%Y%m%d")
    return str(d).replace("-", "")


def _fmt_amount(amt) -> str:
    """Format amount: Tally uses negative for debit in some contexts."""
    return str(round(float(amt), 2))


def build_voucher_xml(voucher: dict) -> str:
    """
    Build a single Tally XML <VOUCHER> element from a TallyVoucher dict.

    Expected voucher dict keys (mirrors TallyVoucher model):
      voucher_type, voucher_number, date, narration, reference,
      party_ledger_name, amount, is_debit,
      counter_ledger_name, counter_amount,
      gst_rate, cgst, sgst, igst, taxable_amount,
      place_of_supply, hsn_code, invoice_no
    """
    vtype = voucher["voucher_type"]
    vdate = _fmt_date(voucher["date"])
    amount = float(voucher.get("amount", 0))
    is_debit = voucher.get("is_debit", True)

    # Build VOUCHER element
    v = ET.Element("VOUCHER", attrib={
        "REMOTEID": str(voucher.get("id", "")),
        "VCHTYPE": vtype,
        "ACTION": "Create",
    })

    ET.SubElement(v, "DATE").text = vdate
    ET.SubElement(v, "VOUCHERTYPENAME").text = vtype
    ET.SubElement(v, "VOUCHERNUMBER").text = voucher.get("voucher_number", "")
    ET.SubElement(v, "NARRATION").text = voucher.get("narration", "")
    ET.SubElement(v, "REFERENCE").text = voucher.get("reference", "")

    if voucher.get("party_ledger_name"):
        ET.SubElement(v, "PARTYLEDGERNAME").text = voucher["party_ledger_name"]

    # ── Ledger entries (double-entry) ──

    # Entry 1: Party ledger
    le1 = ET.SubElement(v, "ALLLEDGERENTRIES.LIST")
    ET.SubElement(le1, "LEDGERNAME").text = voucher.get("party_ledger_name", "")
    # Tally convention: negative = debit, positive = credit
    dr_amt = -amount if is_debit else amount
    ET.SubElement(le1, "ISDEEMEDPOSITIVE").text = "Yes" if is_debit else "No"
    ET.SubElement(le1, "AMOUNT").text = _fmt_amount(dr_amt)

    # Entry 2: Counter ledger (the other side)
    counter_name = voucher.get("counter_ledger_name", "")
    counter_amt = float(voucher.get("counter_amount", amount))
    if counter_name:
        le2 = ET.SubElement(v, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(le2, "LEDGERNAME").text = counter_name
        cr_amt = counter_amt if is_debit else -counter_amt
        ET.SubElement(le2, "ISDEEMEDPOSITIVE").text = "No" if is_debit else "Yes"
        ET.SubElement(le2, "AMOUNT").text = _fmt_amount(cr_amt)

    # ── GST Ledger Entries (if applicable) ──
    cgst = float(voucher.get("cgst", 0) or 0)
    sgst = float(voucher.get("sgst", 0) or 0)
    igst = float(voucher.get("igst", 0) or 0)

    is_output = vtype in ("Sales", "Credit Note")
    gst_prefix = "Output" if is_output else "Input"

    if cgst > 0:
        le_cgst = ET.SubElement(v, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(le_cgst, "LEDGERNAME").text = f"{gst_prefix} CGST"
        ET.SubElement(le_cgst, "ISDEEMEDPOSITIVE").text = "No" if is_output else "Yes"
        ET.SubElement(le_cgst, "AMOUNT").text = _fmt_amount(cgst if is_output else -cgst)

    if sgst > 0:
        le_sgst = ET.SubElement(v, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(le_sgst, "LEDGERNAME").text = f"{gst_prefix} SGST"
        ET.SubElement(le_sgst, "ISDEEMEDPOSITIVE").text = "No" if is_output else "Yes"
        ET.SubElement(le_sgst, "AMOUNT").text = _fmt_amount(sgst if is_output else -sgst)

    if igst > 0:
        le_igst = ET.SubElement(v, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(le_igst, "LEDGERNAME").text = f"{gst_prefix} IGST"
        ET.SubElement(le_igst, "ISDEEMEDPOSITIVE").text = "No" if is_output else "Yes"
        ET.SubElement(le_igst, "AMOUNT").text = _fmt_amount(igst if is_output else -igst)

    return ET.tostring(v, encoding="unicode")


def build_batch_xml(vouchers: list[dict], company_name: str = "") -> str:
    """
    Wrap one or more voucher XMLs into a full Tally import envelope.

    Parameters
    ----------
    vouchers : list of TallyVoucher dicts
    company_name : the Tally company to import into

    Returns
    -------
    str : Complete XML envelope ready to POST to Tally
    """
    envelope = ET.Element("ENVELOPE")

    header = ET.SubElement(envelope, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"

    body = ET.SubElement(envelope, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")

    req_desc = ET.SubElement(import_data, "REQUESTDESC")
    ET.SubElement(req_desc, "REPORTNAME").text = "Vouchers"

    static_vars = ET.SubElement(req_desc, "STATICVARIABLES")
    ET.SubElement(static_vars, "SVCURRENTCOMPANY").text = company_name

    req_data = ET.SubElement(import_data, "REQUESTDATA")

    for v_dict in vouchers:
        voucher_xml_str = build_voucher_xml(v_dict)
        voucher_elem = ET.fromstring(voucher_xml_str)
        req_data.append(voucher_elem)

    raw_xml = ET.tostring(envelope, encoding="unicode", xml_declaration=False)

    # Pretty-print for readability
    try:
        return parseString(raw_xml).toprettyxml(indent="  ", encoding=None)
    except Exception:
        return raw_xml


def build_export_request_xml(report_name: str, company_name: str = "") -> str:
    """
    Build an XML envelope to request data FROM Tally (Export).
    e.g. report_name = "List of Ledgers", "List of Stock Items", "Day Book"
    """
    envelope = ET.Element("ENVELOPE")

    header = ET.SubElement(envelope, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Export Data"

    body = ET.SubElement(envelope, "BODY")
    export_data = ET.SubElement(body, "EXPORTDATA")

    req_desc = ET.SubElement(export_data, "REQUESTDESC")
    ET.SubElement(req_desc, "REPORTNAME").text = report_name

    if company_name:
        static_vars = ET.SubElement(req_desc, "STATICVARIABLES")
        ET.SubElement(static_vars, "SVCURRENTCOMPANY").text = company_name

    return ET.tostring(envelope, encoding="unicode")


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP TRANSPORT
# ═══════════════════════════════════════════════════════════════════════════════


async def send_to_tally(
    xml_payload: str,
    tally_url: Optional[str] = None,
) -> dict:
    """
    Send an XML envelope to Tally's HTTP XML Server.

    Parameters
    ----------
    xml_payload : Complete XML string
    tally_url : Override for Tally server URL (default: TALLY_URL env)

    Returns
    -------
    dict with keys: success, response_xml, error
    """
    url = tally_url or TALLY_URL

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                url,
                content=xml_payload.encode("utf-8"),
                headers={"Content-Type": "application/xml"},
            )

            response_xml = resp.text

            # Tally returns XML with LINEERROR for failures
            success = resp.status_code == 200 and "LINEERROR" not in response_xml

            return {
                "success": success,
                "status_code": resp.status_code,
                "response_xml": response_xml,
                "error": None if success else _extract_tally_error(response_xml),
            }

    except httpx.ConnectError:
        return {
            "success": False,
            "status_code": 0,
            "response_xml": "",
            "error": f"Cannot connect to Tally at {url}. Ensure Tally is running with XML Server enabled.",
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": 0,
            "response_xml": "",
            "error": str(e),
        }


async def fetch_from_tally(
    report_name: str,
    company_name: str = "",
    tally_url: Optional[str] = None,
) -> dict:
    """
    Fetch data from Tally by sending an Export request.

    Returns
    -------
    dict with keys: success, response_xml, error
    """
    xml = build_export_request_xml(report_name, company_name)
    return await send_to_tally(xml, tally_url)


def _extract_tally_error(response_xml: str) -> str:
    """Extract error message from Tally's XML response."""
    try:
        root = ET.fromstring(response_xml)
        # Tally puts errors in LINEERROR or ERRORS
        for tag in ("LINEERROR", "ERRORS", "ERROR"):
            elem = root.find(f".//{tag}")
            if elem is not None and elem.text:
                return elem.text.strip()
    except ET.ParseError:
        pass
    return "Unknown Tally error"


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE: Sync pending vouchers
# ═══════════════════════════════════════════════════════════════════════════════


async def sync_pending_vouchers(
    vouchers: list[dict],
    company_name: str,
    tally_url: Optional[str] = None,
) -> dict:
    """
    Build and send a batch of vouchers to Tally.
    Returns summary: { sent, succeeded, failed, errors }.
    """
    if not vouchers:
        return {"sent": 0, "succeeded": 0, "failed": 0, "errors": []}

    xml = build_batch_xml(vouchers, company_name)
    result = await send_to_tally(xml, tally_url)

    return {
        "sent": len(vouchers),
        "succeeded": len(vouchers) if result["success"] else 0,
        "failed": 0 if result["success"] else len(vouchers),
        "errors": [result["error"]] if result["error"] else [],
        "response_xml": result.get("response_xml", ""),
    }
