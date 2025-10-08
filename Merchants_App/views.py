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
from .serializers import CustomerHomeSerializer
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
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


