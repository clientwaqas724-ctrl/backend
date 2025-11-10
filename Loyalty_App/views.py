# Loyalty_App/views.py
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Transaction
from .serializers import TransactionSerializer
from Merchants_App.models import UserActivity

User = get_user_model()


class TransactionViewSet(viewsets.ModelViewSet):
    """
    Transaction API ViewSet:
    - Customers → only their transactions
    - Merchants → transactions linked to their merchant profile
    - Admins → all transactions, with filters by email, merchant, user, outlet
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    queryset = Transaction.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__email', 'merchant__company_name', 'outlet__name']
    ordering_fields = ['created_at', 'points']
    ordering = ['-created_at']

    # ===========================================================
    # ROLE BASED FILTERING
    # ===========================================================
    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if user.role == 'customer':
            qs = qs.filter(user=user)

        elif user.role == 'merchant':
            qs = qs.filter(merchant__user=user)

        elif user.role == 'admin':
            email = self.request.query_params.get('email')
            merchant_id = self.request.query_params.get('merchant')
            customer_id = self.request.query_params.get('user')
            outlet_id = self.request.query_params.get('outlet')

            if email:
                try:
                    target_user = User.objects.get(email=email)
                    if target_user.role == 'customer':
                        qs = qs.filter(user=target_user)
                    elif target_user.role == 'merchant':
                        qs = qs.filter(merchant__user=target_user)
                except User.DoesNotExist:
                    return qs.none()

            if merchant_id:
                qs = qs.filter(merchant__id=merchant_id)
            if customer_id:
                qs = qs.filter(user__id=customer_id)
            if outlet_id:
                qs = qs.filter(outlet__id=outlet_id)

        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['role'] = self.request.user.role
        return context

    # ===========================================================
    # ✅ AUTO-CREATE USER ACTIVITY WHEN TRANSACTION CREATED
    # ===========================================================
    def perform_create(self, serializer):
        transaction = serializer.save(user=self.request.user)

        # Avoid duplicate within 5 seconds
        recent_duplicate = Transaction.objects.filter(
            user=transaction.user,
            merchant=transaction.merchant,
            points=transaction.points,
            created_at__gte=timezone.now() - timedelta(seconds=5)
        ).exclude(id=transaction.id).exists()

        if recent_duplicate:
            transaction.delete()
            return

        # Define activity type based on transaction points
        if transaction.points < 0:
            activity_type = "redeem_coupon"
            description = "Coupon redeemed"
        else:
            activity_type = "points_awarded"
            description = "Points Awarded"

        # Avoid duplicate UserActivity for same transaction
        if not UserActivity.objects.filter(
            user=transaction.user,
            related_transaction=transaction,
            activity_type=activity_type
        ).exists():
            UserActivity.objects.create(
                user=transaction.user,
                activity_type=activity_type,
                related_transaction=transaction,
                related_coupon=transaction.coupon if transaction.coupon else None,
                description=description
            )


# ===========================================================
# ✅ STANDALONE ENDPOINT FOR CHECKING COUPON REDEMPTION
# ===========================================================
class CheckCouponRedemptionView(APIView):
    """
    POST /api/check-coupon-redemption/
    Input: { "email": "customer@example.com" }
    """

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")

        if not email:
            return Response(
                {"success": False, "message": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"success": False, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        redeemed_activity = (
            UserActivity.objects.filter(user=user, activity_type="redeem_coupon")
            .select_related("related_coupon")
            .order_by("-activity_date")
            .first()
        )

        redeemed_transaction = (
            Transaction.objects.filter(user=user, points__lt=0)
            .select_related("coupon")
            .order_by("-created_at")
            .first()
        )

        if redeemed_activity:
            coupon_title = (
                redeemed_activity.related_coupon.title
                if redeemed_activity.related_coupon
                else "Redeemed coupon"
            )
            return Response(
                {"success": True, "message": "Coupon redeemed", "title": coupon_title},
                status=status.HTTP_200_OK
            )

        elif redeemed_transaction:
            coupon_title = (
                redeemed_transaction.coupon.title
                if redeemed_transaction.coupon
                else "Redeemed coupon"
            )
            return Response(
                {"success": True, "message": "Coupon redeemed", "title": coupon_title},
                status=status.HTTP_200_OK
            )

        return Response(
            {"success": False, "message": "Points Awarded"},
            status=status.HTTP_200_OK
        )
