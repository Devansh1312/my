from rest_framework import serializers
from FutureStar_App.models import *
from urllib.parse import urlparse
from FutureStarAPI.models import *
from django.core.files.images import get_image_dimensions
from django.core.files.storage import default_storage
from django.utils.translation import gettext as _
from django.utils.crypto import get_random_string
from FutureStarFriendlyGame.models import *


class FriendlyGameSerializer(serializers.ModelSerializer):
    team_a = serializers.SerializerMethodField()
    team_b = serializers.SerializerMethodField()
    game_field_id = serializers.SerializerMethodField()

    class Meta:
        model = FriendlyGame
        fields = [
            'id', 'team_a', 'team_b', 'game_name', 'game_number', 'game_date', 'game_start_time', 
            'game_end_time', 'game_field_id', 'game_status','created_by'
        ]

    def get_team_a(self, obj):
        return {
            'id': obj.team_a.id,
            'team_name': obj.team_a.team_name,
            'team_logo': obj.team_a.team_id.team_logo.url if obj.team_a and obj.team_a.team_id.team_logo else None,
        } if obj.team_a else None

    def get_team_b(self, obj):
        return {
            'id': obj.team_b.id,
            'team_name': obj.team_b.team_name,
            'team_logo': obj.team_b.team_id.team_logo.url if obj.team_b and obj.team_b.team_id.team_logo else None,
        } if obj.team_b else None
    
    def get_game_field_id(self, obj):
        return {
                'id': obj.game_field_id.id,
                'game_field_name': obj.game_field_id.field_name,
                'location':{
                    'latitude': obj.game_field_id.latitude,
                    'longitude': obj.game_field_id.longitude,
                    'address': obj.game_field_id.address,
                    'house_no': obj.game_field_id.house_no,
                    'premises': obj.game_field_id.premises,
                    'street': obj.game_field_id.street,
                    'city': obj.game_field_id.city,
                    'state': obj.game_field_id.state,
                    'country_name': obj.game_field_id.country_name,
                    'postalCode': obj.game_field_id.postalCode,
                    'country_code': obj.game_field_id.country_code
                    }
                } if obj.game_field_id else None



class MyFriendlyGameSerializer(serializers.ModelSerializer):
    team_a_name = serializers.CharField(source='team_a.name', read_only=True)
    team_a_logo = serializers.ImageField(source='team_a.logo', read_only=True)
    team_b_name = serializers.CharField(source='team_b.name', read_only=True)
    team_b_logo = serializers.ImageField(source='team_b.logo', read_only=True)
    game_field_id_name = serializers.CharField(source='game_field_id.name', read_only=True)

    class Meta:
        model = FriendlyGame
        fields = '__all__'

class TeamBranchSearchSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = TeamBranch
        fields = ['id', 'name']

    def get_name(self, obj):
        return obj.team_name



class FriendlyGameOficialTypeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = FriendlyGameOfficialsType
        fields = ['id', 'name']  # Only include the fields you need in the response

    def get_name(self, obj):
        # Get the language from the context (set in the view)
        language = self.context.get('language', 'en')
        # Return the appropriate field based on language
        return obj.name_ar if language == 'ar' else obj.name_en
    

class FriendlyTeamUniformColorSerializer(serializers.Serializer):
    game_id = serializers.IntegerField()
    team_id = serializers.CharField()  # Can be either team_a or team_b
    primary_color_player = serializers.CharField(max_length=255, required=True)
    secondary_color_player = serializers.CharField(max_length=255, required=True)
    primary_color_goalkeeper = serializers.CharField(max_length=255, required=True)
    secondary_color_goalkeeper = serializers.CharField(max_length=255, required=True)

    def validate(self, data):
        game_id = data.get('game_id')
        team_id = data.get('team_id')
        team_id = int(team_id)
        try:
            game = FriendlyGame.objects.get(id=game_id)
        except FriendlyGame.DoesNotExist:
            raise serializers.ValidationError("Invalid game specified.")

        if team_id not in [game.team_a.id, game.team_b.id]:
            raise serializers.ValidationError("The specified team_id does not match any team in this game.")
        
        return data

# class FiendlyTournamentGamesHead2HeadSerializer(serializers.ModelSerializer):
#     team_a_logo = serializers.SerializerMethodField()
#     team_b_logo = serializers.SerializerMethodField()
#     team_a_name = serializers.SerializerMethodField()
#     team_b_name = serializers.SerializerMethodField()
#     game_field_name = serializers.SerializerMethodField()
#     type = serializers.SerializerMethodField()  # New field to indicate the game type

#     class Meta:
#         fields = [
#             'id',
#             'team_a_name',
#             'team_b_name',
#             'team_a_goal',
#             'team_b_goal',
#             'game_field_name',
#             'game_date',
#             'team_a_logo',
#             'team_b_logo',
#             'type'  # Include the game type in the output
#         ]

#     def get_team_a_logo(self, obj):
#         # Access the logo for team A
#         if obj.team_a and hasattr(obj.team_a, 'team_id') and obj.team_a.team_id.team_logo:
#             return f"/media/{obj.team_a.team_id.team_logo}"
#         return None

#     def get_team_b_logo(self, obj):
#         # Access the logo for team B
#         if obj.team_b and hasattr(obj.team_b, 'team_id') and obj.team_b.team_id.team_logo:
#             return f"/media/{obj.team_b.team_id.team_logo}"
#         return None

#     def get_team_a_name(self, obj):
#         return obj.team_a.team_name if obj.team_a else None

#     def get_team_b_name(self, obj):
#         return obj.team_b.team_name if obj.team_b else None

#     def get_game_field_name(self, obj):
#         return obj.game_field_id.field_name if obj.game_field_id else None

#     def get_type(self, obj):
#         # Determine the type based on the model
#         return "Tournament" if isinstance(obj, TournamentGames) else "Friendly"

    

class FriendlyGameSwapPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendlyGameLineup
        fields = ['id', 'team_id', 'player_id', 'game_id', 'lineup_status', 'position_1']