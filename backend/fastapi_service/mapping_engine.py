"""
SIZH CA - 3-Layer Mapping Engine
==================================
Layer 1: Field Mapping – map source columns to target Tally fields
Layer 2: GST Mapping  – auto-calculate IGST vs CGST/SGST based on POS
Layer 3: Rule/AI Matching – match narrations to ledgers via saved rules
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation


# ── Target field definitions ─────────────────────────────────────────────────

TARGET_FIELDS = {
    "banking": ["date", "description", "reference", "debit", "credit", "amount"],
    "sales": ["date", "invoice_no", "party_name", "amount", "gst_rate", "place_of_supply"],
    "purchase": ["date", "invoice_no", "party_name", "amount", "gst_rate", "place_of_supply"],
    "sales_return": ["date", "invoice_no", "party_name", "amount", "gst_rate", "place_of_supply"],
    "purchase_return": ["date", "invoice_no", "party_name", "amount", "gst_rate", "place_of_supply"],
    "journal": ["date", "description", "debit", "credit", "reference"],
    "ledger": ["name", "group", "gstin", "state"],
    "items": ["name", "group", "hsn_code", "gst_rate", "uom"],
}


def get_target_fields(voucher_type: str) -> list:
    """Return the list of expected target fields for a voucher type."""
    return TARGET_FIELDS.get(voucher_type, TARGET_FIELDS["banking"])


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 1: FIELD MAPPING
# ═══════════════════════════════════════════════════════════════════════════════


def apply_field_mapping(
    rows: List[Dict[str, Any]],
    mapping: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Map source column names to target field names.
    mapping = { "source_column_name": "target_field_name" }
    Preserves unmapped columns in an 'extra_data' dict.
    """
    mapped_rows = []
    reverse_map = {src: tgt for src, tgt in mapping.items() if tgt}

    for i, row in enumerate(rows):
        mapped = {"_row_number": i + 1, "extra_data": {}}
        for col, val in row.items():
            target = reverse_map.get(col)
            if target:
                mapped[target] = val
            else:
                mapped["extra_data"][col] = val

        # Normalize numeric fields
        for field in ("debit", "credit", "amount", "gst_rate"):
            if field in mapped:
                mapped[field] = _to_decimal(mapped[field])

        # Calculate amount if not present but debit/credit are
        if "amount" not in mapped or not mapped["amount"]:
            debit = mapped.get("debit", 0) or 0
            credit = mapped.get("credit", 0) or 0
            mapped["amount"] = abs(float(debit)) + abs(float(credit))

        mapped_rows.append(mapped)

    return mapped_rows


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 2: GST MAPPING
# ═══════════════════════════════════════════════════════════════════════════════


# Indian state codes for GST
STATE_CODES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
    "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
    "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
    "16": "Tripura", "17": "Meghalaya", "18": "Assam",
    "19": "West Bengal", "20": "Jharkhand", "21": "Odisha",
    "22": "Chattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "26": "Dadra and Nagar Haveli", "27": "Maharashtra", "29": "Karnataka",
    "30": "Goa", "31": "Lakshadweep", "32": "Kerala",
    "33": "Tamil Nadu", "34": "Puducherry", "35": "Andaman and Nicobar Islands",
    "36": "Telangana", "37": "Andhra Pradesh",
}


def _extract_state_from_gstin(gstin: str) -> str:
    """Extract state from first 2 digits of GSTIN."""
    if gstin and len(gstin) >= 2:
        code = gstin[:2]
        return STATE_CODES.get(code, "")
    return ""


def apply_gst_mapping(
    rows: List[Dict[str, Any]],
    voucher_type: str,
    client_state: str = "",
) -> List[Dict[str, Any]]:
    """
    Auto-calculate GST split based on:
    - Place of Supply (POS) vs Client's state
    - If POS == Client state → CGST + SGST (equal split)
    - If POS != Client state → IGST (full)
    - Detect Input/Output based on voucher type
    """
    is_output = voucher_type in ("sales", "sales_return")
    is_input = voucher_type in ("purchase", "purchase_return")

    for row in rows:
        amount = float(row.get("amount", 0) or 0)
        gst_rate = float(row.get("gst_rate", 0) or 0)
        pos = str(row.get("place_of_supply", "")).strip()

        if not gst_rate or not amount:
            row.update({"cgst": 0, "sgst": 0, "igst": 0, "taxable_amount": amount})
            continue

        taxable = amount / (1 + gst_rate / 100)
        gst_amount = amount - taxable

        # Determine inter-state or intra-state
        is_interstate = False
        if pos and client_state:
            is_interstate = pos.lower().strip() != client_state.lower().strip()
        elif pos:
            is_interstate = True  # Default to IGST if client state unknown

        if is_interstate:
            row.update({
                "igst": round(gst_amount, 2),
                "cgst": 0,
                "sgst": 0,
            })
        else:
            half = round(gst_amount / 2, 2)
            row.update({
                "igst": 0,
                "cgst": half,
                "sgst": half,
            })

        row["taxable_amount"] = round(taxable, 2)
        row["gst_type"] = "output" if is_output else "input" if is_input else "na"

    return rows


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 3: RULE MATCHING
# ═══════════════════════════════════════════════════════════════════════════════


def apply_rule_matching(
    rows: List[Dict[str, Any]],
    rules: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Match transaction descriptions/narrations against saved rules.
    Rules are matched by keyword containment in the description field.
    Higher priority rules take precedence.
    """
    if not rules:
        return rows

    # Sort rules by priority descending
    sorted_rules = sorted(rules, key=lambda r: r.get("priority", 0), reverse=True)

    for row in rows:
        if row.get("assigned_ledger"):
            continue  # Already assigned, skip

        desc = str(row.get("description", "")).lower()
        ref = str(row.get("reference", "")).lower()

        for rule in sorted_rules:
            if not rule.get("is_active", True):
                continue

            keyword = str(rule.get("description", "")).lower().strip()
            if not keyword:
                continue

            # Check if keyword matches description or reference
            if keyword in desc or keyword in ref:
                row["assigned_ledger"] = rule.get("target_ledger")
                row["assigned_ledger_name"] = rule.get("target_ledger_name", "")
                row["ledger_source"] = "rule"
                row["matched_rule_id"] = rule.get("id")
                break

    return rows


# ── Utility ──────────────────────────────────────────────────────────────────


def _to_decimal(value) -> float:
    """Safely convert a value to float."""
    if value is None or value == "":
        return 0.0
    try:
        # Remove commas and currency symbols
        cleaned = str(value).replace(",", "").replace("₹", "").replace("$", "").strip()
        return float(cleaned)
    except (ValueError, InvalidOperation):
        return 0.0
