"""
SIZH CA - Transaction Models
==============================
Upload jobs, parsed transaction rows, Tally-standard voucher entries,
field mappings, and ledger assignments for the bulk-upload pipeline.
"""

import uuid
from django.conf import settings
from django.db import models


def upload_file_path(instance, filename):
    return f"uploads/{instance.client_profile_id}/{instance.id}/{filename}"


class UploadJob(models.Model):
    """A single bulk-upload session (one file per job)."""

    class VoucherType(models.TextChoices):
        BANKING = "banking", "Banking"
        SALES = "sales", "Sales"
        PURCHASE = "purchase", "Purchase"
        SALES_RETURN = "sales_return", "Sales Return"
        PURCHASE_RETURN = "purchase_return", "Purchase Return"
        JOURNAL = "journal", "Journal"
        LEDGER = "ledger", "Ledger"
        ITEMS = "items", "Items"

    class JobStatus(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PARSING = "parsing", "Parsing"
        PARSED = "parsed", "Parsed"
        OCR_PROCESSING = "ocr_processing", "OCR Processing"
        OCR_DONE = "ocr_done", "OCR Done"
        MAPPING = "mapping", "Field Mapping"
        MAPPED = "mapped", "Mapped"
        AI_PROCESSING = "ai_processing", "AI Processing"
        READY = "ready", "Ready for Review"
        APPROVED = "approved", "Approved"
        SENT_TO_TALLY = "sent_to_tally", "Sent to Tally"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_profile = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.CASCADE,
        related_name="upload_jobs",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="upload_jobs",
    )
    voucher_type = models.CharField(max_length=20, choices=VoucherType.choices)
    bank_account = models.CharField(
        max_length=255, blank=True, default="",
        help_text="Bank ledger name (for banking voucher type)",
    )
    file = models.FileField(upload_to=upload_file_path)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, blank=True, default="")
    status = models.CharField(
        max_length=20, choices=JobStatus.choices, default=JobStatus.UPLOADED
    )
    # Parsed column headers from the file
    source_headers = models.JSONField(null=True, blank=True)
    # User-defined field mapping: { "source_col": "target_field" }
    field_mapping = models.JSONField(null=True, blank=True)
    # Gemini-detected document type (may differ from user selection)
    detected_document_type = models.CharField(max_length=30, blank=True, default="")
    row_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    # Gemini extraction metadata
    gemini_raw_response = models.TextField(
        blank=True, default="",
        help_text="Raw JSON string returned by Gemini for audit trail",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sizh_upload_jobs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.voucher_type} - {self.original_filename} ({self.status})"


class TransactionRow(models.Model):
    """A single parsed row from an uploaded file."""

    class LedgerSource(models.TextChoices):
        MANUAL = "manual", "Manual"
        RULE = "rule", "Rule"
        AI = "ai", "AI Suggested"
        GEMINI = "gemini", "Gemini Extracted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        UploadJob, on_delete=models.CASCADE, related_name="rows"
    )
    row_number = models.IntegerField()
    # Raw data from the file (all columns as JSON)
    raw_data = models.JSONField(default=dict)
    # Mapped/normalized fields (mirror Tally voucher fields)
    date = models.DateField(null=True, blank=True)
    voucher_type = models.CharField(
        max_length=30, blank=True, default="",
        help_text="Tally voucher type: Payment, Receipt, Contra, Journal, Sales, Purchase, Credit Note, Debit Note",
    )
    voucher_number = models.CharField(max_length=100, blank=True, default="")
    description = models.CharField(max_length=1000, blank=True, default="")
    narration = models.TextField(blank=True, default="", help_text="Full narration / particulars for Tally")
    reference = models.CharField(max_length=255, blank=True, default="")
    party_name = models.CharField(max_length=255, blank=True, default="")
    invoice_no = models.CharField(max_length=100, blank=True, default="")
    # Dr / Cr amounts
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    # GST fields (auto-calculated or Gemini-extracted)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cgst = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sgst = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    igst = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    taxable_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    place_of_supply = models.CharField(max_length=100, blank=True, default="")
    hsn_code = models.CharField(max_length=20, blank=True, default="")
    # Ledger assignment
    assigned_ledger = models.ForeignKey(
        "masters.TallyLedger",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transaction_rows",
    )
    ledger_name = models.CharField(
        max_length=255, blank=True, default="",
        help_text="Gemini-suggested ledger name (before matching to TallyLedger)",
    )
    ledger_source = models.CharField(
        max_length=10, choices=LedgerSource.choices, blank=True, default=""
    )
    # Additional mapped fields (invoice no, party name, etc.)
    extra_data = models.JSONField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        db_table = "sizh_transaction_rows"
        ordering = ["row_number"]

    def __str__(self):
        return f"Row {self.row_number}: {self.description[:50]}"


class TallyVoucher(models.Model):
    """
    Tally-standard voucher entry — the final output that gets pushed to Tally.
    This mirrors Tally's XML voucher structure exactly.
    One TallyVoucher is generated per approved TransactionRow / group.
    """

    class VType(models.TextChoices):
        PAYMENT = "Payment", "Payment"
        RECEIPT = "Receipt", "Receipt"
        CONTRA = "Contra", "Contra"
        JOURNAL = "Journal", "Journal"
        SALES = "Sales", "Sales"
        PURCHASE = "Purchase", "Purchase"
        CREDIT_NOTE = "Credit Note", "Credit Note"
        DEBIT_NOTE = "Debit Note", "Debit Note"

    class SyncStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SENDING = "sending", "Sending"
        SENT = "sent", "Sent to Tally"
        ACK = "acknowledged", "Acknowledged"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_profile = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.CASCADE,
        related_name="tally_vouchers",
    )
    source_job = models.ForeignKey(
        UploadJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vouchers",
    )
    source_row = models.ForeignKey(
        TransactionRow,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vouchers",
    )

    # ── Core Tally Voucher Fields ──
    voucher_type = models.CharField(max_length=30, choices=VType.choices)
    voucher_number = models.CharField(max_length=100, blank=True, default="")
    date = models.DateField()
    narration = models.TextField(blank=True, default="")
    reference = models.CharField(max_length=255, blank=True, default="")

    # Party / Ledger
    party_ledger_name = models.CharField(
        max_length=255,
        help_text="Tally 'Party A/c Name' – the main debit/credit ledger",
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_debit = models.BooleanField(
        help_text="True if this is a debit entry for party_ledger_name",
    )

    # ── GST / Tax Details ──
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cgst = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sgst = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    igst = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    taxable_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    place_of_supply = models.CharField(max_length=100, blank=True, default="")
    hsn_code = models.CharField(max_length=20, blank=True, default="")
    invoice_no = models.CharField(max_length=100, blank=True, default="")

    # ── Counter-entry ledger (the other side of the double-entry) ──
    counter_ledger_name = models.CharField(
        max_length=255, blank=True, default="",
        help_text="Tally ledger for the opposite side (e.g. Bank A/c for payments)",
    )
    counter_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text="Amount for counter-entry (usually equals 'amount')",
    )

    # ── Sync state ──
    sync_status = models.CharField(
        max_length=15, choices=SyncStatus.choices, default=SyncStatus.PENDING
    )
    tally_master_id = models.CharField(
        max_length=255, blank=True, default="",
        help_text="GUID returned by Tally after successful import",
    )
    sync_error = models.TextField(blank=True, default="")
    synced_at = models.DateTimeField(null=True, blank=True)

    # ── Full Tally XML (cached for re-send) ──
    tally_xml = models.TextField(
        blank=True, default="",
        help_text="Complete Tally XML envelope for this voucher",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sizh_tally_vouchers"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["client_profile", "sync_status"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.voucher_type} #{self.voucher_number} – {self.party_ledger_name} ₹{self.amount}"
