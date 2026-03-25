from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from decouple import config
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from clients.models import ClientProfile
from masters.models import TallyItem, TallyLedger
from transactions.models import TallyVoucher


def _parse_amount(value: object) -> Decimal:
    if value in (None, ""):
        return Decimal("0.00")
    raw = str(value).replace(",", "").strip()
    if not raw:
        return Decimal("0.00")
    try:
        return Decimal(raw)
    except InvalidOperation:
        return Decimal("0.00")


def _parse_tally_date(value: str) -> datetime.date | None:
    if not value:
        return None
    text = value.strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


class ConnectorAuthMixin:
    def _authorize(self, request) -> tuple[bool, Response | None, ClientProfile | None]:
        expected_token = config("CONNECTOR_API_TOKEN", default="")
        auth = request.headers.get("Authorization", "")
        company_id = request.headers.get("X-Company-ID", "")

        if not expected_token:
            return False, Response(
                {"error": "CONNECTOR_API_TOKEN is not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ), None

        if auth != f"Bearer {expected_token}":
            return False, Response(
                {"error": "Invalid connector token"},
                status=status.HTTP_401_UNAUTHORIZED,
            ), None

        if not company_id:
            return False, Response(
                {"error": "X-Company-ID header is required"},
                status=status.HTTP_400_BAD_REQUEST,
            ), None

        try:
            client = ClientProfile.objects.get(id=company_id)
        except ClientProfile.DoesNotExist:
            return False, Response(
                {"error": "Client not found for X-Company-ID"},
                status=status.HTTP_404_NOT_FOUND,
            ), None

        return True, None, client


class ConnectorLedgerSyncView(ConnectorAuthMixin, APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        ok, error_response, client = self._authorize(request)
        if not ok:
            return error_response

        records = request.data.get("records", [])
        if not isinstance(records, list):
            return Response({"error": "records must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        created = 0
        updated = 0
        for item in records:
            name = str(item.get("name", "")).strip()
            if not name:
                continue

            defaults = {
                "group": str(item.get("parent", ""))[:255],
                "parent_group": str(item.get("parent", ""))[:255],
                "closing_balance": _parse_amount(item.get("closing_balance")),
                "tally_guid": str(item.get("guid", ""))[:255],
                "is_active": True,
            }

            _, was_created = TallyLedger.objects.update_or_create(
                client_profile=client,
                name=name,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        return Response({"status": "ok", "created": created, "updated": updated})


class ConnectorStockItemSyncView(ConnectorAuthMixin, APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        ok, error_response, client = self._authorize(request)
        if not ok:
            return error_response

        records = request.data.get("records", [])
        if not isinstance(records, list):
            return Response({"error": "records must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        created = 0
        updated = 0
        for item in records:
            name = str(item.get("name", "")).strip()
            if not name:
                continue

            defaults = {
                "group": str(item.get("parent", ""))[:255],
                "uom": str(item.get("base_units", ""))[:50],
                "opening_stock": _parse_amount(item.get("closing_balance")),
                "opening_value": Decimal("0.00"),
                "tally_guid": str(item.get("guid", ""))[:255],
                "is_active": True,
            }

            _, was_created = TallyItem.objects.update_or_create(
                client_profile=client,
                name=name,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        return Response({"status": "ok", "created": created, "updated": updated})


class ConnectorVoucherSyncView(ConnectorAuthMixin, APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        ok, error_response, client = self._authorize(request)
        if not ok:
            return error_response

        records = request.data.get("records", [])
        if not isinstance(records, list):
            return Response({"error": "records must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        created = 0
        updated = 0
        for item in records:
            voucher_number = str(item.get("voucher_number", "")).strip()
            voucher_type = str(item.get("voucher_type", "Journal")).strip() or "Journal"
            tx_date = _parse_tally_date(str(item.get("date", "")))
            if not tx_date:
                continue

            amount = _parse_amount(item.get("amount"))
            party_name = str(item.get("party_ledger_name", "")).strip() or "Unknown Party"

            defaults = {
                "narration": str(item.get("narration", "")),
                "party_ledger_name": party_name[:255],
                "amount": abs(amount),
                "is_debit": amount >= 0,
                "counter_ledger_name": "",
                "counter_amount": abs(amount),
                "reference": str(item.get("guid", ""))[:255],
                "sync_status": TallyVoucher.SyncStatus.ACK,
                "tally_master_id": str(item.get("guid", ""))[:255],
            }

            _, was_created = TallyVoucher.objects.update_or_create(
                client_profile=client,
                voucher_type=voucher_type,
                voucher_number=voucher_number,
                date=tx_date,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        return Response({"status": "ok", "created": created, "updated": updated})
