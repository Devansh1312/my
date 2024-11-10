import mimetypes
from rest_framework import serializers
from FutureStar_App.models import *
from FutureStarTeamApp.models import *
from FutureStarAPI.models import *
from FutureStarTournamentApp.models import *
from urllib.parse import urlparse
from FutureStarAPI.models import *
from django.core.files.images import get_image_dimensions




class TournamentSerializer(serializers.ModelSerializer):
    city_name = serializers.SerializerMethodField()  # To show city name
    country_name = serializers.SerializerMethodField()  # To show country name
    tournament_fields_name = serializers.SerializerMethodField()  # To show field name

    class Meta:
        model = Tournament
        fields = [
            'id',
            'tournament_name',
            'tournament_starting_date',
            'tournament_final_date',
            'number_of_team',
            'number_of_group',
            'age_group',
            'country',
            'country_name',
            'city',
            'city_name',
            'tournament_fields',
            'tournament_fields_name',
            'logo',
            'tournament_banner',
            'tournament_joining_cost',
            
        ]

    def get_country_name(self, obj):
        return obj.country.name if obj.country else None  # Return country name or None

    def get_city_name(self, obj):
        return obj.city.name if obj.city else None  # Return city name or None
    
    def get_tournament_fields_name(self, obj):
        return obj.tournament_fields.field_name if obj.tournament_fields else None  # Return field name or None

    def create(self, validated_data):
        # Automatically associate the tournament with the currently logged-in user
    
        number_of_group = validated_data.pop('number_of_group', 1)  # Get number of groups, default to 1

        # Dynamically create group names based on the number of groups
        if number_of_group < 1:
            raise serializers.ValidationError("Number of groups must be at least 1.")

        # Generate group names dynamically like 'Group-A', 'Group-B', 'Group-C', ...
        group_names = [f"Group-{chr(65 + i)}" for i in range(number_of_group)]

        # Create the tournament instance
        tournament = Tournament.objects.create(number_of_group=number_of_group, **validated_data)

        # Create corresponding groups in GroupTable
        for group_name in group_names:
            GroupTable.objects.create(tournament_id=tournament, group_name=group_name)

        return tournament



class GroupTableSerializer(serializers.ModelSerializer):
    tournament_id_name = serializers.SerializerMethodField() 
    class Meta:
        model = GroupTable
        fields = ['id','tournament_id','tournament_id_name','group_name','created_at','updated_at']

    def get_tournament_id_name(self, obj):
        return obj.tournament_id.tournament_name if obj.tournament_id else None

class TournamentGroupTeamSerializer(serializers.ModelSerializer):
    group_id_name = serializers.SerializerMethodField()
    team_branch_name = serializers.SerializerMethodField()
    tournament_id_name = serializers.SerializerMethodField()
    team_branch_logo= serializers.SerializerMethodField()
    
    class Meta:
        model = TournamentGroupTeam
        fields = ['id','group_id','group_id_name','team_branch_id','team_branch_name','team_branch_logo','tournament_id','tournament_id_name','status','created_at','updated_at']

    def get_group_id_name(self, obj):
        return obj.group_id.group_name if obj.group_id else None
    
    def get_team_branch_name(self, obj):
        return obj.team_branch_id.team_name if obj.team_branch_id else None
    
    def get_tournament_id_name(self, obj):
        return obj.tournament_id.tournament_name if obj.tournament_id else None
    
    def get_team_branch_logo(self, obj):
        if obj.team_branch_id and obj.team_branch_id.team_id and obj.team_branch_id.team_id.team_logo:
             return obj.team_branch_id.team_id.team_logo.url
        return None
    

class TournamentGamesSerializer(serializers.ModelSerializer):
    group_id_name = serializers.SerializerMethodField()
    game_field_id_name = serializers.SerializerMethodField()
    team_a_details = serializers.SerializerMethodField()
    team_b_details = serializers.SerializerMethodField()

    class Meta:
        model = TournamentGames
        fields = [
            'id', 'game_number', 'game_date', 'game_start_time', 'game_end_time',
            'group_id', 'group_id_name', 'team_a', 'team_a_details', 'team_b', 
            'team_b_details', 'game_field_id', 'game_field_id_name', 'created_at', 'updated_at'
        ]

    def get_group_id_name(self, obj):
        return obj.group_id.group_name if obj.group_id else None

    def get_game_field_id_name(self, obj):
        return obj.game_field_id.field_name if obj.game_field_id else None

    def get_team_a_details(self, obj):
        return self._get_team_details(obj, obj.team_a)

    def get_team_b_details(self, obj):
        return self._get_team_details(obj, obj.team_b)

    def _get_team_details(self, obj, team_name):
        try:
            team_entry = TournamentGroupTeam.objects.filter(
                group_id=obj.group_id,
                team_branch_id__team_name=team_name,
                status=TournamentGroupTeam.ACCEPTED
            ).select_related('team_branch_id').first()
            
            if team_entry and team_entry.team_branch_id:
                return {
                    'name': team_entry.team_branch_id.team_name,
                    'logo': team_entry.team_branch_id.team_logo.url if team_entry.team_branch_id.team_logo else None
                }
        except TournamentGroupTeam.DoesNotExist:
            return None
