from django.urls import path
from FutureStarFriendlyGame.views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect

urlpatterns = [

      path('api/friendly-game/create/', CreateFriendlyGame.as_view()),
      path('api/friendly-game/update/', UpdateFriendlyGame.as_view()),
      path('api/friendly-game/team_list_of_manager/', ManagerBranchDetail.as_view()),
      path('api/friendly-game/delete/', DeleteFriendlyGame.as_view()),

      path('api/friendly-game/list/', ListOfFridlyGamesForJoin.as_view()),

      path('api/friendly-game/branch_list/', TeamBranchListView.as_view()),


 path('api/friendlygames/teamplayers/', FriendlyGameTeamPlayersAPIView.as_view()),
    path('api/friendlygames/teamplayers/add/', FriendlyGameTeamPlayersAPIView.as_view()),
    path('api/friendlygames/teamplayers/jersey_no/', AddPlayerJerseyAPIView.as_view()),
    path('api/friendlygames/teamplayers/remove/', FriendlyGameTeamPlayersAPIView.as_view()),

    # Lineup Management
    path('api/friendlygames/lineup/', FriendlyGameLineupPlayers.as_view()),
    path('api/friendlygames/lineup/update/', FriendlyGameLineupPlayers.as_view()),
    path('api/friendlygames/lineup/reset/', FriendlyGameLineupPlayers.as_view()),
    path('api/friendlygames/lineup/player_confirmation/status/', FriendlyGameLineupPlayerStatusAPIView.as_view()),
    path('api/friendlygames/lineup/player_confirmation/status_change/', FriendlyGameLineupPlayerStatusAPIView.as_view()),

    # Game Stats Management
    path('api/friendlygames/game_stats/lineup/', FriendlyGameStatsLineupPlayers.as_view()),
    path('api/friendlygames/game_stats/player_stats/', FriendlyPlayerGameStatsAPIView.as_view()),
    path('api/friendlygames/game_stats/timeline/', FriendlyPlayerGameStatsTimelineAPIView.as_view()),
    path('api/friendlygames/game_stats/team_stats/', FriendlyTeamGameGoalCountAPIView.as_view()),

    # Game Officials Management
    path('api/friendlygames/game_officials/type/', FriendlyGameOficialTypesList.as_view()),  # Typo fixed
    path('api/friendlygames/game_officials/', FriendlyGameOfficialsAPIView.as_view()),
    path('api/friendlygames/game_officials/add/', FriendlyGameOfficialsAPIView.as_view()),
    path('api/friendlygames/game_officials/remove/', FriendlyGameOfficialsAPIView.as_view()),

    # Player Stats & Tournament Details
    path('api/friendlygames/top_player_stats/', FriendlyGameTopPlayerStatsAPIView.as_view()),
    path('api/friendlygames/tournament/details/', FriendlyTournamentGamesDetailAPIView.as_view()),

    # Friendly Game Stats
    path('api/friendlygames/stats/', FriendlyGameStatsAPIView.as_view(), name='friendly_game_stats'),
    path('api/friendlygames/h2h/completed/', FriendlyGamesh2hCompleteAPIView.as_view(), name='friendly_games_completed'),


   ]
       
   