# Merchants_App/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MerchantViewSet,OutletViewSet,CouponViewSet,PromotionViewSet,TierViewSet, UserPointsViewSet, UserActivityViewSet
from .views import CustomerHomeViewSet
from .views import RedeemCouponView
from .views import CustomerCouponsView  # add this import at the top new updated
##########################################################################################
from .views import MerchantDashboardAnalyticsView #######Full new
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
router.register(r'customer/home', CustomerHomeViewSet, basename='customer_home')
urlpatterns = [
    path('', include(router.urls)),
    path('redeem-coupon/', RedeemCouponView.as_view(), name='redeem-coupon'),
    ##################################################################################
    ##new Updated====>
    path('customer/coupons/', CustomerCouponsView.as_view(), name='customer-coupons'),  # ✅ NEW
    path('merchant/dashboard/',MerchantDashboardAnalyticsView.as_view(), name='merchant-dashboard'),
]





