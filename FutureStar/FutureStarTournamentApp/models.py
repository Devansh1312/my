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

# from FutureStarGameSystem.models import *



class Tournament(models.Model):

    team_id = models.ForeignKey(TeamBranch,null=True, blank=True, on_delete=models.CASCADE)
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
    tournament_banner = models.ImageField(upload_to='tournament_logo/', blank=True, null=True)  # Add image field

    tournament_joining_cost = models.CharField(max_length=255,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return self.tournament_name

    class Meta:
        db_table = 'futurestar_app_tournament'





class Tournament_comment(models.Model):
    USER_TYPE = 1
    TEAM_TYPE = 2
    GROUP_TYPE = 3
    
    CREATOR_TYPE_CHOICES = (
        (USER_TYPE, 'User'),
        (TEAM_TYPE, 'Team'),
        (GROUP_TYPE, 'Group'),
    )

    created_by_id = models.IntegerField(default=0)  # Stores ID of User, Team, or Group
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES,default=1)  # Stores 1, 2, or 3 based on the type
    tournament = models.ForeignKey(Tournament, related_name='comments', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', related_name='replies', null=True, blank=True, on_delete=models.CASCADE)
    comment = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return f'Comment by ID {self.created_by_id} on {self.tournament.title}'

    class Meta:
        db_table = 'futurestar_app_tournament_comment'


# models.py

class TournamentView(models.Model):
    USER_TYPE = 1
    TEAM_TYPE = 2
    GROUP_TYPE = 3
    
    CREATOR_TYPE_CHOICES = (
        (USER_TYPE, 'User'),
        (TEAM_TYPE, 'Team'),
        (GROUP_TYPE, 'Group'),
    )

    created_by_id = models.IntegerField(default=0)  # Stores ID of User, Team, or Group
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES,default=1)  # 1, 2, or 3 based on the type
    tournament = models.ForeignKey(Tournament, related_name='views', on_delete=models.CASCADE)
    date_viewed = models.DateTimeField(default=datetime.now)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    class Meta:
        db_table = 'futurestar_app_tournament_view'
        unique_together = ('created_by_id','creator_type','tournament')  # Ensure one view per user/team/group per tournament

class TournamentLike(models.Model):
    USER_TYPE = 1
    TEAM_TYPE = 2
    GROUP_TYPE = 3
    
    CREATOR_TYPE_CHOICES = (
        (USER_TYPE, 'User'),
        (TEAM_TYPE, 'Team'),
        (GROUP_TYPE, 'Group'),
    )

    created_by_id = models.IntegerField(default=0)  # Stores ID of User, Team, or Group
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES,default=1)  # 1, 2, or 3 based on the type
    tournament = models.ForeignKey(Tournament, related_name='likes', on_delete=models.CASCADE)
    date_liked = models.DateTimeField(default=datetime.now)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    class Meta:
        db_table = 'futurestar_app_tournament_like'
        unique_together = ('created_by_id','creator_type','tournament')  # Ensure one like per user/team/group per tournament





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
    REQUESTED=0
    ACCEPTED=1
    REJECTED=2
    JOINNING_TYPE_CHOICES = (
        (REQUESTED, 'REQUESTED'),
        (ACCEPTED, 'ACCEPTED'),
        (REJECTED, 'REJECTED'),   
    )
    id = models.AutoField(primary_key=True)
    group_id = models.ForeignKey(GroupTable, on_delete=models.CASCADE,blank=True, null=True)
    team_branch_id = models.ForeignKey(TeamBranch, on_delete=models.CASCADE,blank=True, null=True)
    tournament_id=models.ForeignKey(Tournament,on_delete=models.CASCADE,blank=True, null=True)
    status = models.IntegerField(choices=JOINNING_TYPE_CHOICES,default=0)  
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str__(self):
        return f'{self.group_id} - {self.team_branch_id}'
    
    class Meta:
        db_table = 'futurestar_app_tournament_groupteam'


class TournamentGames(models.Model):
    id = models.AutoField(primary_key=True)
    tournament_id = models.ForeignKey(Tournament, on_delete=models.CASCADE, blank=True, null=True)
    game_number = models.IntegerField(blank=True, null=True)
    game_statistics_handler=models.ForeignKey(User,on_delete=models.CASCADE,blank=True, null=True)
    game_date = models.DateField(blank=True, null=True)
    game_start_time = models.TimeField(blank=True, null=True)
    game_end_time = models.TimeField(blank=True, null=True)
    group_id = models.ForeignKey(GroupTable, on_delete=models.CASCADE, blank=True, null=True)
    team_a = models.CharField(max_length=100, blank=True, null=True)
    team_a_goal = models.IntegerField(blank=True, null=True)
    team_b = models.CharField(max_length=100, blank=True, null=True)
    team_b_goal = models.IntegerField(blank=True, null=True)
    game_field_id = models.ForeignKey(Field, on_delete=models.CASCADE, blank=True, null=True)
    finish = models.BooleanField(default=False)  # New field to indicate if the game is finished
    winner_id = models.CharField(max_length=100, blank=True, null=True)  # ID of the winning team
    loser_id = models.CharField(max_length=100, blank=True, null=True)   # ID of the losing team
    is_draw = models.BooleanField(default=False)  # True if the game is a draw

    team_a_primary_color_player = models.CharField(max_length=255,null=True,blank=True)
    team_a_secondary_color_player = models.CharField(max_length=255,null=True,blank=True)
    team_a_primary_color_goalkeeper = models.CharField(max_length=255,null=True,blank=True)
    team_a_secondary_color_goalkeeper = models.CharField(max_length=255,null=True,blank=True)
    team_b_primary_color_player = models.CharField(max_length=255,null=True,blank=True)
    team_b_secondary_color_player = models.CharField(max_length=255,null=True,blank=True)
    team_b_primary_color_goalkeeper = models.CharField(max_length=255,null=True,blank=True)
    team_b_secondary_color_goalkeeper = models.CharField(max_length=255,null=True,blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

   
    def __str__(self):
        return f'{self.game_number} - {self.game_date} - {self.group_id}'
    
    class Meta:
        db_table = 'futurestar_app_tournament_games'
