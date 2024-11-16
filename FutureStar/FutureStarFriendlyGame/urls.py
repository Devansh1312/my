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

       path('api/friendly-game/branch_list/', TeamBranchListView.as_view())
       
    ]