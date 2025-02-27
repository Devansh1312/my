from django.utils.translation import gettext as _
from django.utils.translation import activate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from FutureStarAPI.serializers import *
from FutureStarAPI.views import get_group_data,get_user_data
from FutureStarTeamApp.serializers import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from FutureStar_App.models import *
from FutureStarAPI.models import *
from FutureStarTeamApp.models import *
from FutureStarFriendlyGame.models import *
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.utils.translation import gettext as _
from django.utils.crypto import get_random_string
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator, EmptyPage
from django.db import IntegrityError
from django.conf import settings
from django.db import transaction
from django.db.models import Sum,Q,When,Case
from FutureStar.firebase_config import send_push_notification
# FutureStar\firebase_config.py
from FutureStarGameSystem.models import *
from FutureStarTournamentApp.models import *


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
        creator_type = request.query_params.get('creator_type')
        created_by_id = request.query_params.get('created_by_id')
        

        if team_id:
            # Fetch and return the team data if 'team_id' is provided
            try:
                team = Team.objects.get(id=team_id)
                serializer = TeamSerializer(team, context={'request': request})  # Pass request in context
                notification_count = Notifictions.objects.filter(targeted_id=created_by_id, targeted_type=creator_type,read=False).count()

                user = request.user
                # Fetch user data
                user_data = get_user_data(user, request)
                # Fetch group data
                group_data = get_group_data(user, request)
                return Response({
                    'status': 1,
                    'message': _('Team data retrieved successfully.'),
                    'data': {
                        'user': user_data,
                        'team': serializer.data,
                        'group': group_data,
                        'current_type':user.current_type,
                    },
                    "notification_count": notification_count  # Include notification count here
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
                'name': type_name
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
        creator_type = request.query_params.get('creator_type')
        created_by_id = request.query_params.get('created_by_id')

        if not user.role_id in [2, 5]:
            return Response({
                'status': 0,
                'message': _('You do not have permission to create a team.')
            }, status=status.HTTP_403_FORBIDDEN)

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
        if Team.objects.filter(team_username=team_username).exists() or User.objects.filter(username=team_username) or TrainingGroups.objects.filter(group_username=team_username).exists():
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
            unique_suffix = get_random_string(8)
            file_name = f"team/team_logo/{team_instance.team_founder.id}_{team_instance.id}_{unique_suffix}.{file_extension}"
            logo_path = default_storage.save(file_name, logo)
            team_instance.team_logo = logo_path

        # Save the team instance
        team_instance.save()

        # Fetch the newly created team instance from the database to return fresh data
        team_instance = Team.objects.get(id=team_instance.id)

        # Serialize the data
        serializer = TeamSerializer(team_instance)
        # Fetch user data
        user_data = get_user_data(user, request)
        # Fetch group data
        group_data = get_group_data(user, request)
        notification_count = Notifictions.objects.filter(targeted_id=created_by_id, targeted_type=creator_type,read=False).count()

        return Response({
            'status': 1,
            'message': _('Team created successfully.'),
            'data': {
                'user': user_data,
                'team': serializer.data,
                'group': group_data,
                'current_type':user.current_type,
            },
            "notification_count": notification_count  # Include notification count here
        }, status=status.HTTP_201_CREATED)


    def put(self, request):
        team_id = request.data.get('created_by_id')
        user = request.user
        creator_type = request.query_params.get('creator_type')
        created_by_id = request.query_params.get('created_by_id')
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        if not team_id:
            return Response({
                'status': 0, 
                'message': _('Team ID is required.')
                }, status=status.HTTP_400_BAD_REQUEST)

        try:
            team_instance = Team.objects.get(id=team_id, team_founder=request.user)
        except Team.DoesNotExist:
            return Response({
                'status': 0, 
                'message': _('Team not found.')
                }, status=status.HTTP_404_NOT_FOUND)

        # Fetch the team type (category) by its ID, if provided
        team_type_id = request.data.get('team_type')
        if team_type_id:
            try:
                team_type_instance = Category.objects.get(id=team_type_id)
                team_instance.team_type = team_type_instance  # Assign the Category instance
            except Category.DoesNotExist:
                return Response({
                    'status': 0, 
                    'message': _('Invalid team type provided.')
                    }, status=status.HTTP_400_BAD_REQUEST)

        # Update other fields from the request data
        team_instance.team_name = request.data.get('team_name', team_instance.team_name)
        team_instance.team_username = request.data.get('team_username', team_instance.team_username)
        team_instance.bio = request.data.get('bio', team_instance.bio)
        team_instance.team_establishment_date = request.data.get('team_establishment_date', team_instance.team_establishment_date)
        team_instance.team_president = request.data.get('team_president', team_instance.team_president)
        team_instance.team_founder = request.data.get('team_founder', team_instance.team_founder)

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
                return Response({
                    'status': 0, 
                    'message': _('Invalid country ID provided.')
                    }, status=status.HTTP_400_BAD_REQUEST)

        city_id = request.data.get('city_id')
        if city_id:
            try:
                team_instance.city_id = City.objects.get(id=city_id)  # Assuming City is your model for city
            except City.DoesNotExist:
                return Response({
                    'status': 0, 
                    'message': _('Invalid city ID provided.')
                    }, status=status.HTTP_400_BAD_REQUEST)

# Save the team instance
        team_instance.phone = request.data.get('phone', team_instance.phone)
        team_instance.email = request.data.get('email', team_instance.email)

        # Handle background image update
        if 'team_background_image' in request.FILES:
            # Delete old background image if it exists
            if team_instance.team_background_image and default_storage.exists(team_instance.team_background_image.name):  # Use .name here
                default_storage.delete(team_instance.team_background_image.name)  # Use .name here

            # Upload new background image with a unique filename
            background_image = request.FILES['team_background_image']
            file_extension = background_image.name.split('.')[-1]
            unique_suffix = get_random_string(8)  # Ensure the name is unique
            file_name = f"team/team_background_image/{team_instance.team_founder.id}_{team_instance.id}_{unique_suffix}.{file_extension}"
            background_image_path = default_storage.save(file_name, background_image)
            team_instance.team_background_image = background_image_path

        # Handle team uniforms using TeamUniform model
        if 'team_uniform' in request.FILES:
            # Upload new uniforms and save in TeamUniform model
            uniforms = request.FILES.getlist('team_uniform')
            for uniform in uniforms:
                unique_suffix = get_random_string(8)
                file_extension = uniform.name.split('.')[-1]
                file_name = f"team/team_uniform/{team_instance.team_founder.id}_{team_instance.id}_{unique_suffix}.{file_extension}"
                uniform_path = default_storage.save(file_name, uniform)

                # Save each uniform as a new instance in the TeamUniform model
                TeamUniform.objects.create(
                    team_id=team_instance,
                    team_uniform_image=uniform_path
                )


        team_instance.save()

        # Fetch the updated team instance from the database to return fresh data
        team_instance = Team.objects.get(id=team_instance.id)

        # Serialize the data
        serializer = TeamSerializer(team_instance)
        user_data = get_user_data(user, request)
        # Fetch group data
        group_data = get_group_data(user, request)
        # Fetch notification count
        notification_count = Notifictions.objects.filter(targeted_id=created_by_id, targeted_type=creator_type,read=False).count()
        return Response({
            'status': 1,
            'message': _('Team updated successfully.'),
             'data': {
                'user': user_data,
                'team': serializer.data,
                'group': group_data,
                'current_type': user.current_type
            },
            "notification_count": notification_count  # Include notification count here
        }, status=status.HTTP_200_OK)
    
    def patch(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        """API for updating team logo"""
        team_id = request.data.get('created_by_id')
        creator_type = request.query_params.get('creator_type')
        created_by_id = request.query_params.get('created_by_id')
        if not team_id:
            return Response({
                'status': 0, 
                'message': _('Team ID is required.')
                }, status=status.HTTP_400_BAD_REQUEST)

        try:
            team_instance = Team.objects.get(id=team_id, team_founder=request.user)
        except Team.DoesNotExist:
            return Response({
                'status': 0, 
                'message': _('Team not found.')
                }, status=status.HTTP_404_NOT_FOUND)

        if 'team_logo' in request.FILES:
            # Delete old logo if it exists
            if team_instance.team_logo and default_storage.exists(team_instance.team_logo.name):  # Use .name here
                default_storage.delete(team_instance.team_logo.name)  # Use .name here

            # Upload new logo with a unique filename
            logo = request.FILES['team_logo']
            file_extension = logo.name.split('.')[-1]
            unique_suffix = get_random_string(8)  # Generate a random suffix to ensure unique filenames
            file_name = f"team/team_logo/{team_instance.team_founder.id}_{team_instance.id}_{unique_suffix}.{file_extension}"
            logo_path = default_storage.save(file_name, logo)
            team_instance.team_logo = logo_path

        team_instance.save()
        user = request.user

        # Serialize and return the updated data
        serializer = TeamSerializer(team_instance)
        user_data = get_user_data(user, request)
        # Fetch group data
        group_data = get_group_data(user, request)
        notification_count = Notifictions.objects.filter(targeted_id=created_by_id, targeted_type=creator_type,read=False).count()

        return Response({
            'status': 1,
            'message': _('Team logo updated successfully.'),
            'data': {
                'user': user_data,
                'team': serializer.data,
                'group': group_data,
                'current_type': user.current_type
            },
            "notification_count": notification_count  # Include notification count here
        }, status=status.HTTP_200_OK)
    
    ############### Team Delete API ###################
    def delete(self, request, *args, **kwargs):
        # Set language based on the 'Language' header
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        # Get the team_id from query parameters
        team_id = request.query_params.get('created_by_id', None)
        if not team_id:
            return Response({
              'status': 0,
              'message': _('Team ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            team_instance = Team.objects.get(id=team_id, team_founder=request.user)
            team_instance.delete()
            return Response({
               'status': 1,
              'message': _('Team deleted successfully.')
            }, status=status.HTTP_200_OK)

########################### Delete Uniforms BY ID ##################
class DeleteUniformView(APIView):
    def delete(self, request):
        # Get the uniform_id from query parameters
        uniform_id = request.query_params.get('uniform_id')
        
        # Check if uniform_id is provided
        if not uniform_id:
            return Response({
                'status': 0,
                'message': _('Uniform ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the uniform exists
        try:
            uniform = TeamUniform.objects.get(id=uniform_id)
        except TeamUniform.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Uniform not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Delete the image file from storage if it exists
        if uniform.team_uniform_image and default_storage.exists(uniform.team_uniform_image.name):
            default_storage.delete(uniform.team_uniform_image.name)
        
        # Delete the uniform instance
        uniform.delete()

        return Response({
            'status': 1,
            'message': _('Uniform deleted successfully.')
        }, status=status.HTTP_200_OK)        
############# Team Branch Create API #################    
class TeamBranchAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
  
    def post(self, request, *args, **kwargs):
        # Set language based on the 'Language' header
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Initialize the serializer with request data
        serializer = TeamBranchSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # Save the validated data to create a TeamBranch instance
            team_branch_instance = serializer.save()

            # Handle image upload if an image file is provided in request.FILES
            if "upload_image" in request.FILES:
                image = request.FILES["upload_image"]
                file_extension = image.name.split('.')[-1]
                unique_suffix = get_random_string(8)
                
                # Retrieve the team ID for constructing the file name
                team_id = request.data.get("team_id")
                file_name = f"team_branch_images/{team_branch_instance.id}_{team_id}_{unique_suffix}.{file_extension}"
                
                # Save the image using the default storage
                image_path = default_storage.save(file_name, image)
                team_branch_instance.upload_image = image_path
                team_branch_instance.save()

            # Refresh the instance to ensure all fields are up-to-date
            team_branch_instance.refresh_from_db()

            # Return a success response with the created data
            return Response({
                'status': 1,
                'message': _('Team created successfully.'),
                'data': TeamBranchSerializer(team_branch_instance, context={'request': request}).data  # Include context here as well
            }, status=status.HTTP_201_CREATED)
        
        # Return an error response if validation fails
        return Response({
            'status': 0,
            'message': _('Team creation failed.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        # Set language based on the 'Language' header
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get the team_id from query parameters
        team_branch_id = self.request.query_params.get('team_branch_id')
        if not team_branch_id:
            return Response({
                'status': 0,
                'message': _('Team ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the TeamBranch instance associated with the team_id
        try:
            team_branch_instance = TeamBranch.objects.get(id=team_branch_id)
        except TeamBranch.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('No Team found for the given ID.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Serialize and return the TeamBranch data
        serializer = TeamBranchSerializer(team_branch_instance, context={'request': request})
        return Response({
            'status': 1,
            'message': _('Team retrieved successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def patch(self, request, *args, **kwargs):
        # Set language based on the 'Language' header
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get the team_branch_id from the query parameters
        team_branch_id = request.data.get('team_branch_id')
        if not team_branch_id:
            return Response({
                'status': 0,
                'message': _('Team ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the TeamBranch instance associated with the team_id
        try:
            team_branch_instance = TeamBranch.objects.get(id=team_branch_id)
        except TeamBranch.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('No Team found for the given ID.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Initialize the serializer with the existing instance and the updated data
        serializer = TeamBranchSerializer(team_branch_instance, data=request.data, partial=True, context={'request': request})

        if serializer.is_valid():
            # Save the updated data
            team_branch_instance = serializer.save()

            # Handle image upload if an image file is provided in request.FILES
            if "upload_image" in request.FILES:
                image = request.FILES["upload_image"]
                file_extension = image.name.split('.')[-1]
                unique_suffix = get_random_string(8)
                
                # Retrieve the team ID for constructing the file name
                file_name = f"team_branch_images/{team_branch_instance.id}_{team_branch_instance.team_id.id}_{unique_suffix}.{file_extension}"
                
                # Save the image using the default storage
                image_path = default_storage.save(file_name, image)
                team_branch_instance.upload_image = image_path
                team_branch_instance.save()

            # Refresh the instance to ensure all fields are up-to-date
            team_branch_instance.refresh_from_db()

            # Return a success response with the updated data
            return Response({
                'status': 1,
                'message': _('Team Details updated successfully.'),
                'data': TeamBranchSerializer(team_branch_instance, context={'request': request}).data
            }, status=status.HTTP_200_OK)

        # Return an error response if validation fails
        return Response({
            'status': 0,
            'message': _('Team Detail update failed.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        # Set language based on the 'Language' header
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get the team_branch_id from the query parameters
        team_branch_id = self.request.query_params.get('team_branch_id')
        if not team_branch_id:
            return Response({
                'status': 0,
                'message': _('Team ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the TeamBranch instance associated with the team_id
        try:
            team_branch_instance = TeamBranch.objects.get(id=team_branch_id)
        except TeamBranch.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('No Team found for the given ID.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Delete the TeamBranch instance
        team_branch_instance.delete()

        return Response({
            'status': 1,
            'message': _('Team deleted successfully.')
        }, status=status.HTTP_204_NO_CONTENT)
        


class StaffManagementView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        branch_id = request.query_params.get('branch_id')
        if not branch_id:
            return Response({
                'status': 0, 
                'message': _('Team_Id is required.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Filter staff by type
        managerial_staff = JoinBranch.objects.filter(branch_id=branch_id, joinning_type=JoinBranch.MANAGERIAL_STAFF_TYPE)
        coach_staff = JoinBranch.objects.filter(branch_id=branch_id, joinning_type=JoinBranch.COACH_STAFF_TYPE)
        medical_staff = JoinBranch.objects.filter(branch_id=branch_id, joinning_type=JoinBranch.MEDICAL_STAFF_TYPE)
        players = JoinBranch.objects.filter(branch_id=branch_id, joinning_type=JoinBranch.PLAYER_TYPE)

        # Serialize each type
        managerial_serializer = JoinBranchSerializer(managerial_staff, many=True)
        coach_serializer = JoinBranchSerializer(coach_staff, many=True)
        medical_serializer = JoinBranchSerializer(medical_staff, many=True)
        players_serializer = JoinBranchSerializer(players, many=True)

        response_data = {
            'status': 1,
            'message': _('Data retrieved successfully.'),
            'data': {
                'managerial_staff': managerial_serializer.data,
                'coach_staff': coach_serializer.data,
                'medical_staff': medical_serializer.data,
                'players': players_serializer.data
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)
    

    def post(self, request):
        # Activate language from the request header
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        branch_id = request.data.get('branch_id')
        user_id = request.data.get('user_id')
        joinning_type = request.data.get('joinning_type')

        # Check required fields
        if not branch_id or not user_id or joinning_type is None:
            return Response({
                'status': 0, 
                'message': _('Team_id, user_id, and joining_type are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convert joinning_type to an integer and validate it
        try:
            joinning_type = int(joinning_type)
        except (ValueError, TypeError):
            return Response({
                'status': 0,
                'message': _('Please provide a valid joining type')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate joinning_type
        if joinning_type not in [1, 2, 3, 4]:
            return Response({
                'status': 0,
                'message': _('Please provide a valid joining type.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Retrieve the user
                user = User.objects.get(id=user_id)
                success_message = ''

                # Set the language for notification based on user's current_language
               

                # Retrieve the branch and team name
                try:
                    team_branch = TeamBranch.objects.get(id=branch_id)
                    team_name = team_branch.team_name
                except TeamBranch.DoesNotExist:
                    return Response({
                        'status': 0,
                        'message': _('Team not found.')
                    }, status=status.HTTP_404_NOT_FOUND)

                # Check if joining as MANAGERIAL_STAFF and update the role if current role is 5
                if joinning_type == JoinBranch.MANAGERIAL_STAFF_TYPE and user.role_id == 5:
                    user.role_id = 6
                    user.save()
                    success_message = _('Manager added successfully, and user role updated to manager.')

                # Check if joining as PLAYER_TYPE and update the role to 2
                elif joinning_type == JoinBranch.PLAYER_TYPE:
                    user.role_id = 2
                    user.save()
                    success_message = _('Player added successfully, and user role updated to player.')

                # Set success message for other staff types
                elif joinning_type in [JoinBranch.COACH_STAFF_TYPE, JoinBranch.MEDICAL_STAFF_TYPE]:
                    success_message = _('Staff added successfully.')

                # Prepare and save JoinBranch data
                join_branch_data = {
                    'branch_id': branch_id,
                    'user_id': user_id,
                    'joinning_type': joinning_type
                }
                serializer = JoinBranchSerializer(data=join_branch_data)

                if serializer.is_valid():
                    serializer.save()
                    notification_language = user.current_language if user.current_language in ['en', 'ar'] else 'en'
                    activate(notification_language)
                    # Translate and format notification title and body
                    joinning_type_name = dict(JoinBranch.JOINNING_TYPE_CHOICES).get(joinning_type, "Staff")
                    title_template = _('Welcome to {team_name}')
                    body_template = _('{team_name} added you as {joinning_type_name}')

                    title = title_template.format(team_name=team_name)
                    body = body_template.format(team_name=team_name, joinning_type_name=joinning_type_name)

                    # Send push notification to the user
                    if user.device_type in [1, 2, "1", "2"]:
                        push_data = {
                            'type': 'join_branch',
                            'notifier_id': branch_id,
                        }
                        send_push_notification(user.device_token, title, body, user.device_type, data=push_data)
                        notification = Notifictions.objects.create(
                            created_by_id=request.user.id,
                            creator_type=1,  # Assuming 1 is for user
                            targeted_id=user.id,
                            targeted_type=1,  # Assuming 1 is for user
                            title=title,
                            content=body
                        )
                        notification.save()


                    # Return API success message in the selected language
                    activate(language)  # Reactivate header language
                    return Response({
                        'status': 1,
                        'message': success_message,
                        'data': serializer.data
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'status': 0,
                        'message': _('Failed to add staff/player.'),
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            activate(language)
        except User.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('User not found.')
            }, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({
                'status': 0,
                'message': _('User has already joined this Team.')
            }, status=status.HTTP_400_BAD_REQUEST)
        

    ############ Remove Player From Team ##############    
    def delete(self, request):
        """
        Remove a player from a branch.
        Only players (joining_type = 4) can be removed.
        """
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        branch_id = request.query_params.get('branch_id')
        user_id = request.query_params.get('user_id')


        if not branch_id or not user_id:
            return Response({
                'status': 0,
                'message': _('team_id and User_id are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if the user is actually a player and if they belong to the given branch
            player = JoinBranch.objects.get(branch_id=branch_id, user_id=user_id, joinning_type=JoinBranch.PLAYER_TYPE)

            # Proceed to delete the player from the branch
            player.delete()

            return Response({
                'status': 1,
                'message': _('Player removed from the Team successfully.')
            }, status=status.HTTP_200_OK)

        except JoinBranch.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('No player found with the given user_id in the Specific Team.')
            }, status=status.HTTP_404_NOT_FOUND)

        except IntegrityError:
            return Response({
                'status': 0,
                'message': _('Error occurred while removing the player.')
            }, status=status.HTTP_400_BAD_REQUEST)


############ Custom User Search Pagination ##############
class CustomUserSearchPagination(PageNumberPagination):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    page_size = 10
    page_query_param = 'page'
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        # Store the request for later use in get_paginated_response
        self.request = request  
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        try:
            page_number = request.query_params.get(self.page_query_param, 1)
            self.page = int(page_number)
            if self.page < 1:
                raise ValidationError(_("Page number must be a positive integer."))
        except (ValueError, TypeError):
            return Response({
                'status': 0,
                'message': _('Page not found.'),
                'data': []
            }, status=400)

        paginator = self.django_paginator_class(queryset, self.get_page_size(request))
        self.total_pages = paginator.num_pages
        self.total_records = paginator.count

        try:
            page = paginator.page(self.page)
        except EmptyPage:
            return Response({
                'status': 0,
                'message': _('Page not found.'),
                'data': []
            }, status=400)

        self.paginated_data = page
        return list(page)

    def get_paginated_response(self, data):
        # Use self.request which was set in paginate_queryset
        language = self.request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        return Response({
            'status': 1,
            'message': _('Data fetched successfully.'),
            'total_records': self.total_records,
            'total_pages': self.total_pages,
            'current_page': self.page,
            'data': data
        })


############### User Search View ###############
class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = CustomUserSearchPagination  # Set the pagination class

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        # Get the phone parameter
        phone = request.query_params.get('phone')

        # Return empty result if phone is not provided
        if not phone:
            return Response({
                'status': 1, 
                'message': _('No data found.'), 
                "total_records": 0,
                "total_pages": 1,
                "current_page": 1,
                'data': []
                }, status=status.HTTP_200_OK)

        search_type = request.query_params.get('search_type')
        branch_id = request.query_params.get('branch_id')  # Get branch_id from request

        # Check for valid search_type, comparing with string values
        if search_type not in ['1', '2', '3', '4']:  # Add '3' to support coaching staff search
            return Response({'status': 0, 'message': _('Invalid search type. Must be 1, 2, 3, or 4.')}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize a queryset
        users = User.objects.none()

        ###### Search for Manager ##########
        if search_type == '1':
            users = User.objects.filter(role_id=5, is_deleted=False)
        ###### Search for Coaching Staff ##########
        elif search_type == '2':
            users = User.objects.filter(role_id=3, is_deleted=False)
        ####### Search For Medical Staff##################            
        elif search_type == '3':
            users = User.objects.filter(role_id=5, is_deleted=False)
        ###### Search for Player ##########
        elif search_type == '4':
            users = User.objects.filter(role_id__in=[5, 2], is_deleted=False)


        # Filter by phone if provided
        users = users.filter(phone__icontains=phone)

        # Exclude users who have already joined the specified branch
        if branch_id:
            joined_users = JoinBranch.objects.filter(branch_id=branch_id).values_list('user_id', flat=True)
            users = users.exclude(id__in=joined_users)

        # Apply pagination
        paginator = self.pagination_class()
        paginated_users = paginator.paginate_queryset(users, request)

        # Construct the response data manually
        user_data = [
            {
                'id': user.id,
                'username': user.username,
                'phone': user.phone,
                'profile_picture': user.profile_picture.url if user.profile_picture else None,
                'country_id': user.country.id if user.country else None,
                'country_name': user.country.name if user.country else None,
                'flag': user.country.flag.url if user.country else None,

            }
            for user in paginated_users
        ]

        # Return paginated response with custom data
        return paginator.get_paginated_response(user_data)



class TeamStatsView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        team_id = request.query_params.get('team_id')
        years_param = request.query_params.get('years', '0')  # Default to '0' (all-time data)

        if not team_id:
            return Response({
                'status': 0,
                'message': _('team_id is required'),
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Step 1: Parse years parameter
        try:
            years = [int(year.strip()) for year in years_param.split(',') if year.strip().isdigit()]
            if years and any(year < 0 for year in years):
                raise ValueError("Year cannot be negative.")
        except ValueError:
            return Response({
                "status": 0,
                "message": _("Invalid value for 'years'. Please provide a comma-separated list of valid years."),
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        # If no specific years or "0" is provided, fetch all-time data
        if not years or 0 in years:
            time_filter = {}
        else:
            time_filter = {"created_at__year__in": years}

        # Step 2: Fetch all team branches for the given team_id
        all_team_branches = TeamBranch.objects.filter(team_id=team_id)

        if not all_team_branches.exists():
            return Response({
                'status': 1,
                'message': _('No Team found for the given team ID.'),
                'data': []
            }, status=status.HTTP_200_OK)

        team_branch_data = []

        for team_branch in all_team_branches:
            # Step 3: Aggregate statistics for Tournament Games
            tournament_stats = PlayerGameStats.objects.filter(
                team_id=team_branch.id, **time_filter
            ).aggregate(
                total_goals=Sum('goals') or 0,
                total_assists=Sum('assists') or 0,
                total_yellow_cards=Sum('yellow_cards') or 0,
                total_red_cards=Sum('red_cards') or 0
            )

            tournament_games = TournamentGames.objects.filter(
                (Q(team_a=team_branch) | Q(team_b=team_branch)), **time_filter
            )

            tournament_total_games = tournament_games.count()
            tournament_total_wins = tournament_games.filter(winner_id=str(team_branch.id)).count()
            tournament_total_losses = tournament_games.filter(loser_id=str(team_branch.id)).count()
            tournament_total_draws = tournament_games.filter(is_draw=True).count()

            tournament_conceded_goals = tournament_games.aggregate(
                total_conceded=Sum(
                    Case(
                        When(team_a=team_branch, then='team_b_goal'),
                        When(team_b=team_branch, then='team_a_goal'),
                        default=0,
                        output_field=models.IntegerField()
                    )
                )
            )['total_conceded'] or 0

            # Step 4: Aggregate statistics for Friendly Games
            friendly_stats = FriendlyGamesPlayerGameStats.objects.filter(
                team_id=team_branch.id, **time_filter
            ).aggregate(
                total_goals=Sum('goals') or 0,
                total_assists=Sum('assists') or 0,
                total_yellow_cards=Sum('yellow_cards') or 0,
                total_red_cards=Sum('red_cards') or 0
            )

            friendly_games = FriendlyGame.objects.filter(
                (Q(team_a=team_branch) | Q(team_b=team_branch)), **time_filter
            )

            friendly_total_games = friendly_games.count()
            friendly_total_wins = friendly_games.filter(winner_id=str(team_branch.id)).count()
            friendly_total_losses = friendly_games.filter(loser_id=str(team_branch.id)).count()
            friendly_total_draws = friendly_games.filter(is_draw=True).count()

            friendly_conceded_goals = friendly_games.aggregate(
                total_conceded=Sum(
                    Case(
                        When(team_a=team_branch, then='team_b_goal'),
                        When(team_b=team_branch, then='team_a_goal'),
                        default=0,
                        output_field=models.IntegerField()
                    )
                )
            )['total_conceded'] or 0

            # Step 5: Combine statistics from Tournament and Friendly Games
            total_goals = (tournament_stats['total_goals'] or 0) + (friendly_stats['total_goals'] or 0)
            total_assists = (tournament_stats['total_assists'] or 0) + (friendly_stats['total_assists'] or 0)
            total_yellow_cards = (tournament_stats['total_yellow_cards'] or 0) + (friendly_stats['total_yellow_cards'] or 0)
            total_red_cards = (tournament_stats['total_red_cards'] or 0) + (friendly_stats['total_red_cards'] or 0)

            total_games = tournament_total_games + friendly_total_games
            total_wins = tournament_total_wins + friendly_total_wins
            total_losses = tournament_total_losses + friendly_total_losses
            total_draws = tournament_total_draws + friendly_total_draws
            total_conceded_goals = tournament_conceded_goals + friendly_conceded_goals

            team_branch_data.append({
                "team_branch_id": team_branch.id,
                "team_name": team_branch.team_name,
                "age_group": team_branch.age_group_id.name_en if language == 'en' else team_branch.age_group_id.name_ar,
                "team_stats": {
                    "total_goals": total_goals,
                    "total_assists": total_assists,
                    "total_yellow_cards": total_yellow_cards,
                    "total_red_cards": total_red_cards,
                    "total_games_played": total_games,
                    "total_wins": total_wins,
                    "total_losses": total_losses,
                    "total_draws": total_draws,
                    "total_conceded_goals": total_conceded_goals
                }
            })

        return Response({
            'status': 1,
            'message': _('Data fetched successfully.'),
            'data': team_branch_data
        }, status=status.HTTP_200_OK)
