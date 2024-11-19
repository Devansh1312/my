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
    referee = serializers.SerializerMethodField()
    assistant_refree_1st = serializers.SerializerMethodField()
    assistant_refree_2nd = serializers.SerializerMethodField()
    refree_4th = serializers.SerializerMethodField()
    game_field_id = serializers.SerializerMethodField()

    class Meta:
        model = FriendlyGame
        fields = [
            'id', 'team_a', 'team_b', 'game_name', 'game_number', 'game_date', 'game_start_time', 
            'game_end_time', 'game_field_id','referee', 'assistant_refree_1st', 'assistant_refree_2nd', 
            'refree_4th', 'game_status', 'created_at', 'updated_at'
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

    def get_referee(self, obj):
        return self._get_user_data(obj.referee)

    def get_assistant_refree_1st(self, obj):
        return self._get_user_data(obj.assistant_refree_1st)

    def get_assistant_refree_2nd(self, obj):
        return self._get_user_data(obj.assistant_refree_2nd)

    def get_refree_4th(self, obj):
        return self._get_user_data(obj.refree_4th)

    def _get_user_data(self, user):
        return {
            'id': user.id,
            'username': user.username,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
        } if user else None



class TeamBranchSearchSerializer(serializers.ModelSerializer):
    age_group_id = serializers.SerializerMethodField()
    main_team_name = serializers.CharField(source='team_id.team_name', read_only=True)  # Fetch `team_name` from related `Team`

    class Meta:
        model = TeamBranch
        fields = ['id', 'team_name', 'main_team_name', 'age_group_id']

    def get_age_group_id(self, obj):
        request = self.context.get('request')
        language = request.headers.get('Language', 'en') if request else 'en'
        
        if obj.age_group_id:
            return obj.age_group_id.name if language == 'ar' else obj.age_group_id.name_en



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