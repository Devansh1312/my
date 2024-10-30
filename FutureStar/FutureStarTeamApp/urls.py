from django.urls import path
from FutureStarTeamApp.views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect

urlpatterns = [

        ################# Team URL ################
        path('api/team/', TeamViewAPI.as_view()),
  
    ]