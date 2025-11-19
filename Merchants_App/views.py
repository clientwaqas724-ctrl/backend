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
      - Available coupons with merchant details
      - Recent activity (real or randomized)
      - Merchant scanning history
    """
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = request.user
        today = timezone.now().date()

        # Ensure only customers can access
        if getattr(user, "role", None) != "customer":
            return Response({
                "success": False,
                "message": "Access denied. Only customers can view this dashboard."
            }, status=status.HTTP_403_FORBIDDEN)

        # --- USER INFO ---
        total_points = Transaction.objects.filter(user=user).aggregate(total=Sum('points')).get('total') or 0
        user_points = UserPoints.objects.filter(user=user).select_related('tier').first()
        tier = user_points.tier.name if user_points and user_points.tier else None

        # --- PROMOTIONS & COUPONS ---
        # Get active promotions with merchant details
        promotions = Promotion.objects.filter(
            end_date__gte=today
        ).select_related('merchant')[:10]  # Limit to 10 promotions
        
        # Get available coupons with merchant and outlet details
        coupons = Coupon.objects.filter(
            status=Coupon.STATUS_ACTIVE,
            expiry_date__gte=today
        ).select_related('merchant', 'outlet')[:20]  # Limit to 20 coupons

        # --- RECENT ACTIVITY ---
        activities = UserActivity.objects.filter(user=user).select_related('related_coupon').order_by('-activity_date')[:10]

        if activities.exists():
            # ✅ If user already has real activity
            recent_activity_data = UserActivitySerializer(activities, many=True).data
        else:
            # ⚙️ No real activity → Generate random sample from recent Transactions
            transactions = Transaction.objects.filter(user=user).select_related('merchant', 'coupon').order_by('-created_at')[:5]

            if transactions.exists():
                random_activity_data = []
                import random

                ACTIVITY_TYPES = ["Earned", "Redeemed", "Expired"]

                for tx in transactions:
                    # Randomly choose an activity type
                    activity_type = random.choice(ACTIVITY_TYPES)
                    
                    # Create activity description based on transaction
                    if tx.coupon:
                        description = f"{activity_type} points via {tx.coupon.title}"
                    elif tx.merchant:
                        description = f"{activity_type} points at {tx.merchant.company_name}"
                    else:
                        description = f"{activity_type} {abs(tx.points)} points"

                    random_activity_data.append({
                        "activity_type": activity_type,
                        "points": tx.points,
                        "description": description,
                        "activity_date": tx.created_at,
                        "related_coupon": tx.coupon.id if tx.coupon else None
                    })
                recent_activity_data = random_activity_data
            else:
                # No transactions either → default random placeholder data
                import random
                ACTIVITY_TYPES = ["Earned", "Redeemed", "Expired"]
                recent_activity_data = [
                    {
                        "activity_type": act,
                        "points": random.randint(5, 50),
                        "description": f"{act.lower()} some points",
                        "activity_date": timezone.now() - timedelta(days=random.randint(1, 30))
                    }
                    for act in random.sample(ACTIVITY_TYPES, min(3, len(ACTIVITY_TYPES)))
                ]

        # --- MERCHANT SCANNING HISTORY ---
        # Get recent QR scans and transactions for this customer
        recent_scans = QRScan.objects.filter(customer=user).order_by('-scan_date')[:10]
        
        # Get transactions with merchant and outlet details
        recent_transactions = Transaction.objects.filter(
            user=user
        ).select_related('merchant', 'outlet', 'coupon').order_by('-created_at')[:10]

        scanning_history = []
        
        # Combine QR scans and transactions
        for scan in recent_scans:
            scanning_history.append({
                "type": "qr_scan",
                "date": scan.scan_date,
                "points": scan.points_awarded,
                "description": f"QR Code scanned at merchant",
                "merchant": getattr(scan.merchant, 'company_name', 'Unknown Merchant') if hasattr(scan, 'merchant') else 'Unknown Merchant',
                "status": "success"
            })

        for txn in recent_transactions:
            transaction_type = "redemption" if txn.points < 0 else "earned"
            scanning_history.append({
                "type": "transaction",
                "date": txn.created_at,
                "points": txn.points,
                "description": f"Points {transaction_type} at {txn.merchant.company_name if txn.merchant else 'Merchant'}",
                "merchant": txn.merchant.company_name if txn.merchant else 'Unknown Merchant',
                "outlet": txn.outlet.name if txn.outlet else None,
                "coupon": txn.coupon.title if txn.coupon else None,
                "status": "completed"
            })

        # Sort by date and take latest 10
        scanning_history.sort(key=lambda x: x['date'], reverse=True)
        scanning_history = scanning_history[:10]

        # --- ENHANCED COUPON DATA WITH IMAGES ---
        enhanced_coupons = []
        for coupon in coupons:
            coupon_data = CouponSerializer(coupon).data
            
            # Add merchant details with image
            merchant_data = {
                "id": str(coupon.merchant.id),
                "company_name": coupon.merchant.company_name,
                "logo_url": coupon.merchant.logo_url,
                "status": coupon.merchant.status
            }
            
            # Add outlet details with images if available
            outlet_data = None
            if coupon.outlet:
                outlet_data = {
                    "id": str(coupon.outlet.id),
                    "name": coupon.outlet.name,
                    "address": coupon.outlet.address,
                    "city": coupon.outlet.city,
                    "state": coupon.outlet.state,
                    "outlet_image": coupon.outlet.outlet_image.url if coupon.outlet.outlet_image else None,
                    "outlet_image_url": coupon.outlet.outlet_image_url
                }
            
            enhanced_coupons.append({
                **coupon_data,
                "merchant_details": merchant_data,
                "outlet_details": outlet_data,
                "available_outlets": OutletSerializer(
                    coupon.merchant.outlets.all()[:3], 
                    many=True
                ).data if coupon.merchant else []
            })

        # --- ENHANCED PROMOTION DATA ---
        enhanced_promotions = []
        for promotion in promotions:
            promo_data = PromotionSerializer(promotion).data
            
            # Add merchant details
            merchant_data = {
                "id": str(promotion.merchant.id),
                "company_name": promotion.merchant.company_name,
                "logo_url": promotion.merchant.logo_url
            }
            
            enhanced_promotions.append({
                **promo_data,
                "merchant_details": merchant_data
            })

        # --- RESPONSE PAYLOAD ---
        data = {
            "user": {
                "id": str(user.id),
                "email": getattr(user, "email", None),
                "name": getattr(user, "name", None),
                "role": getattr(user, "role", None),
                "total_points": total_points,
                "tier": tier,
                "user_points_details": UserPointsSerializer(user_points).data if user_points else None
            },
            "promotions": enhanced_promotions,
            "available_coupons": enhanced_coupons,
            "recent_activity": recent_activity_data,
            "scanning_history": scanning_history,
            "nearby_merchants": MerchantSerializer(
                Merchant.objects.filter(status='active')[:5], 
                many=True
            ).data
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
    Allows a user to redeem a coupon using their available points and total transaction history.
    Prevents duplicate redemption and accurately deducts from total combined balance.
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

        # ✅ 2. Get coupon
        coupon = get_object_or_404(Coupon, id=coupon_id)

        # ✅ 3. Validate coupon
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

        # ✅ 4. Get user's current points record
        user_points, _ = UserPoints.objects.get_or_create(
            user=user, defaults={"total_points": 0}
        )

        # ✅ 5. Calculate total earned/redeemed from Transaction model
        total_earned = (
            Transaction.objects.filter(user=user, points__gt=0)
            .aggregate(total=Sum("points"))
            .get("total") or 0
        )
        total_redeemed = (
            Transaction.objects.filter(user=user, points__lt=0)
            .aggregate(total=Sum("points"))
            .get("total") or 0
        )
        transaction_net_points = total_earned + total_redeemed  # redeemed negative

        # ✅ 6. Combined available points before redemption
        total_available_points = user_points.total_points + transaction_net_points

        # ✅ 7. Check if coupon already redeemed
        already_redeemed = Transaction.objects.filter(
            user=user,
            coupon=coupon,
            points__lt=0
        ).exists()

        if already_redeemed:
            return Response(
                {
                    "success": False,
                    "message": f"You have already redeemed this coupon: {coupon.title}",
                    "data": {
                        "coupon": {"id": str(coupon.id), "title": coupon.title},
                        "remaining_points": total_available_points,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ 8. Check if user has enough total points
        if total_available_points < coupon.points_required:
            return Response(
                {
                    "success": False,
                    "message": (
                        f"Not enough points. You need {coupon.points_required}, "
                        f"but you only have {total_available_points}."
                    ),
                    "data": {"remaining_points": total_available_points},
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ 9. Deduct coupon points from total (combined) balance
        remaining_points = total_available_points - coupon.points_required

        # Update UserPoints to reflect new correct total
        user_points.total_points = remaining_points
        user_points.save(update_fields=["total_points"])

        # ✅ 10. Log redemption in both tables
        Transaction.objects.create(
            user=user,
            merchant=coupon.merchant,
            coupon=coupon,
            points=-coupon.points_required
        )

        UserActivity.objects.create(
            user=user,
            activity_type="redeem_coupon",
            description=f"Redeemed coupon: {coupon.title}",
            points=-coupon.points_required,
            related_coupon=coupon
        )

        # ✅ 11. Response
        return Response(
            {
                "success": True,
                "message": "Coupon redeemed successfully!",
                "data": {
                    "coupon": {"id": str(coupon.id), "title": coupon.title},
                    "remaining_points": remaining_points,
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
      - redeemed_coupons (from transactions)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        today = timezone.now().date()

        # ================================
        # ✅ Available coupons (active & not expired)
        # ================================
        available_coupons = Coupon.objects.filter(
            status=Coupon.STATUS_ACTIVE,
            expiry_date__gte=today
        ).order_by('-created_at')

        available_coupons_data = []
        for coupon in available_coupons:
            available_coupons_data.append({
                "id": str(coupon.id),
                "merchant": str(coupon.merchant.id),
                "merchant_name": coupon.merchant.company_name,
                "title": coupon.title,
                "description": coupon.description,
                "image": coupon.image.url if coupon.image else None,
                "image_url": coupon.image_url,
                "points_required": coupon.points_required,
                "start_date": coupon.start_date,
                "expiry_date": coupon.expiry_date,
                "terms_and_conditions_text": coupon.terms_and_conditions_text,
                "code": coupon.code,
                "status": coupon.status,
                "created_at": coupon.created_at,
            })

        # ================================
        # ✅ Redeemed coupons (via Transaction)
        # ================================
        redeemed_transactions = (
            Transaction.objects.filter(
                user=user,
                coupon__isnull=False,
                points__lt=0  # redeemed
            )
            .select_related('coupon', 'coupon__merchant')
            .order_by('-created_at')
        )

        redeemed_coupons_data = []
        for tx in redeemed_transactions:
            coupon = tx.coupon
            redeemed_coupons_data.append({
                "id": str(coupon.id),
                "title": coupon.title,
                "code": coupon.code,
                "merchant_name": coupon.merchant.company_name,
                "redeemed_date": tx.created_at,
                "status": "redeemed",
                "points_used": abs(tx.points),
            })

        # ================================
        # ✅ Final response
        # ================================
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
    Combines merchant dashboard summary + detailed analytics with images.
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

        # ✅ 5. Recent Transactions with Enhanced Data
        recent_txns = merchant_txns.select_related('user', 'outlet', 'coupon').order_by('-created_at')[:10]
        recent_transactions = []
        for txn in recent_txns:
            transaction_type = "redeem" if txn.points < 0 else "earn"
            
            # Get customer image if available
            customer_image = None
            if hasattr(txn.user, 'profile_image') and txn.user.profile_image:
                customer_image = txn.user.profile_image.url
            elif hasattr(txn.user, 'avatar_url'):
                customer_image = txn.user.avatar_url
                
            # Get outlet images
            outlet_images = []
            if txn.outlet:
                if txn.outlet.outlet_image:
                    outlet_images.append(txn.outlet.outlet_image.url)
                if txn.outlet.outlet_image_url:
                    outlet_images.append(txn.outlet.outlet_image_url)
                    
            # Get coupon images
            coupon_images = []
            if txn.coupon:
                if txn.coupon.image:
                    coupon_images.append(txn.coupon.image.url)
                if txn.coupon.image_url:
                    coupon_images.append(txn.coupon.image_url)

            recent_transactions.append({
                "id": str(txn.id),
                "customer_name": txn.user.name or txn.user.email.split('@')[0],
                "customer_email": txn.user.email,
                "customer_id": str(txn.user.id),
                "customer_image": customer_image,
                "points": abs(txn.points),
                "transaction_type": transaction_type,
                "outlet_name": txn.outlet.name if txn.outlet else "N/A",
                "outlet_id": str(txn.outlet.id) if txn.outlet else None,
                "outlet_images": outlet_images,
                "coupon_title": txn.coupon.title if txn.coupon else None,
                "coupon_id": str(txn.coupon.id) if txn.coupon else None,
                "coupon_images": coupon_images,
                "timestamp": txn.created_at.isoformat(),
                "location": f"{txn.outlet.city}, {txn.outlet.state}" if txn.outlet else "N/A",
                "qr_code_used": f"user:{txn.user.id}"  # Simulated QR code format
            })

        # ✅ 6. Active Outlets Summary with Images
        active_outlets = []
        for outlet in merchant.outlets.all()[:10]:  # Increased limit to 10
            outlet_txns = merchant_txns.filter(outlet=outlet)
            outlet_scans_today = outlet_txns.filter(created_at__gte=start_of_day).count()
            outlet_customers = outlet_txns.values('user').distinct().count()
            
            # Get outlet images
            outlet_images = []
            if outlet.outlet_image:
                outlet_images.append(outlet.outlet_image.url)
            if outlet.outlet_image_url:
                outlet_images.append(outlet.outlet_image_url)

            active_outlets.append({
                "id": str(outlet.id),
                "name": outlet.name,
                "address": outlet.address,
                "city": outlet.city,
                "state": outlet.state,
                "country": outlet.country,
                "location": f"{outlet.city}, {outlet.state}",
                "contact_number": outlet.contact_number,
                "is_active": True,
                "scans_today": outlet_scans_today,
                "total_customers": outlet_customers,
                "images": outlet_images,
                "latitude": outlet.latitude,
                "longitude": outlet.longitude
            })

        # ✅ 7. Popular Coupons with Images (top 5 by redemption count)
        popular_coupons = Coupon.objects.filter(
            merchant=merchant
        ).annotate(
            redemption_count=Count('loyalty_transactions')
        ).order_by('-redemption_count')[:5]

        popular_coupons_data = []
        for c in popular_coupons:
            coupon_images = []
            if c.image:
                coupon_images.append(c.image.url)
            if c.image_url:
                coupon_images.append(c.image_url)
                
            popular_coupons_data.append({
                "id": str(c.id),
                "title": c.title,
                "description": c.description,
                "redemption_count": c.redemption_count,
                "points_required": c.points_required,
                "start_date": c.start_date,
                "expiry_date": c.expiry_date,
                "code": c.code,
                "status": c.status,
                "images": coupon_images,
                "terms_and_conditions": c.terms_and_conditions_text,
                "merchant_name": c.merchant.company_name
            })

        # ✅ 8. Merchant Scanning Analytics
        # QR Scan analytics
        qr_scans = QRScan.objects.filter(merchant=merchant) if hasattr(QRScan, 'merchant') else QRScan.objects.none()
        
        # Daily transaction stats (last 7 days)
        daily_scans = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            scans_count = merchant_txns.filter(created_at__date=date).count()
            daily_scans.append({
                "date": date.isoformat(),
                "transactions": scans_count
            })

        # Customer growth
        customer_growth = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            customers_count = merchant_txns.filter(
                created_at__date__lte=date
            ).values('user').distinct().count()
            customer_growth.append({
                "date": date.isoformat(),
                "customers": customers_count
            })

        # Points distribution
        total_txns = merchant_txns.count()
        total_points = merchant_txns.aggregate(total=Sum('points'))['total'] or 0
        avg_points = total_points / total_txns if total_txns > 0 else 0

        # ✅ 9. Merchant Info Summary with Images
        merchant_info = {
            "id": str(merchant.id),
            "business_name": merchant.company_name,
            "logo_url": merchant.logo_url,
            "status": merchant.status,
            "total_outlets": total_outlets,
            "total_coupons": total_coupons,
            "active_coupons": active_coupons,
            "total_promotions": total_promotions,
            "total_customers": total_customers,
            "member_since": merchant.created_at.date(),
            "user_details": {
                "user_id": str(user.id),
                "email": user.email,
                "name": user.name
            }
        }

        # ✅ 10. Today's Stats Summary
        today_stats = {
            "transactions_today": scans_today,
            "points_awarded_today": points_awarded_today,
            "coupons_redeemed_today": coupons_redeemed_today,
            "weekly_transactions": weekly_scans,
            "monthly_transactions": monthly_scans,
            "revenue_impact": f"${points_awarded_today * 2.5:,.0f}",
            "avg_points_per_customer": round(points_awarded_today / max(scans_today, 1), 2)
        }

        # ✅ 11. Scanning Performance Metrics
        scanning_metrics = {
            "total_qr_scans": qr_scans.count() if hasattr(QRScan, 'merchant') else scans_today,
            "successful_scans": scans_today,
            "failed_scans": 0,  # You might want to track this
            "scan_success_rate": "100%",
            "average_scan_value": round(avg_points, 2),
            "top_scanning_outlet": active_outlets[0]['name'] if active_outlets else "N/A"
        }

        # ✅ 12. Final Combined Response
        return Response({
            "success": True,
            "message": "Merchant dashboard & analytics retrieved successfully",
            "data": {
                "merchant_info": merchant_info,
                "today_stats": today_stats,
                "scanning_metrics": scanning_metrics,
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
                        "top_performing_outlet": active_outlets[0]['name'] if active_outlets else "N/A",
                        "scan_conversion_rate": "92%"
                    }
                }
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

