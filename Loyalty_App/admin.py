# Loyalty_App/admin.py
from django.contrib import admin
from .models import Transaction
#######################################################################################################################################################
#######################################################################################################################################################
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Admin configuration for Loyalty transactions
    (points history & coupon redemptions).
    """

    list_display = (
        'id',
        'user',
        'merchant',
        'outlet',
        'coupon',
        'points',
        'created_at',
    )
    list_filter = (
        'merchant',
        'outlet',
        'coupon',
        'created_at',
    )
    search_fields = (
        'user__email',
        'merchant__company_name',
        'outlet__name',
        'coupon__title',
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
#######################################################################################################################################################
#######################################################################################################################################################
