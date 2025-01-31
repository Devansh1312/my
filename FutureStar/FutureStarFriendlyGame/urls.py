from django.urls import path
from FutureStarFriendlyGame.views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect

urlpatterns = [

      path('api/friendlygames/create/', CreateFriendlyGame.as_view()),
      path('api/friendlygames/requested_referee/list/', OfficialListView.as_view()),
      path('api/friendlygames/edit_detail/', CreateFriendlyGame.as_view()),
      path('api/friendlygames/update/', UpdateFriendlyGame.as_view()),

      path('api/friendlygames/update_detail/', UpdateFriendlyGameDetailAPIView.as_view()),

      path('api/friendlygames/team_list_of_manager/', ManagerBranchDetail.as_view()),
      path('api/friendlygames/delete/', DeleteFriendlyGame.as_view()),
      path('api/friendlygames/detail/', FriendlyGameDetailAPIView.as_view()),
      
      path('api/send_referee_notification/', SendRefereeNotification.as_view(), name='send_referee_notification'),


      path('api/friendly-game/list/', ListOfFridlyGamesForJoin.as_view()),
      path('api/friendly-game/branch_list/', TeamBranchListView.as_view()),
      path('api/friendlygames/teamplayers/', FriendlyGameTeamPlayersAPIView.as_view()),
      path('api/friendlygames/teamplayers/add/', FriendlyGameTeamPlayersAPIView.as_view()),
      path('api/friendlygames/teamplayers/jersey_no/', FriendlyAddPlayerJerseyAPIView.as_view()),
      path('api/friendlygames/teamplayers/delete/', FriendlyGameTeamPlayersAPIView.as_view()),
      # Lineup Management
      path('api/friendlygames/lineup/', FriendlyGameLineupPlayers.as_view()),
      path('api/friendlygames/lineup/player_substitute/', FriendlyPlayerSubstitutionAPIView.as_view()),
      path('api/friendlygames/lineup/swap_position/', FriendlyGameSwapPositionView.as_view()),
      path('api/friendlygames/lineup/fetch_position/', FriendlyGameSwapPositionView.as_view()),
      path('api/friendlygames/lineup/update/', FriendlyGameLineupPlayers.as_view()),
      path('api/friendlygames/lineup/reset/', FriendlyGameLineupPlayers.as_view()),
      path('api/friendlygames/lineup/player_confirmation/status/', FriendlyGameLineupPlayerStatusAPIView.as_view()),
      path('api/friendlygames/lineup/player_confirmation/status_change/', FriendlyGameLineupPlayerStatusAPIView.as_view()),
      # Game Stats Management
      path('api/friendlygames/game_stats/lineup/', FriendlyGameStatsLineupPlayers.as_view()),
      path('api/friendlygames/game_stats/player_stats/', FriendlyPlayerGameStatsAPIView.as_view()),
      path('api/friendlygames/game_stats/timeline/', FriendlyPlayerGameStatsTimelineAPIView.as_view()),
      # Game Officials Management
      path('api/friendlygames/game_officials/type/', FriendlyGameOficialTypesList.as_view()),  # Typo fixed
      path('api/friendlygames/game_officials/', FriendlyGameOfficialsAPIView.as_view()),
      path('api/friendlygames/game_officials/add/', FriendlyGameOfficialsAPIView.as_view()),
      path('api/friendlygames/game_officials/remove/', FriendlyGameOfficialsAPIView.as_view()),
      path('api/friendlygames/game_officials/search/', FriendlyOfficialSearchView.as_view()),
      # Player Stats & Tournament Details
      path('api/friendlygames/game/linup/details/', FriendlyGamesDetailAPIView.as_view()),
      # Friendly Game Stats
      path('api/friendlygames/h2h/completed/', FriendlyGamesh2hCompleteAPIView.as_view(), name='friendly_games_completed'),
      path('api/friendlygames/game_detail_stats/', FriendlyTeamGameDetailStatsAPIView.as_view(), name='friendly_game_stats'),
      path('api/friendlygames/update_result/',FriendlyGameResult.as_view()),
      # Team Uniform Management
      path('api/friendlygames/team_uniform/create/', FriendlyGameUniformColorAPIView.as_view(), name='friendly_game_stats'),
      path('api/friendlygames/team_uniform/', FetchFriendlyGameUniformColorAPIView.as_view(), name='friendly_game_stats'),
      path('api/friendlygames/uniform_fetch/',FriendlyGameUniformAPIView.as_view()),
]
       
   