"""
SIZH CA - Masters Views
========================
CRUD for Ledgers, Items, and Rules.
Bulk upsert endpoint for Tally sync.
"""

from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q

from clients.models import ClientProfile
from .models import TallyLedger, TallyItem, Rule, LedgerGroup, LedgerTemplate, ClientLedger
from .serializers import (
    TallyLedgerSerializer,
    TallyLedgerListSerializer,
    TallyItemSerializer,
    TallyItemListSerializer,
    RuleSerializer,
    LedgerGroupSerializer,
    LedgerTemplateSerializer,
    ClientLedgerSerializer,
    ClientLedgerBulkSaveSerializer,
)


class ActiveClientMixin:
    """Scope all queries to the user's active client profile."""

    def get_active_client(self):
        active = self.request.user.active_client_profile
        if active:
            return active

        client_id = self.request.headers.get("X-Client-ID")
        if client_id:
            try:
                return ClientProfile.objects.get(id=client_id)
            except ClientProfile.DoesNotExist:
                return None

        return None


# ── Ledgers ──────────────────────────────────────────────────────────────────


class LedgerListView(ActiveClientMixin, generics.ListAPIView):
    serializer_class = TallyLedgerListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "alias", "group", "gstin"]
    ordering_fields = ["name", "group", "opening_balance", "synced_at"]

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return TallyLedger.objects.none()
        qs = TallyLedger.objects.filter(client_profile=client)
        # Optional group filter
        group = self.request.query_params.get("group")
        if group:
            qs = qs.filter(group__icontains=group)
        return qs


class LedgerDetailView(ActiveClientMixin, generics.RetrieveAPIView):
    serializer_class = TallyLedgerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return TallyLedger.objects.none()
        return TallyLedger.objects.filter(client_profile=client)


class BulkLedgerUpsertView(ActiveClientMixin, APIView):
    """Bulk upsert ledgers from Tally sync."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = self.get_active_client()
        if not client:
            return Response(
                {"error": "No active client selected"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ledgers_data = request.data.get("ledgers", [])
        if not ledgers_data:
            return Response(
                {"error": "No ledgers provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created, updated = 0, 0
        for item in ledgers_data:
            name = item.get("name", "").strip()
            if not name:
                continue
            obj, was_created = TallyLedger.objects.update_or_create(
                client_profile=client,
                name=name,
                defaults={
                    k: v
                    for k, v in item.items()
                    if k not in ("id", "client_profile", "name", "created_at")
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        return Response(
            {"created": created, "updated": updated, "total": created + updated},
            status=status.HTTP_200_OK,
        )


# ── Items ────────────────────────────────────────────────────────────────────


class ItemListView(ActiveClientMixin, generics.ListAPIView):
    serializer_class = TallyItemListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "alias", "group", "hsn_code"]
    ordering_fields = ["name", "group", "gst_rate", "synced_at"]

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return TallyItem.objects.none()
        return TallyItem.objects.filter(client_profile=client)


class ItemDetailView(ActiveClientMixin, generics.RetrieveAPIView):
    serializer_class = TallyItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return TallyItem.objects.none()
        return TallyItem.objects.filter(client_profile=client)


class BulkItemUpsertView(ActiveClientMixin, APIView):
    """Bulk upsert items from Tally sync."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = self.get_active_client()
        if not client:
            return Response(
                {"error": "No active client selected"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        items_data = request.data.get("items", [])
        if not items_data:
            return Response(
                {"error": "No items provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created, updated = 0, 0
        for item in items_data:
            name = item.get("name", "").strip()
            if not name:
                continue
            obj, was_created = TallyItem.objects.update_or_create(
                client_profile=client,
                name=name,
                defaults={
                    k: v
                    for k, v in item.items()
                    if k not in ("id", "client_profile", "name", "created_at")
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        return Response(
            {"created": created, "updated": updated, "total": created + updated},
            status=status.HTTP_200_OK,
        )


# ── Rules ────────────────────────────────────────────────────────────────────


class RuleListCreateView(ActiveClientMixin, generics.ListCreateAPIView):
    serializer_class = RuleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["description", "from_field", "to_field"]
    ordering_fields = ["priority", "description", "created_at"]

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return Rule.objects.none()
        qs = Rule.objects.filter(client_profile=client)
        rule_type = self.request.query_params.get("rule_type")
        if rule_type:
            qs = qs.filter(rule_type=rule_type)
        return qs.select_related("target_ledger")

    def perform_create(self, serializer):
        client = self.get_active_client()
        serializer.save(client_profile=client)


class RuleDetailView(ActiveClientMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return Rule.objects.none()
        return Rule.objects.filter(client_profile=client).select_related("target_ledger")


# ═══════════════════════════════════════════════════════════════════════════════
# SMART LEDGER MANAGEMENT VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

import logging
from .ledger_logic import get_default_ledgers, get_ledger_summary, INDUSTRY_TYPES, LEDGER_GROUPS as LEDGER_GROUPS_DATA

logger = logging.getLogger("masters")


class LedgerGroupListView(generics.ListAPIView):
    """List all standard Accounting Groups (Assets, Liabilities, Income, Expense)."""
    serializer_class = LedgerGroupSerializer
    permission_classes = [IsAuthenticated]
    queryset = LedgerGroup.objects.all()


class LedgerTemplateSuggestView(APIView):
    """
    GET /api/masters/ledger-suggest/?industry_type=trading

    Returns the suggested default ledgers for a given industry type.
    Used during client creation: CA reviews → edits → saves.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        industry = request.query_params.get("industry_type", "").lower().strip()
        if industry and industry not in INDUSTRY_TYPES:
            return Response(
                {"error": f"Invalid industry_type. Choose from: {INDUSTRY_TYPES}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get logic-based suggestions
        suggestions = get_default_ledgers(industry)
        summary = get_ledger_summary(industry)

        # Resolve group name → LedgerGroup UUID for each suggestion
        group_map = {g.name: str(g.id) for g in LedgerGroup.objects.all()}
        for item in suggestions:
            item["group_id"] = group_map.get(item["group"])
            item["group_name"] = item["group"]
            item["is_custom"] = False

        logger.info(
            "[Ledger:Suggest] industry_type=%s | total_suggested=%s",
            industry or "all", len(suggestions),
        )

        return Response({
            "industry_type": industry,
            "suggestions": suggestions,
            "summary": summary,
            "available_industries": INDUSTRY_TYPES,
        })


class ClientLedgerListView(ActiveClientMixin, generics.ListAPIView):
    """List all ledgers assigned to the active client."""
    serializer_class = ClientLedgerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "sub_category"]
    ordering_fields = ["name", "group", "created_at"]

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return ClientLedger.objects.none()
        qs = ClientLedger.objects.filter(client_profile=client).select_related("group")
        # Optional group filter
        group = self.request.query_params.get("group")
        if group:
            qs = qs.filter(group__code=group)
        return qs


class ClientLedgerDetailView(ActiveClientMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve / update / delete a single client ledger."""
    serializer_class = ClientLedgerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return ClientLedger.objects.none()
        return ClientLedger.objects.filter(client_profile=client).select_related("group")


class ClientLedgerBulkSaveView(ActiveClientMixin, APIView):
    """
    POST /api/masters/client-ledgers/bulk-save/

    Bulk-save the final approved list of ledgers for the active client.
    This is the endpoint called after the CA reviews suggestions, edits
    names, removes unneeded ones, and adds custom ledgers.

    Payload: { "ledgers": [ { name, group, sub_category, is_custom }, ... ] }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = self.get_active_client()
        if not client:
            return Response(
                {"error": "No active client selected"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ser = ClientLedgerBulkSaveSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ledgers_data = ser.validated_data["ledgers"]

        if not ledgers_data:
            return Response(
                {"error": "No ledgers provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = 0
        skipped = 0
        for item in ledgers_data:
            name = item["name"].strip()
            if not name:
                skipped += 1
                continue

            # Resolve group UUID
            try:
                group = LedgerGroup.objects.get(id=item["group"])
            except LedgerGroup.DoesNotExist:
                skipped += 1
                continue

            _, was_created = ClientLedger.objects.update_or_create(
                client_profile=client,
                name=name,
                defaults={
                    "group": group,
                    "sub_category": item.get("sub_category", ""),
                    "is_custom": item.get("is_custom", False),
                    "opening_balance": item.get("opening_balance", 0),
                },
            )
            if was_created:
                created += 1

        logger.info(
            "[Ledger:BulkSave] client=%s | created=%s | skipped=%s | total_payload=%s",
            client, created, skipped, len(ledgers_data),
        )

        return Response({
            "status": "saved",
            "created": created,
            "updated": len(ledgers_data) - created - skipped,
            "skipped": skipped,
            "total_client_ledgers": ClientLedger.objects.filter(client_profile=client).count(),
        })
