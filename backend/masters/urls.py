from django.urls import path
from .views import (
    LedgerListView,
    LedgerDetailView,
    BulkLedgerUpsertView,
    ItemListView,
    ItemDetailView,
    BulkItemUpsertView,
    RuleListCreateView,
    RuleDetailView,
    # Smart Ledger Management
    LedgerGroupListView,
    LedgerTemplateSuggestView,
    ClientLedgerListView,
    ClientLedgerDetailView,
    ClientLedgerBulkSaveView,
)

app_name = "masters"

urlpatterns = [
    # Ledgers (Tally-synced)
    path("ledgers/", LedgerListView.as_view(), name="ledger_list"),
    path("ledgers/<uuid:pk>/", LedgerDetailView.as_view(), name="ledger_detail"),
    path("ledgers/bulk-upsert/", BulkLedgerUpsertView.as_view(), name="ledger_bulk_upsert"),
    # Items
    path("items/", ItemListView.as_view(), name="item_list"),
    path("items/<uuid:pk>/", ItemDetailView.as_view(), name="item_detail"),
    path("items/bulk-upsert/", BulkItemUpsertView.as_view(), name="item_bulk_upsert"),
    # Rules
    path("rules/", RuleListCreateView.as_view(), name="rule_list_create"),
    path("rules/<uuid:pk>/", RuleDetailView.as_view(), name="rule_detail"),
    # ── Smart Ledger Management ─────────────────────────────────────────
    path("ledger-groups/", LedgerGroupListView.as_view(), name="ledger_group_list"),
    path("ledger-suggest/", LedgerTemplateSuggestView.as_view(), name="ledger_suggest"),
    path("client-ledgers/", ClientLedgerListView.as_view(), name="client_ledger_list"),
    path("client-ledgers/<uuid:pk>/", ClientLedgerDetailView.as_view(), name="client_ledger_detail"),
    path("client-ledgers/bulk-save/", ClientLedgerBulkSaveView.as_view(), name="client_ledger_bulk_save"),
]
