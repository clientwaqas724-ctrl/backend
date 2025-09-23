from rest_framework import serializers
from .models import Merchant,Outlet,Coupon,Promotion
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
