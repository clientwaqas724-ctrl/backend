# Merchants_App/models.py
import uuid
from django.db import models
from django.conf import settings   # to reference the custom User model
#######################################################################################################################################################
########################################################################################################################################################
class Merchant(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # ForeignKey to your custom User model in User_App
    # Assumes AUTH_USER_MODEL = 'User_App.User' in settings.py
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='merchants'
    )

    company_name = models.CharField(max_length=150)
    logo_url = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=8,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'merchants'   # matches your requested table name
        verbose_name = 'Merchant'
        verbose_name_plural = 'Merchants'

    def __str__(self):
        return f"{self.company_name} ({self.user.email})"
#######################################################################################################################################################
########################################################################################################################################################
class Outlet(models.Model):
    """
    Stores merchant outlets such as individual store locations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link each outlet to a merchant
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name='outlets'
    )

    name = models.CharField(max_length=150)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'outlets'
        verbose_name = 'Outlet'
        verbose_name_plural = 'Outlets'

    def __str__(self):
        return f"{self.name} - {self.merchant.company_name}"
###################################################################################################################################################################
# New Coupon and Promotion models
###############################################################################################################################################################
class Coupon(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_EXPIRED = 'expired'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_EXPIRED, 'Expired'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name='coupons'
    )
    title = models.CharField(max_length=150)
    description = models.TextField()
    points_required = models.PositiveIntegerField()
    expiry_date = models.DateField()
    status = models.CharField(
        max_length=8,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'coupons'
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'

    def __str__(self):
        return f"{self.title} ({self.merchant.company_name})"
#######################################################################################################################################################
########################################################################################################################################################
class Promotion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name='promotions'
    )
    title = models.CharField(max_length=150)
    description = models.TextField()
    image_url = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'promotions'
        verbose_name = 'Promotion'
        verbose_name_plural = 'Promotions'
    def __str__(self):
        return f"{self.title} ({self.merchant.company_name})"