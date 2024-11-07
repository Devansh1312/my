from django.db import models
from FutureStar_App.models import *
from FutureStarTeamApp.models import *
from FutureStarAPI.models import *

from django.utils import timezone
import datetime
from django.core.exceptions import ValidationError
from datetime import datetime 
from django.utils import timezone
from datetime import timedelta



class Tournament(models.Model):

    team_id = models.ForeignKey(Team,null=True, blank=True, on_delete=models.CASCADE)
    tournament_name = models.CharField(max_length=255,blank=True,null=True)
    tournament_starting_date = models.DateField(blank=True,null=True)
    tournament_final_date = models.DateField(blank=True,null=True)
    number_of_team = models.CharField(max_length=255,blank=True,null=True)
    number_of_group=models.IntegerField(default=1)
    age_group = models.ForeignKey(AgeGroup,on_delete=models.CASCADE,blank=True,null=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.CASCADE)
    tournament_fields = models.ForeignKey(Field,blank=True,null=True,on_delete=models.CASCADE)
    logo = models.ImageField(upload_to='tournament_logo/', blank=True, null=True)  # Add image field
    tournament_joining_cost = models.CharField(max_length=255,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return self.tournament_name

    class Meta:
        db_table = 'futurestar_app_tournament'

class GroupTable(models.Model):
    id = models.AutoField(primary_key=True)
    tournament_id = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    group_name = models.CharField(max_length=255,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return self.group_name

    class Meta:
        db_table = 'futurestar_app_grouptable'

class TournamentGroupTeam(models.Model):
    id = models.AutoField(primary_key=True)
    group_id = models.ForeignKey(GroupTable, on_delete=models.CASCADE)
    team_branch_id = models.ForeignKey(TeamBranch, on_delete=models.CASCADE,blank=True, null=True)
    tournament_id=models.ForeignKey(Tournament,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str__(self):
        return f'{self.group_id} - {self.team_branch_id}'
    
    class Meta:
        db_table = 'futurestar_app_tournament_groupteam'