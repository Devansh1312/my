from django.urls import path
from FutureStarAPI.views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect

urlpatterns = [

        # path('api/register/', RegisterAPIView.as_view(), name='playerregister'),
        path('api/send-otp/', send_otp.as_view()),
        path('api/verify-and-register/', verify_and_register.as_view()),
        path('api/playerlogin/', LoginAPIView.as_view(), name='playerlogin'),
        path('api/logout/', LogoutAPIView.as_view(), name='playerlogout'),  # Add logout endpoint
        path('api/forgot-password/', ForgotPasswordAPIView.as_view(), name='forgot-password'),
        path('api/verify-otp/', VerifyOTPAPIView.as_view(), name='verify-otp'),
        path('api/change-password-otp/', ChangePasswordOtpAPIView.as_view(), name='change-password-otp'),
        
        # For logged-in users
        path('api/change-password/', ChangePasswordAPIView.as_view(), name='change-password'),   
        
        
        # URL for CreateProfile API (GET for roles, POST for profile creation/update)
        path('api/edit-profile/', EditProfileAPIView.as_view()),


        ######## User Post API ###########
        path('api/posts/', PostListAPIView.as_view(), name='post-list'),
        path('api/posts/create/', PostCreateAPIView.as_view(), name='post-create'),
        path('api/posts/details/', PostDetailAPIView.as_view(), name='post-detail-body'),
        path('api/comments/create/', CommentCreateAPIView.as_view(), name='comment-create'),
        path('api/posts/delete/', PostDeleteAPIView.as_view(), name='post-delete'),


        path('api/fields/', FieldAPIView.as_view()),
        path('api/tournament/', TournamentAPIView.as_view()),


        path('api/team/', TeamViewAPI.as_view()),

        path('api/genders/', UserGenderListAPIView.as_view()),

        
        
        # path('api/locations/', LocationAPIView.as_view()),
        
        
        #new apis generation
        
        # path("api/validation/",RegistartionAPI.as_view(),name="regvalidation"),

        # path("api/otpverification/",RegistartionAPI.as_view(),name="otpVarification"),
        # path("api/googleuseregister/",RegistartionAPI.as_view(),name="googleregister"),
        # path("api/appleuseregister/",RegistartionAPI.as_view(),name="appleregister"),
    ]