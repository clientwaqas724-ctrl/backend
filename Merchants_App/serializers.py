from rest_framework import serializers
from .models import Merchant,Outlet,Coupon,Promotion,Tier, UserPoints, UserActivity
from django.conf import settings
from django.contrib.auth import get_user_model
User = get_user_model()  # ✅ Get actual User model class
#####################################################
from django.utils import timezone   ########today New Updation library###########
import uuid
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
    # ✅ Add both optional image fields
    outlet_image = serializers.ImageField(
        required=False,
        allow_null=True,
        use_url=True
    )
    outlet_image_url = serializers.URLField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

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
            'outlet_image',
            'outlet_image_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required EXCEPT images and read-only fields
        for field_name, field in self.fields.items():
            if field_name not in self.Meta.read_only_fields and field_name not in ['outlet_image', 'outlet_image_url']:
                field.required = True
                field.error_messages['required'] = f"{field_name.replace('_',' ').title()} is required."

    def validate(self, data):
        """
        Ensure only one of outlet_image or outlet_image_url is provided.
        Allow both to be empty.
        """
        image_file = data.get('outlet_image')
        image_url = data.get('outlet_image_url')

        if image_file and image_url:
            raise serializers.ValidationError("Provide either an image file or an image URL, not both.")
        return data
########################################################################################################################################################
#########################################################(New Updation of the CouponSerilizer)#####################################
######################Today new Updations please##############################
class TermsAndConditionsField(serializers.Field):
    """
    Accepts either a string or a list of strings and always stores as a single string in DB.
    Returns a list of strings in API responses.
    """
    def to_internal_value(self, data):
        # Accept list or string as input
        if isinstance(data, list):
            if not all(isinstance(v, str) for v in data):
                raise serializers.ValidationError("All items in terms and conditions list must be strings.")
            return "\n".join(data)  # store as single string
        elif isinstance(data, str):
            return data
        raise serializers.ValidationError("Terms and conditions must be a string or a list of strings.")

    def to_representation(self, value):
        if not value:
            return []
        # Split the stored string by newlines and return as list
        return [line.strip() for line in value.split("\n") if line.strip()]


class CouponSerializer(serializers.ModelSerializer):
    merchant_name = serializers.CharField(source='merchant.company_name', read_only=True)
    terms_and_conditions_text = TermsAndConditionsField()

    class Meta:
        model = Coupon
        fields = [
            'id',
            'merchant',
            'merchant_name',
            'title',
            'description',
            'image',
            'image_url',
            'points_required',
            'start_date',
            'expiry_date',
            'terms_and_conditions_text',
            'code',
            'status',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'status', 'code']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name in ['image', 'image_url']:
                field.required = False
                field.allow_blank = True
            elif field_name not in self.Meta.read_only_fields:
                field.required = True
                field.allow_blank = False
                field.error_messages['required'] = f"{field_name.replace('_', ' ').title()} is required."
                field.error_messages['blank'] = f"{field_name.replace('_', ' ').title()} cannot be blank."

    def validate(self, data):
        start = data.get('start_date', getattr(self.instance, 'start_date', None))
        expiry = data.get('expiry_date', getattr(self.instance, 'expiry_date', None))
        if start and expiry and expiry < start:
            raise serializers.ValidationError("Expiry date must be after start date.")
        return data

    def create(self, validated_data):
        # Auto-generate unique coupon code
        validated_data['code'] = f"COUP-{uuid.uuid4().hex[:8].upper()}"
        return super().create(validated_data)
###################################################################################
######################Today new Updations please##############################
class CustomerCouponActionSerializer(serializers.Serializer):
    """
    Serializer for customer coupon actions (scan/redeem).
    """
    coupon_code = serializers.CharField(required=True, max_length=100)
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
# -------------------------------
# Combined Dashboard Serializer
# -------------------------------
class CustomerHomeSerializer(serializers.Serializer):
    user = UserPointsSerializer()
    promotions = PromotionSerializer(many=True)
    available_coupons = CouponSerializer(many=True)
    recent_activity = UserActivitySerializer(many=True)
# -------------------------------=======================================================================================================
# ===============================Updated NEW API Details information of the api====================================================
# -------------------------------========================================================================================================

# ============================================================
# Customer REDEEMED COUPON SERIALIZER
# ============================================================
class RedeemedCouponSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='related_coupon.title', read_only=True)
    redeemed_date = serializers.DateTimeField(source='activity_date', read_only=True)
    status = serializers.SerializerMethodField()
    points_used = serializers.SerializerMethodField()

    class Meta:
        model = UserActivity
        fields = ['id', 'title', 'redeemed_date', 'status', 'points_used']

    def get_status(self, obj):
        return "redeemed"

    def get_points_used(self, obj):
        return abs(obj.points)  # ensure positive integer
