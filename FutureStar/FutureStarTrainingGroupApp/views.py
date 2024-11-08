from django.utils.translation import gettext as _
from django.utils.translation import activate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from FutureStarTrainingGroupApp.serializers import *
from rest_framework.permissions import IsAuthenticated

from FutureStar_App.models import *
from FutureStarTeamApp.models import *
from FutureStarAPI.models import *
from FutureStarTournamentApp.models import *
from FutureStarTrainingGroupApp.models import *


from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.utils import timezone
from django.core.files.storage import default_storage
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator, EmptyPage

#################################################################### Training Group API #####################################################################################
class TrainingGroupAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    # 1. Get Group Detail by ID
    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)   
        group_id = request.query_params.get('group_id')
        if not group_id:
            return Response({
                'status': 0, 
                'message': _('Group ID is required.')
                },status=status.HTTP_400_BAD_REQUEST)
        
        try:
            group = TrainingGroups.objects.get(id=group_id)
            serializer = TrainingGroupSerializer(group, context={'request': request})
            return Response({
                'status': 1,
                'message': _('Group details retrieved successfully.'),
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except TrainingGroups.DoesNotExist:
            return Response({
                'status': 0, 
                'message': _('Group not found.')
                }, status=status.HTTP_404_NOT_FOUND)
    
    # 2. Create a Group
    def post(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        user = request.user
        try:
            # Check if the user has already created a team
            if TrainingGroups.objects.filter(group_founder=user).exists():
                return Response({
                    'status': 0,
                    'message': _('You can only create one Training Group.')
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log the exception and return an error response
            print(f"Error checking existing group: {e}")
            return Response({
                'status': 0,
                'message': _('An error occurred while checking your existing Training Groups.')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Check if team_username already exists in either the Team or User model
        group_username = request.data.get('group_username')
        if Team.objects.filter(team_username=group_username).exists() or User.objects.filter(username=group_username) or TrainingGroups.objects.filter(group_username=group_username).exists():
            return Response({
                'status': 0, 
                'message': _('The username is already Taken.')}, 
                status=status.HTTP_400_BAD_REQUEST)

        # Proceed with creating the group if no group exists for this user
        data = request.data.copy()
        data['group_founder'] = user.id
        serializer = TrainingGroupSerializer(data=data)

        if serializer.is_valid():
            group = serializer.save(group_founder=user, created_at=timezone.now(), updated_at=timezone.now())

            # Handle group_logo upload
            if 'group_logo' in request.FILES:
                logo = request.FILES['group_logo']
                file_extension = logo.name.split('.')[-1]
                file_name = f"group/group_logo/{group.id}_{get_random_string(8)}.{file_extension}"
                logo_path = default_storage.save(file_name, logo)
                group.group_logo = logo_path

            # Handle group_background_image upload
            if 'group_background_image' in request.FILES:
                background_image = request.FILES['group_background_image']
                file_extension = background_image.name.split('.')[-1]
                file_name = f"group/group_background_image/{group.id}_{get_random_string(8)}.{file_extension}"
                background_image_path = default_storage.save(file_name, background_image)
                group.group_background_image = background_image_path

            group.save()  # Save logo and background image fields
            return Response({
                'status': 1,
                'message': _('Group created successfully.'),
                'data': TrainingGroupSerializer(group).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 0,
            'message': _('Failed to create group.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    
    # 3. Update Group Logo and Background Image
    def patch(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        group_id = request.data.get('group_id')
        if not group_id:
            return Response({
                'status': 0, 
                'message': _('Group ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            group = TrainingGroups.objects.get(id=group_id, group_founder=request.user)
            
            # Update group fields based on request data, retaining old values if not provided
            fields_to_update = [
                'group_name', 'group_username', 'bio', 'latitude', 'longitude',
                'address', 'house_no', 'premises', 'street', 'city',
                'state', 'country_name', 'postalCode', 'country_code', 'phone'
            ]

            for field in fields_to_update:
                new_value = request.data.get(field)
                if new_value is not None:  # Only update if a new value is provided
                    setattr(group, field, new_value)

            # Handle group_logo update and delete old one if exists
            if 'group_logo' in request.FILES:
                if group.group_logo and default_storage.exists(group.group_logo.name):
                    default_storage.delete(group.group_logo.name)
                logo = request.FILES['group_logo']
                file_extension = logo.name.split('.')[-1]
                file_name = f"group/group_logo/{group_id}_{get_random_string(8)}.{file_extension}"
                logo_path = default_storage.save(file_name, logo)
                group.group_logo = logo_path

            # Handle group_background_image update
            if 'group_background_image' in request.FILES:
                if group.group_background_image and default_storage.exists(group.group_background_image.name):
                    default_storage.delete(group.group_background_image.name)
                background_image = request.FILES['group_background_image']
                file_extension = background_image.name.split('.')[-1]
                file_name = f"group/group_background_image/{group_id}_{get_random_string(8)}.{file_extension}"
                background_image_path = default_storage.save(file_name, background_image)
                group.group_background_image = background_image_path

            # No need to get user from request data; it's already part of the group
            user = group.group_founder  

            group.updated_at = timezone.now()  # Set updated_at to the current time
            group.save()  # Save the group instance

            return Response({
                'status': 1,
                'message': _('Group updated successfully.'),
                'data': {
                    'group_id': group.id,
                    'group_name': group.group_name,
                    'group_username': group.group_username,
                    'group_founder': {
                        'username': user.username,
                        'fullname': user.fullname,
                        'phone': user.phone,
                        'email': user.email,
                        'profile_pic': user.profile_picture.url if user.profile_picture else None,  # Use the correct field name
                    },
                    'bio': group.bio,
                    'latitude': group.latitude,
                    'longitude': group.longitude,
                    'address': group.address,
                    'house_no': group.house_no,
                    'premises': group.premises,
                    'street': group.street,
                    'city': group.city,
                    'state': group.state,
                    'country_name': group.country_name,
                    'postalCode': group.postalCode,
                    'country_code': group.country_code,
                    'phone': group.phone,
                    'group_logo': group.group_logo.url if group.group_logo else None,
                    'group_background_image': group.group_background_image.url if group.group_background_image else None,
                    'updated_at': group.updated_at,
                }
            }, status=status.HTTP_200_OK)

        except TrainingGroups.DoesNotExist:
            return Response({
                'status': 0, 
                'message': _('Group not found or you are not the founder.')
            }, status=status.HTTP_404_NOT_FOUND)





################ Pagination ##################
class MemberSearchPagination(PageNumberPagination):
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
                'message': _('Invalid page number.'),
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


class SearchMemberView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = MemberSearchPagination

    def get(self, request):
        phone = request.query_params.get('phone')
        group_id = request.query_params.get('group_id')

        # Validate required parameters
        if not group_id:
            return Response({
                'status': 0,
                'message': 'Group ID is required.'
            }, status=400)

        # Initialize queryset for members with role_id = 5
        users = User.objects.filter(role_id=5)

        # Filter by phone if provided
        if phone:
            users = users.filter(phone__icontains=phone)

        # Exclude users who have already joined the specified group
        joined_users = JoinTrainingGroup.objects.filter(group_id=group_id).values_list('member_id', flat=True)
        users = users.exclude(id__in=joined_users)

        # Apply pagination
        paginator = self.pagination_class()
        paginated_users = paginator.paginate_queryset(users, request)

        # Construct response data
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



###################### Member and Organizer List ######################

class GroupMembersView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request):
        group_id = request.query_params.get('group_id')
        
        # Validate group_id
        if not group_id:
            return Response({
                'status': 0,
                'message': 'Group ID is required.'
            }, status=400)
        
        # Fetch all entries for the specified group
        group_members = JoinTrainingGroup.objects.filter(group_id=group_id)
        
        # Separate members and organizers
        members_data = []
        organizers_data = []
        
        for member in group_members:
            user_data = {
                'id': member.member_id.id,
                'username': member.member_id.username,
                'phone': member.member_id.phone,
                'profile_picture': member.member_id.profile_picture.url if member.member_id.profile_picture else None,
                'country_id': member.member_id.country.id if member.member_id.country else None,
            }
            if member.JoinTrainingGroup_type == JoinTrainingGroup.ORGANIZER:
                organizers_data.append(user_data)
            else:
                members_data.append(user_data)
        
        # Return response with separate lists for members and organizers
        return Response({
            'status': 1,
            'message': 'Group members fetched successfully.',
            'data': {
                'members': members_data,
                'organizers': organizers_data
            }
        })
    
######### Group Membership ######################
class GroupMembersAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Add a member or organizer to a group.
        """
        user_id = request.data.get('user_id')
        group_id = request.data.get('group_id')
        join_type = int(request.data.get('JoinTrainingGroup_type', JoinTrainingGroup.MEMBER))  # Default to MEMBER if not provided

        # Validate inputs
        if not user_id or not group_id:
            return Response({
                'status': 0,
                'message': 'User ID and Group ID are required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the user and group
        try:
            user = User.objects.get(id=user_id)
            group = TrainingGroups.objects.get(id=group_id)
        except User.DoesNotExist:
            return Response({'status': 0, 'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except TrainingGroups.DoesNotExist:
            return Response({'status': 0, 'message': 'Group not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is already in the group
        existing_membership = JoinTrainingGroup.objects.filter(member_id=user, group_id=group).first()

        if existing_membership:
            # If the user is already an organizer, prevent any changes
            if existing_membership.JoinTrainingGroup_type == JoinTrainingGroup.ORGANIZER:
                return Response({
                    'status': 0,
                    'message': 'User is already an organizer and cannot be changed to a member.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # If the user is a member and wants to be upgraded to organizer
            if join_type == JoinTrainingGroup.ORGANIZER:
                existing_membership.JoinTrainingGroup_type = JoinTrainingGroup.ORGANIZER
                existing_membership.save()
                return Response({
                    'status': 1,
                    'message': 'User upgraded to organizer in the group.'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 0,
                    'message': 'User is already a member of this group.'
                }, status=status.HTTP_400_BAD_REQUEST)

        # If the user is not already a member or organizer, create a new record
        JoinTrainingGroup.objects.create(
            member_id=user,
            group_id=group,
            JoinTrainingGroup_type=join_type
        )

        role = "Organizer" if join_type == JoinTrainingGroup.ORGANIZER else "Member"
        return Response({
            'status': 1,
            'message': f'User added as {role} to the group.'
        }, status=status.HTTP_201_CREATED)

    def delete(self, request):
        """
        Delete a member from a group, but not if they are an organizer.
        """
        user_id = request.query_params.get('user_id')
        group_id = request.query_params.get('group_id')

        # Validate inputs
        if not user_id or not group_id:
            return Response({
                'status': 0,
                'message': 'User ID and Group ID are required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the membership record
        try:
            membership = JoinTrainingGroup.objects.get(member_id=user_id, group_id=group_id)
        except JoinTrainingGroup.DoesNotExist:
            return Response({
                'status': 0,
                'message': 'Membership not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is an organizer
        if membership.JoinTrainingGroup_type == JoinTrainingGroup.ORGANIZER:
            return Response({
                'status': 0,
                'message': 'Cannot delete an organizer from the group.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Delete the member
        membership.delete()
        return Response({
            'status': 1,
            'message': 'Member deleted successfully.'
        }, status=status.HTTP_200_OK)