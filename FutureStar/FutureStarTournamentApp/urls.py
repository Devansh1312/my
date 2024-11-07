from django.urls import path
from FutureStarTournamentApp.views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect


handler404 = 'FutureStarFrontend.views.custom_404_view'

urlpatterns = [
    
        path('api/tournament/', TournamentAPIView.as_view()),
        path('api/tournament/create/', TournamentAPIView.as_view()),
        path('api/tournament/detail/', TournamentDetailAPIView.as_view()),


        path('api/group_table/', GroupTableAPIView.as_view()),
        path('api/group_table/team/create/', TournamentGroupTeamListCreateAPIView.as_view()),
        path('api/group_table/team/', TournamentGroupTeamListCreateAPIView.as_view()),

        path('api/search-team-branches/', TeamBranchSearchView.as_view()),





    ]

handler404 = 'FutureStarFrontend.views.custom_404_view'