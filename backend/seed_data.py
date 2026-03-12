#!/usr/bin/env python
"""
SIZH CA - Seed Data Script
============================
Seeds the database with:
1. LedgerGroups (Assets, Liabilities, Income, Expense)
2. LedgerTemplates from the master library (common + industry-specific)
3. 10 realistic Indian mock Clients (mix of Trading, Service, E-commerce, Mfg)
4. ClientLedgers for each client (auto-assigned from templates + custom additions)

Usage:
    cd backend/
    python manage.py shell < seed_data.py
    # OR
    python seed_data.py   (with Django settings configured)
"""

import os
import sys
import django

# ── Django Setup ─────────────────────────────────────────────────────────────
# Ensure Django settings are loaded when running standalone
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Add the backend directory to path if running standalone
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

django.setup()

# ── Imports (must be after django.setup) ─────────────────────────────────────
from accounts.models import User
from clients.models import ClientProfile
from masters.models import LedgerGroup, LedgerTemplate, ClientLedger
from masters.ledger_logic import (
    LEDGER_GROUPS,
    COMMON_LEDGERS,
    INDUSTRY_LEDGERS,
    get_default_ledgers,
)


def seed_ledger_groups():
    """Insert the 4 standard accounting groups."""
    print("\n━━━ Step 1: Seeding Ledger Groups ━━━")
    created_count = 0
    for i, group in enumerate(LEDGER_GROUPS):
        obj, created = LedgerGroup.objects.update_or_create(
            code=group["code"],
            defaults={
                "name": group["name"],
                "nature": group["nature"],
                "display_order": i + 1,
            },
        )
        status = "CREATED" if created else "EXISTS"
        print(f"  [{status}] {obj.name} ({obj.code}, {obj.nature})")
        if created:
            created_count += 1
    print(f"  → {created_count} groups created, {len(LEDGER_GROUPS) - created_count} already existed")
    return created_count


def seed_ledger_templates():
    """Insert ALL master ledger templates (common + industry-specific)."""
    print("\n━━━ Step 2: Seeding Ledger Templates ━━━")

    # Build group name → LedgerGroup lookup
    group_map = {g.name: g for g in LedgerGroup.objects.all()}

    created_count = 0
    errors = 0

    # Common ledgers (industry_type = "")
    print("  ── Common Ledgers (all industries) ──")
    for item in COMMON_LEDGERS:
        group = group_map.get(item["group"])
        if not group:
            print(f"  [ERROR] Group '{item['group']}' not found for '{item['name']}'")
            errors += 1
            continue
        obj, created = LedgerTemplate.objects.update_or_create(
            name=item["name"],
            industry_type="",
            defaults={
                "group": group,
                "sub_category": item.get("sub_category", ""),
            },
        )
        if created:
            created_count += 1

    print(f"  → {len(COMMON_LEDGERS)} common templates processed")

    # Industry-specific ledgers
    for industry, ledgers in INDUSTRY_LEDGERS.items():
        print(f"  ── {industry.title()} Specific ──")
        for item in ledgers:
            group = group_map.get(item["group"])
            if not group:
                print(f"  [ERROR] Group '{item['group']}' not found for '{item['name']}'")
                errors += 1
                continue
            obj, created = LedgerTemplate.objects.update_or_create(
                name=item["name"],
                industry_type=industry,
                defaults={
                    "group": group,
                    "sub_category": item.get("sub_category", ""),
                },
            )
            if created:
                created_count += 1
        print(f"  → {len(ledgers)} {industry} templates processed")

    total = LedgerTemplate.objects.count()
    print(f"\n  ✓ Total templates in DB: {total} | Created: {created_count} | Errors: {errors}")
    return created_count


# ── 10 Realistic Indian Mock Clients ────────────────────────────────────────

MOCK_CLIENTS = [
    {
        "name": "Sharma Trading Co.",
        "trade_name": "Sharma Enterprises",
        "pan": "AABCS1234A",
        "gstin": "07AABCS1234A1ZP",
        "gst_type": "regular",
        "industry_type": "trading",
        "email": "accounts@sharmatrading.in",
        "phone": "9811012345",
        "address": "12, Chandni Chowk, Old Delhi",
        "state": "Delhi",
        "pincode": "110006",
    },
    {
        "name": "Patel Tech Solutions Pvt Ltd",
        "trade_name": "Patel Tech",
        "pan": "AADCP5678B",
        "gstin": "24AADCP5678B1ZN",
        "gst_type": "regular",
        "industry_type": "service",
        "email": "info@pateltech.com",
        "phone": "7926543210",
        "address": "305, SG Highway, Ahmedabad",
        "state": "Gujarat",
        "pincode": "380054",
    },
    {
        "name": "Mumbai Mart E-Retail",
        "trade_name": "MumbaiMart",
        "pan": "AAFCM9012C",
        "gstin": "27AAFCM9012C1ZQ",
        "gst_type": "regular",
        "industry_type": "ecommerce",
        "email": "seller@mumbaimart.co.in",
        "phone": "9820123456",
        "address": "Unit 7, Andheri East Industrial Area, Mumbai",
        "state": "Maharashtra",
        "pincode": "400069",
    },
    {
        "name": "Jain Manufacturing Works",
        "trade_name": "Jain MFG",
        "pan": "AAJPJ3456D",
        "gstin": "33AAJPJ3456D1ZR",
        "gst_type": "regular",
        "industry_type": "manufacturing",
        "email": "factory@jainmfg.co.in",
        "phone": "4428765432",
        "address": "Plot 42, SIDCO Industrial Estate, Chennai",
        "state": "Tamil Nadu",
        "pincode": "600032",
    },
    {
        "name": "Kumar Garments Wholesale",
        "trade_name": "Kumar Garments",
        "pan": "AAGPK7890E",
        "gstin": "29AAGPK7890E1ZS",
        "gst_type": "regular",
        "industry_type": "trading",
        "email": "wholesale@kumargarments.in",
        "phone": "8028741596",
        "address": "22, Commercial Street, Bangalore",
        "state": "Karnataka",
        "pincode": "560001",
    },
    {
        "name": "Reddy & Associates CA",
        "trade_name": "Reddy Associates",
        "pan": "AASPR1234F",
        "gstin": "36AASPR1234F1ZT",
        "gst_type": "regular",
        "industry_type": "service",
        "email": "ca@reddyassociates.in",
        "phone": "4023456789",
        "address": "6th Floor, Banjara Hills, Hyderabad",
        "state": "Telangana",
        "pincode": "500034",
    },
    {
        "name": "Gupta Steel Industries",
        "trade_name": "Gupta Steel",
        "pan": "AADPG5678G",
        "gstin": "09AADPG5678G1ZU",
        "gst_type": "regular",
        "industry_type": "manufacturing",
        "email": "plant@guptasteel.co.in",
        "phone": "5122345678",
        "address": "D-12, Phase II, Noida Industrial Area",
        "state": "Uttar Pradesh",
        "pincode": "201301",
    },
    {
        "name": "Bhatia Online Store",
        "trade_name": "BhatiaKart",
        "pan": "AAKPB9012H",
        "gstin": "06AAKPB9012H1ZV",
        "gst_type": "regular",
        "industry_type": "ecommerce",
        "email": "admin@bhatiakart.com",
        "phone": "1724578901",
        "address": "SCO 145, Sector 17, Chandigarh",
        "state": "Haryana",
        "pincode": "160017",
    },
    {
        "name": "Singh Transport & Logistics",
        "trade_name": "Singh Logistics",
        "pan": "ACLPS3456J",
        "gstin": "03ACLPS3456J1ZW",
        "gst_type": "regular",
        "industry_type": "service",
        "email": "ops@singhlogistics.in",
        "phone": "1812345678",
        "address": "GT Road, Ludhiana, Punjab",
        "state": "Punjab",
        "pincode": "141001",
    },
    {
        "name": "Mehta Spices & Commodities",
        "trade_name": "Mehta Spices",
        "pan": "ABQPM7890K",
        "gstin": "32ABQPM7890K1ZX",
        "gst_type": "composition",
        "industry_type": "trading",
        "email": "trade@mehtaspices.in",
        "phone": "4842345678",
        "address": "Jew Town Road, Mattancherry, Kochi",
        "state": "Kerala",
        "pincode": "682002",
    },
]

# Custom ledgers to add to specific clients (index → list of custom ledgers)
CUSTOM_LEDGERS = {
    0: [  # Sharma Trading Co.
        {"name": "Director Salary", "group_name": "Expense", "sub_category": "Custom"},
    ],
    2: [  # Mumbai Mart E-Retail
        {"name": "Loan from HDFC Bank", "group_name": "Liabilities", "sub_category": "Custom"},
        {"name": "Meesho Commission", "group_name": "Expense", "sub_category": "Custom"},
    ],
    3: [  # Jain Manufacturing Works
        {"name": "Machine Depreciation", "group_name": "Expense", "sub_category": "Custom"},
    ],
    5: [  # Reddy & Associates CA
        {"name": "Article Clerk Stipend", "group_name": "Expense", "sub_category": "Custom"},
        {"name": "Loan from ICICI Bank", "group_name": "Liabilities", "sub_category": "Custom"},
    ],
    6: [  # Gupta Steel Industries
        {"name": "Scrap Sales", "group_name": "Income", "sub_category": "Custom"},
    ],
    9: [  # Mehta Spices
        {"name": "Cold Storage Charges", "group_name": "Expense", "sub_category": "Custom"},
    ],
}


def seed_clients_and_ledgers():
    """Create 10 mock clients and assign ledgers."""
    print("\n━━━ Step 3: Seeding 10 Mock Clients ━━━")

    # Get or create a CA user to own these clients
    user, user_created = User.objects.get_or_create(
        email="demo_ca@sizh.in",
        defaults={
            "username": "demo_ca",
            "first_name": "Demo",
            "last_name": "CA",
            "firm_name": "SIZH Demo CA Firm",
            "is_verified": True,
        },
    )
    if user_created:
        user.set_password("demo@1234")
        user.save()
        print(f"  [CREATED] Demo CA user: {user.email} (password: demo@1234)")
    else:
        print(f"  [EXISTS] Demo CA user: {user.email}")

    group_map = {g.name: g for g in LedgerGroup.objects.all()}

    for idx, client_data in enumerate(MOCK_CLIENTS):
        industry = client_data["industry_type"]

        # Create client
        client, client_created = ClientProfile.objects.update_or_create(
            user=user,
            gstin=client_data["gstin"],
            defaults={
                "name": client_data["name"],
                "trade_name": client_data.get("trade_name", ""),
                "pan": client_data.get("pan", ""),
                "gst_type": client_data.get("gst_type", "regular"),
                "industry_type": industry,
                "email": client_data.get("email", ""),
                "phone": client_data.get("phone", ""),
                "address": client_data.get("address", ""),
                "state": client_data.get("state", ""),
                "pincode": client_data.get("pincode", ""),
            },
        )
        status_tag = "CREATED" if client_created else "EXISTS"
        print(f"\n  [{status_tag}] {idx + 1}. {client.name} ({industry})")

        # Assign default ledgers based on industry
        default_ledgers = get_default_ledgers(industry)
        ledger_count = 0
        for item in default_ledgers:
            group = group_map.get(item["group"])
            if not group:
                continue
            _, created = ClientLedger.objects.get_or_create(
                client_profile=client,
                name=item["name"],
                defaults={
                    "group": group,
                    "sub_category": item.get("sub_category", ""),
                    "is_custom": False,
                },
            )
            if created:
                ledger_count += 1
        print(f"       → {ledger_count} default ledgers assigned ({len(default_ledgers)} total for {industry})")

        # Add custom ledgers if applicable
        custom_list = CUSTOM_LEDGERS.get(idx, [])
        for custom in custom_list:
            group = group_map.get(custom["group_name"])
            if not group:
                continue
            obj, created = ClientLedger.objects.get_or_create(
                client_profile=client,
                name=custom["name"],
                defaults={
                    "group": group,
                    "sub_category": custom.get("sub_category", "Custom"),
                    "is_custom": True,
                },
            )
            if created:
                print(f"       + Custom: {custom['name']} ({custom['group_name']})")

    # Set the first client as the active one
    first_client = ClientProfile.objects.filter(user=user).first()
    if first_client:
        user.active_client_profile = first_client
        user.save(update_fields=["active_client_profile"])
        print(f"\n  Active client set to: {first_client.name}")


def print_summary():
    """Print a final summary of all seeded data."""
    print("\n" + "═" * 60)
    print("  SEED SUMMARY")
    print("═" * 60)
    print(f"  Ledger Groups:      {LedgerGroup.objects.count()}")
    print(f"  Ledger Templates:   {LedgerTemplate.objects.count()}")
    print(f"  Client Profiles:    {ClientProfile.objects.count()}")
    print(f"  Client Ledgers:     {ClientLedger.objects.count()}")
    print(f"    ├─ From Templates: {ClientLedger.objects.filter(is_custom=False).count()}")
    print(f"    └─ Custom:         {ClientLedger.objects.filter(is_custom=True).count()}")
    print(f"  Users:              {User.objects.count()}")
    print("═" * 60)

    # Per-industry breakdown
    print("\n  Per-Industry Breakdown:")
    for ind in ["trading", "service", "ecommerce", "manufacturing"]:
        clients = ClientProfile.objects.filter(industry_type=ind)
        count = clients.count()
        ledger_avg = 0
        if count > 0:
            total_ledgers = sum(
                ClientLedger.objects.filter(client_profile=c).count() for c in clients
            )
            ledger_avg = total_ledgers / count
        print(f"    {ind.title():15} → {count} clients (avg {ledger_avg:.0f} ledgers each)")

    print("\n  ✅ Seed complete!")


# ── Main Execution ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════╗")
    print("║  SIZH CA — Smart Ledger Management Seed Script      ║")
    print("╚══════════════════════════════════════════════════════╝")

    seed_ledger_groups()
    seed_ledger_templates()
    seed_clients_and_ledgers()
    print_summary()
