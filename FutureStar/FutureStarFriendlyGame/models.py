from django.db import models
from FutureStar_App.models import *
from FutureStarAPI.models import *
from FutureStarTournamentApp.models import *
from FutureStarTeamApp.models import *




# Create your models here.
class FriendlyGame(models.Model):
    team_a = models.ForeignKey(TeamBranch, related_name="team_a" ,on_delete=models.CASCADE,null=True, blank=True)
    team_b = models.ForeignKey(TeamBranch, related_name="team_b",on_delete=models.CASCADE,null=True, blank=True)
    game_name = models.CharField(max_length=255, null=True, blank=True)
    game_number = models.IntegerField(default=0)
    game_date = models.DateField(blank=True, null=True)
    game_start_time = models.TimeField(blank=True, null=True)
    game_end_time = models.TimeField(blank=True, null=True)
    game_field_id = models.ForeignKey(Field, on_delete=models.CASCADE)
    referee = models.ForeignKey(User,related_name="referee", null=True,blank=True, on_delete=models.CASCADE)
    assistant_refree_1st = models.ForeignKey(User,related_name="assistant_refree_1st", null=True,blank=True, on_delete=models.CASCADE)
    assistant_refree_2nd = models.ForeignKey(User,related_name="assistant_refree_2nd", null=True,blank=True, on_delete=models.CASCADE)
    refree_4th = models.ForeignKey(User,related_name="refree_4th", null=True,blank=True, on_delete=models.CASCADE)
    game_status = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str__(self):
        return f'{self.game_name} - {self.game_number} - {self.game_date} - {self.game_start_time} - {self.game_end_time} - {self.game_field_id}'
    
    class Meta:
        db_table = 'futurestar_app_friendly_games'
        unique_together = ('game_name', 'game_number', 'game_date', 'game_start_time', 'game_end_time', 'game_field_id')  # Ensure user can join a group only once
        
