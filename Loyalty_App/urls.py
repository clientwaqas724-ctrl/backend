from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet
from .views import CheckCouponRedemptionView   # ✅ import your view
##################################################################################################
router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
    path("check-coupon-redemption/",CheckCouponRedemptionView.as_view(),name="check-coupon-redemption")
]
