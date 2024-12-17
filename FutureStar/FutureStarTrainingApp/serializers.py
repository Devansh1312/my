from rest_framework import serializers
from FutureStar_App.models import *
from FutureStarAPI.models import *
from FutureStarTeamApp.models import *
from FutureStarTrainingApp.models import *
from datetime import datetime, date, timedelta


class TrainingCommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    entity = serializers.SerializerMethodField()

    class Meta:
        model = Training_comment
        fields = ['id', 'created_by_id', 'creator_type', 'training', 'parent', 'comment', 'date_created', 'replies', 'entity']

    def get_replies(self, obj):
        # Only fetch replies (children) where parent is the current comment (obj)
        replies = Training_comment.objects.filter(parent=obj).order_by('-date_created')
        return TrainingCommentSerializer(replies, many=True, context=self.context).data

    def get_entity(self, obj):
        # Get entity details based on creator_type
        if obj.creator_type == Training_comment.TEAM_TYPE:
            team = Team.objects.get(id=obj.created_by_id)
            return {
                'id': team.id,
                'name': team.team_name,
                'profile_image': team.team_logo.url if team.team_logo else None,
                'type': 'team'
            }
        elif obj.creator_type == Training_comment.GROUP_TYPE:
            group = TrainingGroups.objects.get(id=obj.created_by_id)
            return {
                'id': group.id,
                'name': group.group_name,
                'profile_image': group.group_logo.url if group.group_logo else None,
                'type': 'group'
            }
        else:  # USER_TYPE
            user = User.objects.get(id=obj.created_by_id)
            return {
                'id': user.id,
                'username': user.username,
                'profile_image': user.profile_picture.url if user.profile_picture else None,
                'type': 'user'
            }
        return None

################################ For List API ###################################
class TrainingListSerializer(serializers.ModelSerializer):
    gender_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    country_name = serializers.SerializerMethodField()
    training_type_name = serializers.SerializerMethodField()
    training_photo = serializers.SerializerMethodField()
    field_info = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_like = serializers.SerializerMethodField()
    joined_players_count = serializers.SerializerMethodField()
    is_joined = serializers.SerializerMethodField()  # New field for is_joined flag



    class Meta:
        model = Training
        fields = ['id', 'training_name', 'training_photo', 'country', 'country_name', 'city', 'city_name', 
                  'field', 'field_info' ,'gender', 'gender_name', 'training_date', 'start_time', 'training_duration', 
                  'end_time', 'no_of_participants', 'training_type', 'training_type_name', 'cost', 
                  'description', 'like_count', 'is_like','comments','creator_type', 'created_by_id','joined_players_count','is_joined']
        
    def get_joined_players_count(self, obj):
        return Training_Joined.objects.filter(training=obj).count()
    
    def get_is_joined(self, obj):
        request = self.context.get('request')
        if request is None:
            return False
        
        user = request.user  # Get the current user
        # Check if the current user is joined in this training
        return Training_Joined.objects.filter(training=obj, user=user).exists()

    def get_comments(self, obj):
        # Always return the count of top-level comments
        return Training_comment.objects.filter(training=obj, parent=None).count()    
    
    def get_like_count(self, obj):
        return TrainingLike.objects.filter(training=obj).count()
    
    def get_is_like(self, obj):
        request = self.context.get('request')
        if request:
            # Retrieve creator_type and created_by_id from request data or query parameters
            creator_type = request.data.get('creator_type') or request.query_params.get('creator_type')
            created_by_id = request.data.get('created_by_id') or request.query_params.get('created_by_id')

            # Use default values if neither request data nor query parameters provide valid values
            creator_type = int(creator_type) if creator_type not in [None, '', '0'] else TrainingLike.USER_TYPE
            created_by_id = int(created_by_id) if created_by_id not in [None, '', '0'] else request.user.id

            # Check if a like exists for the given post, creator_type, and created_by_id
            if TrainingLike.objects.filter(
                training=obj,
                created_by_id=created_by_id,
                creator_type=creator_type
            ).exists():
                return True

        return False
        
    def get_training_photo(self, obj):
        return obj.training_photo.url if obj.training_photo else None

    def get_gender_name(self, obj):
        request = self.context.get('request')
        if request is None:
            return None

        language = request.headers.get('Language', 'en')
        # Ensure language-based name retrieval (if applicable)
        if obj.gender:
            return obj.gender.name_ar if language == 'ar' else obj.gender.name_en
        return None

    def get_city_name(self, obj):
        request = self.context.get('request')
        if request is None:
            return None

        language = request.headers.get('Language', 'en')
        # Ensure language-based name retrieval
        if obj.city:
            return obj.city.name if language == 'ar' else obj.city.name
        return None

    def get_country_name(self, obj):
        request = self.context.get('request')
        if request is None:
            return None

        language = request.headers.get('Language', 'en')
        # Ensure language-based name retrieval
        if obj.country:
            return obj.country.name if language == 'ar' else obj.country.name
        return None

    def get_training_type_name(self, obj):
        request = self.context.get('request')
        if request is None:
            return None

        language = request.headers.get('Language', 'en')
        # Ensure language-based name retrieval (example with hardcoded types)
        if obj.training_type == 1:
            return "تدريب مفتوح" if language == 'ar' else "Open Training"
        elif obj.training_type == 2:
            return "تدريب مغلق" if language == 'ar' else "Closed Training"
        return None
    
    def get_field_info(self, obj):
        if obj.field:
            return {
                'id': obj.field.id,
                'name': obj.field.field_name,
                'latitude': obj.field.latitude,
                'longitude': obj.field.longitude,
                'address': obj.field.address,
                'house_no': obj.field.house_no,
                'premises': obj.field.premises,
                'street': obj.field.street,
                'city': obj.field.city,
                'state': obj.field.state,
                'country_name': obj.field.country_name,
                'postalCode': obj.field.postalCode,
                'country_code': obj.field.country_code,
            }
        return None



################## For Create And Detail ###########################
class TrainingSerializer(serializers.ModelSerializer):
    gender_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    country_name = serializers.SerializerMethodField()
    training_type_name = serializers.SerializerMethodField()
    training_photo = serializers.SerializerMethodField()
    field_info = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_like = serializers.SerializerMethodField()
    joined_players = serializers.SerializerMethodField()
    joined_players_count = serializers.SerializerMethodField()


    class Meta:
        model = Training
        fields = ['id', 'training_name', 'training_photo', 'country', 'country_name', 'city', 'city_name', 
                  'field', 'field_info' ,'gender', 'gender_name', 'training_date', 'start_time', 'training_duration', 
                  'end_time', 'no_of_participants', 'training_type', 'training_type_name', 'cost', 
                  'description', 'like_count', 'is_like','comments','creator_type', 'created_by_id','joined_players','joined_players_count']
        
    def get_joined_players_count(self, obj):
        return Training_Joined.objects.filter(training=obj).count()

    def get_joined_players(self, obj):
        # Retrieve joined players and format their information
        joined_players = []
        for joined in Training_Joined.objects.filter(training=obj):
            user = joined.user
            player_info = {
                'id': user.id,
                'username': user.username,
                'phone': user.phone,
                'gender':user.gender.id if user.gender else None,
                'profile_picture': user.profile_picture.url if user.profile_picture else None,
                'country_id': user.country.id if user.country else None,
                'country_name': user.country.name if user.country else None,
                'attendance_status': joined.attendance_status
            }
            joined_players.append(player_info)
        return joined_players   

    def get_comments(self, obj):
        # Always return the count of top-level comments
        return Training_comment.objects.filter(training=obj, parent=None).count()    
    
    def get_like_count(self, obj):
        return TrainingLike.objects.filter(training=obj).count()
    
    def get_is_like(self, obj):
        request = self.context.get('request')
        if request:
            # Retrieve creator_type and created_by_id from request data or query parameters
            creator_type = request.data.get('creator_type') or request.query_params.get('creator_type')
            created_by_id = request.data.get('created_by_id') or request.query_params.get('created_by_id')

            # Use default values if neither request data nor query parameters provide valid values
            creator_type = int(creator_type) if creator_type not in [None, '', '0'] else TrainingLike.USER_TYPE
            created_by_id = int(created_by_id) if created_by_id not in [None, '', '0'] else request.user.id

            # Check if a like exists for the given post, creator_type, and created_by_id
            if TrainingLike.objects.filter(
                training=obj,
                created_by_id=created_by_id,
                creator_type=creator_type
            ).exists():
                return True

        return False
        
    def get_training_photo(self, obj):
        return obj.training_photo.url if obj.training_photo else None

    def get_gender_name(self, obj):
        request = self.context.get('request')
        if request is None:
            return None

        language = request.headers.get('Language', 'en')
        # Ensure language-based name retrieval (if applicable)
        if obj.gender:
            return obj.gender.name_ar if language == 'ar' else obj.gender.name_en
        return None

    def get_city_name(self, obj):
        request = self.context.get('request')
        if request is None:
            return None

        language = request.headers.get('Language', 'en')
        # Ensure language-based name retrieval
        if obj.city:
            return obj.city.name if language == 'ar' else obj.city.name
        return None

    def get_country_name(self, obj):
        request = self.context.get('request')
        if request is None:
            return None

        language = request.headers.get('Language', 'en')
        # Ensure language-based name retrieval
        if obj.country:
            return obj.country.name if language == 'ar' else obj.country.name
        return None

    def get_training_type_name(self, obj):
        request = self.context.get('request')
        if request is None:
            return None

        language = request.headers.get('Language', 'en')
        # Ensure language-based name retrieval (example with hardcoded types)
        if obj.training_type == 1:
            return "تدريب مفتوح" if language == 'ar' else "Open Training"
        elif obj.training_type == 2:
            return "تدريب مغلق" if language == 'ar' else "Closed Training"
        return None
    
    def get_field_info(self, obj):
        if obj.field:
            return {
                'id': obj.field.id,
                'name': obj.field.field_name,
                'latitude': obj.field.latitude,
                'longitude': obj.field.longitude,
                'address': obj.field.address,
                'house_no': obj.field.house_no,
                'premises': obj.field.premises,
                'street': obj.field.street,
                'city': obj.field.city,
                'state': obj.field.state,
                'country_name': obj.field.country_name,
                'postalCode': obj.field.postalCode,
                'country_code': obj.field.country_code,
            }
        return None
    


class TrainingMembershipSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    feedbacks = serializers.SerializerMethodField()

    class Meta:
        model = Training_Joined
        fields = ['id', 'training', 'user', 'attendance_status', 'rating', 'feedbacks']

    def get_user(self, obj):
        """Retrieve user data as a dictionary."""
        user = obj.user  # Get the related User object via foreign key
        return {
            'id': user.id,
            'username': user.username,
            'phone': user.phone,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            'country_id': user.country.id if user.country else None,
            'country_name': user.country.name if user.country else None,
        }

    def get_feedbacks(self, obj):
        """Retrieve all feedbacks for the given training and user."""
        feedbacks = Training_Feedback.objects.filter(training=obj.training, user=obj.user)
        return Training_FeedbackSerializer(feedbacks, many=True).data

class Training_FeedbackSerializer(serializers.ModelSerializer):
    injuries = serializers.SerializerMethodField()

    class Meta:
        model = Training_Feedback
        fields = ['id', 'training', 'user', 'feedback', 'injuries', 'date_created', 'created_at', 'updated_at']

    def get_injuries(self, obj):
        """Return a comma-separated string of injury ids."""
        injuries = obj.injuries.all()  # 'injuries' is the correct field name
        injury_ids = [str(injury.id) for injury in injuries]  # Extract only the IDs
        return ','.join(injury_ids)  # Join them into a comma-separated string