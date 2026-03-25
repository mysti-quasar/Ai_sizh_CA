from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from clients.models import ClientProfile
from masters.models import ClientLedger, LedgerGroup
from transactions.models import TallyVoucher, TransactionRow, UploadJob


class Command(BaseCommand):
    help = "Populate dummy business cycle data for Tally Connector testing"

    @transaction.atomic
    def handle(self, *args, **options):
        user = self._create_or_get_user()
        client = self._create_or_get_client(user)

        groups = self._create_standard_groups()
        ledgers = self._create_client_ledgers(client, groups)

        self._create_business_cycle(client, user, ledgers)

        self.stdout.write(self.style.SUCCESS("Dummy data setup completed successfully."))

    def _create_or_get_user(self):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            email="dummy.owner@sizh.local",
            defaults={
                "username": "dummy_owner",
                "first_name": "Dummy",
                "last_name": "Owner",
                "is_verified": True,
            },
        )
        if created:
            user.set_password("DummyPass@123")
            user.save(update_fields=["password"])
            self.stdout.write(self.style.WARNING("Created dummy owner user: dummy.owner@sizh.local"))
        else:
            self.stdout.write("Using existing dummy owner user.")
        return user

    def _create_or_get_client(self, user):
        client, created = ClientProfile.objects.get_or_create(
            user=user,
            name="Global Traders Inc.",
            defaults={
                "trade_name": "Global Traders",
                "gstin": "27ABCDE1234F1Z5",
                "industry_type": ClientProfile.IndustryType.TRADING,
                "gst_type": ClientProfile.GSTType.REGULAR,
                "email": "accounts@globaltraders.test",
                "phone": "9999999999",
                "state": "Maharashtra",
                "address": "Mumbai",
                "tally_company_name": "Global Traders Inc.",
                "financial_year_start": timezone.localdate().replace(month=4, day=1),
            },
        )
        if created:
            self.stdout.write(self.style.WARNING("Created dummy client: Global Traders Inc."))
        else:
            self.stdout.write("Using existing dummy client: Global Traders Inc.")
        return client

    def _create_standard_groups(self):
        definitions = [
            {
                "name": "Sundry Debtors",
                "code": "SUNDRY_DEBTORS",
                "nature": LedgerGroup.Nature.DEBIT,
                "display_order": 10,
                "description": "Receivables from customers",
            },
            {
                "name": "Sundry Creditors",
                "code": "SUNDRY_CREDITORS",
                "nature": LedgerGroup.Nature.CREDIT,
                "display_order": 20,
                "description": "Payables to suppliers",
            },
            {
                "name": "Sales",
                "code": "SALES",
                "nature": LedgerGroup.Nature.CREDIT,
                "display_order": 30,
                "description": "Sales accounts",
            },
            {
                "name": "Purchase",
                "code": "PURCHASE",
                "nature": LedgerGroup.Nature.DEBIT,
                "display_order": 40,
                "description": "Purchase accounts",
            },
            {
                "name": "Cash/Bank",
                "code": "CASH_BANK",
                "nature": LedgerGroup.Nature.DEBIT,
                "display_order": 50,
                "description": "Cash and bank accounts",
            },
        ]

        groups = {}
        for item in definitions:
            group, _ = LedgerGroup.objects.update_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "nature": item["nature"],
                    "display_order": item["display_order"],
                    "description": item["description"],
                },
            )
            groups[group.code] = group
        self.stdout.write(self.style.SUCCESS("Standard ledger groups ensured."))
        return groups

    def _create_client_ledgers(self, client, groups):
        ledger_defs = [
            {
                "name": "Local Customer",
                "group": groups["SUNDRY_DEBTORS"],
                "opening_balance": Decimal("0.00"),
                "sub_category": "Parties",
            },
            {
                "name": "Main Supplier",
                "group": groups["SUNDRY_CREDITORS"],
                "opening_balance": Decimal("0.00"),
                "sub_category": "Parties",
            },
            {
                "name": "Sales Account",
                "group": groups["SALES"],
                "opening_balance": Decimal("0.00"),
                "sub_category": "Revenue",
            },
            {
                "name": "Purchase Account",
                "group": groups["PURCHASE"],
                "opening_balance": Decimal("0.00"),
                "sub_category": "Expense",
            },
            {
                "name": "HDFC Bank",
                "group": groups["CASH_BANK"],
                "opening_balance": Decimal("250000.00"),
                "sub_category": "Bank",
            },
        ]

        ledgers = {}
        for item in ledger_defs:
            ledger, _ = ClientLedger.objects.update_or_create(
                client_profile=client,
                name=item["name"],
                defaults={
                    "group": item["group"],
                    "sub_category": item["sub_category"],
                    "opening_balance": item["opening_balance"],
                    "is_custom": True,
                    "is_active": True,
                },
            )
            ledgers[ledger.name] = ledger

        self.stdout.write(self.style.SUCCESS("Dummy client ledgers ensured."))
        return ledgers

    def _create_business_cycle(self, client, user, ledgers):
        today = timezone.localdate()
        purchase_date = today - timedelta(days=2)
        sales_date = today - timedelta(days=1)
        payment_date = today

        purchase_amount = Decimal("12500.00")
        sales_amount = Decimal("18500.00")
        payment_amount = Decimal("7500.00")

        purchase_job = self._get_or_create_upload_job(
            client=client,
            user=user,
            voucher_type=UploadJob.VoucherType.PURCHASE,
            filename="dummy_purchase.csv",
        )
        sales_job = self._get_or_create_upload_job(
            client=client,
            user=user,
            voucher_type=UploadJob.VoucherType.SALES,
            filename="dummy_sales.csv",
        )
        banking_job = self._get_or_create_upload_job(
            client=client,
            user=user,
            voucher_type=UploadJob.VoucherType.BANKING,
            filename="dummy_banking.csv",
        )

        self._upsert_row(
            job=purchase_job,
            row_number=1,
            tx_date=purchase_date,
            voucher_type="Purchase",
            voucher_number="PUR-0001",
            narration="Purchase of stock from Main Supplier",
            party_name="Main Supplier",
            debit=purchase_amount,
            credit=Decimal("0.00"),
            amount=purchase_amount,
            assigned_ledger_name="Purchase Account",
        )
        self._upsert_row(
            job=sales_job,
            row_number=1,
            tx_date=sales_date,
            voucher_type="Sales",
            voucher_number="SAL-0001",
            narration="Sale of goods to Local Customer",
            party_name="Local Customer",
            debit=Decimal("0.00"),
            credit=sales_amount,
            amount=sales_amount,
            assigned_ledger_name="Sales Account",
        )
        self._upsert_row(
            job=banking_job,
            row_number=1,
            tx_date=payment_date,
            voucher_type="Payment",
            voucher_number="PAY-0001",
            narration="Payment made to Main Supplier via HDFC Bank",
            party_name="Main Supplier",
            debit=Decimal("0.00"),
            credit=payment_amount,
            amount=payment_amount,
            assigned_ledger_name="HDFC Bank",
        )

        self._upsert_voucher(
            client=client,
            source_job=purchase_job,
            voucher_type=TallyVoucher.VType.PURCHASE,
            voucher_number="PUR-0001",
            tx_date=purchase_date,
            narration="Purchase of stock from Main Supplier",
            party_ledger_name="Main Supplier",
            amount=purchase_amount,
            is_debit=False,
            counter_ledger_name="Purchase Account",
        )
        self._upsert_voucher(
            client=client,
            source_job=sales_job,
            voucher_type=TallyVoucher.VType.SALES,
            voucher_number="SAL-0001",
            tx_date=sales_date,
            narration="Sale of goods to Local Customer",
            party_ledger_name="Local Customer",
            amount=sales_amount,
            is_debit=True,
            counter_ledger_name="Sales Account",
        )
        self._upsert_voucher(
            client=client,
            source_job=banking_job,
            voucher_type=TallyVoucher.VType.PAYMENT,
            voucher_number="PAY-0001",
            tx_date=payment_date,
            narration="Supplier payment through HDFC Bank",
            party_ledger_name="Main Supplier",
            amount=payment_amount,
            is_debit=False,
            counter_ledger_name="HDFC Bank",
        )

        self.stdout.write(self.style.SUCCESS("Dummy business cycle vouchers ensured."))

    def _get_or_create_upload_job(self, client, user, voucher_type, filename):
        dummy_file = SimpleUploadedFile(
            name=filename,
            content=b"date,voucher_no,particulars,amount\n",
            content_type="text/csv",
        )
        job, _ = UploadJob.objects.get_or_create(
            client_profile=client,
            voucher_type=voucher_type,
            original_filename=filename,
            defaults={
                "uploaded_by": user,
                "file": dummy_file,
                "file_type": "csv",
                "status": UploadJob.JobStatus.PARSED,
                "row_count": 1,
            },
        )
        return job

    def _upsert_row(
        self,
        job,
        row_number,
        tx_date,
        voucher_type,
        voucher_number,
        narration,
        party_name,
        debit,
        credit,
        amount,
        assigned_ledger_name,
    ):
        TransactionRow.objects.update_or_create(
            job=job,
            row_number=row_number,
            defaults={
                "date": tx_date,
                "voucher_type": voucher_type,
                "voucher_number": voucher_number,
                "description": narration,
                "narration": narration,
                "party_name": party_name,
                "debit": debit,
                "credit": credit,
                "amount": amount,
                "ledger_name": assigned_ledger_name,
                "raw_data": {
                    "voucher_no": voucher_number,
                    "narration": narration,
                    "party": party_name,
                },
            },
        )

    def _upsert_voucher(
        self,
        client,
        source_job,
        voucher_type,
        voucher_number,
        tx_date,
        narration,
        party_ledger_name,
        amount,
        is_debit,
        counter_ledger_name,
    ):
        TallyVoucher.objects.update_or_create(
            client_profile=client,
            voucher_type=voucher_type,
            voucher_number=voucher_number,
            date=tx_date,
            defaults={
                "source_job": source_job,
                "narration": narration,
                "reference": f"REF-{voucher_number}",
                "party_ledger_name": party_ledger_name,
                "amount": amount,
                "is_debit": is_debit,
                "counter_ledger_name": counter_ledger_name,
                "counter_amount": amount,
                "taxable_amount": amount,
                "sync_status": TallyVoucher.SyncStatus.PENDING,
            },
        )
