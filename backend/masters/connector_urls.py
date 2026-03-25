from django.urls import path

from .connector_sync_views import (
    ConnectorLedgerSyncView,
    ConnectorStockItemSyncView,
    ConnectorVoucherSyncView,
)

app_name = "connector_sync"

urlpatterns = [
    path("sync/ledgers/", ConnectorLedgerSyncView.as_view(), name="sync_ledgers"),
    path("sync/vouchers/", ConnectorVoucherSyncView.as_view(), name="sync_vouchers"),
    path("sync/stock-items/", ConnectorStockItemSyncView.as_view(), name="sync_stock_items"),
]
