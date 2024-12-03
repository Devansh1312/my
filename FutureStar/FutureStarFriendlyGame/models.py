from django.db import models
from FutureStar_App.models import *
from FutureStarAPI.models import *
from FutureStarTournamentApp.models import *
from FutureStarTeamApp.models import *




# Create your models here.
class FriendlyGame(models.Model):
    team_a = models.ForeignKey(TeamBranch, related_name="team_a" ,on_delete=models.CASCADE,null=True, blank=True)
    team_b = models.ForeignKey(TeamBranch, related_name="team_b",on_delete=models.CASCADE,null=True, blank=True)
    game_statistics_handler=models.ForeignKey(User,on_delete=models.CASCADE,blank=True, null=True)
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
    
    team_a_goal = models.IntegerField(blank=True, null=True)
    team_b_goal = models.IntegerField(blank=True, null=True)
   
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

    #GAME_STATS
    #General
    general_team_a_possession=models.FloatField(blank=True, null=True,default=0.0)
    general_team_a_interception=models.IntegerField(blank=True, null=True,default=0)
    general_team_a_offside=models.IntegerField(blank=True, null=True,default=0)
    general_team_a_corner=models.IntegerField(blank=True, null=True,default=0)

    general_team_b_possession=models.FloatField(blank=True, null=True,default=0.0)
    general_team_b_interception=models.IntegerField(blank=True, null=True,default=0)
    general_team_b_offside=models.IntegerField(blank=True, null=True,default=0)
    general_team_b_corner=models.IntegerField(blank=True, null=True,default=0)

    #defence
    defence_team_a_possession=models.FloatField(blank=True, null=True,default=0.0)
    defence_team_a_interception=models.IntegerField(blank=True, null=True,default=0)
    defence_team_a_offside=models.IntegerField(blank=True, null=True,default=0)
    defence_team_a_corner=models.IntegerField(blank=True, null=True,default=0)

    defence_team_b_possession=models.FloatField(blank=True, null=True,default=0.0)
    defence_team_b_interception=models.IntegerField(blank=True, null=True,default=0)
    defence_team_b_offside=models.IntegerField(blank=True, null=True,default=0)
    defence_team_b_corner=models.IntegerField(blank=True, null=True,default=0)

    #distribution
    distribution_team_a_possession=models.FloatField(blank=True, null=True,default=0.0)
    distribution_team_a_interception=models.IntegerField(blank=True, null=True,default=0)
    distribution_team_a_offside=models.IntegerField(blank=True, null=True,default=0)
    distribution_team_a_corner=models.IntegerField(blank=True, null=True,default=0)

    distribution_team_b_possession=models.FloatField(blank=True, null=True,default=0.0)
    distribution_team_b_interception=models.IntegerField(blank=True, null=True,default=0)
    distribution_team_b_offside=models.IntegerField(blank=True, null=True,default=0)
    distribution_team_b_corner=models.IntegerField(blank=True, null=True,default=0)

    #attack
    attack_team_a_possession=models.FloatField(blank=True, null=True,default=0.0)
    attack_team_a_interception=models.IntegerField(blank=True, null=True,default=0)
    attack_team_a_offside=models.IntegerField(blank=True, null=True,default=0)
    attack_team_a_corner=models.IntegerField(blank=True, null=True,default=0)

    attack_team_b_possession=models.FloatField(blank=True, null=True,default=0.0)
    attack_team_b_interception=models.IntegerField(blank=True, null=True,default=0)
    attack_team_b_offside=models.IntegerField(blank=True, null=True,default=0)
    attack_team_b_corner=models.IntegerField(blank=True, null=True,default=0)

    #discipline
    discipline_team_a_possession=models.FloatField(blank=True, null=True,default=0.0)
    discipline_team_a_interception=models.IntegerField(blank=True, null=True,default=0)
    discipline_team_a_offside=models.IntegerField(blank=True, null=True,default=0)
    discipline_team_a_corner=models.IntegerField(blank=True, null=True,default=0)

    discipline_team_b_possession=models.FloatField(blank=True, null=True,default=0.0)
    discipline_team_b_interception=models.IntegerField(blank=True, null=True,default=0)
    discipline_team_b_offside=models.IntegerField(blank=True, null=True,default=0)
    discipline_team_b_corner=models.IntegerField(blank=True, null=True,default=0)

    created_by = models.ForeignKey(User, related_name="created_by", on_delete=models.CASCADE,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str__(self):
        return f'{self.game_name} - {self.game_number} - {self.game_date} - {self.game_start_time} - {self.game_end_time} - {self.game_field_id}'
    
    class Meta:
        db_table = 'futurestar_app_friendly_games'
        unique_together = ('game_name', 'game_number', 'game_date', 'game_start_time', 'game_end_time', 'game_field_id')  # Ensure user can join a group only once
        



class FriendlyGameLineup(models.Model):
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
    game_id = models.ForeignKey(FriendlyGame, on_delete=models.CASCADE)
    # tournament_id = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    
    # Player's jersey number
    

    # Status field (1 for added, 2 for substitute)
    lineup_status = models.IntegerField(choices=TEAMLINEUP_TYPE_CHOICES,default=0)

    position_1=models.CharField(max_length=200,blank=True, null=True)
    player_ready = models.BooleanField(default=False)

    # Timestamps for creation and last update
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    created_by_id = models.IntegerField(null=True, blank=True)

    # Enforcing uniqueness for the combination of player_id, game_id, tournament_id, and player_jersey_no
    class Meta:
        db_table = 'futurestar_app_friendlygames_lineup'
        constraints = [
            models.UniqueConstraint(fields=['player_id', 'game_id'], name='unique_friendlygame_lineup')
        ]


    def __str__(self):
        return f"Lineup {self.id} - {self.team_id} - {self.player_id}"


class FriendlyGamePlayerJersey(models.Model):
    id = models.AutoField(primary_key=True)
    lineup_players = models.ForeignKey(FriendlyGameLineup, on_delete=models.CASCADE)
    jersey_number = models.IntegerField()
    created_by_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        db_table = 'futurestar_app_friendlygame_player_jersey'
       

    def __str__(self):
        return f"Player Jersey {self.id} - {self.lineup_players} - {self.jersey_number}"

class FriendlyGameOfficialsType(models.Model):
    id=models.AutoField(primary_key=True)
    name_en=models.CharField(max_length=200,blank=True, null=True)
    name_ar=models.CharField(max_length=200,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str__(self):
        return f"Officials Type {self.id} - {self.name_en} - {self.name_ar}"
    
    class Meta:
        db_table = 'futurestar_app_friendlygame_officials_type'
        constraints = [
            models.UniqueConstraint(fields=['name_en', 'name_ar'], name='unique_friendlygame_officials_type')
        ]


class FriendlyGameGameOfficials(models.Model):
    id=models.AutoField(primary_key=True)
    officials_type_id=models.ForeignKey(FriendlyGameOfficialsType,on_delete=models.CASCADE)
    game_id=models.ForeignKey(FriendlyGame,on_delete=models.CASCADE)
    official_id=models.ForeignKey(User,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str__(self):
        return f"Game Officials {self.id} - {self.officials_type_id} - {self.official_id}"
    
    class Meta:
        db_table = 'futurestar_app_friendlygame_officials'
        constraints = [
            models.UniqueConstraint(fields=['game_id', 'official_id'], name='unique_friendlygame_officials')
        ]
        

class FriendlyGamesPlayerGameStats(models.Model):
    id=models.AutoField(primary_key=True)
    team_id = models.ForeignKey(TeamBranch, on_delete=models.CASCADE)
    player_id = models.ForeignKey(User,null=True,blank=True, on_delete=models.CASCADE)
    game_id = models.ForeignKey(FriendlyGame, on_delete=models.CASCADE)
    # tournament_id = models.ForeignKey(Tournament, on_delete=models.CASCADE)

    goals=models.IntegerField(default=0)
    assists=models.IntegerField(default=0)
    own_goals=models.IntegerField(default=0)
    yellow_cards=models.IntegerField(default=0)
    red_cards=models.IntegerField(default=0)
    game_time=models.TimeField(blank=True, null=True)
   # New fields for substitution
    in_player = models.ForeignKey(User, related_name="in_friendlygame_player_subs", null=True, blank=True, on_delete=models.SET_NULL)
    out_player = models.ForeignKey(User, related_name="out_friendlygame_player_subs", null=True, blank=True, on_delete=models.SET_NULL)

    created_by_id=models.IntegerField(blank=True, null=True)
    
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str__(self):
        return f"Player Game Stats {self.id} - {self.team_id} - {self.player_id}"
    
    class Meta:
        db_table = 'futurestar_app_player_friendlygame_stats'