"""
SIZH CA - Client Profile Serializers
======================================
"""

from rest_framework import serializers
from .models import ClientProfile


class ClientProfileSerializer(serializers.ModelSerializer):
    """Full serializer for ClientProfile CRUD."""

    # Accept a loose string (e.g. "04-01") and store as None
    # rather than failing DateField validation.
    financial_year_start = serializers.CharField(
        allow_blank=True, allow_null=True, required=False, default=None
    )

    def validate_financial_year_start(self, value):
        """Try ISO date parse; if invalid/empty, silently return None."""
        if not value:
            return None
        from datetime import datetime
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m-%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    class Meta:
        model = ClientProfile
        fields = [
            "id", "name", "trade_name", "pan", "gstin", "gst_type",
            "industry_type",
            "email", "phone", "address", "state", "pincode",
            "financial_year_start", "tally_company_name",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ClientProfileListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for dropdown lists and client table."""

    class Meta:
        model = ClientProfile
        fields = ["id", "name", "trade_name", "pan", "gstin", "phone", "industry_type"]


class ClientSearchSerializer(serializers.ModelSerializer):
    """Serializer for client search results."""

    class Meta:
        model = ClientProfile
        fields = ["id", "name", "trade_name", "pan", "gstin", "phone", "industry_type"]
