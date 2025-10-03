from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileView,
################################################################################
    ForgotPasswordView,
    ResetPasswordView,
    ChangePasswordView,
    UserSearchView
)
################################################################################################################
urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('role-search/', UserSearchView.as_view(), name='user-search'),
    #############################################################################
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]
###############################################################################################
