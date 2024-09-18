<<<<<<< Updated upstream
from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect


def custom_404_view(request, exception=None):
    if not request.user.is_authenticated:
        return redirect('login')  # Redirect to login if the user is not authenticated
    return render(request, 'error\error.html', status=404)

handler404 = 'FutureStar_App.urls.custom_404_view'

urlpatterns = [


    #Login URL
    path('', LoginFormView,name="login"),


    #Dashboard URL
    path('Dashboard/', Dashboard.as_view(),name="Dashboard"),


    #Logout URL
    path('logout/', logout_view, name='logout'),  # Add the logout path here

    # Forgot Password 
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/<str:token>/', ResetPasswordView.as_view(), name='reset_password'),

    #System Settings Page
    path('System-Settings/', System_Settings.as_view(),name="System_Settings"),


    #User List URL
    path('players/', PlayerListView.as_view(), name='player_list'),
    path('coach/', CoachListView.as_view(), name='coach_list'),
    path('referee/', RefereeListView.as_view(), name='referee_list'),


    # path('users/<int:user_id>/edit/', UserEditView.as_view(), name='user_edit'),
    # path('users/<int:user_id>/update/', UserEditView.as_view(), name='user_update'),
    # path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
    path('user/<int:pk>/toggle-status/', ToggleUserStatusView.as_view(), name='user_toggle_status'),


    #User Profile
    path('user_profile/',UserProfileView.as_view(),name='user_profile'),
    path('edit_profile/', UserUpdateProfileView.as_view(), name='edit_profile'),


    
    #User Role URL
    path('roles/', RoleListView.as_view(), name='role_list'),
    path('roles/create/', RoleCreateView.as_view(), name='role_create'),
    path('roles/update/<int:pk>/', RoleUpdateView.as_view(), name='role_update'),
    path('roles/delete/<int:pk>/', RoleDeleteView.as_view(), name='role_delete'),

    
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

    # Tournament Style URL
    path('tournamentstyle/', TournamentStyleListView.as_view(), name='tournamentstyle_list'),
    path('tournamentstyle/create/', TournamentStyleCreateView.as_view(), name='tournamentstyle_create'),
    path('tournamentstyle/update/<int:pk>/', TournamentStyleUpdateView.as_view(), name='tournamentstyle_update'),
    path('tournamentstyle/delete/<int:pk>/', TournamentStyleDeleteView.as_view(), name='tournamentstyle_delete'),

    # Event Type URL
    path('eventtype/', EventTypeListView.as_view(), name='eventtype_list'),
    path('eventtype/create/', EventTypeCreateView.as_view(), name='eventtype_create'),
    path('eventtype/update/<int:pk>/', EventTypeUpdateView.as_view(), name='eventtype_update'),
    path('eventtype/delete/<int:pk>/', EventTypeDeleteView.as_view(), name='eventtype_delete'),
    
    # CMS Pages URLS
    path('cmspages/',CMSPages.as_view(),name = "cmspages_urls"),

    #News List URL
    path('news/', NewsListView.as_view(), name='news_list'),
    path('news/create/', NewsCreateView.as_view(), name='news_create'),
    path('news/edit/<int:news_id>/', NewsEditView.as_view(), name='news_edit'),  # Edit URL
    path('news/delete/<int:pk>/', NewsDeleteView.as_view(), name='news_delete'),

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

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)   


=======
from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect


def custom_404_view(request, exception=None):
    if not request.user.is_authenticated:
        return redirect('login')  # Redirect to login if the user is not authenticated
    return render(request, 'error\error.html', status=404)

handler404 = 'FutureStar_App.urls.custom_404_view'

urlpatterns = [


    #Login URL
    path('', LoginFormView,name="login"),


    #Dashboard URL
    path('Dashboard/', Dashboard.as_view(),name="Dashboard"),


    #Logout URL
    path('logout/', logout_view, name='logout'),  # Add the logout path here

    # Forgot Password 
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/<str:token>/', ResetPasswordView.as_view(), name='reset_password'),

    #System Settings Page
    path('System-Settings/', System_Settings.as_view(),name="System_Settings"),


    #User List URL
    path('players/', PlayerListView.as_view(), name='player_list'),
    path('coach/', CoachListView.as_view(), name='coach_list'),
    path('referee/', RefereeListView.as_view(), name='referee_list'),


    # path('users/<int:user_id>/edit/', UserEditView.as_view(), name='user_edit'),
    # path('users/<int:user_id>/update/', UserEditView.as_view(), name='user_update'),
    # path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
    path('user/<int:pk>/toggle-status/', ToggleUserStatusView.as_view(), name='user_toggle_status'),


    #User Profile
    path('user_profile/',UserProfileView.as_view(),name='user_profile'),
    path('edit_profile/', UserUpdateProfileView.as_view(), name='edit_profile'),


    
    #User Role URL
    path('roles/', RoleListView.as_view(), name='role_list'),
    path('roles/create/', RoleCreateView.as_view(), name='role_create'),
    path('roles/update/<int:pk>/', RoleUpdateView.as_view(), name='role_update'),
    path('roles/delete/<int:pk>/', RoleDeleteView.as_view(), name='role_delete'),

    
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

    # Tournament Style URL
    path('tournamentstyle/', TournamentStyleListView.as_view(), name='tournamentstyle_list'),
    path('tournamentstyle/create/', TournamentStyleCreateView.as_view(), name='tournamentstyle_create'),
    path('tournamentstyle/update/<int:pk>/', TournamentStyleUpdateView.as_view(), name='tournamentstyle_update'),
    path('tournamentstyle/delete/<int:pk>/', TournamentStyleDeleteView.as_view(), name='tournamentstyle_delete'),

    # Event Type URL
    path('eventtype/', EventTypeListView.as_view(), name='eventtype_list'),
    path('eventtype/create/', EventTypeCreateView.as_view(), name='eventtype_create'),
    path('eventtype/update/<int:pk>/', EventTypeUpdateView.as_view(), name='eventtype_update'),
    path('eventtype/delete/<int:pk>/', EventTypeDeleteView.as_view(), name='eventtype_delete'),
    
    # CMS Pages URLS
    path('cmspages/',CMSPages.as_view(),name = "cmspages_urls"),

    #News List URL
    path('news/', NewsListView.as_view(), name='news_list'),
    path('news/create/', NewsCreateView.as_view(), name='news_create'),
    path('news/edit/<int:news_id>/', NewsEditView.as_view(), name='news_edit'),  # Edit URL
    path('news/delete/<int:pk>/', NewsDeleteView.as_view(), name='news_delete'),

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

    #cms_pages
    path('contactus/',cms_contactpage.as_view(),name="cms_contactpage"),
    path('savecontactedit/',savecontactpage,name="savecontactpage"),
    
    path('aboutus/',cms_aboutpage.as_view(),name="cms_aboutpage"),
    path('saveaboutusedit/',saveAboutUspage,name="saveaboutuspage"),
    
    path('FAQ/',cms_FAQPage.as_view(),name="cms_faqpage"),
    path('saveFAQedit/',saveFAQpage,name="savefaqpage"),
    
    path('successStory/',cms_successStory.as_view(),name="cms_successStorypage"),
    path('saveSuccessStory/',saveSucessStorypage,name = "saveSucessStorypage")
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)   


>>>>>>> Stashed changes
