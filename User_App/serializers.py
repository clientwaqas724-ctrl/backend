from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from .models import QRScan, CustomerPoints
############################################################################################################################
from Merchants_App.models import Outlet    #########new update for login
###############################################################
###new Updated###############################
############################################################################################################################
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'},
        error_messages={'required': 'This field is required.'}
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'},
        error_messages={'required': 'This field is required.'}
    )
    class Meta:
        model = User
        fields = ['email', 'name', 'tc', 'password', 'password2', 'role', 'phone', 'profile_image']
        extra_kwargs = {
            'email': {'required': True, 'error_messages': {'required': 'This field is required.'}},
            'name': {'required': True, 'error_messages': {'required': 'This field is required.'}},
            'tc': {'required': True, 'error_messages': {'required': 'This field is required.'}},
            'role': {'required': True, 'error_messages': {'required': 'This field is required.'}},
            'phone': {'required': True, 'error_messages': {'required': 'This field is required.'}},
            'profile_image': {'required': True, 'error_messages': {'required': 'This field is required.'}},
        }
    def validate(self, attrs):
        # Check if passwords match
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Check if email already exists
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "User with this email already exists."})
        
        # Check if phone already exists
        if User.objects.filter(phone=attrs['phone']).exists():
            raise serializers.ValidationError({"phone": "User with this phone number already exists."})
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)
############################################################################################################################
############################################################################################################################
class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        error_messages={'required': 'This field is required.'}
    )
    password = serializers.CharField(
        style={'input_type': 'password'},
        required=True,
        error_messages={'required': 'This field is required.'}
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password')
        else:
            raise serializers.ValidationError('Must include "email" and "password"')
        
        attrs['user'] = user
        return attrs
############################################################################################################################
############################################################################################################################
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'phone', 'profile_image', 'tc', 'created_at', 'updated_at']

###############################################################################################################################
###############################################################################################################################
class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users (might want to exclude sensitive fields like tc)
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'phone', 'profile_image', 'created_at','updated_at']
###############################################################################################################################
################################################################################################################################
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        error_messages={'required': 'Email field is required.'}
    )
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value
###############################################################################################################################
################################################################################################################################
class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField(
        required=True,
        error_messages={'required': 'UID field is required.'}
    )
    token = serializers.CharField(
        required=True,
        error_messages={'required': 'Token field is required.'}
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={'required': 'New password field is required.'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={'required': 'Confirm password field is required.'}
    )
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "Invalid user ID"})
        
        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({"token": "Invalid or expired token"})
        
        attrs['user'] = user
        return attrs
###############################################################################################################################
################################################################################################################################
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={'required': 'Old password field is required.'}
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={'required': 'New password field is required.'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={'required': 'Confirm password field is required.'}
    )
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
###############################################################################################################################
################################################################################################################################
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating the user's full profile details.
    Allows changing all editable fields.
    """
    class Meta:
        model = User
        fields = ['name', 'email', 'phone', 'role', 'profile_image', 'tc']

    def validate_email(self, value):
        user = self.context['request'].user
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This email is already taken.")
        return value

    def validate_phone(self, value):
        user = self.context['request'].user
        if User.objects.filter(phone=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This phone number is already taken.")
        return value
###############################################################################################################################
################################################################################################################################
class QRScanSerializer(serializers.Serializer):
    qr_code = serializers.CharField(required=True, error_messages={'required': 'QR code is required.'})

    def validate(self, attrs):
        user = self.context['request'].user
        if user.role != 'customer':
            raise serializers.ValidationError("Only customers can scan QR codes.")
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        qr_code = validated_data['qr_code']

        # Simulate point calculation (can depend on merchant QR logic)
        points_awarded = 10  # you can later make this dynamic

        # Log the scan
        QRScan.objects.create(customer=user, qr_code=qr_code, points_awarded=points_awarded)

        # Update or create total points
        wallet, created = CustomerPoints.objects.get_or_create(customer=user)
        wallet.total_points += points_awarded
        wallet.save()

        return {'points_awarded': points_awarded, 'total_points': wallet.total_points}
#######################################################################################################################
class MyQRSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    email = serializers.EmailField()
    qr_code = serializers.CharField()
##########################################################################################################################################################
##########################################################################################################################################################









