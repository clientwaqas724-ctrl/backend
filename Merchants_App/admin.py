# Merchants_App/admin.py
from django.contrib import admin
from .models import Merchant, Outlet, Coupon, Promotion
from .models import Tier, UserPoints, UserActivity
#################################################################################################################################################
#################################################################################################################################################
@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    # Columns to show in the admin list page
    list_display = (
        'company_name',
        'user',          # will display the related User’s __str__ (email)
        'status',
        'created_at',
        'updated_at',
    )

    # Enable sidebar filters
    list_filter = ('status', 'created_at')

    # Allow searching by company name or the related user's email
    search_fields = ('company_name', 'user__email')

    # Default ordering
    ordering = ('-created_at',)

    # Make certain fields read-only
    readonly_fields = ('created_at', 'updated_at')

    # Optional: group fields into sections in the edit form
    fieldsets = (
        (None, {
            'fields': ('user', 'company_name', 'logo_url', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
#################################################################################################################################################
#################################################################################################################################################
@admin.register(Outlet)
class OutletAdmin(admin.ModelAdmin):
    # Columns to display in the list view
    list_display = (
        "name",
        "merchant",
        "city",
        "state",
        "country",
        "contact_number",
        "created_at",
        "updated_at",
    )

    # Fields you can search by
    search_fields = (
        "name",
        "merchant__company_name",
        "city",
        "state",
        "country",
        "contact_number",
    )

    # Filters shown in the right sidebar
    list_filter = (
        "country",
        "state",
        "city",
        "created_at",
    )

    # Read-only fields (auto timestamps should not be editable)
    readonly_fields = ("created_at", "updated_at")

    # Optional ordering
    ordering = ("name",)
##################################################################################################################################################################################
################################################################################################################################################################################
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'merchant', 'points_required',
        'expiry_date', 'status', 'created_at'
    )
    list_filter = ('status', 'expiry_date', 'created_at')
    search_fields = ('title', 'merchant__company_name')
    ordering = ('-created_at',)
##################################################################################################################################################################################
################################################################################################################################################################################
@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'merchant', 'start_date', 'end_date', 'created_at'
    )
    list_filter = ('start_date', 'end_date', 'created_at')
    search_fields = ('title', 'merchant__company_name')
    ordering = ('-created_at',)
################################################################################################################################################################
@admin.register(Tier)
class TierAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_points', 'max_points', 'benefits')
    list_filter = ('name',)
    search_fields = ('name', 'benefits')
    ordering = ('min_points',)

@admin.register(UserPoints)
class UserPointsAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_points', 'tier', 'created_at', 'updated_at')
    list_filter = ('tier', 'created_at')
    search_fields = ('user__email', 'tier__name')
    ordering = ('-total_points',)
    autocomplete_fields = ('user', 'tier')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'points', 'related_coupon', 'activity_date')
    list_filter = ('activity_type', 'activity_date')
    search_fields = ('user__email', 'description', 'related_coupon__code')
    ordering = ('-activity_date',)
    autocomplete_fields = ('user', 'related_coupon')
    readonly_fields = ('activity_date',)