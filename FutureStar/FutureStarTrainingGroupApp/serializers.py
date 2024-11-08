import mimetypes
from rest_framework import serializers
from FutureStar_App.models import *
from FutureStarTeamApp.models import *
from FutureStarAPI.models import *
from FutureStarTournamentApp.models import *
from urllib.parse import urlparse
from FutureStarAPI.models import *
from django.core.files.images import get_image_dimensions


class TrainingGroupSerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField()  
    followers_count = serializers.SerializerMethodField()  
    following_count = serializers.SerializerMethodField() 
    is_follow = serializers.SerializerMethodField()
    group_logo = serializers.SerializerMethodField()
    group_background_image = serializers.SerializerMethodField()
    group_founder = serializers.SerializerMethodField()
    creator_type = serializers.IntegerField(default=3, read_only=True)


    class Meta:
        model = TrainingGroups
        fields = [
            'id','group_name', 'group_username', 'bio', 'group_founder',
            'latitude', 'longitude', 'address', 'house_no', 'premises', 'street',
            'city', 'state', 'country_name', 'postalCode', 'country_code',
            'phone', 'group_logo', 'group_background_image', 'post_count', 
            'post_count', 'followers_count', 
            'following_count', 'is_follow','creator_type'
        ]
    
    def get_group_founder(self, obj):
        user = obj.group_founder
        if not user:
            return None
        return {
            'username': user.username,
            'fullname': user.fullname,
            'phone': user.phone,
            'email': user.email,
            'profile_pic': user.profile_picture.url if user.profile_picture else None,
        }
    

    def get_group_logo(self, obj):
        """Get the URL of the group logo."""
        return obj.group_logo.url if obj.group_logo else None

    def get_group_background_image(self, obj):
        """Get the URL of the group background image."""
        return obj.group_background_image.url if obj.group_background_image else None
    

    def get_post_count(self, obj):
        # Assuming Post model has a ForeignKey to Team
        return Post.objects.filter(created_by_id=obj.id, creator_type=FollowRequest.GROUP_TYPE).count()


    def get_followers_count(self, obj):
        # Assuming FollowRequest model has target_id and target_type fields
        return FollowRequest.objects.filter(target_id=obj.id, target_type=FollowRequest.GROUP_TYPE).count()

    def get_following_count(self, obj):
        # Assuming FollowRequest model has created_by_id and creator_type fields
        return FollowRequest.objects.filter(created_by_id=obj.id, creator_type=FollowRequest.GROUP_TYPE).count()

    def get_is_follow(self, obj):
        request = self.context.get('request')
        creator_type = None
        created_by_id = None

        if request:
            # Check if `creator_type` and `created_by_id` are provided in `query_params`
            creator_type = request.query_params.get('creator_type')
            created_by_id = request.query_params.get('created_by_id')
            
            # If not provided, default to the authenticated user's ID and type
            if not creator_type or not created_by_id:
                creator_type = FollowRequest.USER_TYPE
                created_by_id = request.user.id if request.user.is_authenticated else None
            else:
                # Ensure `created_by_id` is an integer, if provided
                try:
                    created_by_id = int(created_by_id)
                except ValueError:
                    created_by_id = None

        # If `created_by_id` is still None, return False as follow status
        if created_by_id is None:
            return False

        # Check if the current user (or creator) is following the team
        return FollowRequest.objects.filter(
            created_by_id=created_by_id,
            creator_type=creator_type,
            target_id=obj.id,
            target_type=FollowRequest.GROUP_TYPE
        ).exists()
