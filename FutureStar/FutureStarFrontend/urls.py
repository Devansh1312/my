from django.urls import path
from FutureStarFrontend.views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect

urlpatterns = [
    

    #Dashboard URL
    path('contact/', ContactPage.as_view(),name="contact"),
    path('', HomePage.as_view(),name="index"),
    path('discover/', DiscoverPage.as_view(),name="discover"),
    path('success-stories/', SuccessStoriesPage.as_view(),name="success-stories"),
    path('news/', NewsPage.as_view(),name="news"),
    path('news-detail/<int:pk>/', NewsDetailPage.as_view(), name='news-detail'),
    path('advertise/', AdvertisePage.as_view(),name="advertise"),
    path('about/', AboutPage.as_view(),name="about"),
    path('login', LoginPage.as_view(),name="login"),
    path('register/', RegisterPage.as_view(),name="register"),
    path('privacy-policy/', PrivacyPolicyPage.as_view(),name="privacy-policy"),
    path('terms-of-services/', TermsofServicesPage.as_view(),name="terms-of-services"),
    path('player-dashboard/', PlayerDashboardPage.as_view(),name="player-dashboard"),
    path('register/', RegisterPage.as_view(), name='register'),
    path('verify_otp/', OTPVerificationView.as_view(), name='verify_otp'),
    path('social_signup/', SocialSignupView.as_view(), name='social_signup'),
    # path('google/login/', GoogleLoginView.as_view(), name='google_login'),
    # path('google/callback/', GoogleCallbackView.as_view(), name='GoogleCallbackView'),
    # path('apple/login/', AppleLoginView.as_view(), name='apple_login'),
    # path('apple/callback/', AppleCallbackView.as_view(), name='apple_callback'),
        
        # Add your Google login view
    # path('apple/login/', YourAppleLoginView.as_view(), name='apple_login'),  # Add your Apple login view

    ]

