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
            'tournament_name',
            'tournament_starting_date',
            'tournament_final_date',
            'number_of_team',
            'age_group',
            'country',
            'country_name',
            'city',
            'city_name',
            'tournament_fields',
            'tournament_fields_name',
            'logo',
            'tournament_joining_cost',
            'number_of_group',  # Add number_of_group to create groups based on selection
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

