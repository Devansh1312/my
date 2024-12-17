from django.db import models
from FutureStar_App.models import *
from FutureStarAPI.models import *

# Create your models here.
class JoinBranch(models.Model):
    MANAGERIAL_STAFF_TYPE = 1
    COACH_STAFF_TYPE = 2
    MEDICAL_STAFF_TYPE = 3
    PLAYER_TYPE = 4

    JOINNING_TYPE_CHOICES = (
        (MANAGERIAL_STAFF_TYPE, 'Managerial Staff'),
        (COACH_STAFF_TYPE, 'Coach Staff'),
        (MEDICAL_STAFF_TYPE, 'Medical Staff'),
        (PLAYER_TYPE, 'Player'),
    )

    id = models.AutoField(primary_key=True)
    branch_id = models.ForeignKey(TeamBranch, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    joinning_type = models.IntegerField(choices=JOINNING_TYPE_CHOICES, default=PLAYER_TYPE)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return f"{self.user_id} - {self.branch_id}"

    class Meta:
        db_table = 'futurestar_app_team_join_branch'
        unique_together = ('branch_id', 'user_id')  # Ensure user can join a branch only once
