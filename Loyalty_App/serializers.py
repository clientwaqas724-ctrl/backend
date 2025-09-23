from rest_framework import serializers
from .models import Transaction
#######################################################################################################################################################
#######################################################################################################################################################
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id',
            'user',
            'merchant',
            'outlet',
            'coupon',
            'points',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    # Custom field-level validation for required fields
    def validate(self, attrs):
        errors = {}
        required_fields = ['user', 'merchant', 'outlet', 'points']

        for field in required_fields:
            if not attrs.get(field):
                errors[field] = f"{field.replace('_', ' ').capitalize()} is required."

        # points must never be zero
        if 'points' in attrs and attrs['points'] == 0:
            errors['points'] = "Points cannot be zero."

        if errors:
            raise serializers.ValidationError(errors)
        return attrs
#######################################################################################################################################################
#######################################################################################################################################################
