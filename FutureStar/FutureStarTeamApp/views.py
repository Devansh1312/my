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
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator, EmptyPage
from django.db import IntegrityError


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
                'message': _('Field created successfully.'),
                'data': TeamBranchSerializer(team_branch_instance).data
            }, status=status.HTTP_201_CREATED)
        
        # Return an error response if validation fails
        return Response({
            'status': 0,
            'message': _('Team Branch creation failed.'),
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
                'message': _('Team Branch ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the TeamBranch instance associated with the team_id
        try:
            team_branch_instance = TeamBranch.objects.get(id=team_branch_id)
        except TeamBranch.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('No TeamBranch found for the given ID.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Serialize and return the TeamBranch data
        serializer = TeamBranchSerializer(team_branch_instance, context={'request': request})
        return Response({
            'status': 1,
            'message': _('TeamBranch retrieved successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        


class StaffManagementView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def get(self, request):
        branch_id = request.query_params.get('branch_id')
        if not branch_id:
            return Response({'status': 0, 'message': _('branch_id is required')}, status=status.HTTP_400_BAD_REQUEST)

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
        branch_id = request.data.get('branch_id')
        user_id = request.data.get('user_id')
        joinning_type = request.data.get('joinning_type')

        if not branch_id or not user_id or joinning_type is None:
            return Response({
                'status': 0, 
                'message': _('branch_id, user_id, and joinning_type are required')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Convert joinning_type to an integer and validate it
        try:
            joinning_type = int(joinning_type)
        except (ValueError, TypeError):
            return Response({
                'status': 0,
                'message': _('Please provide a valid joinning type')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate joinning_type to accept only values 1, 2, 3, or 4
        if joinning_type not in [1, 2, 3, 4]:
            return Response({
                'status': 0,
                'message': _('Please provide a valid joinning type.')
            }, status=status.HTTP_400_BAD_REQUEST)

        join_branch_data = {
            'branch_id': branch_id,
            'user_id': user_id,
            'joinning_type': joinning_type
        }

        serializer = JoinBranchSerializer(data=join_branch_data)
        if serializer.is_valid():
            try:
                serializer.save()
                # Set success message based on joinning_type
                if joinning_type in [JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE, JoinBranch.MEDICAL_STAFF_TYPE]:
                    success_message = _('Staff added successfully.')
                elif joinning_type == JoinBranch.PLAYER_TYPE:
                    success_message = _('Player added successfully.')

                return Response({
                    'status': 1,
                    'message': success_message,
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response({
                    'status': 0,
                    'message': _('User has already joined this branch.')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 0,
            'message': _('Failed to add staff/player.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)





################ Pagination ##################
# Custom Pagination class with fixed paginate_queryset
class CustomUserSearchPagination(PageNumberPagination):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    page_size = 10
    page_query_param = 'page'
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        try:
            page_number = request.query_params.get(self.page_query_param, 1)
            self.page = int(page_number)
            if self.page < 1:
                raise ValidationError("Page number must be a positive integer.")
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
        return Response({
            'status': 1,
            'message': 'Data fetched successfully.',
            'total_records': self.total_records,
            'total_pages': self.total_pages,
            'current_page': self.page,
            'data': data
        })
    

class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = CustomUserSearchPagination  # Set the pagination class

    def get(self, request):
        search_type = request.query_params.get('search_type')
        phone = request.query_params.get('phone')
        branch_id = request.query_params.get('branch_id')  # Get branch_id from request

        # Check for valid search_type, comparing with string values
        if search_type not in ['1', '2']:
            return Response({'status': 0, 'message': _('Invalid search type. Must be 1 or 2.')}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize a queryset
        users = User.objects.none()

        if search_type == '1':
            users = User.objects.filter(role_id=5)
        elif search_type == '2':
            users = User.objects.filter(role_id__in=[5, 2])

        # Filter by phone if provided
        if phone:
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
            }
            for user in paginated_users
        ]

        # Return paginated response with custom data
        return paginator.get_paginated_response(user_data)