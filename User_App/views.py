from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.core.mail import send_mail
from django.conf import settings
from django.utils.encoding import force_bytes
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from .serializers import(
    UserRegistrationSerializer,
    UserLoginSerializer, 
    UserProfileSerializer,
######################################################################################################################
    ForgotPasswordSerializer, 
    ResetPasswordSerializer, 
    ChangePasswordSerializer,
    UserListSerializer,
    ##############################################################################################
    UserProfileUpdateSerializer   #####>=============> new api
)
from .models import User
from .serializers import QRScanSerializer  #########-> new api
from .serializers import MyQRSerializer   #########-> last new Updated
######################################################################################
############################################################################################################################
########################################################################################################################################################################
from rest_framework import viewsets  #########now New Updated 
from rest_framework.permissions import IsAuthenticatedOrReadOnly #########now New Updated 
##############################################################################################################################################################
###############################################################################################################################################################
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
#############################################################################################################################################################
import uuid   # ✅ added for unique QR generation
from Merchants_App.models import Merchant, Outlet, Coupon, UserActivity, UserPoints
from datetime import date, timedelta
from django.db.models import Count, Sum
###############################################################################
from django.shortcuts import render, redirect ###---->new updated
########################################################################################################################################################################################################
class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = get_tokens_for_user(user)

            # Create merchant record if user is a merchant
            if user.role == 'merchant':
                Merchant.objects.create(
                    user=user,
                    company_name=request.data.get('company_name', f"{user.name}'s Business")
                )

            return Response({
                'message': 'Registration Successful',
                'token': token,
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'name': user.name,
                    'role': user.role,
                    'phone': user.phone,

                    # ✅ NEW FIELDS
                    'address': user.address,
                    'postalcode': user.postalcode,
                    'region': user.region,
                    'state': user.state,
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
##############################################################################################################################################################
# ✅ User Login View (Updated)
##############################################################################################################################################################
class UserLoginView(APIView):
    permission_classes = [AllowAny]

    ABOUT_INFO = {
        "title": "Customer Loyalty & Rewards App",
        "description": (
            "This app helps customers earn points, claim coupons, and stay updated "
            "with the latest promotions and news. Customers can scan QR codes to collect "
            "points, merchants assign points, and admins manage content."
        )
    }

    DEFAULT_FAQS = [
        {"question": "How are you?", "answer": "Good, thank you! How about you?"},
        {"question": "Can I check my points balance?", "answer": "Yes, it's shown under your profile."},
        {"question": "How do I claim a coupon?", "answer": "Go to the rewards section to redeem coupons."},
        {"question": "Are there new promotions today?", "answer": "Check the promotions tab."},
        {"question": "Can I share rewards?", "answer": "Currently, rewards are personal."},
    ]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token = get_tokens_for_user(user)
            unique_qr_id = str(uuid.uuid4())

            # Profile image URL
            profile_image_url = (
                request.build_absolute_uri(user.profile_image.url)
                if getattr(user, 'profile_image', None) and hasattr(user.profile_image, 'url')
                else user.profile_image
            )

            # Merchant outlet info
            outlet_details = []
            if user.role == User.MERCHANT:
                try:
                    merchant = Merchant.objects.get(user=user)
                    outlets = Outlet.objects.filter(merchant=merchant)
                    for outlet in outlets:
                        outlet_details.append({
                            'id': str(outlet.id),
                            'name': outlet.name,
                            'address': outlet.address,
                            'city': outlet.city,
                            'state': outlet.state,
                            'country': outlet.country,
                            'latitude': outlet.latitude,
                            'longitude': outlet.longitude,
                            'contact_number': outlet.contact_number,
                            'outlet_image': (
                                request.build_absolute_uri(outlet.outlet_image.url)
                                if outlet.outlet_image else outlet.outlet_image_url
                            ),
                            'created_at': outlet.created_at,
                            'updated_at': outlet.updated_at,
                        })
                except Merchant.DoesNotExist:
                    outlet_details = []

            # ✅ RETURN NEW FIELDS
            user_data = {
                'id': str(user.id),
                'email': user.email,
                'name': user.name,
                'role': user.role,
                'phone': user.phone,
                'profile_image': profile_image_url,
                'unique_qr_id': unique_qr_id,

                # NEW FIELDS BELOW
                'address': user.address,
                'postalcode': user.postalcode,
                'region': user.region,
                'state': user.state,

                'outlet_details': outlet_details,
            }

            return Response({
                'message': 'Login Successful',
                'token': token,
                'user': user_data,
                'about': self.ABOUT_INFO,
                'faqs': self.DEFAULT_FAQS
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
##############################################################################################################################################################
# ✅ User Profile View (for logged-in user)
##############################################################################################################################################################
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

##############################################################################################################################################################
# ✅ User Search View (unchanged)
##############################################################################################################################################################
class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.query_params.get('role', None)
        search = request.query_params.get('search', None)
        phone = request.query_params.get('phone', None)

        users = User.objects.all()

        if role:
            users = users.filter(role__iexact=role)
        if search:
            users = users.filter(Q(name__icontains=search) | Q(email__icontains=search))
        if phone:
            users = users.filter(phone__icontains=phone)

        serializer = UserListSerializer(users, many=True)
        return Response({
            'count': users.count(),
            'users': serializer.data
        }, status=status.HTTP_200_OK)
#############################################################################################################################################################
################################################################################################################################################################
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            
            # Generate password reset token
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # In a real application, you would send an email here
            # For demo purposes, we'll return the token in the response
            reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
            
            # Send email (uncomment in production)
            """
            send_mail(
                'Password Reset Request',
                f'Click the link to reset your password: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            """
            
            return Response({
                'message': 'Password reset link has been sent to your email.',
                'uid': uid,
                'token': token,
                'reset_link': reset_link  # Remove this in production
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#############################################################################################################################################################
################################################################################################################################################################
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            new_password = serializer.validated_data['new_password']
            
            user.set_password(new_password)
            user.save()
            
            return Response({
                'message': 'Password has been reset successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#############################################################################################################################################################
################################################################################################################################################################
class ChangePasswordView(APIView):
    # permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            new_password = serializer.validated_data['new_password']
            
            user.set_password(new_password)
            user.save()
            
            return Response({
                'message': 'Password changed successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#############################################################################################################################################################
################################################################################################################################################################
class UserProfileUpdateView(APIView):
    """
    API for updating user profile (all editable fields)
    """
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = UserProfileUpdateSerializer(
            user,
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully.',
                'user': UserProfileSerializer(user).data  # returns new fields too
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        user = request.user
        serializer = UserProfileUpdateSerializer(
            user,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully.',
                'user': UserProfileSerializer(user).data  # returns new fields too
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#############################################################################################################################################################
################################################################################################################################################################
class QRScanAPIView(APIView):
    """
    Customer scans a QR and earns points.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = QRScanSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            result = serializer.save()
            return Response({
                'message': 'QR scanned successfully.',
                'points_awarded': result['points_awarded'],
                'total_points': result['total_points']
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#############################################################################################################################################################
################################################################################################################################################################
class MyQRAPIView(APIView):
    """
    GET /api/my-qr/
    Returns the personal QR code of the authenticated customer.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != 'customer':
            return Response(
                {'error': 'Only customers have personal QR codes.'},
                status=status.HTTP_403_FORBIDDEN
            )

        qr_data = user.generate_qr_code()  # returns dict

        return Response({
            'user_id': str(user.id),
            'email': user.email,
            'qr_text': qr_data['qr_text'],   # "user:<uuid>"
            'qr_image': qr_data['qr_image']  # base64 image for display
        }, status=status.HTTP_200_OK)
##########################################################################################
##############################################################################################################################################################################
##############################################################################################################################################################################
##############################################################################################################################################################################
def My_Home(request):
    return render(request,"index.html")


















