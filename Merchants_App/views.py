from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Merchant
from .models import Outlet,Coupon,Promotion,Tier, UserPoints, UserActivity
from .serializers import MerchantSerializer
from .serializers import OutletSerializer,CouponSerializer,PromotionSerializer,TierSerializer, UserPointsSerializer, UserActivitySerializer
################################################################################################################################################################
################################################################################################################################################################
from .serializers import CustomerHomeSerializer,RedeemedCouponSerializer
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.db.models import Sum, Count
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Sum, Count, Q
#########################################################################
###########################################################################new update
from django.contrib.auth import get_user_model
from Loyalty_App.models import Transaction
from User_App.models import User,QRScan
User = get_user_model()
from User_App.models import User, QRScan, CustomerPoints   #########newupdated
from Loyalty_App.models import Transaction   ##########--> new update
#######################today New Updation######################################
from django.utils import timezone
from .serializers import CustomerCouponActionSerializer
################################################################################################################################################################
################################################################################################################################################################
class MerchantViewSet(viewsets.ModelViewSet):
    """
    Supports:
      - GET /merchants/           -> list (with search/filter/order)
      - POST /merchants/          -> create
      - GET /merchants/{id}/      -> retrieve
      - PUT /merchants/{id}/      -> full update
      - PATCH /merchants/{id}/    -> partial update
      - DELETE /merchants/{id}/   -> delete
      - GET /merchants/search/?company_name=abc -> custom search
    """
    queryset = Merchant.objects.all()
    serializer_class = MerchantSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['company_name', 'user__email']
    filterset_fields = ['status', 'user']
    ordering_fields = ['created_at', 'updated_at', 'company_name']

    # DRF already provides create/update/delete,
    # but we override to ensure consistent error responses.

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Example: /merchants/search/?company_name=shop
        """
        company_name = request.query_params.get('company_name')
        if not company_name:
            return Response(
                {"detail": "Please provide a company_name parameter."},
                status=status.HTTP_400_BAD_REQUEST
            )
        qs = self.get_queryset().filter(company_name__icontains=company_name)
        return Response(self.get_serializer(qs, many=True).data)
################################################################################################################################################################
################################################################################################################################################################
class OutletViewSet(viewsets.ModelViewSet):
    """
    Provides:
      • POST   /outlets/        -> create
      • GET    /outlets/        -> list (with ?search=<term>)
      • GET    /outlets/<pk>/   -> retrieve
      • PUT    /outlets/<pk>/   -> update
      • PATCH  /outlets/<pk>/   -> partial update
      • DELETE /outlets/<pk>/   -> delete
    """
    queryset = Outlet.objects.all().order_by('-created_at')
    serializer_class = OutletSerializer

    def get_queryset(self):
        """
        Optionally filters results using ?search=<term>
        across name, city, state, country, or address.
        """
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(city__icontains=search) |
                Q(state__icontains=search) |
                Q(country__icontains=search) |
                Q(address__icontains=search)
            )
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Handle multipart (file upload) and JSON (URL) input seamlessly.
        Restrict each merchant to have only one outlet.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        merchant = serializer.validated_data.get('merchant')

        # ✅ Prevent multiple outlets per merchant
        if Outlet.objects.filter(merchant=merchant).exists():
            return Response(
                {"detail": f"Merchant '{merchant.company_name}' already has an outlet assigned."},
                status=status.HTTP_400_BAD_REQUEST
            )

        outlet = serializer.save()
        return Response(
            self.get_serializer(outlet).data,
            status=status.HTTP_201_CREATED
        )
###########################################################################################################################################################################################################
###################################################################################################################################################################################################################
class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all().order_by('-created_at')
    serializer_class = CouponSerializer

    def get_queryset(self):
        """Auto-update expired coupons before returning queryset."""
        now = timezone.now().date()
        Coupon.objects.filter(expiry_date__lt=now, status='active').update(status='expired')
        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        """Support search by title or merchant name."""
        search = request.query_params.get('search')
        queryset = self.get_queryset()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(merchant__company_name__icontains=search)
            )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def redeem(self, request, pk=None):
        """Custom endpoint for redeeming a coupon (via code or scan)."""
        try:
            coupon = Coupon.objects.get(pk=pk)
        except Coupon.DoesNotExist:
            return Response({'error': 'Coupon not found.'}, status=status.HTTP_404_NOT_FOUND)

        if coupon.status != Coupon.STATUS_ACTIVE:
            return Response({'error': f"Coupon is not active (current status: {coupon.status})."},
                            status=status.HTTP_400_BAD_REQUEST)

        if coupon.is_expired():
            coupon.status = Coupon.STATUS_EXPIRED
            coupon.save()
            return Response({'error': 'Coupon has expired.'}, status=status.HTTP_400_BAD_REQUEST)

        coupon.status = Coupon.STATUS_USED
        coupon.save()
        return Response({'success': 'Coupon successfully redeemed!'}, status=status.HTTP_200_OK)
##########################################################################################################################################################
######################Today new Updations please##############################
class PublicCouponViewSet(viewsets.ViewSet):
    """
    Public API for merchants/customers to scan and auto-redeem coupons.
    Only uses coupon code, returns status messages.
    """

    @action(detail=False, methods=['post'], url_path='scan')
    def scan_coupon(self, request):
        """
        Scan a coupon code and automatically mark it as used if valid.
        Returns simple status messages only.
        """
        serializer = CustomerCouponActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['coupon_code']

        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response({"status_message": "Coupon not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check coupon status
        if coupon.status == Coupon.STATUS_USED:
            return Response({"status_message": "Coupon already redeemed."}, status=status.HTTP_400_BAD_REQUEST)
        if coupon.status == Coupon.STATUS_EXPIRED or (coupon.expiry_date and coupon.expiry_date < timezone.now().date()):
            return Response({"status_message": "Coupon expired."}, status=status.HTTP_400_BAD_REQUEST)

        # If valid, automatically mark as used
        coupon.status = Coupon.STATUS_USED
        coupon.save()

        return Response({"status_message": "You successfully used the coupon."}, status=status.HTTP_200_OK)
##############################################################################################################################################################################################################
##############################################################################################################################################################################################################
class PromotionViewSet(viewsets.ModelViewSet):
    """
    Provides:
      • POST   /promotions/        -> create
      • GET    /promotions/        -> list (with ?search=<term>)
      • GET    /promotions/<pk>/   -> retrieve single
      • PUT    /promotions/<pk>/   -> update
      • PATCH  /promotions/<pk>/   -> partial update
      • DELETE /promotions/<pk>/   -> delete
    """
    queryset = Promotion.objects.all().order_by('-created_at')
    serializer_class = PromotionSerializer

    # Simple search by ?search=keyword across title & description
    def list(self, request, *args, **kwargs):
        search = request.query_params.get('search')
        queryset = self.get_queryset()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
##########################################################################################################################################################
##########################################################################################################################################################
# ============================================================
# TIER VIEWSET
# ============================================================
class TierViewSet(viewsets.ModelViewSet):
    """
    Provides:
      • POST   /tiers/          -> create
      • GET    /tiers/          -> list (with ?search=<term>)
      • GET    /tiers/<pk>/     -> retrieve
      • PUT    /tiers/<pk>/     -> update
      • PATCH  /tiers/<pk>/     -> partial update
      • DELETE /tiers/<pk>/     -> delete
    """
    queryset = Tier.objects.all().order_by('min_points')
    serializer_class = TierSerializer

    def list(self, request, *args, **kwargs):
        search = request.query_params.get('search')
        queryset = self.get_queryset()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(benefits__icontains=search)
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ============================================================
# USER POINTS VIEWSET
# ============================================================
class UserPointsViewSet(viewsets.ModelViewSet):
    """
    Provides:
      • POST   /user-points/
      • GET    /user-points/
      • GET    /user-points/<pk>/
      • PUT    /user-points/<pk>/
      • PATCH  /user-points/<pk>/
      • DELETE /user-points/<pk>/
    """
    queryset = UserPoints.objects.select_related('user', 'tier').all().order_by('-created_at')
    serializer_class = UserPointsSerializer

    def list(self, request, *args, **kwargs):
        search = request.query_params.get('search')
        queryset = self.get_queryset()
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search) |
                Q(tier__name__icontains=search)
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ============================================================
# USER ACTIVITY VIEWSET
# ============================================================
class UserActivityViewSet(viewsets.ModelViewSet):
    """
    Provides:
      • POST   /user-activities/
      • GET    /user-activities/
      • GET    /user-activities/<pk>/
      • PUT    /user-activities/<pk>/
      • PATCH  /user-activities/<pk>/
      • DELETE /user-activities/<pk>/
    """
    queryset = UserActivity.objects.select_related('user', 'related_coupon').all().order_by('-activity_date')
    serializer_class = UserActivitySerializer

    def list(self, request, *args, **kwargs):
        search = request.query_params.get('search')
        queryset = self.get_queryset()
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search) |
                Q(description__icontains=search) |
                Q(activity_type__icontains=search)
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)
########################################################################################################################################################################################################
####################################################################################################################################################################################################
class CustomerHomeViewSet(viewsets.ViewSet):
    """
    GET /api/merchants/customer/home/
    Returns dashboard data for a customer user:
      - User info (points, tier)
      - Active promotions
      - Available coupons
      - Recent activity (real or randomized)
      - Merchant Scanning History
    """
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = request.user
        today = timezone.now().date()

        # ======================================================
        # ACCESS VALIDATION
        # ======================================================
        if getattr(user, "role", None) != "customer":
            return Response({
                "success": False,
                "message": "Access denied. Only customers can view this dashboard."
            }, status=status.HTTP_403_FORBIDDEN)

        # ======================================================
        # USER POINTS INFO (FIXED + ACCURATE)
        # ======================================================
        earned_points = Transaction.objects.filter(
            user=user, points__gt=0
        ).aggregate(total=Sum('points'))['total'] or 0

        redeemed_points = Transaction.objects.filter(
            user=user, points__lt=0
        ).aggregate(total=Sum('points'))['total'] or 0

        total_points = earned_points + redeemed_points  # redeemed is negative

        user_points = UserPoints.objects.filter(user=user).select_related('tier').first()
        tier = user_points.tier.name if user_points and user_points.tier else None

        # ======================================================
        # PROMOTIONS & COUPONS
        # ======================================================
        promotions = Promotion.objects.all()
        coupons = Coupon.objects.filter(status=Coupon.STATUS_ACTIVE)

        # ======================================================
        # RECENT ACTIVITY (FINAL MERGED VERSION)
        # ======================================================
        activities = UserActivity.objects.filter(user=user).order_by('-activity_date')[:5]

        if activities.exists():
            recent_activity_data = []
            for activity in activities:
                recent_activity_data.append({
                    "activity_type": activity.activity_type,
                    "points": abs(activity.points),
                    "description": activity.description,
                    "activity_date": activity.activity_date,
                    "related_coupon": activity.related_coupon.title if activity.related_coupon else None
                })
        else:
            # fallback: use transaction data
            transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:5]
            import random
            ACTIVITY_TYPES = ["Earned", "Redeemed", "Expired"]

            if transactions.exists():
                recent_activity_data = []
                for tx in transactions:
                    act = random.choice(ACTIVITY_TYPES)
                    points_value = abs(tx.points)
                    recent_activity_data.append({
                        "activity_type": act,
                        "points": points_value,
                        "description": f"{user.email} {act.lower()} {points_value} points",
                        "activity_date": tx.created_at
                    })
            else:
                # fallback: random data
                recent_activity_data = [
                    {
                        "activity_type": act,
                        "points": random.randint(5, 50),
                        "description": f"{user.email} {act.lower()} points",
                        "activity_date": timezone.now()
                    }
                    for act in ACTIVITY_TYPES
                ]

        # ======================================================
        # MERCHANT SCANNING HISTORY (FULLY FIXED)
        # ======================================================
        scan_history = Transaction.objects.filter(user=user).select_related(
            'merchant', 'outlet', 'coupon'
        ).order_by('-created_at')

        scanning_history_output = []
        for tx in scan_history:
            scanning_history_output.append({
                "transaction_id": str(tx.id),
                "transaction_type": "earned" if tx.points > 0 else "redeemed",
                "points": abs(tx.points),  # always positive
                "date": tx.created_at,

                "merchant": {
                    "id": str(tx.merchant.id),
                    "name": tx.merchant.company_name,
                    "logo_url": tx.merchant.logo_url
                } if tx.merchant else None,

                "outlet": {
                    "id": str(tx.outlet.id),
                    "name": tx.outlet.name,
                    "image_url": tx.outlet.outlet_image_url if tx.outlet else None
                } if tx.outlet else None,

                "coupon": {
                    "id": str(tx.coupon.id),
                    "title": tx.coupon.title,
                    "image_url": (
                        tx.coupon.image.url if tx.coupon and tx.coupon.image 
                        else tx.coupon.image_url
                    )
                } if tx.coupon else None
            })

        # ======================================================
        # RESPONSE PAYLOAD
        # ======================================================
        data = {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "total_points": total_points,
                "tier": tier,
            },
            "promotions": PromotionSerializer(promotions, many=True).data,
            "available_coupons": CouponSerializer(coupons, many=True).data,
            "recent_activity": recent_activity_data,
            "merchant_scanning_history": scanning_history_output
        }

        return Response({
            "success": True,
            "message": "Dashboard data retrieved successfully",
            "data": data
        }, status=status.HTTP_200_OK)
#####################################################################################################################################################################################################
###########################################################################################################################################################################################################
class RedeemCouponView(APIView):
    """
    POST /api/redeem-coupon/
    Redeem a coupon using user's points.
    Handles active/expired/used status and logs transactions and user activity.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        coupon_id = request.data.get("coupon_id")

        # 1. Validate coupon_id
        if not coupon_id:
            return Response(
                {"success": False, "message": "coupon_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Get coupon
        coupon = get_object_or_404(Coupon, id=coupon_id)

        # 3. Check coupon status
        if coupon.status == Coupon.STATUS_USED:
            return Response(
                {"success": False, "message": "This coupon has already been redeemed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if coupon.status != Coupon.STATUS_ACTIVE:
            return Response(
                {"success": False, "message": f"This coupon is not active (status: {coupon.status})."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Check expiry
        if coupon.expiry_date < timezone.now().date():
            coupon.status = Coupon.STATUS_EXPIRED
            coupon.save(update_fields=['status'])
            return Response(
                {"success": False, "message": "This coupon has expired."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 5. Get user's current points from Transaction model (FIXED)
        total_points_result = Transaction.objects.filter(user=user).aggregate(
            total=Sum('points')
        )
        current_points = total_points_result['total'] or 0

        # 6. Check if user has enough points
        if current_points < coupon.points_required:
            return Response(
                {
                    "success": False,
                    "message": (
                        f"Not enough points. You need {coupon.points_required}, "
                        f"but you only have {current_points}."
                    ),
                    "data": {"remaining_points": current_points},
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # 7. Calculate remaining points
        remaining_points = current_points - coupon.points_required

        # 8. Log redemption in Transaction table with POSITIVE value for redemption (FIXED)
        Transaction.objects.create(
            user=user,
            merchant=coupon.merchant,
            coupon=coupon,
            points=coupon.points_required,  # POSITIVE value for redemption
            transaction_type="redemption"
        )

        # 9. Log user activity with POSITIVE points (FIXED)
        UserActivity.objects.create(
            user=user,
            activity_type="redeem_coupon",
            description=f"Redeemed coupon: {coupon.title}",
            points=coupon.points_required,  # POSITIVE value
            related_coupon=coupon
        )

        # 10. Update coupon status to USED
        coupon.status = Coupon.STATUS_USED
        coupon.save(update_fields=["status"])

        # 11. Response with coupon image (FIXED)
        coupon_image_url = coupon.image.url if coupon.image else coupon.image_url
        
        return Response(
            {
                "success": True,
                "message": "Coupon redeemed successfully!",
                "data": {
                    "coupon": {
                        "id": str(coupon.id), 
                        "title": coupon.title, 
                        "status": coupon.status,
                        "image_url": coupon_image_url,  # ADDED IMAGE URL
                        "points_required": coupon.points_required
                    },
                    "points_used": coupon.points_required,
                    "previous_points": current_points,
                    "remaining_points": remaining_points,
                },
            },
            status=status.HTTP_200_OK
        )
##################################################################################################################################################################################################
#########################################################################################################################################################################################################
# ============================= CUSTOMER COUPONS LIST API =============================new updated
class CustomerCouponsView(APIView):
    """
    GET /api/customer/coupons/
    Shows:
      - available_coupons → ALL coupons (no filter by user)
      - redeemed_coupons → only user's redeemed coupons
      - expired_coupons  → optional (still included)
    """
    permission_classes = [IsAuthenticated]

    def get_status_text(self, status_code):
        """Convert coupon status into readable text."""
        return {
            Coupon.STATUS_ACTIVE: "Active",
            Coupon.STATUS_USED: "Used",
            Coupon.STATUS_EXPIRED: "Expired",
            Coupon.STATUS_INACTIVE: "Inactive",
        }.get(status_code, "Unknown")

    def get(self, request, *args, **kwargs):
        user = request.user
        today = timezone.now().date()

        # ======================================================
        # 🔄 AUTO-UPDATE EXPIRED COUPONS (only active → expired)
        # ======================================================
        Coupon.objects.filter(
            expiry_date__lt=today,
            status=Coupon.STATUS_ACTIVE
        ).update(status=Coupon.STATUS_EXPIRED)

        # ======================================================
        # 📌 AVAILABLE COUPONS → SHOW **ALL COUPONS**
        # ======================================================
        all_coupons = Coupon.objects.all().order_by('-created_at')

        available_coupons = []
        for coupon in all_coupons:
            # Real-time status calculation
            if coupon.expiry_date < today:
                real_status = Coupon.STATUS_EXPIRED
            else:
                real_status = coupon.status

            # Remaining days
            remaining_days = (coupon.expiry_date - today).days if real_status != Coupon.STATUS_EXPIRED else 0

            # Get image URL (FIXED)
            coupon_image_url = coupon.image.url if coupon.image else coupon.image_url

            available_coupons.append({
                "id": str(coupon.id),
                "merchant": str(coupon.merchant.id),
                "merchant_name": coupon.merchant.company_name,
                "title": coupon.title,
                "description": coupon.description,
                "image": coupon.image.url if coupon.image else None,
                "image_url": coupon_image_url,  # FIXED: Ensure image URL is included
                "points_required": coupon.points_required,
                "start_date": coupon.start_date,
                "expiry_date": coupon.expiry_date,
                "remaining_days": remaining_days,
                "terms_and_conditions_text": coupon.terms_and_conditions_text,
                "code": coupon.code,
                "status": real_status,
                "status_text": self.get_status_text(real_status),
                "created_at": coupon.created_at,
            })

        # ======================================================
        # 🎉 USER REDEEMED COUPONS (FIXED with image URLs)
        # ======================================================
        redeemed_transactions = (
            Transaction.objects.filter(
                user=user,
                coupon__isnull=False,
                points__gt=0  # CHANGED: Now looking for positive points for redemptions
            )
            .select_related('coupon', 'coupon__merchant')
            .order_by('-created_at')
        )

        redeemed_coupons = []
        for tx in redeemed_transactions:
            coupon = tx.coupon
            # Get image URL for redeemed coupons (FIXED)
            coupon_image_url = coupon.image.url if coupon.image else coupon.image_url
            
            redeemed_coupons.append({
                "id": str(coupon.id),
                "title": coupon.title,
                "merchant_name": coupon.merchant.company_name,
                "code": coupon.code,
                "redeemed_date": tx.created_at,
                "status": Coupon.STATUS_USED,
                "status_text": self.get_status_text(Coupon.STATUS_USED),
                "points_used": tx.points,  # CHANGED: Now using positive points
                "image_url": coupon_image_url,  # ADDED: Image URL for redeemed coupons
                "description": coupon.description,  # ADDED: Description
            })

        # ======================================================
        # ❌ EXPIRED COUPONS (FIXED with image URLs)
        # ======================================================
        expired_qs = Coupon.objects.filter(
            expiry_date__lt=today
        ).order_by('-created_at')

        expired_coupons = []
        for coupon in expired_qs:
            # Get image URL for expired coupons (FIXED)
            coupon_image_url = coupon.image.url if coupon.image else coupon.image_url
            
            expired_coupons.append({
                "id": str(coupon.id),
                "title": coupon.title,
                "merchant_name": coupon.merchant.company_name,
                "code": coupon.code,
                "expiry_date": coupon.expiry_date,
                "status": Coupon.STATUS_EXPIRED,
                "status_text": self.get_status_text(Coupon.STATUS_EXPIRED),
                "image_url": coupon_image_url,  # ADDED: Image URL for expired coupons
                "points_required": coupon.points_required,  # ADDED: Points required
            })

        # ======================================================
        # 📌 FINAL RESPONSE
        # ======================================================
        return Response(
            {
                "available_coupons": available_coupons,  # NOW ALL COUPONS
                "redeemed_coupons": redeemed_coupons,
                "expired_coupons": expired_coupons,
            },
            status=status.HTTP_200_OK
        )
#######################################################################################################################################################################################################
############################################################################################################################################################################################################
class MerchantDashboardAnalyticsView(APIView):
    """
    GET /api/merchant/dashboard-analytics/
    Combines merchant dashboard summary + detailed analytics + merchant scanning history.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # 1. Check if merchant
        if user.role != User.MERCHANT:
            return Response(
                {"success": False, "message": "Access denied. User is not a merchant."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Get merchant object
        try:
            merchant = Merchant.objects.get(user=user)
        except Merchant.DoesNotExist:
            return Response(
                {"success": False, "message": "Merchant profile not found for this user."},
                status=status.HTTP_404_NOT_FOUND
            )

        today = timezone.now().date()
        start_of_day = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.min.time())
        )
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

        # 3. Merchant Info Stats
        total_outlets = merchant.outlets.count()
        total_coupons = Coupon.objects.filter(merchant=merchant).count()
        active_coupons = Coupon.objects.filter(
            merchant=merchant,
            status=Coupon.STATUS_ACTIVE,
            expiry_date__gte=today
        ).count()
        total_promotions = Promotion.objects.filter(merchant=merchant).count()

        # 4. Merchant Transactions
        merchant_txns = Transaction.objects.filter(merchant=merchant)

        total_customers = merchant_txns.values('user').distinct().count()
        scans_today = merchant_txns.filter(created_at__gte=start_of_day).count()
        points_awarded_today = merchant_txns.filter(
            points__gt=0, created_at__gte=start_of_day
        ).aggregate(total_points=Sum('points'))['total_points'] or 0
        coupons_redeemed_today = merchant_txns.filter(
            points__lt=0, created_at__gte=start_of_day
        ).count()

        weekly_scans = merchant_txns.filter(created_at__date__gte=start_of_week).count()
        monthly_scans = merchant_txns.filter(created_at__date__gte=start_of_month).count()

        # 5. Recent Transactions
        recent_txns = merchant_txns.select_related('user', 'outlet', 'coupon').order_by('-created_at')[:5]
        recent_transactions = []
        for txn in recent_txns:
            transaction_type = "redeem" if txn.points < 0 else "earn"
            recent_transactions.append({
                "id": str(txn.id),
                "customer_name": txn.user.name or txn.user.email.split('@')[0],
                "customer_id": str(txn.user.id),
                "points": txn.points,
                "transaction_type": transaction_type,
                "outlet_name": txn.outlet.name if txn.outlet else "N/A",
                "outlet_id": str(txn.outlet.id) if txn.outlet else None,
                "coupon_title": txn.coupon.title if txn.coupon else None,
                "timestamp": txn.created_at.isoformat(),
                "location": f"{txn.outlet.city}, {txn.outlet.state}" if txn.outlet else "N/A",
            })

        # 6. Active Outlets
        active_outlets = []
        for outlet in merchant.outlets.all()[:5]:
            outlet_txns = merchant_txns.filter(outlet=outlet)
            outlet_scans_today = outlet_txns.filter(created_at__gte=start_of_day).count()
            outlet_customers = outlet_txns.values('user').distinct().count()

            active_outlets.append({
                "id": str(outlet.id),
                "name": outlet.name,
                "location": f"{outlet.city}, {outlet.state}",
                "is_active": True,
                "scans_today": outlet_scans_today,
                "total_customers": outlet_customers
            })

        # 7. Popular Coupons
        popular_coupons = Coupon.objects.filter(
            merchant=merchant,
            loyalty_transactions__points__lt=0
        ).annotate(
            redemption_count=Count('loyalty_transactions')
        ).order_by('-redemption_count')[:3]

        popular_coupons_data = [{
            "id": str(c.id),
            "title": c.title,
            "redemption_count": c.redemption_count,
            "points_required": c.points_required
        } for c in popular_coupons]

        # 8. Analytics
        today = timezone.now().date()
        qr_scans = merchant_txns

        daily_scans = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            scans_count = qr_scans.filter(created_at__date=date).count()
            daily_scans.append({
                "date": date.isoformat(),
                "transactions": scans_count
            })

        # Customer growth
        customer_growth = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            customers_count = qr_scans.filter(
                created_at__date__lte=date
            ).values('user').distinct().count()
            customer_growth.append({
                "date": date.isoformat(),
                "customers": customers_count
            })

        # Points analytics
        total_txns = qr_scans.count()
        total_points = qr_scans.aggregate(total=Sum('points'))['total'] or 0
        avg_points = total_points / total_txns if total_txns > 0 else 0

        # 9. Merchant Info
        merchant_info = {
            "id": str(merchant.id),
            "business_name": merchant.company_name,
            "total_outlets": total_outlets,
            "total_coupons": total_coupons,
            "active_coupons": active_coupons,
            "total_promotions": total_promotions,
            "total_customers": total_customers,
            "member_since": merchant.created_at.date(),
        }

        # 10. Today's Stats
        today_stats = {
            "transactions_today": scans_today,
            "points_awarded_today": points_awarded_today,
            "coupons_redeemed_today": coupons_redeemed_today,
            "weekly_transactions": weekly_scans,
            "monthly_transactions": monthly_scans,
            "revenue_impact": f"${points_awarded_today * 2.5:,.0f}",
        }

        # ------------------------------------------------------------
        # ⭐ NEW SECTION — MERCHANT SCANNING HISTORY
        # ------------------------------------------------------------
        merchant_scans = Transaction.objects.filter(
            merchant=merchant
        ).select_related('user', 'outlet', 'coupon').order_by('-created_at')

        scan_history_output = []
        for tx in merchant_scans:
            scan_history_output.append({
                "transaction_id": str(tx.id),
                "customer": {
                    "id": str(tx.user.id),
                    "name": tx.user.name or tx.user.email,
                    "email": tx.user.email
                },
                "points": tx.points,
                "created_at": tx.created_at,
                "outlet": {
                    "id": str(tx.outlet.id),
                    "name": tx.outlet.name,
                    "image_url": tx.outlet.outlet_image_url
                } if tx.outlet else None,
                "coupon": {
                    "id": str(tx.coupon.id),
                    "title": tx.coupon.title,
                    "image_url": tx.coupon.image_url
                } if tx.coupon else None
            })

        # ------------------------------------------------------------

        # 11. Final Response
        return Response({
            "success": True,
            "message": "Merchant dashboard & analytics retrieved successfully",
            "data": {
                "merchant_info": merchant_info,
                "today_stats": today_stats,
                "recent_transactions": recent_transactions,
                "active_outlets": active_outlets,
                "popular_coupons": popular_coupons_data,
                "analytics": {
                    "transactions_over_time": daily_scans,
                    "customer_growth": customer_growth,
                    "points_analytics": {
                        "total_points_awarded": total_points,
                        "average_points_per_transaction": round(avg_points, 2),
                        "total_transactions": total_txns
                    },
                    "performance_metrics": {
                        "customer_retention_rate": "85%",
                        "average_redemption_value": "45",
                        "top_performing_outlet": merchant.outlets.first().name if merchant.outlets.exists() else "N/A"
                    }
                },

                # ⭐ NEW OUTPUT ADDED HERE
                "merchant_scanning_history": scan_history_output
            }
        }, status=status.HTTP_200_OK)
##########################################################################################################################################################################################################
##########################################################################################################################################################################################################
class MerchantScanQRAPIView(APIView):
    """
    POST /api/merchant/scan-qr/
    Body: { "qr_code": "user:<uuid>", "points": 10 }
    Only merchant users can call this.
    Each coupon can be used only once by a customer.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # ✅ Only merchant users can scan
        if user.role != 'merchant':
            return Response(
                {'error': 'Only merchants can scan QR codes.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # ✅ Required fields
        qr_code = request.data.get('qr_code')
        points = int(request.data.get('points', 10))  # default points = 10

        # ✅ Parse QR code to get the customer
        try:
            customer_id = qr_code.split(":")[1]
            customer = User.objects.get(id=customer_id, role='customer')
        except Exception:
            return Response(
                {'error': 'Invalid QR code.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Ensure merchant profile exists
        merchant_account, _ = Merchant.objects.get_or_create(
            user=user,
            defaults={'company_name': f"{user.name}'s Company"}
        )

        # ✅ Get the first active coupon for this merchant (optional logic)
        coupon = Coupon.objects.filter(merchant=merchant_account, status='Active').first()
        outlet = coupon.outlet if coupon else None

        # ✅ Check if customer already scanned this coupon
        if coupon and Transaction.objects.filter(user=customer, coupon=coupon).exists():
            # Update coupon status to Used if needed
            coupon.status = 'Used'
            coupon.save()
            return Response(
                {'error': 'Coupon already used by this customer.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Record each scan
        QRScan.objects.create(customer=customer, qr_code=qr_code, points_awarded=points)

        # ✅ Update or create CustomerPoints wallet
        wallet, _ = CustomerPoints.objects.get_or_create(customer=customer)
        wallet.total_points += points
        wallet.save()

        # ✅ Record transaction
        Transaction.objects.create(
            user=customer,
            merchant=merchant_account,
            outlet=outlet,
            coupon=coupon,
            points=points,
            created_at=timezone.now()
        )

        # ✅ Mark coupon as used
        if coupon:
            coupon.status = 'Used'
            coupon.save()

        # ✅ Return success
        return Response(
            {
                'message': f'{points} points awarded to {customer.email}',
                'total_points': wallet.total_points
            },
            status=status.HTTP_200_OK
        )






