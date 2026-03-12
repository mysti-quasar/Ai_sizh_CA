"""
SIZH CA - Transaction Serializers
"""

from rest_framework import serializers
from .models import UploadJob, TransactionRow, TallyVoucher


class UploadJobSerializer(serializers.ModelSerializer):
    row_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = UploadJob
        fields = [
            "id", "voucher_type", "bank_account", "file",
            "original_filename", "file_type", "status",
            "source_headers", "field_mapping",
            "detected_document_type", "row_count",
            "error_message", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "client_profile", "uploaded_by", "original_filename",
            "file_type", "status", "source_headers", "row_count",
            "detected_document_type", "error_message",
            "created_at", "updated_at",
        ]


class UploadJobListSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadJob
        fields = [
            "id", "voucher_type", "bank_account",
            "original_filename", "file_type", "status",
            "detected_document_type", "row_count", "created_at",
        ]


class TransactionRowSerializer(serializers.ModelSerializer):
    assigned_ledger_name = serializers.CharField(
        source="assigned_ledger.name", read_only=True, default=None
    )

    class Meta:
        model = TransactionRow
        fields = [
            "id", "row_number", "raw_data",
            "date", "voucher_type", "voucher_number",
            "description", "narration", "reference",
            "party_name", "invoice_no",
            "debit", "credit", "amount",
            "gst_rate", "cgst", "sgst", "igst",
            "taxable_amount", "place_of_supply", "hsn_code",
            "assigned_ledger", "assigned_ledger_name",
            "ledger_name", "ledger_source",
            "extra_data", "is_approved",
        ]
        read_only_fields = ["id", "row_number", "raw_data"]


class FieldMappingSerializer(serializers.Serializer):
    """Payload for Step 2: user maps source columns to target fields."""

    mapping = serializers.DictField(
        child=serializers.CharField(allow_blank=True),
        help_text="{ 'source_header': 'target_field' }",
    )


class LedgerAssignSerializer(serializers.Serializer):
    """Assign a ledger to one or more transaction rows."""

    row_ids = serializers.ListField(child=serializers.UUIDField())
    ledger_id = serializers.UUIDField()
    source = serializers.ChoiceField(
        choices=TransactionRow.LedgerSource.choices,
        default="manual",
    )


class TallyVoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = TallyVoucher
        fields = [
            "id", "voucher_type", "voucher_number", "date",
            "narration", "reference",
            "party_ledger_name", "amount", "is_debit",
            "gst_rate", "cgst", "sgst", "igst",
            "taxable_amount", "place_of_supply",
            "hsn_code", "invoice_no",
            "counter_ledger_name", "counter_amount",
            "sync_status", "tally_master_id", "sync_error", "synced_at",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "tally_master_id", "sync_error", "synced_at",
            "created_at", "updated_at",
        ]


class TallyVoucherListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TallyVoucher
        fields = [
            "id", "voucher_type", "voucher_number", "date",
            "party_ledger_name", "amount", "sync_status",
            "created_at",
        ]
