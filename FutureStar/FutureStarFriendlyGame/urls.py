from django.urls import path
from FutureStarFriendlyGame.views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect

urlpatterns = [

       path('api/friendly-game/create/', CreateFriendlyGame.as_view()),
       path('api/friendly-game/update/', UpdateFriendlyGame.as_view()),
       path('api/friendly-game/list/', ManagerBranchDetail.as_view()),
       path('api/friendly-game/delete/', DeleteFriendlyGame.as_view()),
       
    ]