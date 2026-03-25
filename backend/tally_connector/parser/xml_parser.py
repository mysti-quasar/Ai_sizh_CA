import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any


# XML 1.0 allowed code points: tab, LF, CR, and valid Unicode scalar ranges.
_INVALID_XML_CHARS_RE = re.compile(r"[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]")
_BARE_AMPERSAND_RE = re.compile(r"&(?!#\d+;|#x[0-9A-Fa-f]+;|[A-Za-z_][\w.\-]*;)")
_NUMERIC_ENTITY_RE = re.compile(r"&#(x[0-9A-Fa-f]+|\d+);")


def _text(node: ET.Element | None, tag: str, default: str = "") -> str:
    if node is None:
        return default
    child = node.find(tag)
    if child is not None and child.text is not None:
        return child.text.strip()
    return default


def _iter_nodes(root: ET.Element, tag: str) -> list[ET.Element]:
    direct = root.findall(f".//{tag}")
    if direct:
        return direct
    upper = root.findall(f".//{tag.upper()}")
    if upper:
        return upper
    lower = root.findall(f".//{tag.lower()}")
    return lower


def _is_valid_xml_codepoint(value: int) -> bool:
    if value in (0x09, 0x0A, 0x0D):
        return True
    if 0x20 <= value <= 0xD7FF:
        return True
    if 0xE000 <= value <= 0xFFFD:
        return True
    if 0x10000 <= value <= 0x10FFFF:
        return True
    return False


def _strip_invalid_numeric_entities(xml_text: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        raw = match.group(1)
        try:
            if raw.startswith("x"):
                value = int(raw[1:], 16)
            else:
                value = int(raw, 10)
        except ValueError:
            return ""
        return match.group(0) if _is_valid_xml_codepoint(value) else ""

    return _NUMERIC_ENTITY_RE.sub(_replace, xml_text)


def _sanitize_xml_text(xml_text: str | bytes) -> str:
    if isinstance(xml_text, bytes):
        decoded = xml_text.decode("utf-8", errors="ignore")
    else:
        # Normalize to UTF-8-safe text even if source string has odd surrogate data.
        decoded = xml_text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

    decoded = decoded.lstrip("\ufeff")
    cleaned = _strip_invalid_numeric_entities(decoded)
    cleaned = _INVALID_XML_CHARS_RE.sub("", cleaned)
    cleaned = _BARE_AMPERSAND_RE.sub("&amp;", cleaned)
    return cleaned


def parse_xml(xml_text: str | bytes) -> ET.Element:
    clean_xml = _sanitize_xml_text(xml_text)
    return ET.fromstring(clean_xml)


def parse_ledgers(xml_text: str) -> list[dict[str, Any]]:
    root = parse_xml(xml_text)
    ledgers = []
    for node in _iter_nodes(root, "LEDGER"):
        item = {
            "name": _text(node, "NAME"),
            "parent": _text(node, "PARENT"),
            "guid": _text(node, "GUID"),
            "altered_on": _text(node, "ALTEREDON"),
            "closing_balance": _text(node, "CLOSINGBALANCE"),
        }
        item["fingerprint"] = _fingerprint(item)
        ledgers.append(item)
    return ledgers


def parse_stock_items(xml_text: str) -> list[dict[str, Any]]:
    root = parse_xml(xml_text)
    items = []
    for node in _iter_nodes(root, "STOCKITEM"):
        item = {
            "name": _text(node, "NAME"),
            "guid": _text(node, "GUID"),
            "parent": _text(node, "PARENT"),
            "base_units": _text(node, "BASEUNITS"),
            "altered_on": _text(node, "ALTEREDON"),
            "closing_balance": _text(node, "CLOSINGBALANCE"),
        }
        item["fingerprint"] = _fingerprint(item)
        items.append(item)
    return items


def parse_vouchers(xml_text: str) -> list[dict[str, Any]]:
    root = parse_xml(xml_text)
    vouchers = []

    for node in _iter_nodes(root, "VOUCHER"):
        voucher_type = node.attrib.get("VCHTYPE", "") or _text(node, "VOUCHERTYPENAME")
        amount = ""
        ledger_entries = node.findall("ALLLEDGERENTRIES.LIST") or node.findall("allledgerentries.list")
        if ledger_entries:
            amount = _text(ledger_entries[0], "AMOUNT")

        item = {
            "guid": _text(node, "GUID") or node.attrib.get("REMOTEID", ""),
            "voucher_type": voucher_type,
            "voucher_number": _text(node, "VOUCHERNUMBER"),
            "date": _text(node, "DATE"),
            "narration": _text(node, "NARRATION"),
            "party_ledger_name": _text(node, "PARTYLEDGERNAME"),
            "amount": amount,
            "altered_on": _text(node, "ALTEREDON"),
        }
        item["fingerprint"] = _fingerprint(item)
        vouchers.append(item)

    return vouchers


def parse_report_summary(xml_text: str) -> dict[str, Any]:
    root = parse_xml(xml_text)
    return {
        "raw_xml_length": len(xml_text),
        "extracted_at": datetime.utcnow().isoformat(),
        "line_error": _extract_line_error(root),
    }


def _extract_line_error(root: ET.Element) -> str:
    for tag in ("LINEERROR", "ERROR", "ERRORS"):
        node = root.find(f".//{tag}")
        if node is not None and node.text:
            return node.text.strip()
    return ""


def _fingerprint(payload: dict[str, Any]) -> str:
    normalized = "|".join(f"{key}={payload.get(key, '')}" for key in sorted(payload.keys()))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
