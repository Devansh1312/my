from django.urls import path
from FutureStarTrainingApp.views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect

urlpatterns = [

    path('api/create_training/', CreateTrainingView.as_view()),
    path('api/open_trainings/', OpenTrainingListView.as_view()),


    ]