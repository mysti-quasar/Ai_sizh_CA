import uuid
from django.conf import settings
from django.db import models


class ClientProfile(models.Model):
    class GSTType(models.TextChoices):
        REGULAR = "regular", "Regular"
        COMPOSITION = "composition", "Composition"
        UNREGISTERED = "unregistered", "Unregistered"
        ISD = "isd", "Input Service Distributor"

    class IndustryType(models.TextChoices):
        TRADING = "trading", "Trading"
        SERVICE = "service", "Service"
        ECOMMERCE = "ecommerce", "E-commerce"
        MANUFACTURING = "manufacturing", "Manufacturing"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_profiles",
    )
    name = models.CharField(max_length=255)
    trade_name = models.CharField(max_length=255, blank=True, default="")
    pan = models.CharField(max_length=10, blank=True, default="")
    gstin = models.CharField(max_length=15, blank=True, default="")
    gst_type = models.CharField(
        max_length=20, choices=GSTType.choices, default=GSTType.REGULAR
    )
    industry_type = models.CharField(
        max_length=20,
        choices=IndustryType.choices,
        blank=True,
        default="",
        help_text="Business type / industry for smart ledger suggestions",
    )
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=15, blank=True, default="")
    address = models.TextField(blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    pincode = models.CharField(max_length=10, blank=True, default="")
    financial_year_start = models.DateField(null=True, blank=True)
    tally_company_name = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sizh_client_profiles"
        unique_together = ("user", "gstin")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.gstin or 'No GSTIN'})" 
