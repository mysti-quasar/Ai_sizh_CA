"""
SIZH CA - Masters Serializers
"""

from rest_framework import serializers
from .models import TallyLedger, TallyItem, Rule, LedgerGroup, LedgerTemplate, ClientLedger


class TallyLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TallyLedger
        fields = "__all__"
        read_only_fields = ["id", "client_profile", "synced_at", "created_at"]


class TallyLedgerListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for dropdowns and table lists."""

    class Meta:
        model = TallyLedger
        fields = [
            "id", "name", "alias", "group", "parent_group",
            "tax_category", "gstin", "gst_registration_type",
            "state", "opening_balance", "closing_balance",
            "is_active", "synced_at",
        ]


class TallyItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TallyItem
        fields = "__all__"
        read_only_fields = ["id", "client_profile", "synced_at", "created_at"]


class TallyItemListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TallyItem
        fields = [
            "id", "name", "alias", "group", "category",
            "uom", "hsn_code", "gst_rate",
            "opening_stock", "opening_value",
            "is_active", "synced_at",
        ]


class BulkLedgerUpsertSerializer(serializers.Serializer):
    """Accepts a list of ledger objects for bulk upsert from Tally sync."""

    ledgers = TallyLedgerSerializer(many=True)


class BulkItemUpsertSerializer(serializers.Serializer):
    """Accepts a list of item objects for bulk upsert from Tally sync."""

    items = TallyItemSerializer(many=True)


class RuleSerializer(serializers.ModelSerializer):
    target_ledger_name = serializers.CharField(
        source="target_ledger.name", read_only=True, default=None
    )

    class Meta:
        model = Rule
        fields = [
            "id", "description", "rule_type", "from_field", "to_field",
            "target_ledger", "target_ledger_name",
            "is_active", "priority", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "client_profile", "created_at", "updated_at"]


# ═══════════════════════════════════════════════════════════════════════════════
# SMART LEDGER MANAGEMENT SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════════


class LedgerGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerGroup
        fields = ["id", "name", "code", "nature", "description", "display_order"]
        read_only_fields = ["id"]


class LedgerTemplateSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)
    group_code = serializers.CharField(source="group.code", read_only=True)

    class Meta:
        model = LedgerTemplate
        fields = [
            "id", "name", "group", "group_name", "group_code",
            "industry_type", "sub_category", "is_active",
        ]
        read_only_fields = ["id"]


class ClientLedgerSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)
    group_code = serializers.CharField(source="group.code", read_only=True)

    class Meta:
        model = ClientLedger
        fields = [
            "id", "name", "group", "group_name", "group_code",
            "sub_category", "opening_balance", "is_custom",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "client_profile", "created_at", "updated_at"]


class ClientLedgerBulkItemSerializer(serializers.Serializer):
    """Schema for a single ledger in the bulk-save payload."""
    name = serializers.CharField(max_length=255)
    group = serializers.UUIDField(help_text="LedgerGroup UUID")
    sub_category = serializers.CharField(max_length=100, required=False, default="")
    opening_balance = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False, default=0
    )
    is_custom = serializers.BooleanField(required=False, default=False)


class ClientLedgerBulkSaveSerializer(serializers.Serializer):
    """Payload for the Save-approved-ledgers endpoint."""
    ledgers = ClientLedgerBulkItemSerializer(many=True)
