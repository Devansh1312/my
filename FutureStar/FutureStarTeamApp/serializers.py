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
    team_founder_id = serializers.SerializerMethodField()
    team_founder_username = serializers.SerializerMethodField()
    team_founder_profile_picture = serializers.SerializerMethodField()
    branches = serializers.SerializerMethodField()  # This will call our custom method for branches
    team_logo = serializers.SerializerMethodField()
    team_background_image = serializers.SerializerMethodField()
    uniforms = serializers.SerializerMethodField()


    class Meta:
        model = Team
        fields = [
            'id', 'team_name', 'team_username', 'team_type', 'team_type_name', 'bio', 'team_establishment_date', 
            'team_founder_id', 'team_founder_username', 'team_founder_profile_picture','team_president', 'latitude', 'longitude', 'address', 
            'house_no', 'premises', 'street', 'city', 'state', 'country_name', 'postalCode', 'country_code', 'country_id', 
            'country_id_name', 'city_id', 'city_id_name', 'phone', 'email','team_logo', 
            'team_background_image', 'uniforms', 'post_count', 'followers_count', 'following_count', 'is_follow', 'creator_type','branches'
        ]

    def get_uniforms(self, obj):
        # Fetch all uniforms related to the team
        uniforms = TeamUniform.objects.filter(team_id=obj)
        
        # Return a list of dictionaries containing the id and image URL
        return [
            {"id": uniform.id, "image": uniform.team_uniform_image.url} 
            for uniform in uniforms if uniform.team_uniform_image
        ]
    
    def get_branches(self, obj):
        request = self.context.get('request')
        language = request.headers.get('Language', 'en') if request else 'en'
        
        # Fetch branches related to the team
        branches = TeamBranch.objects.filter(team_id=obj.id)

        # Format branch information as a list of dictionaries with language-based age group name
        branch_data = [
            {
                'id': branch.id,
                'team_name': branch.team_name,
                'age_group': branch.age_group_id.name_ar if language == 'ar' else branch.age_group_id.name_en if branch.age_group_id else None,
                'gender': branch.gender.id if branch.gender else None,
                'gender_name': branch.gender.name_ar if language == 'ar' else branch.gender.name_en if branch.gender else None,
            }
            for branch in branches
        ]

        return branch_data
    
    def get_team_logo(self, obj):
        # Return only the relative URL for the team logo if it exists
        return obj.team_logo.url if obj.team_logo else None

    def get_team_background_image(self, obj):
        # Return only the relative URL for the team background image if it exists
        return obj.team_background_image.url if obj.team_background_image else None

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
    def get_team_founder_id(self, obj):
        return obj.team_founder.id if obj.team_founder else None

    def get_team_founder_username(self, obj):
        return obj.team_founder.username if obj.team_founder else None

    def get_team_founder_profile_picture(self, obj):
        return obj.team_founder.profile_picture.url if obj.team_founder and obj.team_founder.profile_picture else None



    
class TeamBranchSerializer(serializers.ModelSerializer):
    age_group_name = serializers.SerializerMethodField()
    field_size_name = serializers.SerializerMethodField()
    gender_name = serializers.SerializerMethodField()

    class Meta:
        model = TeamBranch
        fields = [
            'id', 'team_id', 'team_name', 'age_group_id', 'age_group_name', 'upload_image', 'field_size', 
            'field_size_name', 'phone', 'email','gender','gender_name', 'latitude', 'longitude', 'address', 'house_no', 'premises', 
            'street', 'city', 'state', 'country_name', 'postalCode', 'country_code', 'entry_fees', 'description', 
            'created_at', 'updated_at'
        ]
    
    def get_gender_name(self, obj):
        request = self.context.get('request')
        language = request.headers.get('Language', 'en')
        if language == 'ar':
            return obj.gender.name_ar
        return obj.gender.name_en
    

    def get_field_size_name(self, obj):
        return obj.field_size.name if obj.field_size else None  

    def get_age_group_name(self, obj):
        return obj.age_group_id.name_en if obj.age_group_id else None


class JoinBranchSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()  # Custom method to include user data

    class Meta:
        model = JoinBranch
        fields = ['id', 'branch_id', 'user', 'joinning_type', 'user_id']  # Keep 'user_id' here for input purposes

    def get_user(self, obj):
        """Retrieve user data as a dictionary."""
        user = obj.user_id  # Get the related User object via foreign key
        return {
            'id': user.id,
            'username': user.username,
            'phone': user.phone,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            'country_id': user.country.id if user.country else None,
        }

    def to_representation(self, instance):
        """Customize the output representation of the serializer."""
        representation = super().to_representation(instance)
        # Remove 'user_id' from the output as it's already represented in 'user'
        representation.pop('user_id', None)
        return representation