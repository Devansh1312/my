from django.urls import path
from FutureStarTournamentApp.views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect


handler404 = 'FutureStarFrontend.views.custom_404_view'

urlpatterns = [
    
        path('api/tournament/', TournamentAPIView.as_view()),
        path('api/tournament/create/', TournamentAPIView.as_view()),
        
        path('api/tournament/team_request/', TeamJoiningRequest.as_view()),
        path('api/tournament/team_reject/', TeamRejectRequest.as_view()),
        path('api/tournament/team_accept/', TeamRequestApproved.as_view()),


        path('api/tournament/detail/', TournamentDetailAPIView.as_view()),
        path('api/tournament/team/', TournamentGroupTeamListView.as_view()),

        path('api/tournament/games/create/', TournamentGamesAPIView.as_view()),
        path('api/tournament/games/', TournamentGamesAPIView.as_view()),
        path('api/tournament/games/update/', TournamentGamesAPIView.as_view()),

        path('api/games/team_uniform/', TeamUniformColorAPIView.as_view()),

        path('api/tournament/games/details/', TournamentGamesDetailAPIView.as_view()),
        path('api/team_game_stats/', TournamentGameStatsAPIView.as_view()),
        path('api/team_game_h2h/', TournamentGamesh2hCompleteAPIView.as_view()),



        path('api/tournament/games/options/', TournamentGamesDetailAPIView.as_view()),



        path('api/group_table/', GroupTableAPIView.as_view()),
        path('api/group_table/team/create/', TournamentGroupTeamListCreateAPIView.as_view()),
        path('api/group_table/team/', TournamentGroupTeamListCreateAPIView.as_view()),

        path('api/search-team-branches/', TeamBranchSearchView.as_view()),

        ####### Like Coment API ###############
        path('api/tournaments/like/', TournamentLikeAPIView.as_view()),
        path('api/tournaments/comments/', TournamentCommentAPIView.as_view()),  # New API for paginated comments
        path('api/tournaments/comments/create/', TournamentCommentCreateAPIView.as_view()),





    ]

handler404 = 'FutureStarFrontend.views.custom_404_view'