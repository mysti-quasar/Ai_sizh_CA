import uuid
from django.conf import settings
from django.db import models


def document_upload_path(instance, filename):
    return f"documents/{instance.folder.client_profile.id}/{instance.folder.id}/{filename}"


class DocumentFolder(models.Model):
    class DefaultFolder(models.TextChoices):
        BANKING = "banking", "Banking"
        SALES = "sales", "Sales"
        PURCHASE = "purchase", "Purchase"
        MASTER = "master", "Master"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_profile = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.CASCADE,
        related_name="document_folders",
    )
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    is_default = models.BooleanField(default=False)
    default_type = models.CharField(
        max_length=20, choices=DefaultFolder.choices, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sizh_document_folders"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @classmethod
    def create_defaults_for_client(cls, client_profile):
        for folder_type in cls.DefaultFolder:
            cls.objects.get_or_create(
                client_profile=client_profile,
                default_type=folder_type.value,
                is_default=True,
                defaults={"name": folder_type.label},
            )


class DocumentFile(models.Model):
    class FileType(models.TextChoices):
        PDF = "pdf", "PDF"
        IMAGE = "image", "Image"
        EXCEL = "excel", "Excel"
        CSV = "csv", "CSV"
        OTHER = "other", "Other"

    class ProcessingStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folder = models.ForeignKey(
        DocumentFolder, on_delete=models.CASCADE, related_name="files"
    )
    file = models.FileField(upload_to=document_upload_path)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(
        max_length=10, choices=FileType.choices, default=FileType.OTHER
    )
    file_size = models.PositiveIntegerField(default=0)
    processing_status = models.CharField(
        max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.PENDING
    )
    extracted_data = models.JSONField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_documents",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "sizh_document_files"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.original_filename
