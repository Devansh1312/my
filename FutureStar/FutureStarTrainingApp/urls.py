from django.urls import path
from FutureStarTrainingApp.views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect

urlpatterns = [

    path('api/create_training/', CreateTrainingView.as_view()),
    path('api/open_trainings/', OpenTrainingListView.as_view()),

    path('api/training/detail/', TrainingDetailAPIView.as_view()),

    path('api/training/like/', TrainingLikeAPIView.as_view(), name='post-like'),
    path('api/training/comments/', TrainingCommentAPIView.as_view()),  # New API for paginated comments
    path('api/training/comments_create/', TrainingCommentCreateAPIView.as_view()),

    path('api/training/joined/', JoinTrainingAPIView.as_view()),

    path('api/training/feedback/',TrainingFeedbackAPI.as_view()),





    ]