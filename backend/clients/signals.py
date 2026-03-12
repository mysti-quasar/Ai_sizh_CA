"""
SIZH CA - Client Signals
==========================
Auto-create default Document Vault folders when a new ClientProfile is created.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ClientProfile
from documents.models import DocumentFolder


@receiver(post_save, sender=ClientProfile)
def create_default_folders(sender, instance, created, **kwargs):
    """When a new ClientProfile is created, initialize default document folders."""
    if created:
        DocumentFolder.create_defaults_for_client(instance)
