import json
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard HTML Views
# ─────────────────────────────────────────────────────────────────────────────

def dashboard_view(request):
    return render(request, "dashboard.html")


# ─────────────────────────────────────────────────────────────────────────────
# Internal Dashboard JSON API  (DEBUG-only, no JWT required)
# ─────────────────────────────────────────────────────────────────────────────

def _json(data, status=200):
    return JsonResponse(data, status=status, safe=isinstance(data, dict))


@csrf_exempt
@require_http_methods(["GET", "PATCH"])
def dash_api_users(request, user_id=None):
    """GET → list all users  |  PATCH /<id>/ → update role / active state."""
    User = get_user_model()

    if request.method == "PATCH" and user_id:
        try:
            user = User.objects.get(pk=user_id)
            body = json.loads(request.body or "{}")
            if "is_active" in body:
                user.is_active = bool(body["is_active"])
            if "is_staff" in body:
                user.is_staff = bool(body["is_staff"])
            if "is_superuser" in body:
                user.is_superuser = bool(body["is_superuser"])
            user.save(update_fields=["is_active", "is_staff", "is_superuser"])
            return _json({"ok": True, "id": user.pk})
        except User.DoesNotExist:
            return _json({"error": "Not found"}, 404)

    users = list(
        User.objects.values(
            "id", "username", "email", "first_name", "last_name",
            "is_active", "is_staff", "is_superuser", "date_joined", "last_login",
        ).order_by("-date_joined")
    )
    for u in users:
        u["date_joined"] = str(u["date_joined"])[:10] if u["date_joined"] else ""
        u["last_login"]  = str(u["last_login"])[:10]  if u["last_login"]  else "Never"
        u["role"] = "Superuser" if u["is_superuser"] else ("Staff" if u["is_staff"] else "User")
    return _json({"users": users, "total": len(users)})


@csrf_exempt
@require_http_methods(["POST"])
def dash_api_set_password(request, user_id):
    """POST /dashboard/api/users/<id>/set-password/  body: {password: '...'}"""
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
        body = json.loads(request.body or "{}")
        pwd  = body.get("password", "").strip()
        if len(pwd) < 6:
            return _json({"error": "Password must be at least 6 characters."}, 400)
        user.set_password(pwd)
        user.save()
        return _json({"ok": True})
    except User.DoesNotExist:
        return _json({"error": "User not found"}, 404)


@require_http_methods(["GET"])
def dash_api_clients(request):
    from clients.models import ClientProfile
    qs = ClientProfile.objects.all().order_by("-created_at")
    data = list(
        qs.values(
            "id", "name", "trade_name", "gstin", "pan", "gst_type",
            "industry_type", "email", "phone", "state", "created_at",
        )
    )
    for d in data:
        d["id"] = str(d["id"])
        d["created_at"] = str(d["created_at"])[:10]
    return _json({"clients": data, "total": len(data)})


@require_http_methods(["GET"])
def dash_api_documents(request):
    from documents.models import DocumentFolder, DocumentFile
    folders = DocumentFolder.objects.prefetch_related("files").select_related("client_profile").order_by("-created_at")
    folder_data = []
    for f in folders:
        file_count = f.files.count()
        folder_data.append({
            "id": str(f.id),
            "name": f.name,
            "client": f.client_profile.name,
            "is_default": f.is_default,
            "default_type": f.default_type or "",
            "file_count": file_count,
            "created_at": str(f.created_at)[:10],
        })
    recent_files = list(
        DocumentFile.objects.select_related("folder__client_profile").order_by("-uploaded_at")[:50].values(
            "id", "original_filename", "file_type", "file_size",
            "processing_status", "uploaded_at",
            "folder__name", "folder__client_profile__name",
        )
    )
    for rf in recent_files:
        rf["id"] = str(rf["id"])
        rf["uploaded_at"] = str(rf["uploaded_at"])[:16]
        rf["folder_name"] = rf.pop("folder__name", "")
        rf["client"]      = rf.pop("folder__client_profile__name", "")
        rf["file_size_kb"] = round(rf["file_size"] / 1024, 1) if rf["file_size"] else 0
    total_files = DocumentFile.objects.count()
    pending     = DocumentFile.objects.filter(processing_status="pending").count()
    completed   = DocumentFile.objects.filter(processing_status="completed").count()
    return _json({
        "folders": folder_data,
        "recent_files": recent_files,
        "stats": {"total_files": total_files, "pending": pending, "completed": completed},
    })


@require_http_methods(["GET"])
def dash_api_masters(request):
    from masters.models import LedgerGroup, ClientLedger, TallyLedger
    groups = list(LedgerGroup.objects.values("id", "name", "code", "nature", "description").order_by("display_order"))
    for g in groups:
        g["id"] = str(g["id"])
    client_ledgers = list(
        ClientLedger.objects.select_related("group", "client_profile").values(
            "id", "name", "sub_category", "opening_balance", "is_custom", "is_active",
            "group__name", "client_profile__name", "created_at",
        ).order_by("group__name", "name")
    )
    for cl in client_ledgers:
        cl["id"] = str(cl["id"])
        cl["group_name"]  = cl.pop("group__name", "")
        cl["client_name"] = cl.pop("client_profile__name", "")
        cl["opening_balance"] = float(cl["opening_balance"])
        cl["created_at"] = str(cl["created_at"])[:10]
    tally = list(
        TallyLedger.objects.select_related("client_profile").values(
            "id", "name", "group", "tax_category", "gstin",
            "opening_balance", "is_active", "client_profile__name",
        ).order_by("name")[:200]
    )
    for t in tally:
        t["id"] = str(t["id"])
        t["client_name"] = t.pop("client_profile__name", "")
        t["opening_balance"] = float(t["opening_balance"])
    return _json({"ledger_groups": groups, "client_ledgers": client_ledgers, "tally_ledgers": tally})


@require_http_methods(["GET"])
def dash_api_transactions(request):
    from transactions.models import UploadJob, TallyVoucher
    jobs = list(
        UploadJob.objects.select_related("client_profile", "uploaded_by").order_by("-created_at")[:100].values(
            "id", "voucher_type", "original_filename", "status",
            "row_count", "file_type", "error_message", "created_at",
            "client_profile__name", "uploaded_by__username",
        )
    )
    for j in jobs:
        j["id"] = str(j["id"])
        j["client"] = j.pop("client_profile__name", "")
        j["uploaded_by"] = j.pop("uploaded_by__username", "") or "—"
        j["created_at"] = str(j["created_at"])[:16]
    vouchers = list(
        TallyVoucher.objects.select_related("client_profile").order_by("-created_at")[:100].values(
            "id", "voucher_type", "voucher_number", "date", "narration",
            "party_ledger_name", "amount", "is_debit", "client_profile__name",
        )
    )
    for v in vouchers:
        v["id"] = str(v["id"])
        v["client"] = v.pop("client_profile__name", "")
        v["date"]   = str(v["date"]) if v["date"] else ""
        v["amount"] = float(v.get("amount") or 0)
    stats = {
        "total_jobs":    UploadJob.objects.count(),
        "ready_jobs":    UploadJob.objects.filter(status="ready").count(),
        "total_vouchers": TallyVoucher.objects.count(),
    }
    return _json({"jobs": jobs, "vouchers": vouchers, "stats": stats})


# ─────────────────────────────────────────────────────────────────────────────
# Monitor View
# ─────────────────────────────────────────────────────────────────────────────

def monitor_view(request):
    from clients.models import ClientProfile
    from masters.models import TallyLedger, ClientLedger, LedgerGroup

    clients        = ClientProfile.objects.all().order_by("-created_at")
    client_ledgers = ClientLedger.objects.select_related("client_profile", "group").order_by("group", "name")
    tally_ledgers  = TallyLedger.objects.select_related("client_profile").order_by("name")
    ledger_groups  = LedgerGroup.objects.prefetch_related("client_ledgers").order_by("display_order", "name")

    context = {
        "clients":              clients,
        "client_ledgers":       client_ledgers,
        "tally_ledgers":        tally_ledgers,
        "ledger_groups":        ledger_groups,
        "total_clients":        clients.count(),
        "total_client_ledgers": client_ledgers.count(),
        "total_tally_ledgers":  tally_ledgers.count(),
        "total_ledger_groups":  ledger_groups.count(),
    }
    return render(request, "monitor.html", context)


urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("monitor/", monitor_view, name="monitor"),
    # ── Internal Dashboard API (dev/admin only) ────────────────────────
    path("dashboard/api/users/",                  dash_api_users,        name="dash_users"),
    path("dashboard/api/users/<int:user_id>/",    dash_api_users,        name="dash_user_detail"),
    path("dashboard/api/users/<int:user_id>/set-password/", dash_api_set_password, name="dash_set_password"),
    path("dashboard/api/clients/",      dash_api_clients,      name="dash_clients"),
    path("dashboard/api/documents/",    dash_api_documents,    name="dash_documents"),
    path("dashboard/api/masters/",      dash_api_masters,      name="dash_masters"),
    path("dashboard/api/transactions/", dash_api_transactions, name="dash_transactions"),
    # ── Existing App APIs ──────────────────────────────────────────────
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/clients/", include("clients.urls")),
    path("api/documents/", include("documents.urls")),
    path("api/masters/", include("masters.urls")),
    path("api/transactions/", include("transactions.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
