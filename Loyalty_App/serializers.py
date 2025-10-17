from rest_framework import serializers
from .models import Transaction
from Merchants_App.models import Outlet, Coupon
#########################################################################################################################################################
#############################################################################################################################################################
class TransactionSerializer(serializers.ModelSerializer):
    # Read-only user & merchant info
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    merchant_name = serializers.CharField(source='merchant.company_name', read_only=True)

    # Outlet & Coupon display helpers
    outlet = serializers.SerializerMethodField()
    coupon = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id',
            'user',
            'user_name',
            'user_email',
            'merchant',
            'merchant_name',
            'outlet',
            'coupon',
            'points',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    ###################################################################################################
    # CREATE / UPDATE — Auto-assign outlet or coupon if missing
    ###################################################################################################
    def create(self, validated_data):
        merchant = validated_data.get('merchant')

        # Auto-assign an outlet if not provided
        if not validated_data.get('outlet') and merchant:
            outlet = Outlet.objects.filter(merchant=merchant).order_by('created_at').last()
            if outlet:
                validated_data['outlet'] = outlet

        # Auto-assign an active coupon if not provided
        if not validated_data.get('coupon') and merchant:
            coupon = Coupon.objects.filter(
                merchant=merchant,
                status=Coupon.STATUS_ACTIVE
            ).order_by('created_at').last()
            if coupon:
                validated_data['coupon'] = coupon

        return super().create(validated_data)

    def update(self, instance, validated_data):
        merchant = validated_data.get('merchant', instance.merchant)

        # Auto-assign outlet if not already set
        if not validated_data.get('outlet') and not instance.outlet:
            outlet = Outlet.objects.filter(merchant=merchant).order_by('created_at').last()
            if outlet:
                validated_data['outlet'] = outlet

        # Auto-assign coupon if not already set
        if not validated_data.get('coupon') and not instance.coupon:
            coupon = Coupon.objects.filter(
                merchant=merchant,
                status=Coupon.STATUS_ACTIVE
            ).order_by('created_at').last()
            if coupon:
                validated_data['coupon'] = coupon

        return super().update(instance, validated_data)

    ###################################################################################################
    # DISPLAY HELPERS — Fallbacks for outlet and coupon display
    ###################################################################################################
    def get_outlet(self, obj):
        """
        Return the outlet name.
        If missing in the transaction, fall back to the first available outlet.
        """
        try:
            if obj.outlet:
                return obj.outlet.name
            first_outlet = Outlet.objects.first()
            return first_outlet.name if first_outlet else None
        except Exception:
            return None

    def get_coupon(self, obj):
        """
        Return the coupon title.
        If missing in the transaction, fall back to the first available coupon.
        """
        try:
            if obj.coupon:
                return obj.coupon.title
            first_coupon = Coupon.objects.first()
            return first_coupon.title if first_coupon else None
        except Exception:
            return None
