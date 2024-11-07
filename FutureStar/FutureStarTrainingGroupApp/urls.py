from django.urls import path
from FutureStarTrainingGroupApp.views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect


handler404 = 'FutureStarFrontend.views.custom_404_view'

urlpatterns = [
    
        ################# Training Group URL ################
        path('api/training/group/', TrainingGroupAPI.as_view()),

    ]

handler404 = 'FutureStarFrontend.views.custom_404_view'