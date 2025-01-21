from django.urls import path,re_path
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
    path('login/', LoginPage.as_view(), name="login"),
    re_path(r'^login/?$', LoginPage.as_view(), name="login_redirect"),
    path('privacy-policy/', PrivacyPolicyPage.as_view(),name="privacy-policy"),
    path('terms-of-services/', TermsofServicesPage.as_view(),name="terms-of-services"),
    path('terms-and-conditions/', TermsAndConditionsPage.as_view(),name="terms-and-conditions"),

    path('user-dashboard/', PlayerDashboardPage.as_view(),name="player-dashboard"),
    path('user-dashboard-games/', UserDashboardGames.as_view(),name="player-dashboard-games"),
    path('user-dashboard-events/', UserEventBookingInfo.as_view(),name="player-dashboard-events"),
    path('user-dashboard-fileds/', UserCreatedFieldsView.as_view(),name="player-dashboard-fileds"),
    path('user-dashboard-trainings/', UserDashboardTrainings.as_view(),name="player-dashboard-trainings"),
    path('user-dashboard-team-page/', TeamPageDashboard.as_view(),name="player-dashboard-team-page"),
    path('user-dashboard-joined-teams/', UserJoinedTeamInfo.as_view(), name='player-dashboard-joined-teams'),

    path('forgot-password/', ForgotPasswordPage.as_view(), name='forgot_password'),
    path('verify_forgot_password_otp/', verify_forgot_password_otp.as_view(), name='verify_forgot_password_otp'),
    path('reset-password/', ResetPasswordPage.as_view(), name='reset_password'),



    path('register/', RegisterPage.as_view(), name='register'),
    path('verify_otp/', OTPVerificationView.as_view(), name='verify_otp'),
    path('test-404/', custom_404_view),

    path('search/', SearchView.as_view(), name='search'),
    path('team-page-detail/', TeamPageSearchResults.as_view(), name='TeamPageSearchResults'),
    path('player-page/', PlayerInfoPage.as_view(), name='player_info'),
    path('team/', TeamDetailsView.as_view(), name='TeamBranchPageSearchResults'),

    path('auth/google/', GoogleAuthView.as_view(), name='google_auth'),
    path('auth/google/callback/', GoogleCallbackView.as_view(), name='google_auth_callback'),
    path('user_info/update/', UserInfoUpdateView.as_view(), name='user_info_update'),
    path('google_verify_otp/', googleOTPVerificationView.as_view(), name='google_verify_otp'),

    path('auth/apple/', AppleAuthView.as_view(), name='apple_auth'),
    path('auth/apple/callback/', AppleCallbackView.as_view(), name='apple_callback'),
    ]

handler404 = 'FutureStarFrontend.views.custom_404_view'