from django.db import models
from FutureStar_App.models import *
from FutureStarAPI.models import *

from django.utils import timezone
import datetime
from django.core.exceptions import ValidationError
from datetime import datetime 
from django.utils import timezone
from datetime import timedelta


class JoinTrainingGroup(models.Model):
    MEMBER = 1
    ORGANIZER = 2

    # Define choices as a list of tuples
    ROLE_CHOICES = [
        (MEMBER, 'Member'),
        (ORGANIZER, 'Organizer')
    ]

    member_id = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    JoinTrainingGroup_type = models.IntegerField(choices=ROLE_CHOICES, default=MEMBER)
    group_id = models.ForeignKey(TrainingGroups, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str__(self):
        return f'{self.group_id} - {self.member_id}'
    
    class Meta:
        db_table = 'futurestar_app_traininggroup_join'
        unique_together = ('group_id', 'member_id')  # Ensure user can join a group only once