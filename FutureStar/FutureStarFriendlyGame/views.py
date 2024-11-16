from django.utils.translation import gettext as _
from django.utils.translation import activate
from FutureStarTrainingGroupApp.serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from FutureStarFriendlyGame.serializers import *
from rest_framework.permissions import IsAuthenticated
from FutureStar_App.models import *
from FutureStarAPI.models import *
from FutureStarFriendlyGame.models import *
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator, EmptyPage
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q



class ManagerBranchDetail(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        user_id = request.user.id
        if not user_id:
            return Response({
                'status': 0,
                'message': 'User ID is required.',
                
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            join_branch = JoinBranch.objects.get(
                Q(joinning_type=JoinBranch.MANAGERIAL_STAFF_TYPE) | Q(joinning_type=JoinBranch.COACH_STAFF_TYPE),
                user_id=user_id
            )
            team_branch = TeamBranch.objects.get(id=join_branch.branch_id.id)
            
            data = {
                'team_id': team_branch.id,
                'team_name': team_branch.team_name,
                'field_size': team_branch.field_size.id,
                'address': team_branch.address,
                'phone': team_branch.phone,
                'email': team_branch.email,
                'latitude': team_branch.latitude,
                'longitude': team_branch.longitude,
            }

            return Response({
                'status': 1,
                'message': 'Data fetched successfully.',
                'data': data
            })

        except JoinBranch.DoesNotExist:
            return Response({
                'status': 0,
                'message': 'User is not a Managerial Staff.',
                
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)
        except TeamBranch.DoesNotExist:
            return Response({
                'status': 0,
                'message': 'Team Branch not found.',
                
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

class CreateFriendlyGame(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        if request.user.role.id not in [3, 6]:
            return Response({
                'status': 0,
                'message': 'User does not have the required role.',
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)

        game_field_id = request.data.get('game_field_id', None)
        if not game_field_id:
            return Response({
                'status': 0,
                'message': 'Game field ID is required.',
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            game_field = Field.objects.get(id=game_field_id)
        except Field.DoesNotExist:
            return Response({
                'status': 0,
                'message': 'Game field not found.',
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = FriendlyGameSerializer(data=request.data)
        if serializer.is_valid():
            team_a_id = request.data.get('team_a')
            if not team_a_id:
                return Response({
                    'status': 0,
                    'message': 'Team A is required.',
                    'data': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            team_b_id = request.data.get('team_b')
            if team_b_id in ["", 0]:
                team_b_id = None
            if team_b_id and team_b_id == team_a_id:
                return Response({
                    'status': 0,
                    'message': _('Team B cannot be the same as Team A.'),
                    'data': {}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Catch IntegrityError during save operation
            try:
                friendly_game = serializer.save(
                    team_a_id=team_a_id, 
                    team_b_id=team_b_id, 
                    game_field_id=game_field,
                    created_by=request.user
                )
                return Response({
                    'status': 1,
                    'message': 'Friendly game created successfully.',
                    'data': FriendlyGameSerializer(friendly_game).data
                }, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response({
                    'status': 0,
                    'message': 'A game with these details already exists.',
                    'data': {}
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 0,
            'message': 'Invalid data.',
            'data': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class UpdateFriendlyGame(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def put(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Check if the user has the required role
        if request.user.role.id not in [3, 6]:
            return Response({
                'status': 0,
                'message': _('User does not have the required role.'),
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Retrieve and validate game_id
        game_id = request.data.get('game_id')
        if not game_id:
            return Response({
                'status': 0,
                'message': _('Game ID is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve and validate team_b_id
        team_b_id = request.data.get('team_b')
        try:
            team_b_id = int(team_b_id) if team_b_id else None
            team_b_instance = TeamBranch.objects.get(id=team_b_id)  # Fetch the TeamBranch instance
        except (ValueError, TeamBranch.DoesNotExist):
            return Response({
                'status': 0,
                'message': _('Invalid or non-existent Team B ID.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the game instance
            game = FriendlyGame.objects.get(id=game_id)
        except FriendlyGame.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Game not found.'),
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate team_b against team_a
        if team_b_id == game.team_a_id:
            return Response({
                'status': 0,
                'message': _('Team B cannot be the same as Team A.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the game has already started
        if game.game_status == 1:
            return Response({
                'status': 0,
                'message': _('Game is already started.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Assign team_b if not already assigned
        if game.team_b is None:
            game.team_b = team_b_instance  # Assign the TeamBranch instance
            game.game_status = 1  # Set status to started
            game.save()
            data = FriendlyGameSerializer(game).data
            return Response({
                'status': 1,
                'message': _('Game updated successfully.'),
                'data': data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 0,
                'message': _('Team B is already assigned.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)


class DeleteFriendlyGame(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    def delete(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        user_id = request.user.id

        # Check if the user has the required role
        if request.user.role.id != 6:
            return Response({
                'status': 0,
                'message': _('User does not have the required role.'),
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Get the game ID from query parameters
        game_id = request.query_params.get('game_id')
        if not game_id:
            return Response({
                'status': 0,
                'message': _('Game ID is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve the game instance, ensuring it was created by the current user
            game = FriendlyGame.objects.get(id=game_id, created_by=user_id)

            # Check if the game date is in the future
            if game.game_date >= timezone.now().date():
                game.delete()
                return Response({
                    'status': 1,
                    'message': _('Game Deleted successfully.'),
                    'data': {}
                }, status=status.HTTP_204_NO_CONTENT)

            return Response({
                'status': 0,
                'message': _('Cannot delete a game that has already occurred.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        except FriendlyGame.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Game not found or not created by you.'),
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)
        



################ Pagination ##################
# Custom Pagination class with fixed paginate_queryset
class CustomFriendlyGamesPagination(PageNumberPagination): 
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    page_size = 10
    page_query_param = 'page'
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
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

        
################ List OF Friendly Games Where Only One Team is There  #######################

class ListOfFridlyGamesForJoin(APIView):
    pagination_class = CustomFriendlyGamesPagination
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Filter games where game_status=0 and team_b is None
        friendly_games = FriendlyGame.objects.filter(game_status=0, team_b=None)
        
        # Initialize pagination
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(friendly_games, request, view=self)

        # If paginated queryset exists, serialize the data and return paginated response
        if paginated_queryset is not None:
            serializer = FriendlyGameSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Fallback response if no pagination
        serializer = FriendlyGameSerializer(friendly_games, many=True)
        return Response({
            'status': 1,
            'message': 'Data fetched successfully.',
            'data': serializer.data
        })
    


######################### List of all Teams for Team B  ###################
class TeamBranchListView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    def get(self, request, *args, **kwargs):
        team_a_id = request.query_params.get('team_a_id',None)  # ID to exclude
        search_key = request.query_params.get('search', '')  # Search key for team_name

        # Get all branches
        queryset = TeamBranch.objects.all()

        # Exclude team_a if provided
        if team_a_id:
            queryset = queryset.exclude(id=team_a_id)

        # Filter by team_name if search_key is provided
        if search_key:
            queryset = queryset.filter(team_name__icontains=search_key)

        # Serialize data with pagination
        paginator = CustomFriendlyGamesPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = TeamBranchSearchSerializer(paginated_queryset, many=True,context={'request': request})

        # Return paginated response
        return paginator.get_paginated_response(serializer.data)
