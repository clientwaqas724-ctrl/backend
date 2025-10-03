from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Transaction
from .serializers import TransactionSerializer
#######################################################################################################################################################
#######################################################################################################################################################
class TransactionViewSet(viewsets.ModelViewSet):
    """
    Provides:
    - create (POST)
    - retrieve (GET /<id>/)
    - list + search (GET)
    - update/partial_update (PUT/PATCH)
    - destroy (DELETE)
    """
    serializer_class = TransactionSerializer
    # permission_classes = [IsAuthenticated]
    queryset = Transaction.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__email', 'merchant__company_name', 'outlet__name']
    ordering_fields = ['created_at', 'points']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Optionally restricts the returned transactions to a given user/merchant/outlet,
        by filtering against query parameters in the URL.
        Example: ?merchant=<uuid>&user=<uuid>
        """
        qs = super().get_queryset()
        user_id = self.request.query_params.get('user')
        merchant_id = self.request.query_params.get('merchant')
        outlet_id = self.request.query_params.get('outlet')

        if user_id:
            qs = qs.filter(user__id=user_id)
        if merchant_id:
            qs = qs.filter(merchant__id=merchant_id)
        if outlet_id:
            qs = qs.filter(outlet__id=outlet_id)

        return qs
#######################################################################################################################################################
#######################################################################################################################################################
