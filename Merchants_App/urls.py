# Merchants_App/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MerchantViewSet,OutletViewSet,CouponViewSet,PromotionViewSet,TierViewSet, UserPointsViewSet, UserActivityViewSet
router = DefaultRouter()
router.register(r'merchants',MerchantViewSet)
router.register(r'outlets',OutletViewSet)   # NEW
router.register(r'coupons',CouponViewSet)
router.register(r'promotions', PromotionViewSet)
#####################################################################
router.register(r'tiers', TierViewSet)
router.register(r'user-points', UserPointsViewSet)
router.register(r'user-activities', UserActivityViewSet)
#####################################################################

urlpatterns = [
    path('', include(router.urls)),
]
