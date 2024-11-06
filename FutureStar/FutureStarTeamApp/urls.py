from django.urls import path
from FutureStarTeamApp.views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect

urlpatterns = [

        ################# Team URL ################
        path('api/team/', TeamViewAPI.as_view()),
        path('api/team_branch/', TeamBranchAPIView.as_view()),
        path('api/team_branch/create/', TeamBranchAPIView.as_view()),
        path('api/staff-management/', StaffManagementView.as_view()),
        path('api/search_users/', UserSearchView.as_view()),

    ]