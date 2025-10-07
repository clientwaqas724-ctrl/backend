from rest_framework import serializers
from .models import Merchant,Outlet,Coupon,Promotion,Tier, UserPoints, UserActivity
from django.conf import settings
from django.contrib.auth import get_user_model
User = get_user_model()  # ✅ Get actual User model class
################################################################################################################################################################
class MerchantSerializer(serializers.ModelSerializer):
    # Explicitly override fields to force required=True
    user = serializers.PrimaryKeyRelatedField(
        queryset=Merchant._meta.get_field('user').remote_field.model.objects.all(),
        required=True
    )
    company_name = serializers.CharField(max_length=150, required=True)
    logo_url = serializers.CharField(required=True, allow_blank=False)
    status = serializers.ChoiceField(
        choices=Merchant.STATUS_CHOICES,
        required=True
    )
    class Meta:
        model = Merchant
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
    # ---- Field-level validations ----
    def validate_company_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Company name is required.")
        return value.strip()
    def validate_logo_url(self, value):
        if not value.strip():
            raise serializers.ValidationError("Logo URL is required.")
        return value
    def validate(self, attrs):
        # Extra cross-field checks can go here if needed
        return attrs
##########################################################################################################################################################
class OutletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outlet
        fields = [
            'id',
            'merchant',
            'name',
            'address',
            'city',
            'state',
            'country',
            'latitude',
            'longitude',
            'contact_number',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    # enforce every field to be required + custom messages
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in self.Meta.read_only_fields:
                field.required = True
                field.error_messages['required'] = f"{field_name.replace('_',' ').title()} is required."
########################################################################################################################################################
class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            'id',
            'merchant',
            'title',
            'description',
            'points_required',
            'expiry_date',
            'status',
            'created_at',
        ]
        # these are automatically generated; keep them read-only
        read_only_fields = ['id', 'created_at']
    def __init__(self, *args, **kwargs):
        """
        Enforce every non–read-only field to be required
        and provide a clear, human-friendly error message.
        """
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in self.Meta.read_only_fields:
                field.required = True
                field.allow_blank = False
                # Custom messages
                field.error_messages['required'] = (
                    f"{field_name.replace('_', ' ').title()} is required."
                )
                field.error_messages['blank'] = (
                    f"{field_name.replace('_', ' ').title()} cannot be blank."
                )
################################################################################################################################################################
class PromotionSerializer(serializers.ModelSerializer):
    # Override each field to add custom required messages
    merchant = serializers.PrimaryKeyRelatedField(
        queryset=Promotion._meta.get_field('merchant').remote_field.model.objects.all(),
        error_messages={'required': 'Merchant ID is required.'}
    )
    title = serializers.CharField(
        max_length=150,
        error_messages={
            'required': 'Title is required.',
            'blank': 'Title cannot be blank.'
        }
    )
    description = serializers.CharField(
        error_messages={
            'required': 'Description is required.',
            'blank': 'Description cannot be blank.'
        }
    )
    # image_url remains optional but we can still validate if needed
    image_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    start_date = serializers.DateField(
        error_messages={'required': 'Start date is required.'}
    )
    end_date = serializers.DateField(
        error_messages={'required': 'End date is required.'}
    )

    class Meta:
        model = Promotion
        fields = [
            'id',
            'merchant',
            'title',
            'description',
            'image_url',
            'start_date',
            'end_date',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
################################################################################################################################################################
# ============================================================
# TIER SERIALIZER
# ============================================================
class TierSerializer(serializers.ModelSerializer):
    name = serializers.ChoiceField(
        choices=Tier.TIER_CHOICES,
        error_messages={'required': 'Tier name is required.'}
    )
    min_points = serializers.IntegerField(
        error_messages={'required': 'Minimum points are required.'}
    )
    max_points = serializers.IntegerField(
        error_messages={'required': 'Maximum points are required.'}
    )
    benefits = serializers.CharField(
        required=False,
        allow_blank=True
    )

    class Meta:
        model = Tier
        fields = ['id', 'name', 'min_points', 'max_points', 'benefits']
        read_only_fields = ['id']


# ============================================================
# USER POINTS SERIALIZER
# ============================================================
class UserPointsSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),   # ✅ FIXED: use actual model
        error_messages={'required': 'User ID is required.'}
    )
    tier = serializers.PrimaryKeyRelatedField(
        queryset=Tier.objects.all(),
        required=False,
        allow_null=True
    )
    total_points = serializers.IntegerField(
        error_messages={'required': 'Total points are required.'}
    )

    class Meta:
        model = UserPoints
        fields = ['id', 'user', 'total_points', 'tier', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================
# USER ACTIVITY SERIALIZER
# ============================================================
class UserActivitySerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        error_messages={'required': 'User ID is required.'}
    )
    activity_type = serializers.ChoiceField(
        choices=UserActivity.ACTIVITY_CHOICES,
        error_messages={'required': 'Activity type is required.'}
    )
    description = serializers.CharField(
        error_messages={
            'required': 'Description is required.',
            'blank': 'Description cannot be blank.'
        }
    )
    points = serializers.IntegerField(
        error_messages={'required': 'Points are required.'}
    )
    related_coupon = serializers.PrimaryKeyRelatedField(
        queryset=Coupon.objects.all(),   # ✅ FIXED: now has queryset
        required=False,
        allow_null=True
    )

    class Meta:
        model = UserActivity
        fields = [
            'id',
            'user',
            'activity_type',
            'description',
            'points',
            'related_coupon',
            'activity_date'
        ]
        read_only_fields = ['id', 'activity_date']
# ============================================================
# Customer Home SERIALIZER
# ============================================================
class CustomerHomeSerializer(serializers.Serializer):
    user = UserPointsSerializer()
    promotions = PromotionSerializer(many=True)
    available_coupons = CouponSerializer(many=True)
    recent_activity = UserActivitySerializer(many=True)

