import mimetypes
from rest_framework import serializers
from FutureStar_App.models import *
from FutureStarAPI.models import *
from FutureStarTeamApp.models import *
from urllib.parse import urlparse
from FutureStarAPI.models import *
from django.core.files.images import get_image_dimensions




class TeamSerializer(serializers.ModelSerializer):
    # Custom fields
    team_type_name = serializers.SerializerMethodField()
    country_id_name = serializers.CharField(source='country_id.name', allow_null=True)  # Assuming 'country_id' is a ForeignKey
    city_id_name = serializers.CharField(source='city_id.name', allow_null=True)  # Assuming 'city_id' is a ForeignKey
    post_count = serializers.SerializerMethodField()  # Adding the post count field
    followers_count = serializers.SerializerMethodField()  # Adding the followers count field
    following_count = serializers.SerializerMethodField()  # Adding the following count field
    is_follow = serializers.SerializerMethodField()  # Adding the is_follow field
    creator_type = serializers.IntegerField(default=2, read_only=True)  # Static field with value 2
    # New fields for team president
    team_president_id = serializers.SerializerMethodField()
    team_president_username = serializers.SerializerMethodField()
    team_president_profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            'id', 'user_id', 'team_name', 'team_username', 'team_type', 'team_type_name', 'bio', 'team_establishment_date', 
            'team_president_id', 'team_president_username', 'team_president_profile_picture', 'latitude', 'longitude', 'address', 
            'house_no', 'premises', 'street', 'city', 'state', 'country_name', 'postalCode', 'country_code', 'country_id', 
            'country_id_name', 'city_id', 'city_id_name', 'phone', 'email', 'age_group', 'entry_fees', 'team_logo', 
            'team_background_image', 'team_uniform', 'post_count', 'followers_count', 'following_count', 'is_follow', 'creator_type'
        ]

    def get_post_count(self, obj):
        # Assuming Post model has a ForeignKey to Team
        return Post.objects.filter(created_by_id=obj.id, creator_type=FollowRequest.TEAM_TYPE).count()

    def get_team_type_name(self, obj):
        request = self.context.get('request')
        language = request.headers.get('Language', 'en') if request else 'en'
        return obj.team_type.name_ar if language == 'ar' else obj.team_type.name_en

    def get_team_logo(self, obj):
        return obj.team_logo.url if obj.team_logo else None

    def get_team_background_image(self, obj):
        # Return the relative path for the team background image
        return obj.team_background_image.url if obj.team_background_image else None

    def get_followers_count(self, obj):
        # Assuming FollowRequest model has target_id and target_type fields
        return FollowRequest.objects.filter(target_id=obj.id, target_type=FollowRequest.TEAM_TYPE).count()

    def get_following_count(self, obj):
        # Assuming FollowRequest model has created_by_id and creator_type fields
        return FollowRequest.objects.filter(created_by_id=obj.id, creator_type=FollowRequest.TEAM_TYPE).count()

    def get_is_follow(self, obj):
        request = self.context.get('request')

        # Attempt to get creator_type and created_by_id from query_params if request data is not available
        if request:
            creator_type = request.data.get('creator_type') or request.query_params.get('creator_type')
            created_by_id = request.data.get('created_by_id') or request.query_params.get('created_by_id')
            print(creator_type)
            print(created_by_id)

        else:
            creator_type = None
            created_by_id = None

        # Validate and set defaults for creator_type and created_by_id
        if creator_type and created_by_id and created_by_id not in [0, '', None]:
            created_by_id = int(created_by_id)
        else:
            # Default to the request user ID and user type
            created_by_id = request.user.id if request else None
            creator_type = FollowRequest.USER_TYPE if request else None  # Assuming USER_TYPE is the default user type

        # Check if the current user (or creator) is following the team
        return FollowRequest.objects.filter(
            created_by_id=created_by_id,
            creator_type=creator_type,
            target_id=obj.id,
            target_type=FollowRequest.TEAM_TYPE
        ).exists()
    
    # Custom methods to get the team president details
    def get_team_president_id(self, obj):
        return obj.team_president.id if obj.team_president else None

    def get_team_president_username(self, obj):
        return obj.team_president.username if obj.team_president else None

    def get_team_president_profile_picture(self, obj):
        return obj.team_president.profile_picture.url if obj.team_president and obj.team_president.profile_picture else None
