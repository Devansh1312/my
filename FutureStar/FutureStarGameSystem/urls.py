from django.urls import path

from FutureStarGameSystem.views import *

from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect

urlpatterns = [
    path('api/teamplayers/',TeamPlayersAPIView.as_view()),
    path('api/teamplayers/Add/',TeamPlayersAPIView.as_view()),
    path('api/teamplayers/jersey_no/',AddPlayerJerseyAPIView.as_view()),

    path('api/teamplayers/delete/', DeleteLineupView.as_view()),
    path('api/teamplayers/update/', LineupPlayers.as_view()),
    path('api/lineup/reset/', LineupPlayers.as_view()),
 


    path('api/lineup/',LineupPlayers.as_view()),
    path('api/game_stats/lineup/',GameStatsLineupPlayers.as_view()),

   





    ]