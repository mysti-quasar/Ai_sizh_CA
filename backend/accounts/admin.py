from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "username", "first_name", "last_name", "firm_name", "is_verified", "is_staff")
    list_filter = ("is_verified", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "username", "first_name", "last_name", "firm_name")
    ordering = ("-date_joined",)
    fieldsets = BaseUserAdmin.fieldsets + (
        ("SIZH CA Fields", {"fields": ("phone", "firm_name", "is_verified", "active_client_profile")}),
    )
