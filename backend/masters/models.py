"""
SIZH CA - Masters Models
=========================
Tally Ledgers, Stock Items, and Banking/Narration Rules
linked to each ClientProfile for multi-tenancy.
"""

import uuid
from django.conf import settings
from django.db import models


class TallyLedger(models.Model):
    """Ledger synced from Tally ERP/Prime."""

    class TaxCategory(models.TextChoices):
        GST = "gst", "GST"
        TDS = "tds", "TDS"
        TCS = "tcs", "TCS"
        NONE = "none", "None"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_profile = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.CASCADE,
        related_name="tally_ledgers",
    )
    name = models.CharField(max_length=255)
    alias = models.CharField(max_length=255, blank=True, default="")
    group = models.CharField(max_length=255, blank=True, default="")
    parent_group = models.CharField(max_length=255, blank=True, default="")
    tax_category = models.CharField(
        max_length=10, choices=TaxCategory.choices, default=TaxCategory.NONE
    )
    # GST Details
    gstin = models.CharField(max_length=15, blank=True, default="")
    gst_registration_type = models.CharField(max_length=50, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="India")
    # Financial
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    # Metadata
    tally_guid = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    synced_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sizh_tally_ledgers"
        unique_together = ("client_profile", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.group})"


class TallyItem(models.Model):
    """Stock Item synced from Tally ERP/Prime."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_profile = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.CASCADE,
        related_name="tally_items",
    )
    name = models.CharField(max_length=255)
    alias = models.CharField(max_length=255, blank=True, default="")
    group = models.CharField(max_length=255, blank=True, default="")
    category = models.CharField(max_length=255, blank=True, default="")
    uom = models.CharField(max_length=50, blank=True, default="")  # Unit of Measure
    hsn_code = models.CharField(max_length=20, blank=True, default="")
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    opening_stock = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    opening_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    # Metadata
    tally_guid = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    synced_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sizh_tally_items"
        unique_together = ("client_profile", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.group})"


# ═══════════════════════════════════════════════════════════════════════════════
# SMART LEDGER MANAGEMENT MODELS
# ═══════════════════════════════════════════════════════════════════════════════


class LedgerGroup(models.Model):
    """
    Standard Accounting Group: Assets, Liabilities, Income, Expense.
    These are system-defined and rarely customised.
    """

    class Nature(models.TextChoices):
        DEBIT = "debit", "Debit"
        CREDIT = "credit", "Credit"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    nature = models.CharField(max_length=10, choices=Nature.choices)
    description = models.TextField(blank=True, default="")
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sizh_ledger_groups"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class LedgerTemplate(models.Model):
    """
    Master library of default ledger names mapped to Industry Types.
    These are seeded once and used to suggest defaults during client creation.
    Records with industry_type='' are common (applicable to ALL industries).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    group = models.ForeignKey(
        LedgerGroup,
        on_delete=models.CASCADE,
        related_name="templates",
    )
    industry_type = models.CharField(
        max_length=20,
        blank=True,
        default="",
        db_index=True,
        help_text="Blank = common to all industries",
    )
    sub_category = models.CharField(
        max_length=100, blank=True, default="",
        help_text="Grouping label: GST, General Expenses, Parties, etc.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sizh_ledger_templates"
        unique_together = ("name", "industry_type")
        ordering = ["group", "name"]

    def __str__(self):
        ind = self.industry_type or "common"
        return f"{self.name} [{ind}] → {self.group.name}"


class ClientLedger(models.Model):
    """
    Actual ledger assigned to a specific Client.
    Seeded from LedgerTemplate suggestions, but CA can add custom ones.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_profile = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.CASCADE,
        related_name="client_ledgers",
    )
    name = models.CharField(max_length=255)
    group = models.ForeignKey(
        LedgerGroup,
        on_delete=models.CASCADE,
        related_name="client_ledgers",
    )
    sub_category = models.CharField(max_length=100, blank=True, default="")
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_custom = models.BooleanField(
        default=False,
        help_text="True if manually added by the CA (not from template)",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sizh_client_ledgers"
        unique_together = ("client_profile", "name")
        ordering = ["group", "name"]

    def __str__(self):
        tag = " [custom]" if self.is_custom else ""
        return f"{self.name} ({self.group.name}){tag}"


class Rule(models.Model):
    """Auto-categorization rule for banking narrations / vendor matching."""

    class RuleType(models.TextChoices):
        PAYMENT = "payment", "Payment"
        RECEIPT = "receipt", "Receipt"
        CONTRA = "contra", "Contra"
        JOURNAL = "journal", "Journal"
        SALES = "sales", "Sales"
        PURCHASE = "purchase", "Purchase"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_profile = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.CASCADE,
        related_name="rules",
    )
    description = models.CharField(
        max_length=500,
        help_text="Keyword/narration pattern to match (e.g. 'Salary', 'NEFT-ABC Corp')",
    )
    rule_type = models.CharField(
        max_length=20, choices=RuleType.choices, default=RuleType.PAYMENT
    )
    from_field = models.CharField(
        max_length=255, blank=True, default="",
        help_text="Source field value / from account",
    )
    to_field = models.CharField(
        max_length=255, blank=True, default="",
        help_text="Destination field value / to account",
    )
    target_ledger = models.ForeignKey(
        TallyLedger,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rules",
        help_text="Tally Ledger to auto-assign when this rule matches",
    )
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Higher priority rules match first")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sizh_rules"
        ordering = ["-priority", "description"]

    def __str__(self):
        return f"{self.description} → {self.target_ledger or 'No Ledger'}"
