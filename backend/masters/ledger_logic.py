"""
SIZH CA - Smart Ledger Suggestion Logic
=========================================
Maps Industry Types → Default Ledgers grouped under standard Accounting Groups.

This module contains:
- LEDGER_GROUPS: The 4 standard accounting group categories
- COMMON_LEDGERS: Ledgers applicable to ALL industries
- INDUSTRY_LEDGERS: Industry-specific additions (Trading, Service, E-commerce, Mfg)
- get_default_ledgers(industry_type): Returns the full suggested list

Usage:
    from masters.ledger_logic import get_default_ledgers
    suggestions = get_default_ledgers("trading")
    # → [{"name": "Bank Account", "group": "Assets", ...}, ...]
"""

from typing import Optional

# ─── Standard Accounting Groups ──────────────────────────────────────────────

LEDGER_GROUPS = [
    {"name": "Assets", "code": "assets", "nature": "debit"},
    {"name": "Liabilities", "code": "liabilities", "nature": "credit"},
    {"name": "Income", "code": "income", "nature": "credit"},
    {"name": "Expense", "code": "expense", "nature": "debit"},
]

# ─── Common Ledgers (Applicable to ALL Industries) ──────────────────────────

COMMON_LEDGERS = [
    # Bank Related
    {"name": "Bank Account", "group": "Assets", "sub_category": "Bank Related"},
    {"name": "Cash", "group": "Assets", "sub_category": "Bank Related"},
    {"name": "Bank Charges", "group": "Expense", "sub_category": "Bank Related"},
    {"name": "Interest Income", "group": "Income", "sub_category": "Bank Related"},

    # GST Ledgers
    {"name": "Input CGST", "group": "Assets", "sub_category": "GST"},
    {"name": "Input SGST", "group": "Assets", "sub_category": "GST"},
    {"name": "Input IGST", "group": "Assets", "sub_category": "GST"},
    {"name": "Output CGST", "group": "Liabilities", "sub_category": "GST"},
    {"name": "Output SGST", "group": "Liabilities", "sub_category": "GST"},
    {"name": "Output IGST", "group": "Liabilities", "sub_category": "GST"},
    {"name": "GST Payable", "group": "Liabilities", "sub_category": "GST"},

    # Expenses
    {"name": "Office Expenses", "group": "Expense", "sub_category": "General Expenses"},
    {"name": "Electricity Expenses", "group": "Expense", "sub_category": "General Expenses"},
    {"name": "Internet Charges", "group": "Expense", "sub_category": "General Expenses"},
    {"name": "Telephone Expenses", "group": "Expense", "sub_category": "General Expenses"},
    {"name": "Salary", "group": "Expense", "sub_category": "General Expenses"},
    {"name": "Rent", "group": "Expense", "sub_category": "General Expenses"},
    {"name": "Printing & Stationery", "group": "Expense", "sub_category": "General Expenses"},
    {"name": "Travel Expenses", "group": "Expense", "sub_category": "General Expenses"},
    {"name": "Repair & Maintenance", "group": "Expense", "sub_category": "General Expenses"},
    {"name": "Professional Fees", "group": "Expense", "sub_category": "General Expenses"},

    # Purchase/Sales
    {"name": "Purchase Account", "group": "Expense", "sub_category": "Purchase/Sales"},
    {"name": "Sales Account", "group": "Income", "sub_category": "Purchase/Sales"},
    {"name": "Sales Return", "group": "Income", "sub_category": "Purchase/Sales"},
    {"name": "Purchase Return", "group": "Expense", "sub_category": "Purchase/Sales"},

    # Parties
    {"name": "Sundry Debtors", "group": "Assets", "sub_category": "Parties"},
    {"name": "Sundry Creditors", "group": "Liabilities", "sub_category": "Parties"},

    # Statutory
    {"name": "TDS Payable", "group": "Liabilities", "sub_category": "Statutory"},
    {"name": "TDS Receivable", "group": "Assets", "sub_category": "Statutory"},
    {"name": "Provident Fund", "group": "Liabilities", "sub_category": "Statutory"},
    {"name": "ESI Payable", "group": "Liabilities", "sub_category": "Statutory"},

    # Adjustments
    {"name": "Round Off", "group": "Expense", "sub_category": "Adjustments"},
    {"name": "Discount Allowed", "group": "Expense", "sub_category": "Adjustments"},
    {"name": "Discount Received", "group": "Income", "sub_category": "Adjustments"},
    {"name": "Suspense Account", "group": "Assets", "sub_category": "Adjustments"},
]

# ─── Industry-Specific Additions ────────────────────────────────────────────

INDUSTRY_LEDGERS = {
    "trading": [
        {"name": "Freight", "group": "Expense", "sub_category": "Industry Specific"},
        {"name": "Packing Charges", "group": "Expense", "sub_category": "Industry Specific"},
    ],
    "service": [
        {"name": "Service Income", "group": "Income", "sub_category": "Industry Specific"},
        {"name": "Consulting Fees", "group": "Income", "sub_category": "Industry Specific"},
    ],
    "ecommerce": [
        {"name": "Amazon Commission", "group": "Expense", "sub_category": "Industry Specific"},
        {"name": "Flipkart Commission", "group": "Expense", "sub_category": "Industry Specific"},
        {"name": "Payment Gateway Charges", "group": "Expense", "sub_category": "Industry Specific"},
        {"name": "Shipping Charges", "group": "Expense", "sub_category": "Industry Specific"},
    ],
    "manufacturing": [
        {"name": "Raw Material Purchase", "group": "Expense", "sub_category": "Industry Specific"},
        {"name": "Work in Progress", "group": "Assets", "sub_category": "Industry Specific"},
        {"name": "Production Cost", "group": "Expense", "sub_category": "Industry Specific"},
        {"name": "Factory Expense", "group": "Expense", "sub_category": "Industry Specific"},
    ],
}

# Valid industry types (used for validation)
INDUSTRY_TYPES = list(INDUSTRY_LEDGERS.keys())


def get_default_ledgers(industry_type: str) -> list[dict]:
    """
    Return a combined list of Common + Industry-specific default ledgers.

    Args:
        industry_type: One of 'trading', 'service', 'ecommerce', 'manufacturing'.
                       If the type is unknown, only common ledgers are returned.

    Returns:
        List of dicts, each with keys: name, group, sub_category
    """
    industry_key = industry_type.lower().strip()

    # Start with common ledgers (deep copy to avoid mutation)
    result = [dict(item) for item in COMMON_LEDGERS]

    # Add industry-specific ledgers
    extras = INDUSTRY_LEDGERS.get(industry_key, [])
    for item in extras:
        result.append(dict(item))

    return result


def get_ledger_summary(industry_type: str) -> dict:
    """
    Return a summary of suggested ledgers for a given industry type.

    Returns:
        {
            "industry_type": "trading",
            "total_count": 38,
            "by_group": {"Assets": 8, "Liabilities": 7, ...},
            "industry_specific_count": 2,
        }
    """
    ledgers = get_default_ledgers(industry_type)
    by_group: dict[str, int] = {}
    for ledger in ledgers:
        g = ledger["group"]
        by_group[g] = by_group.get(g, 0) + 1

    industry_key = industry_type.lower().strip()
    industry_count = len(INDUSTRY_LEDGERS.get(industry_key, []))

    return {
        "industry_type": industry_key,
        "total_count": len(ledgers),
        "by_group": by_group,
        "industry_specific_count": industry_count,
    }
