from django.contrib import admin
from .models import TallyLedger, TallyItem, Rule, LedgerGroup, LedgerTemplate, ClientLedger


@admin.register(TallyLedger)
class TallyLedgerAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "tax_category", "gstin", "state", "client_profile", "is_active", "synced_at")
    list_filter = ("tax_category", "is_active", "group")
    search_fields = ("name", "alias", "group", "gstin")
    readonly_fields = ("id", "synced_at", "created_at")


@admin.register(TallyItem)
class TallyItemAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "hsn_code", "gst_rate", "uom", "client_profile", "is_active", "synced_at")
    list_filter = ("is_active", "group")
    search_fields = ("name", "alias", "group", "hsn_code")
    readonly_fields = ("id", "synced_at", "created_at")


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("description", "rule_type", "from_field", "to_field", "target_ledger", "is_active", "priority")
    list_filter = ("rule_type", "is_active")
    search_fields = ("description", "from_field", "to_field")
    readonly_fields = ("id", "created_at", "updated_at")


# ─── Smart Ledger Management Admin ──────────────────────────────────────────


@admin.register(LedgerGroup)
class LedgerGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "nature", "display_order")
    ordering = ("display_order",)
    readonly_fields = ("id", "created_at")


@admin.register(LedgerTemplate)
class LedgerTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "industry_type", "sub_category", "is_active")
    list_filter = ("group", "industry_type", "is_active")
    search_fields = ("name", "sub_category")
    readonly_fields = ("id", "created_at")


@admin.register(ClientLedger)
class ClientLedgerAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "client_profile", "is_custom", "opening_balance", "is_active")
    list_filter = ("group", "is_custom", "is_active")
    search_fields = ("name", "client_profile__name")
    readonly_fields = ("id", "created_at", "updated_at")
