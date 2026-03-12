from django.contrib import admin
from .models import ClientProfile


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "trade_name", "pan", "gstin", "gst_type", "user", "created_at")
    list_filter = ("gst_type", "created_at")
    search_fields = ("name", "trade_name", "pan", "gstin", "user__email")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
