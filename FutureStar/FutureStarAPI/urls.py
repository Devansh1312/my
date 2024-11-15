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
        

        # Switch Current User Type 
        path('api/user/update-current-type/', UpdateCurrentTypeAPIView.as_view()),
        path('api/user_account_delete_reasons/list/', DeleteAccountReasonsListView.as_view()),


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



        path('api/media/album_detail/', DetailAlbumListAPIView.as_view()),
        path('api/media/album_create/', DetailAlbumCreateAPIView.as_view()),
        path('api/media/all_albums/', AlbumListAPIView.as_view()),
       
        #############gallary############
       
        path('api/media/all_photos/', ImageGallaryListAPIView.as_view(), name='gallary-list'),
        path('api/media/all_videos/', VideoGallaryListAPIView.as_view(), name='gallary-list'),
        
        path('api/media/create/', GallaryCreateAPIView.as_view(), name='gallary-create'),
        path('api/media/recent/', LatestGallaryListAPIView.as_view()),
       
        #############delete album & gallary############

        path('api/media/album_delete/', AlbumDeleteAPIView.as_view()),
        path('api/media/delete/', GallaryDeleteAPIView.as_view()),

        ########################## Events URL ##################
       
        path('api/events/', EventsAPIView.as_view()),
        path('api/events/create/', EventCreateAPIView.as_view()),
        path('api/events/types/', EventCreateAPIView.as_view()),

        path('api/events/update/', UpdateEventAPIView.as_view()),
        # path('api/events/delete/',DeleteEventAPIView.as_view()),
        path('api/events/booking/', EventBookingDetailView.as_view()),
        # path('api/joined_events/', EventsJoinedAPIView.as_view()),

        path('api/events/booking/create/', EventBookingCreateAPIView.as_view()),

        path('api/events/detail/', EventDetailAPIView.as_view()),
        # path('api/team_events/', TeamEventAPIView.as_view()),
        # path('api/user_events/', UserEventsAPIView.as_view()),


        path('api/events/like/', EventLikeAPIView.as_view()),
        path('api/events/comments/', EventCommentAPIView.as_view()),  # New API for paginated comments
        path('api/events/comments/create/', EventCommentCreateAPIView.as_view()),
      

      

     

        ########################## Sponsor URL ##################
        path('api/sponsor/', SponsorAPI.as_view()),
        path('api/sponsor/detail/', SponsorDetailAPIView.as_view()),



        ########################## Report URL ##################

        path('api/reports/', ReportListAPIView.as_view()),
        path('api/reports/create/', PostReportCreateView.as_view()),

        ################## fileds URL ################
        path('api/fields/', FieldAPIView.as_view()),

        ############### Additional API #########################
        path('api/genders/', UserGenderListAPIView.as_view()),
        path('api/age_groups/', AgeGroupListAPIView.as_view()),

        path('api/general/settings/', GeneralSettingsList.as_view()),
        path('api/faq/', FAQListAPIView.as_view()),
        path('api/role/', UserRoleListAPIView.as_view()),
        path('api/locations/', LocationAPIView.as_view()),
        path('api/playing_positions/', PlayingPositionListAPIView.as_view()),
        path('api/injury_types/', InjuryListAPIView.as_view()),

        ###################### New Coach or Refree Profile ########################
        path('api/profile/create/', ProfileTypeView.as_view()),
        
        ################## Mobile Dashboard Image  ################
        
        path('api/dashboard-images/', DashboardImageAPI.as_view())
         
        #new apis generation
        
        # path("api/validation/",RegistartionAPI.as_view(),name="regvalidation"),

        # path("api/otpverification/",RegistartionAPI.as_view(),name="otpVarification"),
        # path("api/googleuseregister/",RegistartionAPI.as_view(),name="googleregister"),
        # path("api/appleuseregister/",RegistartionAPI.as_view(),name="appleregister"),
    ]