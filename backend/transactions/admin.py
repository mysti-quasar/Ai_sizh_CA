from django.contrib import admin
from .models import UploadJob, TransactionRow, TallyVoucher


@admin.register(UploadJob)
class UploadJobAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "voucher_type", "status", "row_count", "detected_document_type", "client_profile", "created_at")
    list_filter = ("voucher_type", "status", "created_at")
    search_fields = ("original_filename", "bank_account")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(TransactionRow)
class TransactionRowAdmin(admin.ModelAdmin):
    list_display = ("row_number", "date", "voucher_type", "description", "amount", "assigned_ledger", "ledger_name", "ledger_source", "is_approved")
    list_filter = ("ledger_source", "is_approved", "voucher_type")
    search_fields = ("description", "reference", "party_name", "narration")
    readonly_fields = ("id",)


@admin.register(TallyVoucher)
class TallyVoucherAdmin(admin.ModelAdmin):
    list_display = ("voucher_type", "voucher_number", "date", "party_ledger_name", "amount", "sync_status", "client_profile")
    list_filter = ("voucher_type", "sync_status", "date")
    search_fields = ("party_ledger_name", "counter_ledger_name", "narration", "voucher_number")
    readonly_fields = ("id", "created_at", "updated_at", "tally_xml")
