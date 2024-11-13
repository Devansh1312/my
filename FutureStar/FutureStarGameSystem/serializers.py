from rest_framework import serializers
from FutureStar_App.models import *
from FutureStarTeamApp.models import *
from FutureStarAPI.models import *
from FutureStarTournamentApp.models import *
from urllib.parse import urlparse
from FutureStarAPI.models import *
from django.core.files.images import get_image_dimensions
from FutureStarGameSystem.models import *


class LineUpSerializer(serializers.ModelSerializer):
    player_name = serializers.SerializerMethodField() # Assuming `username` is the field in User
    team_name = serializers.SerializerMethodField() # Assuming `team_name` is the field in Team

    player_profile_picture= serializers.SerializerMethodField()
    player_playing_position = serializers.SerializerMethodField()

    class Meta:
        model = Lineup
        fields = ['id', 'team_id','team_name', 'player_id', 'player_name','player_profile_picture','player_playing_position','game_id','tournament_id', 'created_at', 'updated_at']


    def get_player_name(self, obj):
   
        return obj.player_id.username if obj.player_id else None
    
    def get_player_profile_picture(self, obj):
        return obj.player_id.profile_picture.url if obj.player_id and obj.player_id.profile_picture else None

    
    def get_player_playing_position(self, obj):
   
        return obj.player_id.main_playing_position if obj.player_id else None
    
    def get_team_name(self, obj):
   
        return obj.team_id.branch_id.team_name if obj.team_id else None


class GameOficialTypeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = OfficialsType
        fields = ['id', 'name']  # Only include the fields you need in the response

    def get_name(self, obj):
        # Get the language from the context (set in the view)
        language = self.context.get('language', 'en')
        # Return the appropriate field based on language
        return obj.name_ar if language == 'ar' else obj.name_en