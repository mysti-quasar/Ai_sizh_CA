"""
SIZH CA - Transaction Views
=============================
Upload jobs, transaction rows, field mapping, ledger assignment,
Tally voucher generation and list.
"""

import logging

from rest_framework import generics, status, parsers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UploadJob, TransactionRow, TallyVoucher
from .serializers import (
    UploadJobSerializer,
    UploadJobListSerializer,
    TransactionRowSerializer,
    FieldMappingSerializer,
    LedgerAssignSerializer,
    TallyVoucherSerializer,
    TallyVoucherListSerializer,
)
from masters.models import TallyLedger

logger = logging.getLogger("transactions")


class ActiveClientMixin:
    def get_active_client(self):
        return self.request.user.active_client_profile


# ── Upload Jobs ──────────────────────────────────────────────────────────────


class UploadJobListCreateView(ActiveClientMixin, generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return UploadJobListSerializer
        return UploadJobSerializer

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return UploadJob.objects.none()
        qs = UploadJob.objects.filter(client_profile=client)
        vt = self.request.query_params.get("voucher_type")
        if vt:
            qs = qs.filter(voucher_type=vt)
        return qs

    def perform_create(self, serializer):
        client = self.get_active_client()
        if not client:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("No active client selected. Please select a client first.")
        uploaded_file = self.request.FILES.get("file")
        fname = uploaded_file.name if uploaded_file else ""
        ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
        vtype = self.request.data.get("voucher_type", "unknown")
        file_size_kb = round(uploaded_file.size / 1024, 1) if uploaded_file else 0
        logger.info(
            "[Job:Create] New upload job | user=%s | client=%s | file=%s | ext=%s | voucher_type=%s | size=%sKB",
            self.request.user, client, fname, ext, vtype, file_size_kb,
        )
        serializer.save(
            client_profile=client,
            uploaded_by=self.request.user,
            original_filename=fname,
            file_type=ext,
        )


class UploadJobDetailView(ActiveClientMixin, generics.RetrieveDestroyAPIView):
    serializer_class = UploadJobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return UploadJob.objects.none()
        return UploadJob.objects.filter(client_profile=client)


class UploadJobFieldMappingView(ActiveClientMixin, APIView):
    """Step 2: Submit field mapping for a job."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        client = self.get_active_client()
        if not client:
            return Response({"error": "No active client"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            job = UploadJob.objects.get(pk=pk, client_profile=client)
        except UploadJob.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        ser = FieldMappingSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        job.field_mapping = ser.validated_data["mapping"]
        job.status = UploadJob.JobStatus.MAPPED
        job.save(update_fields=["field_mapping", "status", "updated_at"])
        logger.info(
            "[Job:FieldMapping] Saved | job_id=%s | voucher_type=%s | mapping_keys=%s",
            pk, job.voucher_type, list(ser.validated_data["mapping"].keys()),
        )
        return Response(UploadJobSerializer(job).data)


# ── Transaction Rows ─────────────────────────────────────────────────────────


class TransactionRowListView(ActiveClientMixin, generics.ListAPIView):
    serializer_class = TransactionRowSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return TransactionRow.objects.none()
        job_id = self.kwargs.get("job_id")
        return (
            TransactionRow.objects.filter(job_id=job_id, job__client_profile=client)
            .select_related("assigned_ledger")
        )


class TransactionRowDetailView(ActiveClientMixin, generics.RetrieveUpdateAPIView):
    serializer_class = TransactionRowSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return TransactionRow.objects.none()
        return TransactionRow.objects.filter(
            job__client_profile=client
        ).select_related("assigned_ledger")


class BulkLedgerAssignView(ActiveClientMixin, APIView):
    """Assign a ledger to one or more transaction rows."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = self.get_active_client()
        if not client:
            return Response({"error": "No active client"}, status=status.HTTP_400_BAD_REQUEST)

        ser = LedgerAssignSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        try:
            ledger = TallyLedger.objects.get(
                pk=ser.validated_data["ledger_id"], client_profile=client
            )
        except TallyLedger.DoesNotExist:
            return Response({"error": "Ledger not found"}, status=status.HTTP_404_NOT_FOUND)

        rows = TransactionRow.objects.filter(
            id__in=ser.validated_data["row_ids"],
            job__client_profile=client,
        )
        count = rows.update(
            assigned_ledger=ledger,
            ledger_source=ser.validated_data["source"],
        )
        logger.info(
            "[Ledger:Assign] Assigned ledger | client=%s | ledger=%s | rows_updated=%s | source=%s",
            client, ledger.name, count, ser.validated_data["source"],
        )
        return Response({"updated": count})


class ApproveJobView(ActiveClientMixin, APIView):
    """Mark all rows in a job as approved, ready to send to Tally."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        client = self.get_active_client()
        if not client:
            return Response({"error": "No active client"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            job = UploadJob.objects.get(pk=pk, client_profile=client)
        except UploadJob.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        row_count = job.rows.count()
        job.rows.update(is_approved=True)
        job.status = UploadJob.JobStatus.APPROVED
        job.save(update_fields=["status", "updated_at"])
        logger.info(
            "[Job:Approve] Approved | job_id=%s | voucher_type=%s | rows=%s | client=%s",
            pk, job.voucher_type, row_count, client,
        )
        return Response({"status": "approved", "rows": row_count})


class BulkSaveRowsView(APIView):
    """
    Bulk-create TransactionRows from FastAPI's parsed/mapped data.
    Called internally by the FastAPI /upload/save-rows endpoint.
    Accepts JSON: { job_id, rows: [ { row_number, raw_data, date, ... }, ... ] }
    """

    # Allow unauthenticated internal calls (FastAPI → Django)
    permission_classes = []

    def post(self, request, pk):
        from datetime import datetime as dt

        try:
            job = UploadJob.objects.get(pk=pk)
        except UploadJob.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        rows_data = request.data.get("rows", [])
        if not rows_data:
            logger.warning("[Job:SaveRows] No rows in payload | job_id=%s", pk)
            return Response({"error": "No rows provided"}, status=status.HTTP_400_BAD_REQUEST)

        existing = job.rows.count()
        logger.info(
            "[Job:SaveRows] START | job_id=%s | voucher_type=%s | incoming_rows=%s | deleting_existing=%s",
            pk, job.voucher_type, len(rows_data), existing,
        )
        # Delete any existing rows for re-processing
        job.rows.all().delete()

        objs = []
        for row in rows_data:
            date_val = None
            raw_date = row.get("date")
            if raw_date:
                for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%y", "%d/%m/%y", "%m/%d/%Y"):
                    try:
                        date_val = dt.strptime(str(raw_date).strip(), fmt).date()
                        break
                    except (ValueError, TypeError):
                        continue

            objs.append(TransactionRow(
                job=job,
                row_number=row.get("row_number", 0),
                raw_data=row.get("raw_data", {}),
                date=date_val,
                voucher_type=str(row.get("voucher_type", ""))[:30],
                voucher_number=str(row.get("voucher_number", ""))[:100],
                description=str(row.get("description", ""))[:1000],
                narration=str(row.get("narration", "")),
                reference=str(row.get("reference", ""))[:255],
                party_name=str(row.get("party_name", ""))[:255],
                invoice_no=str(row.get("invoice_no", ""))[:100],
                debit=row.get("debit", 0) or 0,
                credit=row.get("credit", 0) or 0,
                amount=row.get("amount", 0) or 0,
                gst_rate=row.get("gst_rate", 0) or 0,
                cgst=row.get("cgst", 0) or 0,
                sgst=row.get("sgst", 0) or 0,
                igst=row.get("igst", 0) or 0,
                taxable_amount=row.get("taxable_amount", 0) or 0,
                place_of_supply=str(row.get("place_of_supply", ""))[:100],
                hsn_code=str(row.get("hsn_code", ""))[:20],
                ledger_name=str(row.get("ledger_name", ""))[:255],
                ledger_source=row.get("ledger_source", ""),
                extra_data=row.get("extra_data"),
            ))

        TransactionRow.objects.bulk_create(objs)
        job.row_count = len(objs)
        job.status = UploadJob.JobStatus.READY
        job.save(update_fields=["row_count", "status", "updated_at"])

        logger.info(
            "[Job:SaveRows] DONE | job_id=%s | voucher_type=%s | rows_created=%s | status=ready",
            pk, job.voucher_type, len(objs),
        )
        return Response({
            "status": "saved",
            "rows_created": len(objs),
            "job_id": str(job.id),
        })


# ── Tally Voucher Generation ────────────────────────────────────────────────


class GenerateVouchersView(ActiveClientMixin, APIView):
    """
    Generate TallyVoucher entries from approved TransactionRows of a job.
    Maps each approved row → one TallyVoucher with proper double-entry fields.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        client = self.get_active_client()
        if not client:
            return Response({"error": "No active client"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            job = UploadJob.objects.get(pk=pk, client_profile=client)
        except UploadJob.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        if job.status not in (UploadJob.JobStatus.APPROVED, UploadJob.JobStatus.READY):
            logger.warning(
                "[Voucher:Generate] Job not in approvable state | job_id=%s | status=%s",
                pk, job.status,
            )
            return Response(
                {"error": f"Job status is '{job.status}', must be 'approved' or 'ready'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rows = job.rows.filter(is_approved=True).select_related("assigned_ledger")
        if not rows.exists():
            logger.warning("[Voucher:Generate] No approved rows | job_id=%s", pk)
            return Response({"error": "No approved rows to generate vouchers from."}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(
            "[Voucher:Generate] START | job_id=%s | voucher_type=%s | approved_rows=%s | client=%s",
            pk, job.voucher_type, rows.count(), client,
        )

        vouchers_created = 0
        for row in rows:
            # Determine voucher type from row or fall back to job's type
            vtype = _map_voucher_type(row.voucher_type or job.voucher_type)
            is_debit = float(row.debit) > 0

            # Party ledger = the assigned ledger or Gemini-suggested name
            party_name = ""
            if row.assigned_ledger:
                party_name = row.assigned_ledger.name
            elif row.ledger_name:
                party_name = row.ledger_name
            elif row.party_name:
                party_name = row.party_name

            # Counter ledger – for banking, it's the bank account
            counter = job.bank_account or ""
            if not counter and job.voucher_type in ("sales", "sales_return"):
                counter = "Sales Account"
            elif not counter and job.voucher_type in ("purchase", "purchase_return"):
                counter = "Purchase Account"

            TallyVoucher.objects.create(
                client_profile=client,
                source_job=job,
                source_row=row,
                voucher_type=vtype,
                voucher_number=row.voucher_number or row.invoice_no or "",
                date=row.date or job.created_at.date(),
                narration=row.narration or row.description or "",
                reference=row.reference or "",
                party_ledger_name=party_name,
                amount=abs(row.amount) if row.amount else abs(row.debit or row.credit or 0),
                is_debit=is_debit,
                gst_rate=row.gst_rate,
                cgst=row.cgst,
                sgst=row.sgst,
                igst=row.igst,
                taxable_amount=row.taxable_amount,
                place_of_supply=row.place_of_supply,
                hsn_code=row.hsn_code,
                invoice_no=row.invoice_no,
                counter_ledger_name=counter,
                counter_amount=abs(row.amount) if row.amount else abs(row.debit or row.credit or 0),
            )
            vouchers_created += 1

        logger.info(
            "[Voucher:Generate] DONE | job_id=%s | voucher_type=%s | vouchers_created=%s",
            pk, job.voucher_type, vouchers_created,
        )
        return Response({"vouchers_created": vouchers_created, "job_id": str(job.id)})


class TallyVoucherListView(ActiveClientMixin, generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return TallyVoucherListSerializer

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return TallyVoucher.objects.none()
        qs = TallyVoucher.objects.filter(client_profile=client)
        sync = self.request.query_params.get("sync_status")
        if sync:
            qs = qs.filter(sync_status=sync)
        return qs


class TallyVoucherDetailView(ActiveClientMixin, generics.RetrieveAPIView):
    serializer_class = TallyVoucherSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        client = self.get_active_client()
        if not client:
            return TallyVoucher.objects.none()
        return TallyVoucher.objects.filter(client_profile=client)


# ── Helpers ──────────────────────────────────────────────────────────────────

_VOUCHER_TYPE_MAP = {
    "banking": "Payment",
    "sales": "Sales",
    "purchase": "Purchase",
    "sales_return": "Credit Note",
    "purchase_return": "Debit Note",
    "journal": "Journal",
    "payment": "Payment",
    "receipt": "Receipt",
    "contra": "Contra",
}


def _map_voucher_type(raw: str) -> str:
    """Map internal voucher type strings to Tally-standard names."""
    raw_lower = raw.lower().strip()
    return _VOUCHER_TYPE_MAP.get(raw_lower, raw if raw else "Payment")
