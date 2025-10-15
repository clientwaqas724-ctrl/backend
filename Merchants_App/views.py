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
      • GET    /outlets/<pk>/   -> retrieve single
      • PUT    /outlets/<pk>/   -> update
      • PATCH  /outlets/<pk>/   -> partial update
      • DELETE /outlets/<pk>/   -> delete
    """
    queryset = Outlet.objects.all().order_by('-created_at')
    serializer_class = OutletSerializer

    # simple search by ?search=keyword across name, city, state, country
    def list(self, request, *args, **kwargs):
        search = request.query_params.get('search')
        queryset = self.get_queryset()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(city__icontains=search) |
                Q(state__icontains=search) |
                Q(country__icontains=search) |
                Q(address__icontains=search)
            )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
###############################################################################################################################################################
###############################################################################################################################################################
class CouponViewSet(viewsets.ModelViewSet):
    """
    Provides:
      • POST   /coupons/        -> create
      • GET    /coupons/        -> list (with ?search=<term>)
      • GET    /coupons/<pk>/   -> retrieve single
      • PUT    /coupons/<pk>/   -> update
      • PATCH  /coupons/<pk>/   -> partial update
      • DELETE /coupons/<pk>/   -> delete
    """
    queryset = Coupon.objects.all().order_by('-created_at')
    serializer_class = CouponSerializer

    # simple search by ?search=keyword across title or merchant company name
    def list(self, request, *args, **kwargs):
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
##########################################################################################################################################################
##########################################################################################################################################################
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
################################################################################################################################################################
################################################################################################################################################################
class CustomerHomeViewSet(viewsets.ViewSet):
    """
    Provides:
      • GET /customer/home/
    Returns the customer dashboard data including:
      - user details (points, tier)
      - promotions
      - available coupons
      - recent activity
    """
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = request.user
        today = timezone.now().date()

        # 1️⃣ Get user points
        try:
            user_points = UserPoints.objects.select_related('tier', 'user').get(user=user)
        except UserPoints.DoesNotExist:
            user_points = UserPoints(user=user, total_points=0)

        # 2️⃣ Active promotions
        promotions = Promotion.objects.filter(start_date__lte=today, end_date__gte=today)

        # 3️⃣ Active coupons
        coupons = Coupon.objects.filter(status=Coupon.STATUS_ACTIVE)

        # 4️⃣ Recent user activities (limit 5)
        activities = UserActivity.objects.filter(user=user).order_by('-activity_date')[:5]

        # 5️⃣ Serialize data
        serializer = CustomerHomeSerializer({
            "user": user_points,
            "promotions": promotions,
            "available_coupons": coupons,
            "recent_activity": activities
        })

        # 6️⃣ Final response
        return Response({
            "success": True,
            "message": "Dashboard data retrieved successfully",
            "data": serializer.data
        })
##############################################################################################################################################
##############################################################################################################################################
# ============================= Redeem Coupon API =============================
class RedeemCouponView(APIView):
    """
    POST /api/redeem-coupon/
    Allows a user to redeem a coupon using their available points.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        coupon_id = request.data.get("coupon_id")

        # ✅ 1. Validate coupon_id
        if not coupon_id:
            return Response(
                {"success": False, "message": "coupon_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ 2. Get coupon object
        coupon = get_object_or_404(Coupon, id=coupon_id)

        # ✅ 3. Check coupon validity
        if coupon.status != Coupon.STATUS_ACTIVE:
            return Response(
                {"success": False, "message": "This coupon is not active."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if coupon.expiry_date < timezone.now().date():
            return Response(
                {"success": False, "message": "This coupon has expired."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ 4. Get user’s current points
        user_points, created = UserPoints.objects.get_or_create(user=user, defaults={"total_points": 0})
        if user_points.total_points < coupon.points_required:
            return Response(
                {
                    "success": False,
                    "message": f"You need {coupon.points_required} points but you only have {user_points.total_points}."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ 5. Deduct points
        user_points.total_points -= coupon.points_required
        user_points.save()

        # ✅ 6. Log redemption in UserActivity
        UserActivity.objects.create(
            user=user,
            activity_type="redeem_coupon",  # ensure this choice exists in your ACTIVITY_CHOICES
            description=f"Redeemed coupon: {coupon.title}",
            points=-coupon.points_required,
            related_coupon=coupon
        )

        # ✅ 7. Response
        return Response(
            {
                "success": True,
                "message": "Coupon redeemed successfully!",
                "data": {
                    "coupon": {
                        "id": str(coupon.id),
                        "title": coupon.title,
                    },
                    "remaining_points": user_points.total_points,
                },
            },
            status=status.HTTP_200_OK
        )
##############################################################################################################################################
##############################################################################################################################################
# ============================= CUSTOMER COUPONS LIST API =============================new updated
class CustomerCouponsView(APIView):
    """
    GET /api/customer/coupons/
    Returns:
      - available_coupons (active and not expired)
      - redeemed_coupons (from user activity)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        today = timezone.now().date()

        # ✅ Available coupons (active and not expired)
        available_coupons = Coupon.objects.filter(
            status=Coupon.STATUS_ACTIVE,
            expiry_date__gte=today
        )

        available_coupons_data = CouponSerializer(available_coupons, many=True).data

        # ✅ Redeemed coupons (based on UserActivity)
        redeemed_activities = UserActivity.objects.filter(
            user=user,
            activity_type='redeem_coupon'
        ).select_related('related_coupon').order_by('-activity_date')

        redeemed_coupons_data = RedeemedCouponSerializer(redeemed_activities, many=True).data

        # ✅ Final response
        return Response(
            {
                "available_coupons": available_coupons_data,
                "redeemed_coupons": redeemed_coupons_data,
            },
            status=status.HTTP_200_OK
        )
##############################################################################################################################################
##############################################################################################################################################
class MerchantDashboardAnalyticsView(APIView):
    """
    GET /api/merchant/dashboard-analytics/
    Combines merchant dashboard summary + detailed analytics.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # ✅ 1. Check if user is merchant
        if user.role != User.MERCHANT:
            return Response(
                {"success": False, "message": "Access denied. User is not a merchant."},
                status=status.HTTP_403_FORBIDDEN
            )

        # ✅ 2. Get merchant object
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

        # ✅ 3. Merchant Basic Info
        total_outlets = merchant.outlets.count()
        total_coupons = Coupon.objects.filter(merchant=merchant).count()
        active_coupons = Coupon.objects.filter(
            merchant=merchant,
            status=Coupon.STATUS_ACTIVE,
            expiry_date__gte=today
        ).count()
        total_promotions = Promotion.objects.filter(merchant=merchant).count()

        # ✅ 4. Transaction Statistics
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

        # ✅ 5. Recent Transactions (using Loyalty_App.models.Transaction)
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

        # ✅ 6. Active Outlets Summary
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

        # ✅ 7. Popular Coupons (top 3 by redemption count)
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

        # ✅ 8. Analytics Section
        today = timezone.now().date()
        qr_scans = merchant_txns

        # Daily transaction stats (last 7 days)
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

        # Points distribution
        total_txns = qr_scans.count()
        total_points = qr_scans.aggregate(total=Sum('points'))['total'] or 0
        avg_points = total_points / total_txns if total_txns > 0 else 0

        # ✅ 9. Merchant Info Summary
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

        # ✅ 10. Today's Stats Summary
        today_stats = {
            "transactions_today": scans_today,
            "points_awarded_today": points_awarded_today,
            "coupons_redeemed_today": coupons_redeemed_today,
            "weekly_transactions": weekly_scans,
            "monthly_transactions": monthly_scans,
            "revenue_impact": f"${points_awarded_today * 2.5:,.0f}",
        }

        # ✅ 11. Final Combined Response
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
                }
            }
        }, status=status.HTTP_200_OK)
##############################################################################################################################################
##############################################################################################################################################
class MerchantScanQRAPIView(APIView):
    """
    POST /api/merchant/scan-qr/
    Body: { "qr_code": "user:<uuid>", "points": 10 }
    Only merchant users can call this.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role != 'merchant':
            return Response({'error': 'Only merchants can scan QR codes.'},
                            status=status.HTTP_403_FORBIDDEN)

        qr_code = request.data.get('qr_code')
        points = int(request.data.get('points', 10))  # default = 10 points

        # Parse QR and get the customer
        try:
            customer_id = qr_code.split(":")[1]
            customer = User.objects.get(id=customer_id, role='customer')
        except Exception:
            return Response({'error': 'Invalid QR code.'}, status=status.HTTP_400_BAD_REQUEST)

        # Record the QR scan
        QRScan.objects.create(customer=customer, qr_code=qr_code, points_awarded=points)

        # Update or create CustomerPoints wallet
        wallet, _ = CustomerPoints.objects.get_or_create(customer=customer)
        wallet.total_points += points
        wallet.save()

        # Record the transaction
        merchant_account = user.merchants.first()  # get merchant profile
        Transaction.objects.create(
            user=customer,
            merchant=merchant_account,
            outlet=None,
            points=points
        )

        return Response({
            'message': f'{points} points awarded to {customer.email}',
            'total_points': wallet.total_points
        }, status=status.HTTP_200_OK)






















