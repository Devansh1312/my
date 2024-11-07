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

from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.utils import timezone
from django.core.files.storage import default_storage
from django.utils.crypto import get_random_string
from django.utils.timezone import now


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
        request.data['group_founder'] = request.user.id  # Set the logged-in user as the group founder
        serializer = TrainingGroupSerializer(data=request.data)
        
        if serializer.is_valid():
            group = serializer.save(created_at=now(), updated_at=now())

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
        else:
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

