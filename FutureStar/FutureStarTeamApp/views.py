from django.utils.translation import gettext as _
from django.utils.translation import activate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from FutureStarAPI.serializers import *
from FutureStarTeamApp.serializers import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from FutureStar_App.models import *
from FutureStarAPI.models import *
from FutureStarTeamApp.models import *
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.utils.translation import gettext as _
from django.utils.crypto import get_random_string


################################################################## TEAM API ###############################################################################################
class TeamViewAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Check if 'team_id' is provided in the request
        team_id = request.query_params.get('team_id', None)

        if team_id:
            # Fetch and return the team data if 'team_id' is provided
            try:
                team = Team.objects.get(id=team_id)
                serializer = TeamSerializer(team, context={'request': request})  # Pass request in context
                return Response({
                    'status': 1,
                    'message': _('Team data retrieved successfully.'),
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            except Team.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Team not found.')
                }, status=status.HTTP_404_NOT_FOUND)

        # If no 'team_id' is provided, return categories
        categories = Category.objects.all()

        # Construct the response data with language-specific names
        type_data = []
        for category in categories:
            if language == 'ar':
                type_name = category.name_ar
            else:
                type_name = category.name_en
            type_data.append({
                'id': category.id,
                'type_name': type_name
            })

        return Response({
            'status': 1,
            'message': _('Categories retrieved successfully.'),
            'data': type_data
        }, status=status.HTTP_200_OK)
    

    def post(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        user = request.user

        # Check if the user has already created a team
        if Team.objects.filter(team_founder=user).exists():
            return Response({
                'status': 0,
                'message': _('You can only create one team.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the team type (category) by its ID from the request
        try:
            team_type_id = request.data.get('team_type')
            team_type_instance = Category.objects.get(id=team_type_id)
        except Category.DoesNotExist:
            return Response({
                'status': 0, 
                'message': _('Invalid team type provided.')}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if team_username already exists in either the Team or User model
        team_username = request.data.get('team_username')
        if Team.objects.filter(team_username=team_username).exists() or User.objects.filter(username=team_username).exists():
            return Response({
                'status': 0, 
                'message': _('The username is already in use either as a team username or a user username.')}, 
                status=status.HTTP_400_BAD_REQUEST)

        # Create a new team instance
        team_instance = Team(
            team_founder=user,
            team_name=request.data.get('team_name'),
            team_username=request.data.get('team_username'),
            team_type=team_type_instance,
        )

        # Handle file uploads (same as your existing logic)
        if 'team_logo' in request.FILES:
            logo = request.FILES['team_logo']
            file_extension = logo.name.split('.')[-1]
            file_name = f"team/team_logo/{team_instance.team_name}_{team_instance.id}.{file_extension}"
            logo_path = default_storage.save(file_name, logo)
            team_instance.team_logo = logo_path

        # Save the team instance
        team_instance.save()

        # Fetch the newly created team instance from the database to return fresh data
        team_instance = Team.objects.get(id=team_instance.id)

        # Serialize the data
        serializer = TeamSerializer(team_instance)

        return Response({
            'status': 1,
            'message': _('Team created successfully.'),
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


    def put(self, request):
        team_id = request.data.get('team_id')
        print(team_id)
        user = request.user
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        if not team_id:
            return Response({'status': 0, 'message': _('Team ID is required.')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            print(team_id)
            team_instance = Team.objects.get(id=team_id, team_founder=request.user)
            print(team_instance)
        except Team.DoesNotExist:
            return Response({'status': 0, 'message': _('Team not found.')}, status=status.HTTP_404_NOT_FOUND)

        # Fetch the team type (category) by its ID, if provided
        team_type_id = request.data.get('team_type')
        if team_type_id:
            try:
                team_type_instance = Category.objects.get(id=team_type_id)
                team_instance.team_type = team_type_instance  # Assign the Category instance
            except Category.DoesNotExist:
                return Response({'status': 0, 'message': _('Invalid team type provided.')}, status=status.HTTP_400_BAD_REQUEST)

        # Update other fields from the request data
        team_instance.team_name = request.data.get('team_name', team_instance.team_name)
        team_instance.team_username = request.data.get('team_username', team_instance.team_username)
        team_instance.bio = request.data.get('bio', team_instance.bio)
        team_instance.team_establishment_date = request.data.get('team_establishment_date', team_instance.team_establishment_date)
        team_instance.team_president = request.data.get('team_president', team_instance.team_president)
        team_instance.team_founder = request.data.get('team_founder', team_instance.team_founder)

        team_instance.entry_fees = request.data.get('entry_fees', team_instance.entry_fees)


        # Add the remaining fields from the model
        team_instance.latitude = request.data.get('latitude', team_instance.latitude)
        team_instance.longitude = request.data.get('longitude', team_instance.longitude)
        team_instance.address = request.data.get('address', team_instance.address)
        team_instance.house_no = request.data.get('house_no', team_instance.house_no)
        team_instance.premises = request.data.get('premises', team_instance.premises)
        team_instance.street = request.data.get('street', team_instance.street)
        team_instance.city = request.data.get('city', team_instance.city)
        team_instance.state = request.data.get('state', team_instance.state)
        team_instance.country_name = request.data.get('country_name', team_instance.country_name)
        team_instance.postalCode = request.data.get('postalCode', team_instance.postalCode)
        team_instance.country_code = request.data.get('country_code', team_instance.country_code)
        country_id = request.data.get('country_id')
        if country_id:
            try:
                team_instance.country_id = Country.objects.get(id=country_id)
            except Country.DoesNotExist:
                return Response({'status': 0, 'message': _('Invalid country ID provided.')}, status=status.HTTP_400_BAD_REQUEST)

        city_id = request.data.get('city_id')
        if city_id:
            try:
                team_instance.city_id = City.objects.get(id=city_id)  # Assuming City is your model for city
            except City.DoesNotExist:
                return Response({'status': 0, 'message': _('Invalid city ID provided.')}, status=status.HTTP_400_BAD_REQUEST)

# Save the team instance
        team_instance.phone = request.data.get('phone', team_instance.phone)
        team_instance.email = request.data.get('email', team_instance.email)
        team_instance.age_group = request.data.get('age_group', team_instance.age_group)

        # Handle background image update
        if 'team_background_image' in request.FILES:
            # Delete old background image if it exists
            if team_instance.team_background_image and default_storage.exists(team_instance.team_background_image.name):  # Use .name here
                default_storage.delete(team_instance.team_background_image.name)  # Use .name here

            # Upload new background image with a unique filename
            background_image = request.FILES['team_background_image']
            file_extension = background_image.name.split('.')[-1]
            unique_suffix = get_random_string(8)  # Ensure the name is unique
            file_name = f"team/team_background_image/{team_instance.id}_{unique_suffix}.{file_extension}"
            background_image_path = default_storage.save(file_name, background_image)
            team_instance.team_background_image = background_image_path

        # Handle team uniform update
        if 'team_uniform' in request.FILES:
            # Delete old uniform if it exists
            if team_instance.team_uniform:
                old_uniforms = team_instance.team_uniform.split(',')
                for old_uniform in old_uniforms:
                    if default_storage.exists(old_uniform):
                        default_storage.delete(old_uniform)

            # Upload new team uniform with unique filenames
            uniforms = request.FILES.getlist('team_uniform')
            team_uniform_images = []
            for uniform in uniforms:
                unique_suffix = get_random_string(8)
                file_extension = uniform.name.split('.')[-1]
                file_name = f"team/team_uniform/{team_instance.id}_{unique_suffix}.{file_extension}"
                uniform_path = default_storage.save(file_name, uniform)
                team_uniform_images.append(uniform_path)

            team_instance.team_uniform = ','.join(team_uniform_images)


        team_instance.save()

        # Fetch the updated team instance from the database to return fresh data
        team_instance = Team.objects.get(id=team_instance.id)

        # Serialize the data
        serializer = TeamSerializer(team_instance)

        return Response({
            'status': 1,
            'message': _('Team updated successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def patch(self, request):
        """API for updating team logo"""
        team_id = request.data.get('team_id')
        if not team_id:
            return Response({'status': 0, 'message': _('Team ID is required.')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            team_instance = Team.objects.get(id=team_id, team_founder=request.user)
        except Team.DoesNotExist:
            return Response({'status': 0, 'message': _('Team not found.')}, status=status.HTTP_404_NOT_FOUND)

        if 'team_logo' in request.FILES:
            # Delete old logo if it exists
            if team_instance.team_logo and default_storage.exists(team_instance.team_logo.name):  # Use .name here
                default_storage.delete(team_instance.team_logo.name)  # Use .name here

            # Upload new logo with a unique filename
            logo = request.FILES['team_logo']
            file_extension = logo.name.split('.')[-1]
            unique_suffix = get_random_string(8)  # Generate a random suffix to ensure unique filenames
            file_name = f"team/team_logo/{team_instance.id}_{unique_suffix}.{file_extension}"
            logo_path = default_storage.save(file_name, logo)
            team_instance.team_logo = logo_path

        team_instance.save()

        # Serialize and return the updated data
        serializer = TeamSerializer(team_instance)

        return Response({
            'status': 1,
            'message': _('Team logo updated successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
