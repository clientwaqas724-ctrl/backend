# Merchants_App/models.py
import uuid
from django.db import models
from django.conf import settings   # to reference the custom User model
########################################################################
##########New Updated#########################################
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
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
        'Merchant',
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

    # ✅ New optional outlet image field
    outlet_image = models.ImageField(
        upload_to='outlets/images/',
        null=True,
        blank=True,
        help_text="Upload an image or provide an image URL."
    )

    # ✅ Optional URL field for image URI
    outlet_image_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Alternatively, provide an image URL if no file is uploaded."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'outlets'
        verbose_name = 'Outlet'
        verbose_name_plural = 'Outlets'

    def __str__(self):
        return f"{self.name} - {self.merchant.company_name}"

    def clean(self):
        """
        Allow either an uploaded image or a URL, or neither — but not both.
        """
        if self.outlet_image and self.outlet_image_url:
            raise ValidationError("Please provide either an image file or an image URL, not both.")

        # Validate URL if provided
        if self.outlet_image_url:
            validator = URLValidator()
            try:
                validator(self.outlet_image_url)
            except ValidationError:
                raise ValidationError("Invalid image URL provided.")
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
#########################################################################################################################################################
#########################################################################################################################################################
# ============================================================
# TIER MODEL
# ============================================================
class Tier(models.Model):
    TIER_BRONZE = 'bronze'
    TIER_SILVER = 'silver'
    TIER_GOLD = 'gold'
    TIER_PLATINUM = 'platinum'

    TIER_CHOICES = [
        (TIER_BRONZE, 'Bronze'),
        (TIER_SILVER, 'Silver'),
        (TIER_GOLD, 'Gold'),
        (TIER_PLATINUM, 'Platinum'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=10, choices=TIER_CHOICES, unique=True)
    min_points = models.PositiveIntegerField()
    max_points = models.PositiveIntegerField()
    benefits = models.TextField(blank=True)

    class Meta:
        db_table = 'tiers'
        verbose_name = 'Tier'
        verbose_name_plural = 'Tiers'

    def __str__(self):
        return self.get_name_display()


# ============================================================
# USER POINTS MODEL
# ============================================================
class UserPoints(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='points'
    )
    total_points = models.PositiveIntegerField(default=0)
    tier = models.ForeignKey(
        Tier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_points'
        verbose_name = 'User Points'
        verbose_name_plural = 'User Points'

    def __str__(self):
        return f"{self.user.email} - {self.total_points} points"


# ============================================================
# USER ACTIVITY MODEL
# ============================================================
class UserActivity(models.Model):
    ACTIVITY_EARNED = 'earned'
    ACTIVITY_REDEEMED = 'redeemed'
    ACTIVITY_EXPIRED = 'expired'

    ACTIVITY_CHOICES = [
        (ACTIVITY_EARNED, 'Earned'),
        (ACTIVITY_REDEEMED, 'Redeemed'),
        (ACTIVITY_EXPIRED, 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(max_length=1000, choices=ACTIVITY_CHOICES)
    description = models.TextField()
    points = models.IntegerField()  # +ve for earned, -ve for redeemed
    related_coupon = models.ForeignKey(
        'Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities'
    )
    activity_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_activities'
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        ordering = ['-activity_date']

    def __str__(self):
        return f"{self.user.email} - {self.activity_type} - {self.points} points"



