from django.urls import path
from .views import (
    UploadJobListCreateView,
    UploadJobDetailView,
    UploadJobFieldMappingView,
    TransactionRowListView,
    TransactionRowDetailView,
    BulkLedgerAssignView,
    ApproveJobView,
    BulkSaveRowsView,
    GenerateVouchersView,
    TallyVoucherListView,
    TallyVoucherDetailView,
)

app_name = "transactions"

urlpatterns = [
    # Upload Jobs
    path("jobs/", UploadJobListCreateView.as_view(), name="job_list_create"),
    path("jobs/<uuid:pk>/", UploadJobDetailView.as_view(), name="job_detail"),
    path("jobs/<uuid:pk>/field-mapping/", UploadJobFieldMappingView.as_view(), name="job_field_mapping"),
    path("jobs/<uuid:pk>/approve/", ApproveJobView.as_view(), name="job_approve"),
    path("jobs/<uuid:pk>/save-rows/", BulkSaveRowsView.as_view(), name="bulk_save_rows"),
    path("jobs/<uuid:pk>/generate-vouchers/", GenerateVouchersView.as_view(), name="generate_vouchers"),
    # Transaction Rows
    path("jobs/<uuid:job_id>/rows/", TransactionRowListView.as_view(), name="row_list"),
    path("rows/<uuid:pk>/", TransactionRowDetailView.as_view(), name="row_detail"),
    # Bulk assign ledger
    path("rows/assign-ledger/", BulkLedgerAssignView.as_view(), name="bulk_assign_ledger"),
    # Tally Vouchers
    path("vouchers/", TallyVoucherListView.as_view(), name="voucher_list"),
    path("vouchers/<uuid:pk>/", TallyVoucherDetailView.as_view(), name="voucher_detail"),
]
