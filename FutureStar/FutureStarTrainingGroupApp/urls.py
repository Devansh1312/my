from django.urls import path
from FutureStarTrainingGroupApp.views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect


handler404 = 'FutureStarFrontend.views.custom_404_view'

urlpatterns = [
    
        ################# Training Group URL ################
        path('api/training/group/', TrainingGroupAPI.as_view()),
        path('api/member_search/', SearchMemberView.as_view()),
        path('api/members_list/', GroupMembersView.as_view()),
        path('api/member_add/', GroupMembersAddView.as_view()),
        path('api/member_delete/', GroupMembersAddView.as_view()),
    ]

handler404 = 'FutureStarFrontend.views.custom_404_view'