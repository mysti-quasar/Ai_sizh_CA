"""
SIZH CA - Document Vault Serializers
======================================
"""

from rest_framework import serializers
from .models import DocumentFolder, DocumentFile


class DocumentFileSerializer(serializers.ModelSerializer):
    """Serializer for document files."""
    name = serializers.CharField(source="original_filename", read_only=True)

    class Meta:
        model = DocumentFile
        fields = [
            "id", "folder", "name", "file", "original_filename",
            "file_type", "file_size", "processing_status",
            "extracted_data", "uploaded_at",
        ]
        # folder, original_filename, file_type are injected by the view via
        # serializer.save(...), so they must not be validated from request data.
        read_only_fields = [
            "id", "name", "folder", "original_filename", "file_type",
            "file_size", "processing_status", "extracted_data", "uploaded_at",
        ]


class DocumentFolderSerializer(serializers.ModelSerializer):
    """Serializer for document folders with nested file count."""

    file_count = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    # Computed slug from name for frontend compatibility
    slug = serializers.SerializerMethodField()

    class Meta:
        model = DocumentFolder
        fields = [
            "id", "name", "slug", "parent", "is_default",
            "default_type", "file_count", "children",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_default", "default_type", "created_at", "updated_at"]

    def get_file_count(self, obj):
        return obj.files.count()

    def get_slug(self, obj):
        return obj.default_type or obj.name.lower().replace(" ", "-")

    def get_children(self, obj):
        children = obj.children.all()
        return DocumentFolderSerializer(children, many=True).data
