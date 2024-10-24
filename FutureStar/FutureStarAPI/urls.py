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
        path('api/update-profile-img/', UpdateProfilePictureAPIView.as_view()),


        ## Follow Following 
        path('api/follow_unfollow/', FollowUnfollowAPI.as_view()),
        path('api/followers/', ListFollowersAPI.as_view()),
        path('api/following/', ListFollowingAPI.as_view()),

        ######## User Post API ###########

        path('api/posts/like/', PostLikeAPIView.as_view(), name='post-like'),
        # path('api/post/view/', PostViewAPIView.as_view(), name='post-view'),


        path('api/posts/all/', AllPostsListAPIView.as_view()),
        path('api/posts/', PostListAPIView.as_view()),
        path('api/posts/create/', PostCreateAPIView.as_view()),
        path('api/posts/edit/', PostEditAPIView.as_view()),

        path('api/posts/details/', PostDetailAPIView.as_view()), #Post Detail View As well As Post View Increment 
        path('api/comments/', PostCommentAPIView.as_view()),  # New API for paginated comments

        path('api/comments/create/', CommentCreateAPIView.as_view()),
        path('api/posts/delete/', PostDeleteAPIView.as_view()),

        #############album############
        path('api/detail_albums/', DetailAlbumListAPIView.as_view()),
        path('api/albums/create/', DetailAlbumCreateAPIView.as_view()),
        path('api/albums/', AlbumListAPIView.as_view()),
       
        #############gallary############
       
        path('api/gallary_items/', GallaryListAPIView.as_view(), name='gallary-list'),
        path('api/gallary_items/create/', GallaryCreateAPIView.as_view(), name='gallary-create'),
        path('api/latest_gallary_items/', LatestGallaryListAPIView.as_view()),
       
        #############delete album & gallary############

        path('api/albums/delete/', AlbumDeleteAPIView.as_view()),
        path('api/gallary_items/delete/', GallaryDeleteAPIView.as_view()),

        ########################## Events URL ##################
        path('api/events/', EventsAPIView.as_view()),
        path('api/events/create/', EventCreateAPIView.as_view()),
        path('api/events/detail/', EventDetailAPIView.as_view()),
        path('api/team_events/', TeamEventAPIView.as_view()),
        path('api/event/like/', EventLikeAPIView.as_view()),
        path('api/event/comments/', EventCommentAPIView.as_view()),  # New API for paginated comments
        path('api/event/comments/create/', EventCommentCreateAPIView.as_view()),
      

     

        ########################## Sponsor URL ##################
        path('api/sponsor/', SponsorAPI.as_view()),
        path('api/sponsor/detail/', SponsorDetailAPIView.as_view()),



        ########################## Report URL ##################

        path('api/reports/', ReportListAPIView.as_view()),
        path('api/reports/create/', PostReportCreateView.as_view()),

        ################## fileds URL ################
        path('api/fields/', FieldAPIView.as_view()),
        path('api/tournament/', TournamentAPIView.as_view()),


        path('api/team/', TeamViewAPI.as_view()),

        path('api/genders/', UserGenderListAPIView.as_view()),

        path('api/role/', UserRoleListAPIView.as_view()),
        
        path('api/locations/', LocationAPIView.as_view()),
        

        path('api/profile/create/', ProfileTypeView.as_view()),
        
        path('api/locations/', LocationAPIView.as_view()),
        
        
        ################## Mobile Dashboard Image  ################
        
        path('api/dashboard-images/', DashboardImageAPI.as_view())
         
        #new apis generation
        
        # path("api/validation/",RegistartionAPI.as_view(),name="regvalidation"),

        # path("api/otpverification/",RegistartionAPI.as_view(),name="otpVarification"),
        # path("api/googleuseregister/",RegistartionAPI.as_view(),name="googleregister"),
        # path("api/appleuseregister/",RegistartionAPI.as_view(),name="appleregister"),
    ]