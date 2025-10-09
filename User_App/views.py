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
################################################################################################################################################################
class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = get_tokens_for_user(user)
            return Response({
                'token': token,
                'message': 'Registration Successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'role': user.role,
                    'phone': user.phone
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#############################################################################################################################################################
################################################################################################################################################################
class UserLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token = get_tokens_for_user(user)
            # ✅ Generate a temporary unique ID for QR generation
            unique_qr_id = str(uuid.uuid4())
            # ✅ Build absolute image URL if available
            image_path = (
                request.build_absolute_uri(user.profile_image)
                if user.profile_image else None
            )
            return Response({
                'token': token,
                'message': 'Login Successful',
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'name': user.name,
                    'role': user.role,
                    'phone': user.phone,
                    'profile_image': image_path,
                    'unique_qr_id': unique_qr_id,  # ✅ Added unique temporary ID
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
###########################################################################################################################################################
#############################################################################################################################################################
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
#############################################################################################################################################################
################################################################################################################################################################
class UserSearchView(APIView):
    """
    View for searching users based on role and other criteria
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Search users by role, name, or email
        Query parameters:
        - role: filter by specific role
        - search: search in name and email fields
        - phone: filter by phone number (optional)
        """
        # Get query parameters
        role = request.query_params.get('role', None)
        search = request.query_params.get('search', None)
        phone = request.query_params.get('phone', None)
        
        # Start with all users
        users = User.objects.all()
        
        # Apply role filter
        if role:
            users = users.filter(role__iexact=role)
        
        # Apply search filter (name and email)
        if search:
            users = users.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search)
            )
        
        # Apply phone filter if needed
        if phone:
            users = users.filter(phone__icontains=phone)
        
        # Serialize results
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
            user, data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully.',
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        user = request.user
        serializer = UserProfileUpdateSerializer(
            user, data=request.data, partial=True, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully.',
                'user': UserProfileSerializer(user).data
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
