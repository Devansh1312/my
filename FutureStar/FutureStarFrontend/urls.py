from django.urls import path
from FutureStarFrontend.views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect


handler404 = 'FutureStarFrontend.views.custom_404_view'

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
    path('login/', LoginPage.as_view(),name="login"),
    path('register/', RegisterPage.as_view(),name="register"),
    path('privacy-policy/', PrivacyPolicyPage.as_view(),name="privacy-policy"),
    path('terms-of-services/', TermsofServicesPage.as_view(),name="terms-of-services"),
    path('terms-and-conditions/', TermsAndConditionsPage.as_view(),name="terms-and-conditions"),

    path('player-dashboard/', PlayerDashboardPage.as_view(),name="player-dashboard"),
    path('player-dashboard-games/', UserDashboardGames.as_view(),name="player-dashboard-games"),
    path('player-dashboard-events/', UserEventBookingInfo.as_view(),name="player-dashboard-events"),
    path('player-dashboard-fileds/', UserCreatedFieldsView.as_view(),name="player-dashboard-fileds"),
    path('player-dashboard-trainings/', UserDashboardTrainings.as_view(),name="player-dashboard-trainings"),



    path('register/', RegisterPage.as_view(), name='register'),
    path('verify_otp/', OTPVerificationView.as_view(), name='verify_otp'),
    path('social_signup/', SocialSignupView.as_view(), name='social_signup'),
    path('test-404/', custom_404_view),

    path('search/', SearchView.as_view(), name='search'),
    path('team-page-detail/', TeamPageSearchResults.as_view(), name='TeamPageSearchResults'),
    path('player-page/', PlayerInfoPage.as_view(), name='player_info'),
    path('team-detail-page/', TeamDetailsView.as_view(), name='TeamBranchPageSearchResults'),



    # path('google/login/', GoogleLoginView.as_view(), name='google_login'),
    # path('google/callback/', GoogleCallbackView.as_view(), name='GoogleCallbackView'),
    # path('apple/login/', AppleLoginView.as_view(), name='apple_login'),
    # path('apple/callback/', AppleCallbackView.as_view(), name='apple_callback'),
        
        # Add your Google login view
    # path('apple/login/', YourAppleLoginView.as_view(), name='apple_login'),  # Add your Apple login view

    ]

handler404 = 'FutureStarFrontend.views.custom_404_view'