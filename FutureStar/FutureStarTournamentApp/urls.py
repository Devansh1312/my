from django.urls import path
from FutureStarTournamentApp.views import *

urlpatterns = [
    
        path('api/tournament/', TournamentAPIView.as_view()),
        path('api/tournament/my_tournament/', MyTournamentsAPIView.as_view()),
        path('api/tournament/create/', TournamentAPIView.as_view()),
        path('api/tournament/update/', TournamentAPIView.as_view()),
        path('api/tournament/delete/', TournmanetDeleteAPIView.as_view()),
        path('api/tournament/game/detail/', GameDetailsAPIView.as_view()),
        path('api/tournament/team_request/', TeamJoiningRequest.as_view()),
        path('api/tournament/team_reject/', TeamRejectRequest.as_view()),
        path('api/tournament/team_accept/', TeamRequestApproved.as_view()),
        path('api/tournament/detail/', TournamentDetailAPIView.as_view()),
        path('api/tournament/team/', TournamentGroupTeamListView.as_view()),
        path('api/tournament/team/create/', TournamentGroupTeamListCreateAPIView.as_view()),    
        
        
        ## Tournament Game Create Edit Delete API
        path('api/tournament/games/create/', TournamentGamesAPIView.as_view()),
        path('api/tournament/games/edit/', UpdateTournamentGameDetailAPIView.as_view()),
        path('api/tournament/games/delete/', UpdateTournamentGameDetailAPIView.as_view()),

        path('api/tournament/games/', TournamentGamesAPIView.as_view()),
        path('api/tournament/games/update/', TournamentGamesAPIView.as_view()),
        path('api/games/team_uniform/', TeamUniformColorAPIView.as_view()),
        path('api/games/refree/fetch_team_uniform/', FetchTeamUniformColorAPIView.as_view()),
        path('api/games/uniform_fetch/',GameUniformColorAPIView.as_view()),
        path('api/games/refree/confirm_team_uniform/', FetchTeamUniformColorAPIView.as_view()),
        path('api/tournament/game/linup/details/', TournamentGamesDetailAPIView.as_view()),
        path('api/tournament/team_game_h2h/', TournamentGamesh2hCompleteAPIView.as_view()),
        path('api/tournament/games/options/', TournamentGamesOptionsAPIView.as_view()),
        path('api/group_table/', GroupTableAPIView.as_view()),
        path('api/group_table/team/create/', TournamentGroupTeamListCreateAPIView.as_view()),
        path('api/group_table/team/', TournamentGroupTeamListCreateAPIView.as_view()),
        path('api/search-team-branches/', TeamBranchSearchView.as_view()),
        ####### Like Coment API ###############
        path('api/tournaments/like/', TournamentLikeAPIView.as_view()),
        path('api/tournaments/comments/', TournamentCommentAPIView.as_view()),  # New API for paginated comments
        path('api/tournaments/comments/create/', TournamentCommentCreateAPIView.as_view()),
        path('api/upcoming/games/', UpcomingGameView.as_view()),
        path('api/my_games/', FetchMyGamesAPIView.as_view()),
        path('api/all_games/', FetchAllGamesAPIView.as_view()),
        ########## Tournaments Game Stats ######################
        path('api/tournament/game_detail_stats/', TeamGameDetailStatsAPIView.as_view()),
        ############ Extra time ############\
        path('api/update_extra_time/', ExtraTimeAPIView.as_view(), name='update_extra_time'),

        #################### Crone Job For Finish All games if Day's Has been Gone ################
        path('api/if/not/complete/tournament/finish_all_games/',FinishPastGamesAPIView.as_view()),
    ]
