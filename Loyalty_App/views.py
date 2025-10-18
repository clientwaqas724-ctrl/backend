# Loyalty_App/views.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import Transaction
from .serializers import TransactionSerializer

User = get_user_model()


class TransactionViewSet(viewsets.ModelViewSet):
    """
    Transaction API ViewSet:
    - Customers → only their transactions
    - Merchants → all transactions linked to their merchant profile
    - Admins → all transactions, with optional filters:
        • ?email=<user_email> (for merchant or customer)
        • ?merchant=<uuid>
        • ?user=<uuid>
        • ?outlet=<uuid>
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    queryset = Transaction.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__email', 'merchant__company_name', 'outlet__name']
    ordering_fields = ['created_at', 'points']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        # ==========================
        # ROLE-BASED FILTERING
        # ==========================
        if user.role == 'customer':
            # Customer → only their transactions
            qs = qs.filter(user=user)

        elif user.role == 'merchant':
            # Merchant → only transactions related to their merchant profile
            qs = qs.filter(merchant__user=user)

        elif user.role == 'admin':
            # Admin → can filter by email, merchant, or user
            email = self.request.query_params.get('email')
            merchant_id = self.request.query_params.get('merchant')
            customer_id = self.request.query_params.get('user')
            outlet_id = self.request.query_params.get('outlet')

            # ✅ Filter by email (merchant or customer automatically)
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
        """Provide user role context for serializer (optional)."""
        context = super().get_serializer_context()
        context['role'] = self.request.user.role
        return context
