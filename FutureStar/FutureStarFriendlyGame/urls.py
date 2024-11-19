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





      path('api/f_teamplayers/',FriendlyGameTeamPlayersAPIView.as_view()),
      path('api/f_teamplayers/Add/',FriendlyGameTeamPlayersAPIView.as_view()),
      path('api/f_teamplayers/jersey_no/',AddPlayerJerseyAPIView.as_view()),
      path('api/f_teamplayers/delete/', FriendlyGameTeamPlayersAPIView.as_view()),

      path('api/f_lineup/update/', FriendyGameLineupPlayers.as_view()),
      path('api/f_lineup/reset/', FriendyGameLineupPlayers.as_view()),
      path('api/f_lineup/',FriendyGameLineupPlayers.as_view()),
   


      path('api/f_lineup/player_confirmation/status/',FriendlyGameLineupPlayerStatusAPIView.as_view()),
      path('api/f_lineup/player_confirmation/status_change/',FriendlyGameLineupPlayerStatusAPIView.as_view()),
      # path('api/lineup/player_substitute/',PlayerSubstitutionAPIView.as_view()),


      path('api/game_stats/f_lineup/',FriendlyGameStatsLineupPlayers.as_view()),
      path('api/game_stats/f_player_stats/',FriendlyPlayerGameStatsAPIView.as_view()),
      
      path('api/game_stats/f_timeline/',FriendlyPlayerGameStatsTimelineAPIView.as_view()),
      
      # path('api/game_stats/team_stats/',TeamGameGoalCountAPIView.as_view()),
      
      


      # path('api/game_officials_type/',GameOficialTypesList.as_view()),


      # path('api/game-officials/', GameOfficialsAPIView.as_view()),
      # path('api/game-officials/add/', GameOfficialsAPIView.as_view()),
      # path('api/game-officials/remove/', GameOfficialsAPIView.as_view()),



      # path('api/top_player_stats/', TopPlayerStatsAPIView.as_view()),
   ]
       
   