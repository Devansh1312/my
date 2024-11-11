from rest_framework import serializers
from FutureStar_App.models import *
from FutureStarAPI.models import *
from FutureStarTeamApp.models import *
from FutureStarTrainingApp.models import *
from datetime import datetime, date, timedelta

class TrainingSerializer(serializers.ModelSerializer):
    gender_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    country_name = serializers.SerializerMethodField()
    training_type_name = serializers.SerializerMethodField()
    training_photo = serializers.SerializerMethodField()
    field_info = serializers.SerializerMethodField()

    class Meta:
        model = Training
        fields = ['id', 'training_name', 'training_photo', 'country', 'country_name', 'city', 'city_name', 
                  'field', 'field_info' ,'gender', 'gender_name', 'training_date', 'start_time', 'training_duration', 
                  'end_time', 'no_of_participants', 'training_type', 'training_type_name', 'cost', 
                  'description', 'creator_type', 'created_by_id']
        
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
    
    def create(self, validated_data):
        # Ensure 'created_by_id' is passed in validated_data if not already present
        user = self.context.get('request').user  # Assuming the logged-in user is creating the training
        validated_data['created_by_id'] = user.id
        
        # Calculate end_time based on start_time and training_duration
        start_time = validated_data.get('start_time')
        duration = validated_data.get('training_duration')
        
        if start_time and duration:
            validated_data['end_time'] = (datetime.combine(date.min, start_time) + timedelta(minutes=duration)).time()
        
        return super().create(validated_data)




# class JoinTraining(serializers.ModelSerializer):
#     user = serializers.SerializerMethodField()  # Custom method to include user data

#     class Meta:
#         model = JoinBranch
#         fields = ['id', 'branch_id', 'user', 'joinning_type', 'user_id']  # Keep 'user_id' here for input purposes

#     def get_user(self, obj):
#         """Retrieve user data as a dictionary."""
#         user = obj.user_id  # Get the related User object via foreign key
#         return {
#             'id': user.id,
#             'username': user.username,
#             'phone': user.phone,
#             'profile_picture': user.profile_picture.url if user.profile_picture else None,
#             'country_id': user.country.id if user.country else None,
#         }

#     def to_representation(self, instance):
#         """Customize the output representation of the serializer."""
#         representation = super().to_representation(instance)
#         # Remove 'user_id' from the output as it's already represented in 'user'
#         representation.pop('user_id', None)
#         return representation