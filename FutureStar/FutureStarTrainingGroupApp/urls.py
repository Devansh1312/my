from django.urls import path
from FutureStarTrainingGroupApp.views import *


urlpatterns = [
    
        ################# Training Group URL ################
        path('api/training/group/', TrainingGroupAPI.as_view()),
        path('api/member_search/', SearchMemberView.as_view()),
        path('api/members_list/', GroupMembersView.as_view()),
        path('api/member_add/', GroupMembersAddView.as_view()),
        path('api/member_delete/', GroupMembersAddView.as_view()),
    ]
