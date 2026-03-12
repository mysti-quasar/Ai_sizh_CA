from django.contrib import admin
from .models import DocumentFolder, DocumentFile


@admin.register(DocumentFolder)
class DocumentFolderAdmin(admin.ModelAdmin):
    list_display = ("name", "client_profile", "parent", "is_default", "default_type", "created_at")
    list_filter = ("is_default", "default_type", "created_at")
    search_fields = ("name", "client_profile__name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(DocumentFile)
class DocumentFileAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "folder", "file_type", "processing_status", "uploaded_at")
    list_filter = ("file_type", "processing_status", "uploaded_at")
    search_fields = ("original_filename", "folder__name")
    readonly_fields = ("id", "uploaded_at", "processed_at")
