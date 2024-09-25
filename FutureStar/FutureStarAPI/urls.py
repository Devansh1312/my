from django.urls import path
from FutureStarAPI.views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect

urlpatterns = [

        path('api/register/', RegisterAPIView.as_view(), name='register'),
        path('api/playerlogin/', LoginAPIView.as_view(), name='playerlogin'),
        path('api/logout/', LogoutAPIView.as_view(), name='playerlogout'),  # Add logout endpoint
        path('api/forgot-password/', ForgotPasswordAPIView.as_view(), name='forgot-password'),
        path('api/verify-otp/', VerifyOTPAPIView.as_view(), name='verify-otp'),
        path('api/change-password-otp/', ChangePasswordOtpAPIView.as_view(), name='change-password-otp'),
        
        # For logged-in users
        path('api/change-password/', ChangePasswordAPIView.as_view(), name='change-password'),                 

    ]