from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from FutureStar.firebase_config import send_push_notification
from .models import *
from .serializers import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.utils.translation import gettext as _
from django.utils.crypto import get_random_string
from django.utils.translation import activate 
from django.core.files.storage import default_storage
from datetime import date
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
import json

class CreateTrainingView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')

        if language in ['en', 'ar']:
            activate(language)

        creator_type = request.data.get('creator_type', None)
        created_by_id = request.data.get('created_by_id', None)
        repeat_type = int(request.data.get('repeat_type', 2))  # Default to single if not provided
        days = request.data.get('Days', '[]')
        if isinstance(days, str):
            days = json.loads(days)  # Expected to be a list of integers [1,2,...7]
        start_times = request.data.get('start_time', '[]')
        end_times = request.data.get('end_time', '[]')
        end_date = request.data.get('end_date', None)

        creator_type = int(creator_type)
        created_by_id = int(created_by_id)

        context = {'request': request}
        serializer = TrainingSerializer(data=request.data, context=context)

        if serializer.is_valid():
            # Handle image saving logic if training photo is uploaded
            if "training_photo" in request.FILES:
                image = request.FILES["training_photo"]
                file_extension = image.name.split('.')[-1]
                unique_suffix = get_random_string(8)
                file_name = f"training_photo/{request.user.id}_{unique_suffix}.{file_extension}"
                image_path = default_storage.save(file_name, image)
                serializer.validated_data['training_photo'] = image_path

            training_instances = []

            if repeat_type == 2:  # Single training
                training_instance = serializer.save()
                training_instances.append(training_instance)

            elif repeat_type == 1:  # Multiple training
                if not end_date or not days or not start_times or not end_times:
                    return Response({
                        'status': 0,
                        'message': _('End date, Days, Start time, and End time are required for repeat_type 1.')
                    }, status=status.HTTP_400_BAD_REQUEST)

                try:
                    start_date = serializer.validated_data['training_date']
                    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                    current_date = start_date

                    # Custom weekday mapping
                    weekday_mapping = {
                        0: 2,  # Monday -> 2
                        1: 3,  # Tuesday -> 3
                        2: 4,  # Wednesday -> 4
                        3: 5,  # Thursday -> 5
                        4: 6,  # Friday -> 6
                        5: 7,  # Saturday -> 7
                        6: 1   # Sunday -> 1
                    }

                    while current_date <= end_date:
                        if weekday_mapping.get(current_date.weekday()) in map(int, days):  # Adjust weekday mapping
                            # Get index for the day to assign corresponding start_time and end_time
                            day_index = days.index(weekday_mapping.get(current_date.weekday()))
                            training_data = serializer.validated_data.copy()
                            training_data['training_date'] = current_date
                            training_data['start_time'] = start_times[day_index]
                            training_data['end_time'] = end_times[day_index]
                            training_instance = Training.objects.create(**training_data)
                            training_instances.append(training_instance)

                        current_date += timedelta(days=1)

                except Exception as e:
                    return Response({
                        'status': 0,
                        'message': _('Invalid data for creating multiple trainings.'),
                        'error': str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)

            for training_instance in training_instances:
                if creator_type == 1:  # User
                    Training_Joined.objects.create(
                        training=training_instance,
                        user=request.user,
                        attendance_status=False  # Default attendance status
                    )
                elif creator_type == 2:  # Team
                    try:
                        team = Team.objects.get(id=created_by_id)
                        team_founder = team.team_founder
                        if team_founder:
                            Training_Joined.objects.create(
                                training=training_instance,
                                user=team_founder,
                                attendance_status=False
                            )
                    except Team.DoesNotExist:
                        return Response({
                            'status': 0,
                            'message': _('No team found with the provided ID.')
                        }, status=status.HTTP_404_NOT_FOUND)

            training_serializer = TrainingSerializer(
                training_instances, many=True, context={'request': request}
            )
            return Response({
                'status': 1,
                'message': _('Trainings successfully created'),
                'data': training_serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 0,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# class CreateTrainingView(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = [MultiPartParser, FormParser]

#     def post(self, request, *args, **kwargs):
#         language = request.headers.get('Language', 'en')

#         if language in ['en', 'ar']:
#             activate(language)

#         creator_type = request.data.get('creator_type', None)
#         created_by_id = request.data.get('created_by_id', None)

#         creator_type = int(creator_type)
#         created_by_id = int(created_by_id)

#         context = {'request': request}
#         serializer = TrainingSerializer(data=request.data, context=context)


#         if serializer.is_valid():


#             # Handle image saving logic if training photo is uploaded
#             if "training_photo" in request.FILES:
#                 image = request.FILES["training_photo"]
#                 file_extension = image.name.split('.')[-1]
#                 unique_suffix = get_random_string(8)
#                 file_name = f"training_photo/{request.user.id}_{unique_suffix}.{file_extension}"
#                 image_path = default_storage.save(file_name, image)
#                 serializer.validated_data['training_photo'] = image_path
#             training_instance = serializer.save()

#             if creator_type == 1:  # User
#                 Training_Joined.objects.create(
#                     training=training_instance,
#                     user=request.user,
#                     attendance_status=False  # Default attendance status
#                 )
#             elif creator_type == 2:  # Team
#                 try:
#                     team = Team.objects.get(id=created_by_id)
#                     team_founder = team.team_founder
#                     if team_founder:
#                         Training_Joined.objects.create(
#                             training=training_instance,
#                             user=team_founder,
#                             attendance_status=False
#                         )
#                 except Team.DoesNotExist:
#                     return Response({
#                         'status': 0,
#                         'message': _('No team found with the provided ID.')
#                     }, status=status.HTTP_404_NOT_FOUND)

#             training_instance = Training.objects.get(id=training_instance.id)
#             serializer = TrainingSerializer(training_instance, context={'request': request})
#             return Response({
#                 'status': 1,
#                 'message': _('Training successfully created'),
#                 'data': serializer.data  # Use the re-serialized data with language context
#             }, status=status.HTTP_201_CREATED)
#         return Response({
#             'status': 0,
#             'errors': serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)


##################### Get trainings Details ##################################
    

class TrainingDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Fetch the training using the training_id from the query parameters
        training_id = request.query_params.get('training_id')

        if not training_id:
            return Response({
                'status': 0,
                'message': _('Training ID is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the training object using the provided tournament_id
            training = Training.objects.get(id=training_id)
            
            # Serialize the training data
            serializer = TrainingSerializer(training, context={'request': request})

            # Format the response as required
            return Response({
                'status': 1,
                'message': _('Training details fetched successfully.'),
                'data':  serializer.data,
               
            }, status=status.HTTP_200_OK)

        except Training.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Training not found.'),
            }, status=status.HTTP_404_NOT_FOUND)

###################### Edit Training ############################

    def get_object(self, training_id):
            try:
                # Retrieve the training instance by ID
                return Training.objects.get(id=training_id)
            except Training.DoesNotExist:
                return None
            
            
    def patch(self, request, *args, **kwargs):
        # Retrieve the training ID from the request data (in request.data)
        training_id = request.data.get('training_id')

        if not training_id:
            return Response({
                'status': 0,
                'message': _('Training ID is required for update'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the training instance to update
        training_instance = self.get_object(training_id)

        if not training_instance:
            return Response({
                'status': 0,
                'message': _('Training not found'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        # Pass the full 'request' object in the context
        context = {'request': request}

        # Initialize the serializer with the current instance and the updated data
        serializer = TrainingSerializer(training_instance, data=request.data, partial=True, context=context)

        if serializer.is_valid():
            # Handle image saving logic if a new training photo is uploaded
            if "training_photo" in request.FILES:
                image = request.FILES["training_photo"]
                file_extension = image.name.split('.')[-1]
                unique_suffix = get_random_string(8)
                file_name = f"training_photo/{request.user.id}_{unique_suffix}.{file_extension}"

                # Save the image using the default storage
                image_path = default_storage.save(file_name, image)
                serializer.validated_data['training_photo'] = image_path

            # Save the updated training instance
            updated_training_instance = serializer.save()

            # Re-fetch the training instance with the correct context for language handling
            updated_training_instance = Training.objects.get(id=updated_training_instance.id)

            # Re-serialize the updated training instance
            serializer = TrainingSerializer(updated_training_instance, context={'request': request})

            # Return the successfully updated training data
            return Response({
                'status': 1,
                'message': _('Training successfully updated'),
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        # If validation fails, return the errors
        return Response({
            'status': 0,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

###################### Delete Training ############################
    def delete(self, request, *args, **kwargs):
        # Retrieve the training ID from the query parameters
        training_id = request.query_params.get('training_id')

        if not training_id:
            return Response({
                'status': 0,
                'message': _('Training ID is required for deletion'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the training instance to delete
        training_instance = self.get_object(training_id)

        if not training_instance:
            return Response({
                'status': 0,
                'message': _('Training not found'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        # Delete the training instance
        training_instance.delete()

        # Return a success response
        return Response({
            'status': 1,
            'message': _('Training successfully deleted'),
            'data': []
        }, status=status.HTTP_204_NO_CONTENT) 

###################### Training LIKE ##################################
class TrainingLikeAPIView(APIView):
    parser_classes=[MultiPartParser, FormParser,JSONParser]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        training_id = request.data.get('training_id')

        if not training_id:
            return Response({
                'status': 0,
                'message': _('Training ID is required.')
            }, status=400)

        try:
            training = Training.objects.get(id=training_id)
        except Training.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Training not found.')
            }, status=404)

        # Toggle like/unlike
        creator_type = request.data.get('creator_type')
        created_by_id = request.data.get('created_by_id', request.user.id)  # Default to logged-in user ID

        training_like, created = TrainingLike.objects.get_or_create(created_by_id=created_by_id, training=training, creator_type=creator_type)
        
        if not created:
            # If the user already liked the Training, unlike it (delete the like)
            training_like.delete()
            message = _('Training unliked successfully.')
        else:
            message = _('Training liked successfully.')

        # Serialize the Training data with comments set to empty
        serializer = TrainingSerializer(training, context={'request': request})
        
        # Return the full Training data with an empty comment list
        return Response({
            'status': 1,
            'message': message,
            'data': serializer.data
        }, status=200)
    

################################## Pagination ##############################
class CustomTrainingPagination(PageNumberPagination):
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    page_size = 10  # Number of records per page
    page_query_param = 'page'  # Custom page number param in the body
    page_size_query_param = 'page_size'
    max_page_size = 100  # Set max size if needed

    def paginate_queryset(self, queryset, request, view=None):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Get the page number from the body (default: 1)
        try:
            # Try to fetch and validate the page number
            page_number = request.data.get(self.page_query_param, 1)
            self.page = int(page_number)
            if self.page < 1:
                raise ValidationError(_("Page number must be a positive integer."))
        except (ValueError, TypeError):
            # If the page number is invalid, return a custom error response
            return Response({
                'status': 0,
                'message': _('Page Not Found'),
                'data': []
            }, status=400)

        # Get total number of pages based on the queryset
        paginator = self.django_paginator_class(queryset, self.get_page_size(request))
        total_pages = paginator.num_pages

        # Check if the requested page number is out of range
        if self.page > total_pages:
            # Return custom response for an invalid page
            return Response({
                'status': 0,
                'message': _('Page Not Found'),
                'data': []
            }, status=400)

        # Perform standard pagination if the page is valid
        return super().paginate_queryset(queryset, request, view)
    
################################ Get comment API #############################
class TrainingCommentPagination(CustomTrainingPagination):
    def paginate_queryset(self, queryset, request, view=None):
        return super().paginate_queryset(queryset, request, view)

class TrainingCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Validate training_id from request data
        training_id = request.data.get('training_id')
        training_id = int(training_id)
        if not training_id:
            return Response({
                'status': 0,
                'message': _('Training ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            training = Training.objects.get(id=training_id)
        except Training.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Training not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Get only top-level comments (parent=None) for the post
        top_level_comments = Training_comment.objects.filter(training=training, parent=None).order_by('-date_created')

        # Paginate the comments
        paginator = TrainingCommentPagination()
        paginated_comments = paginator.paginate_queryset(top_level_comments, request)

        # If pagination fails or no comments are found
        if paginated_comments is None:
            return Response({
                'status': 1,
                'message': _('No comments found for this Training.'),
                'data': {
                    'total_records': 0,
                    'total_pages': 0,
                    'current_page': 1,
                    'results': []
                }
            }, status=status.HTTP_200_OK)

        # Serialize the paginated comments
        serializer = TrainingCommentSerializer(paginated_comments, many=True, context={'request': request})

        # Return paginated response
        return Response({
            'status': 1,
            'message': _('Comments fetched successfully.'),
            'data': serializer.data,
            'total_records': top_level_comments.count(),
            'total_pages': paginator.page.paginator.num_pages,
            'current_page': paginator.page.number,
        }, status=status.HTTP_200_OK)



######################## COMMNET CREATE API ###########################
class TrainingCommentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        data = request.data
        training_id = data.get('training_id')
        comment_text = data.get('comment')
        parent_id = data.get('parent_id')
        created_by_id = data.get('created_by_id')
        creator_type = data.get('creator_type')

        # Validate the required fields
        if not training_id or not comment_text or not created_by_id or not creator_type:
            return Response({
                'status': 0,
                'message': _('training_id, comment, created_by_id and creator_type are required.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate training_id from request data
        training_id = request.data.get('training_id')
        training_id = int(training_id)

        try:
            training_id = Training.objects.get(id=training_id)
        except Training.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Training not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate parent comment if provided
        parent_comment = None
        if parent_id:
            try:
                parent_comment = Training_comment.objects.get(id=parent_id)
            except Training_comment.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Parent comment not found.')
                }, status=status.HTTP_404_NOT_FOUND)

        # Create the comment using the new fields
        comment = Training_comment.objects.create(
            created_by_id=created_by_id,
            creator_type=creator_type,
            training=training_id,
            comment=comment_text,
            parent=parent_comment
        )

        return Response({
            'status': 1,
            'message': _('Comment created successfully.'),
            'data': TrainingCommentSerializer(comment).data
        }, status=status.HTTP_201_CREATED)



#### VIEW TO RETRIEVE ALL OPEN TRAININGS FOR THE USER  ####
class OpenTrainingListView(APIView):
    def get(self, request, *args, **kwargs):
        # Get today's date
        today = date.today()

        # Query all open training sessions that have not passed
        open_trainings = Training.objects.filter(
            training_type=Training.OPEN_TRAINING,
            training_date__gte=today  # Only future or today
        ).order_by('-training_date')

        creator_type = request.query_params.get('creator_type')
        created_by_id = request.query_params.get('created_by_id')

        notification_count = Notifictions.objects.filter(targeted_id=created_by_id, targeted_type=creator_type,read=False).count()


        # Initialize custom pagination
        paginator = CustomTrainingPagination()

        # Paginate the queryset
        paginated_trainings = paginator.paginate_queryset(open_trainings, request)
        if paginated_trainings is not None:
            # Serialize the paginated data
            serializer = TrainingListSerializer(paginated_trainings, many=True, context={'request': request})

            # Prepare the pagination data
            pagination_data = {
                'total_records': open_trainings.count(),
                'total_pages': paginator.page.paginator.num_pages,
                'current_page': paginator.page.number
            }

            # Return paginated data in the response, with the serialized data directly under 'data'
            return Response({
                'status': 1,
                'message': "Open trainings retrieved successfully",
                'data': {
                    **pagination_data,
                    'trainings': serializer.data  # Put serialized data directly here
                },
                'notification_count': notification_count  # Include the notification count in the response
            }, status=status.HTTP_200_OK)

        # If pagination is not applied, just return the serialized data
        serializer = TrainingListSerializer(open_trainings, many=True, context={'request': request})
        return Response({
            'status': 1,
            'message': "Open trainings retrieved successfully",
            'data': {
                'total_records': open_trainings.count(),
                'total_pages': 1,
                'current_page': 1,
                'trainings': serializer.data  # Put serialized data directly here
            },
            'notification_count': notification_count  # Include the notification count in the response
        }, status=status.HTTP_200_OK)
    


###### My Created Training List API ######
class MyTrainingsView(APIView):
    def get(self, request, *args, **kwargs):
        # Retrieve the logged-in user ID
        user = request.user.id

        # Get all trainings initially
        trainings = Training.objects.all().order_by('-training_date')

        # Filter trainings based on access logic
        accessible_trainings = []
        for training in trainings:
            if self._has_access(training, user):
                accessible_trainings.append(training)

        # Sort the trainings by `training_date` in descending order
        accessible_trainings = sorted(accessible_trainings, key=lambda t: t.training_date, reverse=True)

        # Apply custom pagination
        paginator = CustomTrainingPagination()

        # Paginate the accessible trainings
        paginated_trainings = paginator.paginate_queryset(accessible_trainings, request)
        if paginated_trainings is not None:
            # Serialize the paginated data
            serializer = TrainingListSerializer(paginated_trainings, many=True, context={'request': request})

            # Prepare pagination metadata
            pagination_data = {
                'total_records': len(accessible_trainings),
                'total_pages': paginator.page.paginator.num_pages,
                'current_page': paginator.page.number,
                'data': serializer.data
            }

            # Return paginated response
            return Response({
                'status': 1,
                'message': 'Trainings retrieved successfully',
                'data': pagination_data
            }, status=status.HTTP_200_OK)

        # If pagination is not applied, return all serialized data
        serializer = TrainingListSerializer(accessible_trainings, many=True, context={'request': request})
        return Response({
            'status': 1,
            'message': 'Trainings retrieved successfully',
            'data': {
                'total_records': len(accessible_trainings),
                'total_pages': 1,
                'current_page': 1,
                'data': serializer.data
            }
        }, status=status.HTTP_200_OK)
    
    def _has_access(self, training, user):

        # Case 1: Creator type is USER_TYPE
        if training.creator_type == 1:
            if training.created_by_id == user:  # Request user is the creator
                return True

            # Check if the request user is in the same branch as the creator
            creator_branches = JoinBranch.objects.filter(
                user_id=training.created_by_id,
                joinning_type=4
            ).values_list('branch_id', flat=True)

            user_branch = JoinBranch.objects.filter(
                user_id=user
            ).values_list('branch_id', flat=True)

            if not creator_branches:
                return False

            request_user_branches = JoinBranch.objects.filter(
                user_id=user,
                branch_id__in=creator_branches,
                joinning_type__in=[1, 3]
            )

            if not request_user_branches.exists():
                return False

            return True

        # Case 2: Creator type is TEAM_TYPE
        elif training.creator_type == 2:
            team = get_object_or_404(Team, id=training.created_by_id)
            if team.team_founder_id == user:  # Request user is the team's founder
                return True

        # Default: No access
        return False
    
############ My Joined Training List API #################
class MyJoinedTrainingsView(APIView):
    def get(self, request, *args, **kwargs):
        # Get the current authenticated user
        user = request.user

        # Fetch all the trainings the user has joined and order by training_date (newest first)
        joined_trainings = Training_Joined.objects.filter(user=user).select_related('training').order_by('-training__training_date')
        
        # If the user has not joined any training, return a message
        if not joined_trainings.exists():
            return Response({
                'status': 0,
                'message': 'No joined trainings found',
                'data': []
            }, status=status.HTTP_200_OK)

        # Get the training sessions by joining the Training model
        trainings = [entry.training for entry in joined_trainings]

        # Order the trainings by training_date (newest first)
        trainings = sorted(trainings, key=lambda x: x.training_date, reverse=True)

        # Initialize custom pagination
        paginator = CustomTrainingPagination()

        # Paginate the queryset
        paginated_trainings = paginator.paginate_queryset(trainings, request)
        if paginated_trainings is not None:
            # Serialize the paginated data
            serializer = TrainingListSerializer(paginated_trainings, many=True, context={'request': request})

            # Prepare the pagination data
            pagination_data = {
                'total_records': len(trainings),
                'total_pages': paginator.page.paginator.num_pages,
                'current_page': paginator.page.number,
                'data': serializer.data  # Directly place the data in 'data'
            }

            # Return paginated data in the response
            return Response({
                'status': 1,
                'message': 'Joined trainings retrieved successfully',
                'data': pagination_data
            }, status=status.HTTP_200_OK)

        # If pagination is not applied, just return the serialized data
        serializer = TrainingListSerializer(trainings, many=True, context={'request': request})
        return Response({
            'status': 1,
            'message': 'Joined trainings retrieved successfully',
            'data': {
                'total_records': len(trainings),
                'total_pages': 1,
                'current_page': 1,
                'data': serializer.data  # Directly place the data in 'data'
            }
        }, status=status.HTTP_200_OK)


############################## Join Training API ##############################

class JoinTrainingAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, training, user):
      

        # Case 1: Creator type is USER_TYPE
        if training.creator_type == 1:
            if training.created_by_id == user:  # Request user is the creator'
                return True

            # Check if the request user is in the same branch as the creator
            creator_branches = JoinBranch.objects.filter(
                user_id=training.created_by_id,
                joinning_type=4
            ).values_list('branch_id', flat=True)

            user_branch = JoinBranch.objects.filter(
                user_id=user,
                # joinning_type=4
            ).values_list('branch_id', flat=True)

            if not creator_branches:
                return False

            request_user_branches = JoinBranch.objects.filter(
                user_id=user,
                branch_id__in=creator_branches,
                joinning_type__in=[1, 3]
            )

            if not request_user_branches.exists():
                return False

            return True


        # Case 2: Creator type is TEAM_TYPE
        elif training.creator_type == 2:
            team = get_object_or_404(Team, id=training.created_by_id)
            if team.team_founder_id == user:  # Request user is the team's founder
                return True

        # Default: No access
        return False
    ######### Create a new training membership for the user ###################
    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Validate training_id
        training_id = request.data.get('training_id')
        if not training_id:
            return Response({'status': 0, 'message': _('Training ID is required.')}, status=status.HTTP_400_BAD_REQUEST)

        # Validate user existence
        user = request.user
        if not user:
            return Response({'status': 0, 'message': _('User not found.')}, status=status.HTTP_404_NOT_FOUND)

        if not user.gender:
            return Response({'status': 0, 'message': _('Please add your gender first.')}, status=status.HTTP_400_BAD_REQUEST)

        # Validate training existence
        try:
            training = Training.objects.get(id=training_id)
        except Training.DoesNotExist:
            return Response({'status': 0, 'message': _('Training not found.')}, status=status.HTTP_404_NOT_FOUND)

        # Check closed training restriction
        if training.training_type == Training.CLOSED_TRAINING:
            if not hasattr(user, 'role') or user.role.id != 2:
                return Response({'status': 0, 'message': _('Only Players can join closed training.')}, status=status.HTTP_403_FORBIDDEN)

        # Ensure user is not already a member
        if Training_Joined.objects.filter(user=user, training=training).exists():
            return Response({'status': 0, 'message': _('User is already a member of the training.')}, status=status.HTTP_400_BAD_REQUEST)

        # Create training membership
        membership = Training_Joined.objects.create(user=user, training=training)

        # Notify relevant users
        notifications_sent = self.notify_relevant_users(training, user)

        serializer = TrainingMembershipSerializer(membership)
        return Response({
            'status': 1,
            'message': _('User joined the training successfully.'),
            'data': serializer.data,
            'notifications_sent': notifications_sent
        }, status=status.HTTP_201_CREATED)

    def notify_relevant_users(self, training, user):
        """
        Notify relevant users: creator, branch managers, coaches.
        """
        message = _("A new player has joined the training.")
        comments_message = _("Don't forget to engage with the new player.")
        push_data = {
            "training_id": training.id,
          
            "type":"training"
        }

        notifications_sent = 0

        if training.creator_type == Training.USER_TYPE:
            creator_branches = JoinBranch.objects.filter(
                user_id=training.created_by_id, joinning_type=4
            ).values_list('branch_id', flat=True)          

            if creator_branches.exists():
                branch_managers_and_coaches = JoinBranch.objects.filter(
                    branch_id__in=creator_branches, joinning_type__in=[1, 3]
                ).select_related('user_id')

                for branch in branch_managers_and_coaches:
                    manager_or_coach = branch.user
                    self.send_notification(manager_or_coach, message, comments_message, push_data)
                    notifications_sent += 1
            else:
                creator = User.objects.get(id=training.created_by_id)
                self.send_notification(creator, message, comments_message, push_data)
                notifications_sent += 1

        elif training.creator_type == Training.TEAM_TYPE:
            team = Team.objects.get(id=training.created_by_id)
            team_founder = team.team_founder
            self.send_notification(team_founder, message, comments_message, push_data)
            notifications_sent += 1

        elif training.creator_type == Training.GROUP_TYPE:
            training_group = TrainingGroups.objects.get(id=training.created_by_id)
            group_founder = training_group.group_founder
            self.send_notification(group_founder, message, comments_message, push_data)
            notifications_sent += 1

        return notifications_sent

    def send_notification(self, user, message, comments_message, push_data):
        """
        Helper method to send notifications to a user.
        """
        notification_language = user.current_language
        if notification_language in ['ar', 'en']:
            activate(notification_language)

        send_push_notification(user.device_token, message, comments_message, device_type=user.device_type, data=push_data)
        send_push_notification(user.device_token,  message, comments_message, device_type=user.device_type, data=push_data)

        Notifictions.objects.create(
            created_by_id=1, creator_type=1, targeted_id=user.id, targeted_type=1,
            title=_("Training Reminder"), content=message + "\n" + comments_message
        )

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
            # Get the training ID from the request
            training_id = request.query_params.get('training_id')
            if not training_id:
                return Response({
                'status': 0,
                'message': _('Training ID is required.')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the user from the request
            user_id = request.query_params.get('user_id')
            if not user_id:
                return Response({
                'status': 0,
                'message': _('User not found.')
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate the training ID
            try:
                training = Training.objects.get(id=training_id)
            except Training.DoesNotExist:
                return Response({
                'status': 0,
                'message': _('Training not found.')
                }, status=status.HTTP_404_NOT_FOUND)

            user = request.user.id
            try:
                membership = Training_Joined.objects.get(user=user_id, training=training)
                serializer = TrainingMembershipSerializer(membership, context={'request': request})
                
                # Modify the serialized data by adding injury_type inside feedbacks
                data = serializer.data
                # Assuming feedbacks are part of the serialized data, no need to remove anything else
                
                return Response({
                'status': 1,
                'message': _('User membership retrieved successfully.'),
                'data': data
                }, status=status.HTTP_200_OK)
            except Training_Joined.DoesNotExist:
                return Response({
                'status': 0,
                'message': _('User is not a member of the training.')
                }, status=status.HTTP_404_NOT_FOUND)

    
    def delete(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
            # Get the training ID from the request
            training_id = request.query_params.get('training_id')
            if not training_id:
                return Response({
                 'status': 0,
                 'message': _('Training ID is required.')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the user from the request
            user_id = request.query_params.get('user_id')
            if not user_id:
                return Response({
                 'status': 0,
                 'message': _('User not found.')
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate the training ID
            try:
                training = Training.objects.get(id=training_id)
            except Training.DoesNotExist:
                return Response({
                'status': 0,
                'message': _('Training not found.')
                }, status=status.HTTP_404_NOT_FOUND)
            user = request.user.id
            if not self._has_access(training, user):  # Pass None for manager_id and coach_id if not needed
                return Response({
                    'status': 0,
                    'message': _('User does not have access to delete this training.')
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get the membership of the user in the training
            try:
                membership = Training_Joined.objects.get(user=user_id, training=training)
            except Training_Joined.DoesNotExist:
                return Response({
                'status': 0,
                'message': _('User is not a member of the training.')
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Delete the membership
            membership.delete()
            return Response({
            'status': 1,
            'message': _('User membership deleted successfully.')
            }, status=status.HTTP_200_OK)
        
            

class TrainingFeedbackAPI(APIView):
    def _has_access(self, training, user):

        # Case 1: Creator type is USER_TYPE
        if training.creator_type == 1:
            if training.created_by_id == user:  # Request user is the creator'
                return True

            # Check if the request user is in the same branch as the creator
            creator_branches = JoinBranch.objects.filter(
                user_id=training.created_by_id,
                joinning_type=4
            ).values_list('branch_id', flat=True)

            user_branch = JoinBranch.objects.filter(
                user_id=user,
                # joinning_type=4
            ).values_list('branch_id', flat=True)

            if not creator_branches:
                return False

            request_user_branches = JoinBranch.objects.filter(
                user_id=user,
                branch_id__in=creator_branches,
                joinning_type__in=[1, 3]
            )

            if not request_user_branches.exists():
                return False

            return True


        # Case 2: Creator type is TEAM_TYPE
        elif training.creator_type == 2:
            team = get_object_or_404(Team, id=training.created_by_id)
            if team.team_founder_id == user:  # Request user is the team's founder
                return True

        # Default: No access
        return False



    
    def patch(self, request, *args, **kwargs):
        # Set language based on the request header
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract required and optional fields from request data
        user_id = request.data.get('user_id')
        training_id = request.data.get('training_id')
        feedback_id = request.data.get('feedback_id')  # Optional feedback ID
        attendance_status = request.data.get('attendance_status')
        feedback_text = request.data.get('feedback')
        rating = request.data.get('rating')
        injury_ids = request.data.get('injury_ids')  # A comma-separated list of injury IDs (e.g., '1,2,3')

        # Check if both training_id and user_id are provided
        if not user_id or not training_id:
            return Response({
                "status": 0,
                "message": _("user_id and training_id are required")
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            training = Training.objects.get(id=training_id)
        except Training.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Training not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        user = request.user.id
        if not self._has_access(training, user):
            return Response({
                "status": 0,
                "message": _("Access denied")
            }, status=status.HTTP_403_FORBIDDEN)

        # Fetch the Training_Joined object
        training_joined = get_object_or_404(Training_Joined, user=user_id, training=training_id)

        # Initialize a flag to track if any changes were made
        updated = False
        update_messages = []

        # Update attendance status if provided
        if attendance_status is not None:
            training_joined.attendance_status = attendance_status
            updated = True
            update_messages.append(_("Attendance updated"))

        # Update rating if provided
        if rating is not None:
            training_joined.rating = rating
            updated = True
            update_messages.append(_("Rating updated"))

        # Save the updated Training_Joined record if there are any updates
        if updated:
            training_joined.save()

        # Handle feedback update or creation
        if feedback_id:
            feedback = get_object_or_404(Training_Feedback, id=feedback_id, user_id=user_id, training_id=training_id)

            # Update feedback text if provided
            if feedback_text:
                feedback.feedback = feedback_text
                update_messages.append(_("Feedback updated"))

            # Update injuries related to the feedback if provided
            if injury_ids:
                injury_id_list = [int(id) for id in injury_ids.split(',')]
                injuries = InjuryType.objects.filter(id__in=injury_id_list)
                feedback.injuries.set(injuries)

                notification_message = _("Someone Injured!!! Don't forget to add their injury to keep track.")
                self.notify_users(training, notification_message, {"type": "injury", "training_id": training_id})
                update_messages.append(_("Injury details updated and notification sent"))

            feedback.save()

        elif feedback_text:
            feedback = Training_Feedback.objects.create(
                training_id=training_id,
                user_id=user_id,
                feedback=feedback_text
            )

            if injury_ids:
                injury_id_list = [int(id) for id in injury_ids.split(',')]
                injuries = InjuryType.objects.filter(id__in=injury_id_list)
                feedback.injuries.set(injuries)

                notification_message = _("Someone Injured!!! Don't forget to add their injury to keep track.")
                self.notify_users(training, notification_message, {"type": "injury", "training_id": training_id})
                update_messages.append(_("New feedback added and injury notification sent"))

        # Serialize data
        feedbacks = Training_Feedback.objects.filter(training_id=training_id, user_id=user_id).order_by("-created_at")
        feedback_data = [
            {
                "id": feedback.id,
                "training": feedback.training.id,
                "user": feedback.user.id,
                "feedback": feedback.feedback,
                "injury_type": list(feedback.injuries.values_list("id", flat=True)),
                "date_created": feedback.date_created,
                "created_at": feedback.created_at,
                "updated_at": feedback.updated_at
            }
            for feedback in feedbacks
        ]

        joined_data = {
            "id": training_joined.id,
            "training": training_joined.training.id,
            "user": {
                "id": training_joined.user.id,
                "username": training_joined.user.username,
                "phone": training_joined.user.phone,
                "profile_picture": training_joined.user.profile_picture.url if training_joined.user.profile_picture else None,
                "country_id": training_joined.user.country.id if training_joined.user.country else None,
                "country_name": training_joined.user.country.name if training_joined.user.country else None,
            },
            "attendance_status": training_joined.attendance_status,
            "rating": training_joined.rating,
            "feedbacks": feedback_data
        }

        update_message = ", ".join(update_messages) if update_messages else _("No changes made")
        return Response({
            "status": 1,
            "message": update_message,
            "data": joined_data
        }, status=status.HTTP_200_OK)

    def notify_users(self, training, message, push_data):
        """
        Notify users based on the creator type of the training.
        """
        notifications_sent = 0

        if training.creator_type == Training.USER_TYPE:
            creator_branches = JoinBranch.objects.filter(
                user_id=training.created_by_id,
                joinning_type=4  # Assuming 4 means team member/player
            ).values_list('branch_id', flat=True)

            if creator_branches.exists():
                branch_managers_and_coaches = JoinBranch.objects.filter(
                    branch_id__in=creator_branches,
                    joinning_type__in=[1, 3]  # 1 = Coach, 3 = Manager
                ).select_related('user')

                for branch in branch_managers_and_coaches:
                    manager_or_coach = branch.user
                    self.send_notification(manager_or_coach, message, "", push_data)
                    notifications_sent += 1
            else:
                user = User.objects.get(id=training.created_by_id)
                self.send_notification(user, message, "", push_data)
                notifications_sent += 1

        elif training.creator_type == Training.TEAM_TYPE:
            team = Team.objects.get(id=training.created_by_id)
            self.send_notification(team.team_founder, message, "", push_data)
            notifications_sent += 1

        elif training.creator_type == Training.GROUP_TYPE:
            group = TrainingGroups.objects.get(id=training.created_by_id)
            self.send_notification(group.group_founder, message, "", push_data)
            notifications_sent += 1

    def send_notification(self, user, message, comments_message, push_data):
        """
        Helper method to send notifications to a user.
        """
        notification_language = user.current_language
        if notification_language in ['ar', 'en']:
            activate(notification_language)

        send_push_notification(
            user.device_token,
            _("Training Notification"),
            message,
            device_type=user.device_type,
            data=push_data
        )

        if comments_message:
            send_push_notification(
                user.device_token,
                _("Training Notification"),
                comments_message,
                device_type=user.device_type,
                data=push_data
            )

        Notifictions.objects.create(
            created_by_id=1,  # Replace with the actual creator ID
            creator_type=1,
            targeted_id=user.id,
            targeted_type=1,
            title=_("Training Notification"),
            content=message + "\n" + comments_message
        )
