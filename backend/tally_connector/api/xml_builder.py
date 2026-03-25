import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Any, Iterable


def _fmt_date(value: Any) -> str:
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    return str(value).replace("-", "")


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def build_export_report_request(
    report_name: str,
    company_name: str = "",
    from_date: Any | None = None,
    to_date: Any | None = None,
    static_variables: dict[str, Any] | None = None,
) -> str:
    envelope = ET.Element("ENVELOPE")

    header = ET.SubElement(envelope, "HEADER")
    ET.SubElement(header, "VERSION").text = "1"
    ET.SubElement(header, "TALLYREQUEST").text = "Export"
    ET.SubElement(header, "TYPE").text = "Data"
    ET.SubElement(header, "ID").text = report_name

    body = ET.SubElement(envelope, "BODY")
    desc = ET.SubElement(body, "DESC")
    statics = ET.SubElement(desc, "STATICVARIABLES")

    if company_name:
        ET.SubElement(statics, "SVCURRENTCOMPANY").text = company_name
    if from_date is not None:
        ET.SubElement(statics, "SVFROMDATE").text = _fmt_date(from_date)
    if to_date is not None:
        ET.SubElement(statics, "SVTODATE").text = _fmt_date(to_date)

    if static_variables:
        for key, value in static_variables.items():
            ET.SubElement(statics, key).text = _to_text(value)

    return ET.tostring(envelope, encoding="unicode")


def _base_import_envelope(company_name: str = "") -> tuple[ET.Element, ET.Element]:
    envelope = ET.Element("ENVELOPE")
    header = ET.SubElement(envelope, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"

    body = ET.SubElement(envelope, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")
    request_desc = ET.SubElement(import_data, "REQUESTDESC")
    ET.SubElement(request_desc, "REPORTNAME").text = "All Masters"

    if company_name:
        static_vars = ET.SubElement(request_desc, "STATICVARIABLES")
        ET.SubElement(static_vars, "SVCURRENTCOMPANY").text = company_name

    request_data = ET.SubElement(import_data, "REQUESTDATA")
    return envelope, request_data


def build_ledger_create_xml(payload: dict[str, Any], company_name: str = "") -> str:
    envelope, request_data = _base_import_envelope(company_name)

    message = ET.SubElement(request_data, "TALLYMESSAGE", attrib={"xmlns:UDF": "TallyUDF"})
    ledger = ET.SubElement(message, "LEDGER", attrib={"NAME": _to_text(payload.get("name")), "ACTION": "Create"})

    ET.SubElement(ledger, "NAME").text = _to_text(payload.get("name"))
    ET.SubElement(ledger, "PARENT").text = _to_text(payload.get("parent", "Sundry Debtors"))
    ET.SubElement(ledger, "ISBILLWISEON").text = _to_text(payload.get("is_bill_wise", "Yes"))
    ET.SubElement(ledger, "OPENINGBALANCE").text = _to_text(payload.get("opening_balance", "0"))

    return ET.tostring(envelope, encoding="unicode")


def build_stock_item_create_xml(payload: dict[str, Any], company_name: str = "") -> str:
    envelope, request_data = _base_import_envelope(company_name)

    message = ET.SubElement(request_data, "TALLYMESSAGE", attrib={"xmlns:UDF": "TallyUDF"})
    stock_item = ET.SubElement(message, "STOCKITEM", attrib={"NAME": _to_text(payload.get("name")), "ACTION": "Create"})

    ET.SubElement(stock_item, "NAME").text = _to_text(payload.get("name"))
    ET.SubElement(stock_item, "PARENT").text = _to_text(payload.get("parent", "Primary"))
    ET.SubElement(stock_item, "BASEUNITS").text = _to_text(payload.get("base_units", "Nos"))

    return ET.tostring(envelope, encoding="unicode")


def build_voucher_create_xml(payload: dict[str, Any], company_name: str = "") -> str:
    envelope, request_data = _base_import_envelope(company_name)

    voucher_type = _to_text(payload.get("voucher_type", "Sales"))
    voucher = ET.SubElement(
        ET.SubElement(request_data, "TALLYMESSAGE", attrib={"xmlns:UDF": "TallyUDF"}),
        "VOUCHER",
        attrib={"VCHTYPE": voucher_type, "ACTION": "Create"},
    )

    amount = float(payload.get("amount", 0) or 0)
    is_debit = bool(payload.get("is_debit", True))

    ET.SubElement(voucher, "DATE").text = _fmt_date(payload.get("date", datetime.utcnow().date()))
    ET.SubElement(voucher, "VOUCHERTYPENAME").text = voucher_type
    ET.SubElement(voucher, "VOUCHERNUMBER").text = _to_text(payload.get("voucher_number"))
    ET.SubElement(voucher, "NARRATION").text = _to_text(payload.get("narration"))

    entry_one = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
    ET.SubElement(entry_one, "LEDGERNAME").text = _to_text(payload.get("party_ledger_name"))
    ET.SubElement(entry_one, "ISDEEMEDPOSITIVE").text = "Yes" if is_debit else "No"
    ET.SubElement(entry_one, "AMOUNT").text = str(-amount if is_debit else amount)

    counter_name = _to_text(payload.get("counter_ledger_name"))
    if counter_name:
        entry_two = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(entry_two, "LEDGERNAME").text = counter_name
        ET.SubElement(entry_two, "ISDEEMEDPOSITIVE").text = "No" if is_debit else "Yes"
        ET.SubElement(entry_two, "AMOUNT").text = str(amount if is_debit else -amount)

    return ET.tostring(envelope, encoding="unicode")


def build_bulk_import_xml(xml_chunks: Iterable[str], company_name: str = "") -> str:
    envelope, request_data = _base_import_envelope(company_name)

    for chunk in xml_chunks:
        if not chunk:
            continue
        try:
            node = ET.fromstring(chunk)
            request_data.append(node)
        except ET.ParseError:
            continue

    return ET.tostring(envelope, encoding="unicode")
