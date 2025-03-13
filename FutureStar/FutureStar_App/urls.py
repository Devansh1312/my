from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [


    #Login URL
    path('adminlogin/', LoginFormView,name="adminlogin"),

    #Dashboard URL
    path('Dashboard/', Dashboard.as_view(),name="Dashboard"),

    #Logout URL
    path('logout/', logout_view, name='logout'),  # Add the logout path here

    # # Forgot Password 
    # path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    # path('reset-password/<str:token>/', ResetPasswordView.as_view(), name='reset_password'),

    #System Settings Page
    path('System-Settings/', System_Settings.as_view(),name="System_Settings"),

    #User List URL
    path('players/', PlayerListView.as_view(), name='player_list'),
    path('coach/', CoachListView.as_view(), name='coach_list'),
    path('manager/', ManagerListView.as_view(), name='manager_list'),
    path('Deleted-Accounts/', DeletedAccountUserList.as_view(), name='DeletedAccountUserList'),



    path('referee/', RefereeListView.as_view(), name='referee_list'),
    path('default-user/', DefaultUserList.as_view(), name='default_user_list'),
    path('user/', UserDetailView.as_view(), name='user_detail'),

    path('player-games/<int:user_id>/update-stats/', UpdatePlayerStatsView.as_view(), name='update_player_game_stats'),


    # path('manager/<int:pk>/', ManagerDetailView.as_view(), name='manager_detail'),
    path('tournament_list/', TournamentListView.as_view(), name='tournament_list'),
    path('tournament_detail/<int:pk>/', TournamentDetailView.as_view(), name='tournament_detail'),
    



    # path('users/<int:user_id>/edit/', UserEditView.as_view(), name='user_edit'),
    # path('users/<int:user_id>/update/', UserEditView.as_view(), name='user_update'),
    # path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
    path('user/<int:pk>/toggle-status/', ToggleUserStatusView.as_view(), name='user_toggle_status'),

    #User Profile
    path('user_profile/',UserProfileView.as_view(),name='user_profile'),
    path('edit_profile/', UserUpdateProfileView.as_view(), name='edit_profile'),
    path('change_password_ajax/', change_password_ajax, name='change_password_ajax'),
    
    #User Role URL
    path('roles/', RoleListView.as_view(), name='role_list'),
    path('roles/create/', RoleCreateView.as_view(), name='role_create'),
    path('roles/update/<int:pk>/', RoleUpdateView.as_view(), name='role_update'),
    path('roles/delete/<int:pk>/', RoleDeleteView.as_view(), name='role_delete'),
    
    #User AgeGroup URL
    path('agegroup/', AgeGroupListView.as_view(), name='agegroup_list'),
    path('agegroup/create/', AgeGroupCreateView.as_view(), name='agegroup_create'),
    path('agegroup/update/<int:pk>/', AgeGroupUpdateView.as_view(), name='agegroup_update'),
    path('agegroup/delete/<int:pk>/', AgeGroupDeleteView.as_view(), name='agegroup_delete'),

    #Category List URL
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/create/', CategoryCreateView.as_view(), name='category_create'),
    path('categories/update/<int:pk>/', CategoryUpdateView.as_view(), name='category_update'),
    path('categories/delete/<int:pk>/', CategoryDeleteView.as_view(), name='category_delete'),

    # #Gender Role URL
    # path('gender/', GenderListView.as_view(), name='gender_list'),
    # path('gender/create/', GenderCreateView.as_view(), name='gender_create'),
    # path('gender/update/<int:pk>/', GenderUpdateView.as_view(), name='gender_update'),
    # path('gender/delete/<int:pk>/', GenderDeleteView.as_view(), name='gender_delete'),

    # FieldCapacity URL
    path('fieldcapacity/', FieldCapacityListView.as_view(), name='fieldcapacity_list'),
    path('fieldcapacity/create/', FieldCapacityCreateView.as_view(), name='fieldcapacity_create'),
    path('fieldcapacity/update/<int:pk>/', FieldCapacityUpdateView.as_view(), name='fieldcapacity_update'),
    path('fieldcapacity/delete/<int:pk>/', FieldCapacityDeleteView.as_view(), name='fieldcapacity_delete'),

    # Ground Materials URL
    path('groundmaterial/', GroundMaterialListView.as_view(), name='groundmaterial_list'),
    path('groundmaterial/create/', GroundMaterialCreateView.as_view(), name='groundmaterial_create'),
    path('groundmaterial/update/<int:pk>/', GroundMaterialUpdateView.as_view(), name='groundmaterial_update'),
    path('groundmaterial/delete/<int:pk>/', GroundMaterialDeleteView.as_view(), name='groundmaterial_delete'),

    # Event Type URL
    path('eventtype/', EventTypeListView.as_view(), name='eventtype_list'),
    path('eventtype/create/', EventTypeCreateView.as_view(), name='eventtype_create'),
    path('eventtype/update/<int:pk>/', EventTypeUpdateView.as_view(), name='eventtype_update'),
    path('eventtype/delete/<int:pk>/', EventTypeDeleteView.as_view(), name='eventtype_delete'),

    # Events
    path('events/', EventListView.as_view(), name='event_list'),
    path('events_detail/<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('event/<int:pk>/approval/', EventApprovalView.as_view(), name='event_approval'),

    

       

    #field
    path('fields/', FieldListView.as_view(), name='field_list'),
    path('fields_detail/<int:pk>/', FieldDetailView.as_view(), name='field_detail'),

    
    
   # CMS Pages URLS
    path('cmspages/',CMSPages.as_view(),name = "cmspages_urls"),
    #cms_pages
    path('contactus/',cms_contactpage.as_view(),name="cms_contactpage"),
    path('savecontactedit/',savecontactpage,name="savecontactpage"),
    
    path('aboutus/',cms_aboutpage.as_view(),name="cms_aboutpage"),
    path('saveaboutusedit/',saveAboutUspage,name="saveaboutuspage"),
    
    path('NewsCms/',cms_newsPage.as_view(),name="cms_newspage"),
    path('savenewsedit/',savenewspage,name="savenewspage"),

    path('successStory/',cms_successStory.as_view(),name="cms_successStorypage"),
    path('saveSuccessStory/',saveSucessStorypage,name = "saveSucessStorypage"),
    
    #privacypolicy
    path('privacypolicy/',cms_privacypolicy.as_view(),name = "cms_privacypolicypage"),
    path('saveprivacypolicypage/',saveprivacypolicypage,name = "saveprivacypolicypage"),

    #termandservice
    path('termandservice/',cms_termandserice.as_view(),name = "cms_termandservicepage"),
    path('savetermservicepage/',savetermservicepage,name="cms_saveterservicepage"),
    #termconditionpage
    path('termcondition/',cms_termcondition.as_view(),name="termcondition"),
    path('savetermcondition/',savetermconditionpage,name="savetermconditionpage"),
    
    #newsdetail
    path('cms_newsdetail/',cms_newsdetail.as_view(),name = "cms_newsdetail"),
    path('savenewsdetail/',savenewsdetail,name = "savenewsdetail"),

    #cms_discoverypage
    path('cms_discoverypage/',cms_discoverypage.as_view(),name = "cms_discoverypage"),
    path('saveDiscoverdetail/',saveDiscoverdetail,name="saveDiscoverdetail"),
    #cms_advertisepage
    path('cms_advertisepage/',cms_advertisepage.as_view(),name = "cms_advertisepage"),
    path('saveadvertisedetail/',saveadvertisedetail,name = "advertisedetail"),

    #cms home page
    path('cms-homepage/',cms_homepage.as_view(),name="cms_homepage"),
    path('savehomepage/',savehomedetail,name="savehomepage"),
    
    #cms_loginpage
    path('cms-login/',cms_Login.as_view(),name="cms_login"),
    path('cms_logindetail/',savelogindetail,name="savelogindetail"),

    #Registration 
    path('cms-regpage/',cms_registration.as_view(),name="cms_reg"),
    path('cms_regdetail/',saveregdetail,name="saveregdetail"),

    #dashboard 
    path('cms-dashboardpage/',cms_dashboard.as_view(),name="cms_dashboard"),
    path('cms_dashboarddetail/',savedashdetail,name="savedashdetail"),
    
    #News List URL
    path('news_list/', NewsListView.as_view(), name='news_list'),
    path('news_list/create/', NewsCreateView.as_view(), name='news_create'),
    path('news_list/edit/<int:news_id>/', NewsEditView.as_view(), name='news_edit'),  # Edit URL
    path('news_list/delete/<int:pk>/', NewsDeleteView.as_view(), name='news_delete'),

    #Partners List URL
    path('partners/', PartnersListView.as_view(), name='partners_list'),
    path('partners/create/', PartnersCreateView.as_view(), name='partners_create'),
    path('partners/edit/<int:partners_id>/', PartnersEditView.as_view(), name='partners_edit'),  # Edit URL
    path('partners/delete/<int:pk>/', PartnersDeleteView.as_view(), name='partners_delete'),

    #Global_Clients List URL
    path('global_clients/', Global_ClientsListView.as_view(), name='global_clients_list'),
    path('global_clients/create/', Global_ClientsCreateView.as_view(), name='global_clients_create'),
    path('global_clients/edit/<int:global_clients_id>/', Global_ClientsEditView.as_view(), name='global_clients_edit'),  # Edit URL
    path('global_clients/delete/<int:pk>/', Global_ClientsDeleteView.as_view(), name='global_clients_delete'),

    #Tryout Club List URL
    path('tryout_club/', Tryout_ClubListView.as_view(), name='tryout_club_list'),
    path('tryout_club/create/', Tryout_ClubCreateView.as_view(), name='tryout_club_create'),
    path('tryout_club/edit/<int:tryout_club_id>/', Tryout_ClubEditView.as_view(), name='tryout_club_edit'),  # Edit URL
    path('tryout_club/delete/<int:pk>/', Tryout_ClubDeleteView.as_view(), name='tryout_club_delete'),

    #Inquires List URL
    path('inquire/', InquireListView.as_view(), name='inquire_list'),

    #Tryout Club List URL
    path('testimonial/', TestimonialListView.as_view(), name='testimonial_list'),
    path('testimonial/create/', TestimonialCreateView.as_view(), name='testimonial_create'),
    path('testimonial/edit/<int:testimonial_id>/', TestimonialEditView.as_view(), name='testimonial_edit'),  # Edit URL
    path('testimonial/delete/<int:pk>/', TestimonialDeleteView.as_view(), name='testimonial_delete'),

    #Team_Members List URL
    path('team_members/', Team_MembersListView.as_view(), name='team_members_list'),
    path('team_members/create/', Team_MembersCreateView.as_view(), name='team_members_create'),
    path('team_members/edit/<int:team_members_id>/', Team_MembersEditView.as_view(), name='team_members_edit'),  # Edit URL
    path('team_members/delete/<int:pk>/', Team_MembersDeleteView.as_view(), name='team_members_delete'),

    #App_Feature List URL
    path('app_feature/', App_FeatureListView.as_view(), name='app_feature_list'),
    path('app_feature/create/', App_FeatureCreateView.as_view(), name='app_feature_create'),
    path('app_feature/edit/<int:app_feature_id>/', App_FeatureEditView.as_view(), name='app_feature_edit'),  # Edit URL
    path('app_feature/delete/<int:pk>/', App_FeatureDeleteView.as_view(), name='app_feature_delete'),

    # Slider_Content URL
    path('slider_content/', Slider_ContentListView.as_view(), name='slider_content_list'),
    path('slider_content/create/', Slider_ContentCreateView.as_view(), name='slider_content_create'),
    path('slider_content/update/<int:pk>/', Slider_ContentUpdateView.as_view(), name='slider_content_update'),
    path('slider_content/delete/<int:pk>/', Slider_ContentDeleteView.as_view(), name='slider_content_delete'),

    #dashboard_banner URL
    path('dashboard_banner/', MobileDashboardBannerListView.as_view(), name='dashboard_banner_list'),
    path('dashboard_banner/create/', MobileDashboardBannerCreateView.as_view(), name='dashboard_banner_create'),
    path('dashboard_banner/edit/<int:pk>/', MobileDashboardBannerEditView.as_view(), name='dashboard_banner_edit'),  # Edit URL
    path('dashboard_banner/delete/<int:pk>/', MobileDashboardBannerDeleteView.as_view(), name='dashboard_banner_delete'),
    
    #Report URl's
    path('reports/', ReportListView.as_view(), name='report_list'),
    path('reports/create/', ReportCreateView.as_view(), name='report_create'),
    path('reports/edit/<int:report_id>/', ReportEditView.as_view(), name='report_edit'),
    path('reports/delete/<int:pk>/', ReportDeleteView.as_view(), name='report_delete'),

    #Post Report URL's
    path('post_reports/', PostReportListView.as_view(), name='post_report_list'),
    path('post_reports/delete/<int:pk>/', PostReportDeleteView.as_view(), name='report_delete'),
    
    #Team list URL's
    path('team_lists/', TeamListView.as_view(), name='team_list'),
   
    path('team_profile_detail/', TeamDetailView.as_view(), name='team_detail'),
    path('team_detail/', BranchDetailView.as_view(), name='branch_detail'),
    
    #User injury type URL
    path('injurytype/', InjuryTypeListView.as_view(), name='injurytype_list'),
    path('injurytype/create/', InjuryTypeCreateView.as_view(), name='injurytype_create'),
    path('injurytype/update/<int:pk>/', InjuryTypeUpdateView.as_view(), name='injurytype_update'),
    path('injurytype/delete/<int:pk>/', InjuryTypeDeleteView.as_view(), name='injurytype_delete'),

    #Game Officials TypeForm URL
    path('gameofficialstype/', GameOfficialsTypeListView.as_view(), name='gameofficialstype_list'),
    path('gameofficialstype/create/', GameOfficialsTypeCreateView.as_view(), name='gameofficialstype_create'),
    path('gameofficialstype/update/<int:pk>/', GameOfficialsTypeUpdateView.as_view(), name='gameofficialstype_update'),
    path('gameofficialstype/delete/<int:pk>/', GameOfficialsTypeDeleteView.as_view(), name='gameofficialstype_delete'),

    #Game Officials TypeForm URL
    path('accountdeletereason/', AccountDeleteReasonListView.as_view(), name='accountdeletereason_list'),
    path('accountdeletereason/create/', AccountDeleteReasonCreateView.as_view(), name='accountdeletereason_create'),
    path('accountdeletereason/update/<int:pk>/', AccountDeleteReasonUpdateView.as_view(), name='accountdeletereason_update'),
    path('accountdeletereason/delete/<int:pk>/', AccountDeleteReasonDeleteView.as_view(), name='accountdeletereason_delete'),


    #Playing Position URLS's
    path('playing_positions/', PlayingPositionListView.as_view(), name='playing_position_list'),
    path('playing_positions/create/', PlayingPositionCreateView.as_view(), name='playing_position_create'),
    path('playing_positions/edit/<int:playing_position_id>/', PlayingPositionEditView.as_view(), name='playing_position_edit'),


    ############# Assign user for Tournament #################
    path('tournament-games-list/', TournamentGamesListView.as_view(), name='tournament_games_list'),
    path('api/assignd_users_search/', fetch_users, name='fetch_users'),
    path('api/tournament-games/<int:game_id>/assign-user/', AssignUserToGameView.as_view(), name='assign_user_to_game'),

    ########### Assign user for Freindly #########################
    # Friendly Games
    path('friendly-games-list/', FriendlyGamesListView.as_view(), name='friendly_games_list'),
    path('api/friendly-games/<int:game_id>/assign-user/', AssignUserToFriendlyGameView.as_view(), name='assign_user_to_friendly_game'),

  
  ################## Tournament Game States Add URLS ############################
    # path('games/', TournamentGameStatsView.as_view(), name='games_list'),
    # path('games/edit/<int:game_id>/', TournamentGameEditStatsView.as_view(), name='edit_game_stats'),
    path('tournament-games/<int:pk>/update-stats/', UpdateGameStatsView.as_view(), name='update_game_stats'),
    path('tournament-games/<int:game_id>/details/', TournamentGameDetailView.as_view(), name='game_detail'),



    ################## Friendly Game States Add URLS ############################
  
    # path('friendly-games/', FriendlyGameStatsView.as_view(), name='friendly_games_list_stats'),
    path('friendly-games/<int:pk>/update-stats/', FriendlyGameEditStatsView.as_view(), name='update_game_stats'),


    path('friendly-games/<int:game_id>/details/', FriendlyGameDetailView.as_view(), name='friendly_game_detail'),




    ################# User Apply role list ##################
    path('user/role/apply/', UserRoleAppliedListView.as_view(), name='user_apply_list'),
    path('user/role/action/', UserRoleActionView.as_view(), name='user_role_action'),



    ########## Pendding Booking of Event ############
    path('requested-event-booking/', PendingEventBookingListView.as_view(), name='PendingEventBookingListView'),
    path('booking-detail/', PendingBookingDetailView.as_view(), name='booking_detail'),
    path('approve-reject-booking/', ApproveRejectBookingView.as_view(), name='approve_or_reject_booking'),


     ############ Training URL's ##############
    path('open-trainings/', OpenTrainingListView.as_view(), name='open-trainings'),
    path("open-training/<int:training_id>/", OpenTrainingDetailView.as_view(), name="open_training_detail"),
    path('close-trainings/', ClosedTrainingListView.as_view(), name='close-trainings'),
    path("close-training/<int:training_id>/", CloseTrainingDetailView.as_view(), name="close_training_detail"),




] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)   
