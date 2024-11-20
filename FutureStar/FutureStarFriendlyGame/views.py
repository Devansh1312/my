from collections import defaultdict
from django.shortcuts import get_object_or_404
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
from django.db.models import Sum
from django.db.models import Count


from django.core.exceptions import ObjectDoesNotExist


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

################## participates players of particular team for particular tournament ###############
class FriendlyGameTeamPlayersAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, team_id):
        """
        Check if the user has the required role and valid membership in the team.
        """
        if user.role.id not in [3, 6]:  # Allowed roles: Managerial and Coach
            return False

        try:
            # Verify if the user is part of the team as managerial or coach staff
            JoinBranch.objects.get(
                branch_id_id=team_id,
                user_id=user,
                joinning_type__in=[JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE],
            )
            return True
        except ObjectDoesNotExist:
            return False

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        team_id = request.query_params.get('team_id')

        if not team_id:
            return Response({
                'status': 0,
                'message': _('team_id is required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        team_name = TeamBranch.objects.get(id=team_id)

        # Fetch players in the specified team
        players = JoinBranch.objects.filter(
            branch_id__id=team_id,
            joinning_type=JoinBranch.PLAYER_TYPE
        )

        if not players.exists():
            return Response({
                'status': 0,
                'message': _('No players found for the provided team.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        # Get user_ids of players in JoinBranch
        player_user_ids = [player.user_id.id for player in players]

        # Filter out players already in the Lineup model for the given team_id
        excluded_player_ids = FriendlyGameLineup.objects.filter(
            team_id=team_id,
            player_id__in=player_user_ids
        ).values_list('player_id', flat=True)
        
        # Get player details excluding those in the Lineup
        lineups = User.objects.filter(id__in=player_user_ids).exclude(id__in=excluded_player_ids)

        response_data = []
        for lineup in lineups:
            response_data.append({
                "id": lineup.id,
                "team_id": team_id,
                "team_name": team_name.team_name,
                "player_id": lineup.id,
                "player_name": lineup.username,
                "player_profile_picture": lineup.profile_picture.url if lineup.profile_picture else None,
                "created_at": lineup.created_at,
                "updated_at": lineup.updated_at,
            })

        return Response({
            'status': 1,
            'message': _('Players fetched successfully.'),
            'data': response_data
        }, status=status.HTTP_200_OK)
    

    def post(self, request, *args, **kwargs):
        """
        Add a player to the lineup for a specific game and team.
        """
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        team_id = request.data.get('team_id')
        player_id = request.data.get('player_id')
        game_id = request.data.get('game_id')
        team_id=int(team_id)

        if not self._has_access(request.user, team_id):
            return Response({
                'status': 0,
                'message': _('You do not have permission to access this team.'),
                'data': []
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            team = TeamBranch.objects.get(id=team_id)
        except TeamBranch.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('The specified team does not exist.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            player = JoinBranch.objects.get(
                branch_id__id=team_id,
                joinning_type=JoinBranch.PLAYER_TYPE,
                user_id__id=player_id
            )
        except JoinBranch.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('The specified player is not part of this team.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            game = FriendlyGame.objects.get(id=game_id)
        except FriendlyGame.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('The specified game does not exist.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)
        
        if team_id != game.team_a.id and team_id != game.team_b.id:
            print(type(game.team_a.id))
            print(type(game.team_a.id))

            return Response({
                'status': 0,
                'message': _('The specified team is not part of this game.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        if FriendlyGameLineup.objects.filter(player_id=player.user_id, game_id=game).exists():
            return Response({
                'status': 0,
                'message': _('This player is already added to the lineup for this game.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        player_count = FriendlyGameLineup.objects.filter(team_id=team, game_id=game).count()
        lineup_status = FriendlyGameLineup.SUBSTITUTE if player_count >= 11 else FriendlyGameLineup.ADDED

        lineup = FriendlyGameLineup.objects.create(
            team_id=team,
            player_id=player.user_id,
            game_id=game,
            lineup_status=lineup_status,
            created_by_id=request.user.id
        )

        return Response({
            'status': 1,
            'message': _('Player added to lineup successfully.'),
            'data': {
                'team_id': team.id,
                'team_name': team.team_name,
                'player_id': player.user_id.id,
                'player_name': player.user_id.username,
                'game_id': game.id,
                'game_number': game.game_number,
                'status': 'ADDED' if lineup_status == FriendlyGameLineup.ADDED else 'SUBSTITUTE'
            }
        }, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """
        Remove a player from the lineup for a specific game and team.
        """
        team_id = request.data.get('team_id')
        player_id = request.data.get('player_id')
        game_id = request.data.get('game_id')
      


        if not player_id or not team_id or not game_id:
            return Response({
                'status': 0,
                'message': _('player_id, team_id, and game_id are required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        if not self._has_access(request.user, team_id):
            return Response({
                'status': 0,
                'message': _('You do not have permission to access this team.'),
                'data': []
            }, status=status.HTTP_403_FORBIDDEN)

        lineup = FriendlyGameLineup.objects.filter(
            player_id=player_id,
            team_id=team_id,
            game_id=game_id,
            lineup_status=FriendlyGameLineup.ADDED
        ).first()

        if lineup is None:
            return Response({
                'status': 0,
                'message': _('No matching active lineup entries found.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        lineup.lineup_status = 0  # REMOVED
        lineup.created_by_id = request.user.id
        lineup.save()

        return Response({
            'status': 1,
            'message': _('Lineup entries removed successfully.'),
            'data': {
                'player_id': lineup.player_id.id,
                'team_id': lineup.team_id.id,
                'game_id': lineup.game_id.id,
                'lineup_status': lineup.lineup_status
            }
        }, status=status.HTTP_200_OK)
    
################## Added Players ###############

class FriendlyGameLineupPlayers(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, team_id):
        """
        Check if the user has the required role and valid membership in the team.
        """
        # Check if the user has role 6
        if user.role.id not in [3, 6]:
            return False

        # Check if the user is part of the team with joinning_type = 1 (Managerial Staff)
        try:
            # We check if the joinning_type is either Managerial Staff or Coach Staff
            JoinBranch.objects.get(
                branch_id_id=team_id,
                user_id=user,
                joinning_type__in=[JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE],
            )
            return True
        except ObjectDoesNotExist:
            return False

    ################## Added Players lIST ###############

    def get(self, request, *args, **kwargs):
            language = request.headers.get('Language', 'en')
            if language in ['en', 'ar']:
                activate(language)

            team_id = request.query_params.get('team_id')
            game_id = request.query_params.get('game_id')
            

            user = request.user
            if not self._has_access(user, team_id):
                return Response({
                    'status': 0,
                    'message': _('You do not have the required permissions to perform this action.'),
                }, status=status.HTTP_403_FORBIDDEN)

            if not team_id or not game_id :
                return Response({
                    'status': 0,
                    'message': _('team_id, game_id, are required.'),
                    'data': []
                }, status=status.HTTP_400_BAD_REQUEST)

            # Filter players in Lineup by team, game, and tournament, separating by status
            added_lineups = FriendlyGameLineup.objects.filter(
                team_id=team_id,
                game_id=game_id,
               
                lineup_status=FriendlyGameLineup.ADDED
            )
            substitute_lineups = FriendlyGameLineup.objects.filter(
                team_id=team_id,
                game_id=game_id,
              
                lineup_status=FriendlyGameLineup.SUBSTITUTE
            )
            already_added_lineups = FriendlyGameLineup.objects.filter(
                team_id=team_id,
                game_id=game_id,
                
                lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP
            )

            # Prepare response data for added players
            added_data = [{
                'id':lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'position_2': lineup.position_2
            } for lineup in added_lineups]

            # Prepare response data for substitute players
            substitute_data = [{
                'id':lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'position_2': lineup.position_2
            } for lineup in substitute_lineups]

            already_added_data = [{
                'id':lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'position_2': lineup.position_2
            } for lineup in already_added_lineups]

            # Return the response with the status and message
            return Response({
                'status': 1,
                'message': _('Lineup players fetched successfully with status "ADDED".'),
                'data': {
                    'added': added_data,
                    'substitute': substitute_data,
                    'player_added_in_lineup':already_added_data,
                }
            }, status=status.HTTP_200_OK)
    
    ################## Added Players TO STARTING 11 Drag n Drop ###############


    def patch(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
    # Retrieve fields from the request data
        player_id = request.data.get('player_id')
        position_1 = request.data.get('position_1')
        position_2 = request.data.get('position_2')
        team_id = request.data.get('team_id')
       
        game_id = request.data.get('game_id')

        # Check if the user has the required permissions
        user = request.user
        if not self._has_access(user, team_id):
            return Response({
                'status': 0,
                'message': _('You do not have the required permissions to perform this action.'),
            }, status=status.HTTP_403_FORBIDDEN)

        # Validate that all necessary fields are provided
        if not player_id or not position_1 or not position_2 or not team_id  or not game_id:
            return Response({
                'status': 0,
                'message': _('player_id, position_1, position_2, team_id, and game_id are required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch lineup by player_id, team_id, tournament_id, and game_id
            lineup = FriendlyGameLineup.objects.get(
                player_id=player_id,
                team_id=team_id,
             
                game_id=game_id
            )
            
            # Update lineup details
            lineup.lineup_status = FriendlyGameLineup.ALREADY_IN_LINEUP  # Set status to ALREADY_IN_LINEUP
            lineup.position_1 = position_1
            lineup.position_2 = position_2
            lineup.created_by_id = user.id  # Add created_by_id when updating the lineup
     
            lineup.save()

            # Fetch all players in the team that are already added to the lineup for the same tournament and game
            already_added_lineups = FriendlyGameLineup.objects.filter(
                team_id=team_id,
              
                game_id=game_id,
                lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP
            )
           
            # Prepare response data for players already added in the lineup
            already_added_data = [{
                'id':player.id,
                'player_id': player.player_id.id,
                'player_username': player.player_id.username,
                'profile_picture': player.player_id.profile_picture.url if player.player_id.profile_picture else None,
                'position_1': player.position_1,
                'position_2': player.position_2
            } for player in already_added_lineups]

            return Response({
                'status': 1,
                'message': _('Lineup updated successfully.'),
                'data': {
                    'already_added': already_added_data,
                 
                }
            }, status=status.HTTP_200_OK)

        except FriendlyGameLineup.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Lineup not found for the given player_id, team_id, and game_id.'),
            }, status=status.HTTP_404_NOT_FOUND)
  
#     ################## Remove Players TO STARTING 11 map Drag n Drop ###############

    def post(self, request, *args, **kwargs):
    # Retrieve fields from the request data
        player_id = request.data.get('player_id')
        team_id = request.data.get('team_id')
      
        game_id = request.data.get('game_id')

        # Validate that all necessary fields are provided
        if not player_id or not team_id or not game_id:
            return Response({
                'status': 0,
                'message': _('player_id, team_id, and game_id are required.'),
            }, status=status.HTTP_400_BAD_REQUEST)
          
        if not self._has_access(request.user, team_id):
            return Response({
                'status': 0,
                'message': _('You do not have the required permissions to perform this action.'),
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            # Fetch lineup by player_id, team_id, tournament_id, and game_id
            lineup = FriendlyGameLineup.objects.get(
                player_id=player_id,
                team_id=team_id,
               
                game_id=game_id
            )
            
            # Reset lineup details
            lineup.lineup_status = FriendlyGameLineup.ADDED  # Set status back to ADDED
            lineup.position_1 = None
            lineup.position_2 = None
            lineup.created_by_id = request.user.id  # Reset created_by_id when resetting the lineup

            lineup.save()

            # Fetch all players already added to the lineup for the same team, tournament, and game
            already_added_lineups = FriendlyGameLineup.objects.filter(
                team_id=team_id,
              
                game_id=game_id,
                lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP
            )
            substitute_lineups = FriendlyGameLineup.objects.filter(
                team_id=team_id,
                game_id=game_id,
                
                lineup_status=FriendlyGameLineup.SUBSTITUTE
            )

            # Prepare response data for players already added in the lineup
            already_added_data = [{
                'id':player.id,
                'player_id': player.player_id.id,
                'username': player.player_id.username,
                'profile_picture': player.player_id.profile_picture.url if player.player_id.profile_picture else None,
                'position_1': player.position_1,
                'position_2': player.position_2
            } for player in already_added_lineups]

            substitute_data = [{
                'id':lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'position_2': lineup.position_2
            } for lineup in substitute_lineups]

            return Response({
                'status': 1,
                'message': _('Lineup reset successfully.'),
                'data': {
                    'already_added': already_added_data,
                    'substitute': substitute_data

                }
            }, status=status.HTTP_200_OK)

        except FriendlyGameLineup.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Lineup not found for the given player_id, team_id, and game_id.'),
            }, status=status.HTTP_404_NOT_FOUND)

# ################## Add player jersey of particular team of particular games in particular tournament ###############
        
class AddPlayerJerseyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, team_id):
        """
        Check if the user has the required role and valid membership in the team.
        """
        # Check if the user has role 6
        if user.role.id not in [3, 6]:
            return False

        # Check if the user is part of the team with joinning_type = 1 (Managerial Staff)
        try:
            # We check if the joinning_type is either Managerial Staff or Coach Staff
            JoinBranch.objects.get(
                branch_id_id=team_id,
                user_id=user,
                joinning_type__in=[JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE],
            )
            return True
        except ObjectDoesNotExist:
            return False

    def post(self, request, *args, **kwargs):
        # Set language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        # Get player_id, team_id, tournament_id, game_id, and jersey_number from request data
        player_id = request.data.get('player_id')
        team_id = request.data.get('team_id')
        game_id = request.data.get('game_id')
        jersey_number = request.data.get('jersey_number')

        # Check if the user has the required permissions
        if not self._has_access(request.user, team_id):
            return Response({
                'status': 0,
                'message': _('You do not have the required permissions to perform this action.'),
                'data': []
            }, status=status.HTTP_403_FORBIDDEN)
        
        
        # Ensure all required fields are provided
        if not player_id or not team_id  or not game_id or not jersey_number:
            return Response({
                'status': 0,
                'message': _('player_id, team_id, game_id, and jersey_number are required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the player exists in the Lineup model for the given team_id, tournament_id, and game_id
        try:
            lineup = FriendlyGameLineup.objects.get(player_id=player_id, team_id=team_id, game_id=game_id)
        except FriendlyGameLineup.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('The specified player does not exist in the lineup for the given team, tournament, and game.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if a jersey number is already assigned for the given combination
        if FriendlyGamePlayerJersey.objects.filter(
            lineup_players=lineup,
            lineup_players__team_id=team_id,
            lineup_players__game_id=game_id,
            jersey_number=jersey_number
        ).exists():
            return Response({
                'status': 0,
                'message': _('This jersey number is already assigned to another player in the lineup for the specified team, game, and tournament.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create and save the PlayerJersey entry
        player_jersey = FriendlyGamePlayerJersey.objects.create(
            lineup_players=lineup,
            jersey_number=jersey_number,
            created_by_id=request.user.id 
        )
        
        # Return success response with player and jersey details
        return Response({
            'status': 1,
            'message': _('Jersey number added successfully for the player.'),
            'data': {
                'player_id': lineup.player_id.id,
                'team_id': lineup.team_id.id,
                'game_id': lineup.game_id.id,
                'jersey_number': player_jersey.jersey_number
            }
        }, status=status.HTTP_201_CREATED)

# ################## Players games stats in tournament ###############

   
class FriendlyGameStatsLineupPlayers(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, game_id=None):
        """
        Check if the user is the game_statistics_handler for the specified game and tournament.
        """
        # Check if the user is the game_statistics_handler for the given game and tournament
        if game_id :
            try:
                game = FriendlyGame.objects.get(id=game_id)
                if game.game_statistics_handler == user:
                    return True
            except FriendlyGame.DoesNotExist:
                pass  # Game not found or doesn't match; access denied

        return False   
    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        team_a_id = request.query_params.get('team_a_id')
        team_b_id = request.query_params.get('team_b_id')
        game_id = request.query_params.get('game_id')
     

        if not team_a_id or not team_b_id or not game_id :
            return Response({
                'status': 0,
                'message': _('team_a_id, team_b_id, game_id are required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        if not self._has_access(request.user, game_id=game_id):
            return Response({
                'status': 0,
                'message': _('You do not have access to this resource.'),
                'data': []
            }, status=status.HTTP_403_FORBIDDEN)

        # Fetch lineup data for both teams
        lineup_data = {}
        for team_id, team_key in [(team_a_id, 'team_a'), (team_b_id, 'team_b')]:
            substitute_lineups = FriendlyGameLineup.objects.filter(
                team_id=team_id,
                game_id=game_id,
                
                lineup_status=FriendlyGameLineup.SUBSTITUTE
            )
            already_added_lineups = FriendlyGameLineup.objects.filter(
                team_id=team_id,
                game_id=game_id,
             
                lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP
            )

            # Prepare response data for substitute and already added players
            substitute_data = [{
                'id':lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'position_2': lineup.position_2
            } for lineup in substitute_lineups]

            already_added_data = [{
                'id':lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'position_2': lineup.position_2
            } for lineup in already_added_lineups]

            # Retrieve managerial staff related to the given team
            managerial_staff = JoinBranch.objects.filter(
                branch_id=team_id,
                joinning_type=JoinBranch.MANAGERIAL_STAFF_TYPE  # Assuming this is the constant for managerial staff type
            ).select_related('user_id')

            managerial_staff_data = [{
                'id':staff.id,
                'staff_id': staff.user_id.id,
                'staff_username': staff.user_id.username,
                'profile_picture': staff.user_id.profile_picture.url if staff.user_id.profile_picture else None,
                'joining_type_id': staff.joinning_type,
                'joining_type_name': staff.get_joinning_type_display()
            } for staff in managerial_staff]

            # Add the data for each team to the response
            lineup_data[team_key] = {
                'player_added_in_lineup': already_added_data,
                'substitute': substitute_data,
                'managerial_staff': managerial_staff_data
            }

        # Return the response with the status and message
        return Response({
            'status': 1,
            'message': _('Lineup players and managerial staff fetched successfully for both teams.'),
            'data': lineup_data
        }, status=status.HTTP_200_OK)


class FriendlyGameLineupPlayerStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, game_id=None):
        """
        Check if the user has access to the game based on role and official type for a specific game in a specific tournament.
        """
        # Check if the user's role is 4
        print(user.role)
        if user.role.id != 4:
            return False

        if game_id:
            try:
                # Check if the game exists for the given tournament
                game = FriendlyGame.objects.get(id=game_id)

                # Check if the user is associated with the game as an official with specific types
                official = FriendlyGameGameOfficials.objects.filter(
                    game_id_id=game_id,
                    official_id=user,
                    officials_type_id__in=[2, 3, 4, 5]  # Allowed official types
                ).exists()

                if official:
                    return True

            except FriendlyGame.DoesNotExist:
                pass  # Game not found or doesn't match; access denied
            except FriendlyGameGameOfficials.DoesNotExist:
                pass  # Official entry not found or doesn't match; access denied

        # Default to denying access
        return False

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        # Retrieve team_id, tournament_id, and game_id from query parameters
        team_id = request.query_params.get('team_id')
      
        game_id = request.query_params.get('game_id')

        # Check if all required query parameters are provided
        if not team_id or not game_id:
            return Response({
                'status': 0,
                'message': _('team_id, and game_id are required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not self._has_access(request.user, game_id):
                return Response({
                    'status': 0,
                    'message': _('Access denied. You do not have permission to view this game.'),
                    'data': []
                }, status=status.HTTP_403_FORBIDDEN)

        # Filter lineup entries by team_id, tournament_id, game_id, and specific statuses
        lineup_entries = FriendlyGameLineup.objects.filter(
            lineup_status__in=[FriendlyGameLineup.SUBSTITUTE, FriendlyGameLineup.ALREADY_IN_LINEUP],
            team_id=team_id,
          
            game_id=game_id
        )

        # If no lineup entries are found, return a not found response
        if not lineup_entries.exists():
            return Response({
                'status': 0,
                'message': _('No players found for the specified criteria.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        # Prepare the response data for each lineup entry, classified by lineup_status
        added_players = []
        substitute_players = []
        for lineup in lineup_entries:
            player = lineup.player_id
            player_data = {
                'id': lineup.id,
                'team_id': lineup.team_id.id,
                'team_name': lineup.team_id.team_name,  # Assuming team_name field exists in TeamBranch
                'player_id': player.id,
                'player_username': player.username,
                'player_profile_picture': player.profile_picture.url if player.profile_picture else None,
                'position_1': lineup.position_1,
                'position_2': lineup.position_2,
                'player_ready': lineup.player_ready,
                'created_at': lineup.created_at,
                'updated_at': lineup.updated_at,
            }

            # Classify players based on lineup_status
            if lineup.lineup_status == FriendlyGameLineup.ALREADY_IN_LINEUP:
                added_players.append(player_data)
            elif lineup.lineup_status == FriendlyGameLineup.SUBSTITUTE:
                substitute_players.append(player_data)

        # Return the response with classified players
        return Response({
            'status': 1,
            'message': _('Players fetched successfully.'),
            'data': {
                'added_lineup': added_players,
                'substitute': substitute_players
            }
        }, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Retrieve player_id, team_id, tournament_id, and game_id from request data
        player_id = request.data.get('player_id')
        team_id = request.data.get('team_id')
      
        game_id = request.data.get('game_id')

        # Ensure all required fields are provided
        if not player_id or not team_id  or not game_id:
            return Response({
                'status': 0,
                'message': _('player_id, team_id, and game_id are required.')
            }, status=status.HTTP_400_BAD_REQUEST)
        if not self._has_access(request.user, game_id):
                return Response({
                    'status': 0,
                    'message': _('Access denied. You do not have permission to view this game.'),
                    'data': []
                }, status=status.HTTP_403_FORBIDDEN)

        # Try to retrieve the lineup entry
        try:
            lineup_entry = FriendlyGameLineup.objects.get(
                player_id=player_id,
                team_id=team_id,
            
                game_id=game_id
            )
        except FriendlyGameLineup.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Lineup entry not found with the specified criteria.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Toggle the player_ready status
        lineup_entry.player_ready = not lineup_entry.player_ready
        lineup_entry.created_by_id = request.user.id
        lineup_entry.save()

        return Response({
            'status': 1,
            'message': _('Player ready status updated successfully.'),
            'data': {
                'player_id': player_id,
                'team_id': team_id,
                
                'game_id': game_id,
                'player_ready': lineup_entry.player_ready
            }
        }, status=status.HTTP_200_OK)

# ###### Game Official Types API Views ######
class FriendlyGameOficialTypesList(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    serializer_class = FriendlyGameOficialTypeSerializer

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Get all official types
        official_types = FriendlyGameOfficialsType.objects.all()

        # Serialize the official types with language in context
        serializer = self.serializer_class(official_types, many=True, context={'language': language})
        # Prepare the response
        return Response({
           'status': 1,
           'message': _('official types retrieved successfully.'),
           'data': serializer.data
        }, status=status.HTTP_200_OK)
    



# ################### Game Officilals API Views ###################

class FriendlyGameOfficialsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    def get(self, request, *args, **kwargs):
        # Set language from request headers
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get game_id from request data
        game_id = request.query_params.get('game_id')
        if not game_id:
            return Response({
                'status': 0,
                'message': _('game_id is required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the game exists
        game = get_object_or_404(FriendlyGame, id=game_id)

        # Fetch all officials for the given game, grouped by officials type
        game_officials = FriendlyGameGameOfficials.objects.filter(game_id=game_id)
        if not game_officials.exists():
            return Response({
                'status': 0,
                'message': _('No officials found for the specified game.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        # Organize officials by their type
        officials_by_type = {}
        for official in game_officials:
            # Serialize the official type
            type_serializer = FriendlyGameOficialTypeSerializer(official.officials_type_id, context={'language': language})
            type_name = type_serializer.data['name']

            if type_name not in officials_by_type:
                officials_by_type[type_name] = []

            # Add official details including profile picture
            officials_by_type[type_name].append({
                'official_id': official.official_id.id,
                'official_name': official.official_id.username,
                'profile_picture': official.official_id.profile_picture.url if official.official_id.profile_picture else None,
                'officials_type_id': official.officials_type_id.id,
            })

        return Response({
            'status': 1,
            'message': _('Officials retrieved successfully.'),
            'data': officials_by_type
        }, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        # Set language from request headers
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract data from request
        game_id = request.data.get('game_id')
        official_id = request.data.get('official_id')
        officials_type_id = request.data.get('officials_type_id')

        # Ensure required fields are provided
        if not game_id or not official_id or not officials_type_id:
            return Response({
                'status': 0,
                'message': _('game_id, official_id, and officials_type_id are required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate existence of the required objects
        game = get_object_or_404(FriendlyGame, id=game_id)
        official = get_object_or_404(User, id=official_id)
        officials_type = get_object_or_404(FriendlyGameOfficialsType, id=officials_type_id)

        # Check if the official is already assigned to this game with the same type
        if FriendlyGameGameOfficials.objects.filter(game_id=game, official_id=official).exists():
            return Response({
                'status': 0,
                'message': _('This official is already assigned to this game.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create the new GameOfficial entry
        game_official = FriendlyGameGameOfficials.objects.create(
            game_id=game,
            official_id=official,
            officials_type_id=officials_type
        )

        # Serialize the official type for the response
        type_serializer = FriendlyGameOficialTypeSerializer(officials_type, context={'language': language})

        return Response({
            'status': 1,
            'message': _('Official added successfully.'),
            'data': {
                'game_id': game.id,
                'official_id': official.id,
                'official_name': official.username,
                'profile_picture': official.profile_picture.url if official.profile_picture else None,
                'officials_type_id': officials_type.id,
                'officials_type_name': type_serializer.data['name']
            }
        }, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        # Set language from request headers
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get game_id and official_id from request data
        game_id = request.query_params.get('game_id')
        official_id = request.query_params.get('official_id')

        # Ensure both game_id and official_id are provided
        if not game_id or not official_id:
            return Response({
                'status': 0,
                'message': _('Both game_id and official_id are required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Attempt to delete the specified GameOfficial entry
        game_official = FriendlyGameGameOfficials.objects.filter(game_id=game_id, official_id=official_id)
        if game_official.exists():
            game_official.delete()
            return Response({
                'status': 1,
                'message': _('Official removed successfully from the game.'),
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 0,
                'message': _('No matching official found for the given game and official ID.'),
            }, status=status.HTTP_404_NOT_FOUND)



class FriendlyPlayerGameStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, game_id=None):
        """
        Check if the user is the game_statistics_handler for the specified game and tournament.
        """
        # Check if the user is the game_statistics_handler for the given game and tournament
        if game_id:
            try:
                game = FriendlyGame.objects.get(id=game_id)
                if game.game_statistics_handler == user:
                    return True
            except FriendlyGame.DoesNotExist:
                pass  # Game not found or doesn't match; access denied

        return False

    def post(self, request, *args, **kwargs):
         # Set language based on the request headers
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        # Retrieve required identifiers from the request data
        player_id = request.data.get('player_id')
        team_id = request.data.get('team_id')
      
        game_id = request.data.get('game_id')
        game_id=int(game_id)
        print(game_id)
        
        # Validate that all necessary fields are provided
        if not all([player_id, team_id, game_id]):
            return Response({
                'status': 0,
                'message': _('player_id, team_id, and game_id are required.')
            }, status=status.HTTP_400_BAD_REQUEST)
       
        if not self._has_access(request.user, game_id=game_id):
            return Response({
                'status': 0,
                'message': _('You do not have access to this resource.'),
                'data': []
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Retrieve related model instances
        team_instance = get_object_or_404(TeamBranch, id=team_id)
        player_instance = get_object_or_404(User, id=player_id)
      
        game_instance = get_object_or_404(FriendlyGame, id=game_id)
        
        # Retrieve stats values from request data
        goals = int(request.data.get('goals', 0) or 0)
        assists = int(request.data.get('assists', 0) or 0)
        own_goals = int(request.data.get('own_goals', 0) or 0)
        yellow_cards = int(request.data.get('yellow_cards', 0) or 0)
        red_cards = int(request.data.get('red_cards', 0) or 0)
        
        # Create a new entry for each submission
        new_stat = FriendlyGamesPlayerGameStats.objects.create(
            player_id=player_instance,
            team_id=team_instance,
           
            game_id=game_instance,
            goals=goals,
            assists=assists,
            own_goals=own_goals,
            yellow_cards=yellow_cards,
            red_cards=red_cards,
            created_by_id=request.user.id 
        )
        
        # Aggregate totals for this player, team, game, and tournament combination
        total_stats = FriendlyGamesPlayerGameStats.objects.filter(
            player_id=player_instance,
            team_id=team_instance,
           
            game_id=game_instance
        ).aggregate(
            total_goals=Sum('goals'),
            total_assists=Sum('assists'),
            total_own_goals=Sum('own_goals'),
            total_yellow_cards=Sum('yellow_cards'),
            total_red_cards=Sum('red_cards')
        )
        
        # Calculate the increment for each new entry
        increment_data = {
            'goals_increment': goals,
            'assists_increment': assists,
            'own_goals_increment': own_goals,
            'yellow_cards_increment': yellow_cards,
            'red_cards_increment': red_cards
        }
        
        # Respond with the cumulative and incremental stats
        response_data = {
            'id': new_stat.id,
            'team_id': team_instance.id,
            'player_id': player_instance.id,
            'game_id': game_instance.id,
            
            'total_goals': total_stats['total_goals'] or 0,
            'total_assists': total_stats['total_assists'] or 0,
            'total_own_goals': total_stats['total_own_goals'] or 0,
            'total_yellow_cards': total_stats['total_yellow_cards'] or 0,
            'total_red_cards': total_stats['total_red_cards'] or 0,
            'incremental_data': increment_data,
            'created_at': new_stat.created_at,
            'updated_at': new_stat.updated_at
        }
        
        message = _('Player stats recorded successfully.')
        return Response({
            'status': 1,
            'message': message,
            'data': response_data
        }, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
    # Set language based on the request headers
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Retrieve query parameters for filtering
        player_id = request.query_params.get('player_id')
        team_id = request.query_params.get('team_id')
       
        game_id = request.query_params.get('game_id')

        # Validate that all necessary fields are provided
        if not player_id or not team_id  or not game_id:
            return Response({
                'status': 0,
                'message': _('player_id, team_id, and game_id are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if not self._has_access(request.user, game_id=game_id):
            return Response({
                'status': 0,
                'message': _('You do not have access to this resource.'),
                'data': []
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            # Retrieve all matching player stats
            stats = FriendlyGamesPlayerGameStats.objects.filter(
                player_id=player_id,
                team_id=team_id,
                
                game_id=game_id
            )

            if not stats.exists():
                return Response({
                    'status': 0,
                    'message': _('Player stats not found for the specified criteria.')
                }, status=status.HTTP_404_NOT_FOUND)

            # Prepare the stats data
            stats_data = [
                {
                    'id': stat.id,
                    'team_id': stat.team_id.id,
                    'player_id': stat.player_id.id,
                    'game_id': stat.game_id.id,
                 
                    'goals': stat.goals,
                    'assists': stat.assists,
                    'own_goals': stat.own_goals,
                    'yellow_cards': stat.yellow_cards,
                    'red_cards': stat.red_cards,
                    'game_time': stat.game_time,
                    'in_player': stat.in_player.id if stat.in_player else None,
                    'out_player': stat.out_player.id if stat.out_player else None,
                    'created_at': stat.created_at,
                    'updated_at': stat.updated_at
                } for stat in stats
            ]

            # Respond with the retrieved data
            return Response({
                'status': 1,
                'message': _('Player stats fetched successfully.'),
                'data': stats_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': 0,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class FriendlyPlayerGameStatsTimelineAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, game_id=None):
        """
        Check if the user is the game_statistics_handler for the specified game and tournament.
        """
        # Check if the user is the game_statistics_handler for the given game and tournament
        if game_id:
            try:
                game = FriendlyGame.objects.get(id=game_id)
                if game.game_statistics_handler == user:
                    return True
            except FriendlyGame.DoesNotExist:
                pass  # Game not found or doesn't match; access denied

        return False

    
    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Retrieve query parameters
        game_id = request.query_params.get('game_id')
      
        include_game_time = request.query_params.get('game_time')  # Check if game_time is provided

        # Validate query parameters
        if not game_id :
            return Response({
                'status': 0,
                'message': _('game_id are required.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not self._has_access(request.user, game_id=game_id):
            return Response({
                'status': 0,
                'message': _('You do not have access to this resource.'),
                'data': []
            }, status=status.HTTP_403_FORBIDDEN)

        # Retrieve all relevant stats related to the given game and tournament
        team_stats = FriendlyGamesPlayerGameStats.objects.filter(
            game_id=game_id,
            
        ).select_related('player_id', 'team_id', 'in_player', 'out_player').order_by('updated_at')

        # Prepare a list to hold the timeline data
        stats_data = []

        # Iterate over the stats and add every stat to the response, including duplicates
        for stat in team_stats:
            stat_info = {
                'id': stat.id,
                'player_id': stat.player_id.id,
                'player_name': stat.player_id.username,  # Assuming player has a 'name' field
                'team_id': stat.team_id.id,
                'team_name': stat.team_id.team_name,  # Assuming team has a 'name' field
                'goals': stat.goals,
                'assists': stat.assists,
                'own_goals': stat.own_goals,
                'yellow_cards': stat.yellow_cards,
                'red_cards': stat.red_cards,
                'created_at': stat.created_at,
                'updated_at': stat.updated_at,
                'substitution_in_player': stat.in_player.id if stat.in_player else None,
                'substitution_out_player': stat.out_player.id if stat.out_player else None,
                # Include game_time if include_game_time is set; otherwise, set to None
                'game_time': stat.game_time if include_game_time else None
            }
            # Add the stat information to the list
            stats_data.append(stat_info)

        # Return the response with all timeline data, including duplicates
        return Response({
            'status': 1,
            'message': _('Team stats timeline fetched successfully.'),
            'data': stats_data
        }, status=status.HTTP_200_OK)
    
    ####################  player substitute #####################
class FriendlyPlayerSubstitutionAPIView(APIView):

    def _has_access(self, user, game_id=None):
        """
        Check if the user is the game_statistics_handler for the specified game and tournament.
        """
        # Check if the user is the game_statistics_handler for the given game and tournament
        if game_id :
            try:
                game = FriendlyGame.objects.get(id=game_id)
                if game.game_statistics_handler == user:
                    return True
            except FriendlyGame.DoesNotExist:
                pass  # Game not found or doesn't match; access denied

        return False
    def post(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        team_id = request.data.get("team_id")
      
        game_id = request.data.get("game_id")
        player_a_id = request.data.get("player_a_id")
        player_b_id = request.data.get("player_b_id")

        if not all([team_id, game_id, player_a_id, player_b_id]):
            return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not self._has_access(request.user, game_id=game_id):
            return Response({
                'status': 0,
                'message': _('You do not have access to this resource.'),
                'data': []
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            # Retrieve player A (must have status ALREADY_IN_LINEUP)
            player_a = FriendlyGameLineup.objects.get(
                team_id=team_id,
             
                game_id=game_id,
                player_id=player_a_id,
                lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP
            )
        except FriendlyGameLineup.DoesNotExist:
            return Response ({"error": "Player A not found or not in the correct lineup status."})

        try:
            # Retrieve player B (must have status SUBSTITUTE)
            player_b = FriendlyGameLineup.objects.get(
                team_id=team_id,
               
                game_id=game_id,
                player_id=player_b_id,
                lineup_status=FriendlyGameLineup.SUBSTITUTE
            )
        except FriendlyGameLineup.DoesNotExist:
            return Response({"error": "Player B not found or not in the correct lineup status."})

        # Swap positions and update statuses
        player_b.position_1, player_b.position_2 = player_a.position_1, player_a.position_2
        player_a.position_1, player_a.position_2 = None, None

        # Update player_ready and lineup_status
        player_a.player_ready = False
        player_b.player_ready = True

        player_a.lineup_status = FriendlyGameLineup.SUBSTITUTE
        player_b.lineup_status = FriendlyGameLineup.ALREADY_IN_LINEUP

        # Save the updated players

        user_a = get_object_or_404(User, id=player_a.player_id.id)  # Get User instance for player_a
        user_b = get_object_or_404(User, id=player_b.player_id.id)  # Get User instance for player_b
        # print(player_a.player_id)
        # print(user_b)
        # Get other related instances
        team_branch = get_object_or_404(TeamBranch, id=team_id)
       
        game_instance = get_object_or_404(FriendlyGame, id=game_id)

        # Create a new PlayerGameStats record to log the substitution
        player_game_stat = FriendlyGamesPlayerGameStats.objects.create(
            team_id=team_branch,
            game_id=game_instance,
       
            in_player=user_b,  # Corrected to use the ID of player_b
            out_player=user_a,  # Corrected to use the ID of player_a
            created_by_id=request.user.id
        )
       
        player_a.save()
        player_b.save()
        return Response({
            "message": "Player substitution successful",
            "player_a": {
                "id": player_a_id,
                "position_1": player_a.position_1,
                "position_2": player_a.position_2,
                "player_ready": player_a.player_ready,
                "lineup_status": player_a.lineup_status,
            },
            "player_b": {
                "id": player_b_id,
                "position_1": player_b.position_1,
                "position_2": player_b.position_2,
                "player_ready": player_b.player_ready,
                "lineup_status": player_b.lineup_status,
            }
        }, status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):   

        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        team_id = request.query_params.get('team_id')
        game_id = request.query_params.get('game_id')
     

        if not team_id or not game_id:
            return Response({
                'status': 0,
                'message': _('team_id, game_id are required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not self._has_access(request.user, game_id=game_id):
            return Response({
                'status': 0,
                'message': _('You do not have access to this resource.'),
                'data': []
            }, status=status.HTTP_403_FORBIDDEN)

        # Filter players in Lineup by team, game, and tournament, separating by status
        
        substitute_lineups = FriendlyGameLineup.objects.filter(
            team_id=team_id,
            game_id=game_id,
      
            lineup_status=FriendlyGameLineup.SUBSTITUTE
        )
        

        # Prepare response data for added players
        
        # Prepare response data for substitute players
        substitute_data = [{
            'id': lineup.player_id.id,
            'username': lineup.player_id.username,
            'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
            'position_1': lineup.position_1,
            'position_2': lineup.position_2
        } for lineup in substitute_lineups]

        
        # Return the response with the status and message
        return Response({
            'status': 1,
            'message': _('Lineup players fetched successfully with status "ADDED".'),
            'data': {
                
                'substitute_players': substitute_data,
                
            }
        }, status=status.HTTP_200_OK)


class FriendlyTeamGameGoalCountAPIView(APIView):
        def _has_access(self, user, game_id=None):
            """
            Check if the user is the game_statistics_handler for the specified game and tournament.
            """
            # Check if the user is the game_statistics_handler for the given game and tournament
            if game_id:
                try:
                    game = FriendlyGame.objects.get(id=game_id)
                    if game.game_statistics_handler == user:
                        return True
                except FriendlyGame.DoesNotExist:
                    pass  # Game not found or doesn't match; access denied

            return False
        
        def get(self, request):
                # Activate language if specified in the header
            language = request.headers.get('Language', 'en')
            if language in ['en', 'ar']:
                activate(language)

                
            team_id = request.query_params.get('team_id')
            game_id = request.query_params.get('game_id')
          

            # Validate required URL parameters (team_id, game_id, tournament_id)
            if not (team_id and game_id ):
                return Response({
                    'status': 0,
                    'message': _('team_id, game_id, and  are required.'),
                    'data': []
                }, status=status.HTTP_400_BAD_REQUEST)
            if not self._has_access(request.user, game_id=game_id):
                return Response({
                    'status': 0,
                    'message': _('You do not have access to this resource.'),
                    'data': []
                }, status=status.HTTP_403_FORBIDDEN)

            # Filter PlayerGameStats entries for the specified team, game, and tournament
            goal_stats = FriendlyGamesPlayerGameStats.objects.filter(
                team_id=team_id,
                game_id=game_id,
              
            )
            
            # Calculate the total goals
            total_goals = goal_stats.aggregate(total_goals=Sum('goals'))['total_goals'] or 0

            try:
                # Fetch the TournamentGames entry
                tournament_game = FriendlyGame.objects.get(id=game_id)
                
                # Check if team_id matches team_a or team_b, and update the corresponding goal field
                if str(tournament_game.team_a) == str(team_id):
                    tournament_game.team_a_goal = total_goals
                elif str(tournament_game.team_b) == str(team_id):
                    tournament_game.team_b_goal = total_goals
                else:
                    return Response({
                        'status': 0,
                        'message': _('team_id does not match either team_a or team_b in this game.')
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Save the updated goal count
                tournament_game.save()
                return Response({
                'status': 1,
                'message': _('Team stats fetched successfully.'),
                'data':  {
                    'team_id': team_id,
                    'game_id': game_id,
                  
                    'total_goals': total_goals,
                }
            }, status=status.HTTP_200_OK)
                

            except TournamentGames.DoesNotExist:
                return Response({'error': _('Game not found')}, status=status.HTTP_404_NOT_FOUND)


################### Tournament Satustics for top Goal and all ###########################
class FriendlyGameTopPlayerStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Any logged-in user can access
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        game_id = request.query_params.get('game_id')

        if not game_id:
            return Response({
                'status': 0,
                'message': _('game_id is required.'),
                'data': []
            }, status=400)

        try:
            # Fetch stats for goals, assists, yellow cards, and red cards
            stats = FriendlyGamesPlayerGameStats.objects.filter(game_id=game_id)

            top_goals = stats.values('player_id', 'team_id').annotate(total_goals=Sum('goals')).order_by('-total_goals')[:5]
            top_assists = stats.values('player_id', 'team_id').annotate(total_assists=Sum('assists')).order_by('-total_assists')[:5]
            top_yellow_cards = stats.values('player_id', 'team_id').annotate(total_yellow_cards=Sum('yellow_cards')).order_by('-total_yellow_cards')[:5]
            top_red_cards = stats.values('player_id', 'team_id').annotate(total_red_cards=Sum('red_cards')).order_by('-total_red_cards')[:5]

            # Fetch top 5 players based on appearances where lineup_status=3
            top_appearances = (
                FriendlyGameLineup.objects.filter(game_id=game_id, lineup_status=3)
                .values('player_id', 'team_id')
                .annotate(appearances=Count('id'))
                .order_by('-appearances')[:5]
            )

            def format_player_data(data, stat_field):
                """
                Helper function to format player data with additional details.
                """
                formatted_data = []
                for player in data:
                    # Fetch player username
                    player_instance = User.objects.filter(id=player['player_id']).first()
                    player_username = player_instance.username if player_instance else None

                    # Fetch team and branch details
                    branch_instance = TeamBranch.objects.filter(id=player['team_id']).select_related('team_id').first()
                    if branch_instance:
                        branch_name = branch_instance.team_name
                        team_logo = branch_instance.team_id.team_logo.url if branch_instance.team_id.team_logo else None
                    else:
                        branch_name = None
                        team_logo = None

                    formatted_data.append({
                        'player_id': player['player_id'],
                        'player_username': player_username,
                        'branch_id': player['team_id'],
                        'branch_name': branch_name,
                        'team_logo': team_logo,
                        'stat_value': player[stat_field]
                    })

                return formatted_data

            # Format appearances data
            def format_appearance_data(data):
                """
                Helper function to format appearance data.
                """
                formatted_data = []
                for player in data:
                    # Fetch player username
                    player_instance = User.objects.filter(id=player['player_id']).first()
                    player_username = player_instance.username if player_instance else None

                    # Fetch team and branch details
                    branch_instance = TeamBranch.objects.filter(id=player['team_id']).select_related('team_id').first()
                    if branch_instance:
                        branch_name = branch_instance.team_name
                        team_logo = branch_instance.team_id.team_logo.url if branch_instance.team_id.team_logo else None
                    else:
                        branch_name = None
                        team_logo = None

                    formatted_data.append({
                        'player_id': player['player_id'],
                        'player_username': player_username,
                        'branch_id': player['team_id'],
                        'branch_name': branch_name,
                        'team_logo': team_logo,
                        'appearances': player['appearances']
                    })

                return formatted_data

            # Prepare structured response data
            response_data = {
                'top_goals': format_player_data(top_goals, 'total_goals'),
                'top_assists': format_player_data(top_assists, 'total_assists'),
                'top_yellow_cards': format_player_data(top_yellow_cards, 'total_yellow_cards'),
                'top_red_cards': format_player_data(top_red_cards, 'total_red_cards'),
                'top_appearances': format_appearance_data(top_appearances),
            }

            return Response({
                'status': 1,
                'message': _('Top players fetched successfully.'),
                'data': response_data
            }, status=200)

        except Exception as e:
            return Response({
                'status': 0,
                'message': _('An error occurred while fetching player stats.'),
                'error': str(e)
            }, status=500)




class FriendlyGameStatsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        # Retrieve the query parameters
        team_a_id = request.query_params.get('team_a_id')
        team_b_id = request.query_params.get('team_b_id')

        # Initialize the dictionary to hold statistics for each team
        team_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0})

        # Query all Friendly Games
        games = FriendlyGame.objects.all()

        # Apply filters based on provided query parameters
        if team_a_id:
            games = games.filter(team_a_id=team_a_id)
        if team_b_id:
            games = games.filter(team_b_id=team_b_id)

        # Iterate through games and calculate statistics
        for game in games:
            if game.is_draw:
                team_stats[game.team_a.id]['draws'] += 1
                team_stats[game.team_b.id]['draws'] += 1
            elif game.winner_id == str(game.team_a.id):
                team_stats[game.team_a.id]['wins'] += 1
                team_stats[game.team_b.id]['losses'] += 1
            elif game.winner_id == str(game.team_b.id):
                team_stats[game.team_b.id]['wins'] += 1
                team_stats[game.team_a.id]['losses'] += 1

        # Prepare response data
        response_data = {
            "status": 1,
            "message": _("Friendly game stats fetched successfully"),
            "data": {
                "Team_A": team_stats.get(int(team_a_id), {"wins": 0, "losses": 0, "draws": 0}) if team_a_id else None,
                "Team_B": team_stats.get(int(team_b_id), {"wins": 0, "losses": 0, "draws": 0}) if team_b_id else None,
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)


class FriendlyGamesh2hCompleteAPIView(APIView):
    def get(self, request, *args, **kwargs):
        # Retrieve query parameters
        team_a_id = request.query_params.get('team_a_id', None)
        team_b_id = request.query_params.get('team_b_id', None)

        # Filter games by 'finish' field being True
        games = FriendlyGame.objects.filter(finish=True)

        # Apply additional filters
        if team_a_id:
            games = games.filter(team_a_id=team_a_id)
        if team_b_id:
            games = games.filter(team_b_id=team_b_id)

        # Check if any games exist
        if not games.exists():
            return Response({
                'status': 0,
                'message': _("No completed friendly games found for the given teams"),
            }, status=status.HTTP_404_NOT_FOUND)

        # Serialize the data
        serializer = FriendlyGameSerializer(games, many=True)

        # Prepare response data
        return Response({
            'status': 1,
            'message': _("Friendly games fetched successfully"),
            'data': serializer.data,
        }, status=status.HTTP_200_OK)



class FriendlyTournamentGamesDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        # Set language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get parameters from request query
        team_id = request.query_params.get('team_id')
        game_id = request.query_params.get('game_id')

        if not team_id or not game_id:
            return Response({
                'status': 0,
                'message': _('team_id and game_id are required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Filter players in FriendlyGameLineup by team and game, separating by status
        substitute_lineups = FriendlyGameLineup.objects.filter(
            team_id=team_id,
            game_id=game_id,
            lineup_status=FriendlyGameLineup.SUBSTITUTE
        )
        already_added_lineups = FriendlyGameLineup.objects.filter(
            team_id=team_id,
            game_id=game_id,
            lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP
        )

        # Fetch the staff types for the given team_id, including joining_type and user details
        staff_types = JoinBranch.objects.filter(
            branch_id=team_id
        ).select_related('user_id')  # Assuming JoinBranch has a foreign key to user_id

        staff_data = {
            'managerial_staff': [],
            'coach_staff': [],
            'medical_staff': []
        }

        for staff in staff_types:
            staff_info = {
                'id': staff.user_id.id,
                'username': staff.user_id.username,
                'profile_picture': staff.user_id.profile_picture.url if staff.user_id.profile_picture else None,
                'joining_type_id': staff.joinning_type,
                'joining_type_name': staff.get_joinning_type_display()  # Assuming `get_joinning_type_display()` gives the name of the joining type
            }

            if staff.joinning_type == JoinBranch.MANAGERIAL_STAFF_TYPE:
                staff_data['managerial_staff'].append(staff_info)
            elif staff.joinning_type == JoinBranch.COACH_STAFF_TYPE:
                staff_data['coach_staff'].append(staff_info)
            elif staff.joinning_type == JoinBranch.MEDICAL_STAFF_TYPE:
                staff_data['medical_staff'].append(staff_info)

        # Prepare response data for substitute players
        substitute_data = [{
            'id': lineup.player_id.id,
            'username': lineup.player_id.username,
            'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
            'position_1': lineup.position_1,
            'position_2': lineup.position_2
        } for lineup in substitute_lineups]

        already_added_data = [{
            'id': lineup.player_id.id,
            'username': lineup.player_id.username,
            'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
            'position_1': lineup.position_1,
            'position_2': lineup.position_2
        } for lineup in already_added_lineups]

        # Return the response with the status and message
        return Response({
            'status': 1,
            'message': _('Lineup players fetched successfully with status "ADDED".'),
            'data': {
                'player_added_in_lineup': already_added_data,
                'substitute': substitute_data,
                **staff_data
                # Adding staff types with detailed fields to response
            }
        }, status=status.HTTP_200_OK)