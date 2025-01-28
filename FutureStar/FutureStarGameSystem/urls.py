from django.urls import path

from FutureStarGameSystem.views import *

from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect

urlpatterns = [
    path('api/teamplayers/',TeamPlayersAPIView.as_view()),
    path('api/teamplayers/Add/',TeamPlayersAPIView.as_view()),
    path('api/teamplayers/jersey_no/',AddPlayerJerseyAPIView.as_view()),
    path('api/teamplayers/delete/', TeamPlayersAPIView.as_view()),
    path('api/lineup/update/', LineupPlayers.as_view()),
    path('api/lineup/reset/', LineupPlayers.as_view()),
    path('api/lineup/',LineupPlayers.as_view()),
    path('api/lineup/player_confirmation/status/',LineupPlayerStatusAPIView.as_view()),
    path('api/lineup/player_confirmation/status_change/',LineupPlayerStatusAPIView.as_view()),
    path('api/lineup/player_substitute/',PlayerSubstitutionAPIView.as_view()),
    path('api/lineup/swap_position/', SwapPositionView.as_view()),
    path('api/lineup/fetch_position/', SwapPositionView.as_view()),
    path('api/game_stats/lineup/',GameStatsLineupPlayers.as_view()),
    path('api/game_stats/player_stats/',PlayerGameStatsAPIView.as_view()),
    path('api/game_stats/timeline/',TeamGameStatsTimelineAPIView.as_view()),   
    path('api/game_officials_type/',GameOficialTypesList.as_view()),
    path('api/game-officials/', GameOfficialsAPIView.as_view()),
    path('api/game-officials/add/', GameOfficialsAPIView.as_view()),
    path('api/game-officials/remove/', GameOfficialsAPIView.as_view()),
    path('api/game-officials/search/', OfficialSearchView.as_view()),
    path('api/top_player_stats/', TopPlayerStatsAPIView.as_view()),
    ]