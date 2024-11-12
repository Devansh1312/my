from django.db import models
from FutureStar_App.models import *
from FutureStarTeamApp.models import *
from FutureStarAPI.models import *
from FutureStarTournamentApp.models import *

from django.utils import timezone
import datetime
from django.core.exceptions import ValidationError
from datetime import datetime 
from django.utils import timezone
from datetime import timedelta
# Create your models here.


class Lineup(models.Model):
    ADDED = 1
    SUBSTITUTE = 2
    ALREADY_IN_LINEUP=3
    
    TEAMLINEUP_TYPE_CHOICES = (
        (ADDED, 'ADDED'),
        (SUBSTITUTE, 'SUBSTITUTE'),
        (ALREADY_IN_LINEUP, 'ALREADY_IN_LINEUP'),
        
    )

   
    id = models.AutoField(primary_key=True)
    
    # Foreign key relationships
    team_id = models.ForeignKey(TeamBranch, on_delete=models.CASCADE)
    player_id = models.ForeignKey(User, on_delete=models.CASCADE)
    game_id = models.ForeignKey(TournamentGames, on_delete=models.CASCADE)
    tournament_id = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    
    # Player's jersey number
    

    # Status field (1 for added, 2 for substitute)
    lineup_status = models.IntegerField(choices=TEAMLINEUP_TYPE_CHOICES,default=1)

    position_1=models.CharField(max_length=200,blank=True, null=True)
    position_2=models.CharField(max_length=200,blank=True, null=True)

    # Timestamps for creation and last update
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    # Enforcing uniqueness for the combination of player_id, game_id, tournament_id, and player_jersey_no
    class Meta:
        db_table = 'futurestar_app_lineup'
        constraints = [
            models.UniqueConstraint(fields=['player_id', 'game_id', 'tournament_id'], name='unique_lineup')
        ]


    def __str__(self):
        return f"Lineup {self.id} - {self.team_id} - {self.player_id}"


class PlayerJersey(models.Model):
    id = models.AutoField(primary_key=True)
    lineup_players=models.ForeignKey(Lineup,on_delete=models.CASCADE)
    jersey_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str__(self):
        return f"Player Jersey {self.id} - {self.lineup_players} - {self.jersey_number}"
    
    class Meta:
        db_table = 'futurestar_app_player_jersey'