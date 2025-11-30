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
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
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
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = request.user

        if getattr(user, "role", None) != "customer":
            return Response({
                "success": False,
                "message": "Access denied. Only customers can view this dashboard."
            }, status=status.HTTP_403_FORBIDDEN)

        # =============================
        # ✅ GET USER POINTS (UPDATED LIVE)
        # =============================
        try:
            user_points_obj = UserPoints.objects.get(user=user)
            user_points_obj.refresh_from_db()  # ensures latest deduction appears
            total_points = int(user_points_obj.total_points or 0)
            tier_name = user_points_obj.tier.name if user_points_obj.tier else None
        except UserPoints.DoesNotExist:
            total_points = 0
            tier_name = None

        # =============================
        # ✅ PROMOTIONS & COUPONS
        # =============================
        promotions = Promotion.objects.all()
        coupons = Coupon.objects.filter(status=Coupon.STATUS_ACTIVE)

        # =============================
        # ✅ RECENT ACTIVITY (SHOW ABS POSITIVE ALWAYS)
        # =============================
        activities = UserActivity.objects.filter(user=user).order_by('-activity_date')[:5]

        recent_activity_data = [
            {
                "activity_type": a.activity_type,
                "points": abs(int(a.points or 0)),
                "description": a.description,
                "activity_date": a.activity_date.isoformat() if a.activity_date else None,
                "related_coupon": a.related_coupon.title if a.related_coupon else None
            }
            for a in activities
        ]

        # =============================
        # ✅ TRANSACTIONS HISTORY (POSITIVE ONLY)
        # =============================
        scan_history = Transaction.objects.filter(user=user).select_related(
            'merchant', 'outlet', 'coupon'
        ).order_by('-created_at')

        scanning_history_output = []

        for tx in scan_history:
            scanning_history_output.append({
                "transaction_id": str(tx.id),
                "transaction_type": "earned" if tx.points > 0 else "redeemed",
                "points": abs(int(tx.points or 0)),
                "date": tx.created_at.isoformat() if tx.created_at else None,
                "merchant": {
                    "id": str(tx.merchant.id),
                    "name": getattr(tx.merchant, "company_name", None),
                    "logo_url": getattr(tx.merchant, "logo_url", None)
                } if tx.merchant else None,
                "outlet": {
                    "id": str(tx.outlet.id),
                    "name": getattr(tx.outlet, "name", None),
                    "image_url": getattr(tx.outlet, "outlet_image_url", None)
                } if tx.outlet else None,
                "coupon": {
                    "id": str(tx.coupon.id),
                    "title": tx.coupon.title,
                    "image_url": tx.coupon.image.url if tx.coupon.image else tx.coupon.image_url
                } if tx.coupon else None
            })

        return Response({
            "success": True,
            "message": "Dashboard data retrieved successfully",
            "data": {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "name": getattr(user, "name", None),
                    "role": getattr(user, "role", None),
                    "total_points": total_points,   # UPDATED CLEAN VALUE
                    "tier": tier_name,
                },
                "promotions": PromotionSerializer(promotions, many=True).data,
                "available_coupons": CouponSerializer(coupons, many=True).data,
                "recent_activity": recent_activity_data,
                "merchant_scanning_history": scanning_history_output
            }
        }, status=status.HTTP_200_OK)



############################################################################################################
#########################################  REDEEM COUPON  ##################################################
############################################################################################################

class RedeemCouponView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        coupon_id = request.data.get("coupon_id")

        if not coupon_id:
            return Response(
                {"success": False, "message": "coupon_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        coupon = get_object_or_404(Coupon, id=coupon_id)

        # Check expiry
        if coupon.expiry_date < timezone.now().date():
            return Response(
                {"success": False, "message": "This coupon has expired."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            user_points_obj, created = UserPoints.objects.get_or_create(
                user=user,
                defaults={"total_points": 0}
            )

            # Lock row to prevent race conditions
            user_points = UserPoints.objects.select_for_update().get(pk=user_points_obj.pk)

            # Prevent redeeming same coupon twice (checks positive and negative)
            already_redeemed = Transaction.objects.filter(
                user=user,
                coupon=coupon
            ).exists()

            if already_redeemed:
                return Response({
                    "success": False,
                    "message": "You already redeemed this coupon.",
                    "remaining_points": user_points.total_points
                }, status=status.HTTP_400_BAD_REQUEST)

            points_required = int(coupon.points_required or 0)

            # Check sufficient points
            if user_points.total_points < points_required:
                return Response({
                    "success": False,
                    "message": "Not enough points",
                    "remaining_points": user_points.total_points
                }, status=status.HTTP_400_BAD_REQUEST)

            # ============================================
            # 🔥 DEDUCT USER POINTS (LIVE UPDATE)
            # ============================================
            UserPoints.objects.filter(pk=user_points.pk).update(
                total_points=F("total_points") - points_required
            )
            user_points.refresh_from_db()  # ensures fresh value

            # ============================================
            # 🔥 SAVE TRANSACTION AS POSITIVE POINTS
            # ============================================
            Transaction.objects.create(
                user=user,
                merchant=coupon.merchant,
                coupon=coupon,
                points=points_required   # 👍 POSITIVE ONLY
            )

            # ============================================
            # 🔥 LOG NEGATIVE ACTIVITY (to show deduction history)
            # ============================================
            UserActivity.objects.create(
                user=user,
                activity_type="redeem_coupon",
                description=f"Redeemed coupon {coupon.title}",
                points=-points_required,
                related_coupon=coupon
            )

            return Response({
                "success": True,
                "message": "Coupon redeemed successfully",
                "remaining_points": user_points.total_points,
                "coupon": {
                    "id": str(coupon.id),
                    "title": coupon.title,
                    "points_required": points_required,
                    "image": coupon.image.url if coupon.image else coupon.image_url
                }
            }, status=status.HTTP_200_OK)
##################################################################################################################################################################################################
#########################################################################################################################################################################################################
# ============================= CUSTOMER COUPONS LIST API =============================new updated
# ============================= CUSTOMER COUPONS LIST API =============================
class CustomerCouponsView(APIView):
    """
    GET /api/customer/coupons/
    Returns:
      - user_points
      - available_coupons (ALL coupons, not expired)
      - redeemed_coupons (user history)
      - available_coupons includes user_has_redeemed flag
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        today = timezone.now().date()

        # Ensure user points exist
        user_points_obj, _ = UserPoints.objects.get_or_create(
            user=user,
            defaults={"total_points": 0}
        )
        user_points_obj.refresh_from_db(fields=["total_points"])
        current_points = int(user_points_obj.total_points or 0)

        # ==============================================================
        # ALL AVAILABLE COUPONS (Not expired, independent of user)
        # ==============================================================
        available_coupons = Coupon.objects.filter(
            expiry_date__gte=today
        ).order_by('-created_at')

        # ==============================================================
        # Redeemed coupons list (NEW LOGIC)
        # ==============================================================
        redeemed_coupon_ids = set(
            Transaction.objects.filter(
                user=user,
                coupon__isnull=False
            ).values_list("coupon_id", flat=True)
        )

        # Build available coupons output
        available_coupons_data = []
        for coupon in available_coupons:
            available_coupons_data.append({
                "id": str(coupon.id),
                "merchant_name": coupon.merchant.company_name if coupon.merchant else None,
                "title": coupon.title,
                "description": coupon.description,
                "image": coupon.image.url if getattr(coupon, "image", None) else getattr(coupon, "image_url", None),
                "points_required": coupon.points_required,
                "expiry_date": coupon.expiry_date,
                "status": coupon.status,
                "user_has_redeemed": coupon.id in redeemed_coupon_ids,
            })

        # ==============================================================
        # Redeemed coupons history
        # ==============================================================
        redeemed_transactions = Transaction.objects.filter(
            user=user,
            coupon__isnull=False
        ).select_related("coupon", "coupon__merchant").order_by("-created_at")

        redeemed_coupons_data = []
        for tx in redeemed_transactions:
            coupon = tx.coupon
            redeemed_coupons_data.append({
                "id": str(coupon.id),
                "title": coupon.title,
                "merchant_name": coupon.merchant.company_name if coupon.merchant else None,
                "redeemed_date": tx.created_at,
                "points_used": abs(int(tx.points)),   # always positive
                "transaction_id": str(tx.id)
            })

        # ==============================================================
        # FINAL RESPONSE
        # ==============================================================
        return Response(
            {
                "user_points": current_points,
                "available_coupons": available_coupons_data,
                "redeemed_coupons": redeemed_coupons_data
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
        qr_scans = merchant_txns

        daily_scans = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            scans_count = qr_scans.filter(created_at__date=date).count()
            daily_scans.append({
                "date": date.isoformat(),
                "transactions": scans_count
            })

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

        total_txns = qr_scans.count()
        total_points = qr_scans.aggregate(total=Sum('points'))['total'] or 0
        avg_points = total_points / total_txns if total_txns > 0 else 0

        # ------------------------------------------------------------
        # ⭐ MERCHANT SCANNING HISTORY (UserPoints-Based)
        # ------------------------------------------------------------
        customer_points_records = UserPoints.objects.select_related('user').order_by('-updated_at')

        scan_history_output = []
        for record in customer_points_records:
            scan_history_output.append({
                "customer": {
                    "id": str(record.user.id),
                    "name": record.user.name or record.user.email,
                    "email": record.user.email
                },
                "total_points": record.total_points,
                "tier": record.tier.name if hasattr(record, 'tier') and record.tier else None,
                "last_updated": record.updated_at,
                "profile_image": record.user.profile_image if record.user.profile_image else None
            })

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
                # ⭐ SCANNING HISTORY OUTPUT
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

        # ✅ Parse QR to get the customer
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

        # ✅ Get first active coupon (if any)
        coupon = Coupon.objects.filter(merchant=merchant_account, status='Active').first()
        outlet = coupon.outlet if coupon else None

        # ============================
        # 1️⃣ Update UserPoints
        # ============================
        user_points, created = UserPoints.objects.get_or_create(
            user=customer,
            defaults={"total_points": points, "tier": None}
        )
        if not created:
            user_points.total_points += points
            user_points.save()

        # ============================
        # 2️⃣ Create Transaction for dashboard analytics
        # ============================
        Transaction.objects.create(
            user=customer,
            merchant=merchant_account,
            points=points,
            coupon=coupon,
            outlet=outlet
        )

        # ============================
        # 3️⃣ Mark coupon as used (if exists)
        # ============================
        if coupon:
            coupon.status = 'Used'
            coupon.save()

        # ============================
        # 4️⃣ Response
        # ============================
        return Response(
            {
                'message': f'{points} points awarded to {customer.email}',
                'total_points': user_points.total_points
            },
            status=status.HTTP_200_OK
        )















