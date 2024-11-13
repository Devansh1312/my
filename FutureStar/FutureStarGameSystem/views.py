from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
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
from FutureStarGameSystem.models import *
from FutureStarGameSystem.serializers import *
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.utils.translation import gettext as _
from django.utils.crypto import get_random_string
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator, EmptyPage
from django.db import IntegrityError


################## participates players of particular team for particular tournament ###############
class TeamPlayersAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    def get(self, request):
        # Set language based on request headers
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Retrieve team_id and tournament_id from query parameters
        team_id = request.query_params.get('team_id')
        tournament_id = request.query_params.get('tournament_id')

        # Validate presence of both team_id and tournament_id
        if not team_id or not tournament_id:
            return Response({
                'status': 0,
                'message': _('team_id and tournament_id are required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch lineup entries with lineup_status as null or 0 for the given team and tournament
        lineups = Lineup.objects.filter(
            team_id=team_id,
            tournament_id=tournament_id,
            lineup_status__in=[0, None]
        ).select_related('team_id', 'player_id')

        # If no players are found with status null or 0, return an empty response
        if not lineups.exists():
            return Response({
                'status': 0,
                'message': _('No players with lineup status null or 0 found for the provided team and tournament.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        # Prepare response data
        response_data = []
        for lineup in lineups:
            player = lineup.player_id
            response_data.append({
                "id": lineup.id,
                "team_id": lineup.team_id.id,
                "team_name": lineup.team_id.team_name,
                "player_id": player.id,
                "player_name": player.username,
                "player_profile_picture": player.profile_picture.url if player.profile_picture else None,
                "player_playing_position": player.main_playing_position.name_en if player.main_playing_position else None,
                "created_at": lineup.created_at,
                "updated_at": lineup.updated_at,
            })

        # Return the response with fetched player details
        return Response({
            'status': 1,
            'message': _('Players fetched successfully.'),
            'data': response_data
        }, status=status.HTTP_200_OK)
    
################## added players of particular team for particular tournament for particular games ###############

    def post(self, request, *args, **kwargs):
    # Set language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract required fields
        team_id = request.data.get('team_id')
        player_id = request.data.get('player_id')
        game_id = request.data.get('game_id')
        tournament_id = request.data.get('tournament_id')
      

        # Check if the team exists
        try:
            team = TeamBranch.objects.get(id=team_id)
        except TeamBranch.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('The specified team does not exist.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate player joined in the same team
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

        # Check if the tournament exists
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('The specified tournament does not exist.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if the game exists for the given tournament
        try:
            game = TournamentGames.objects.get(id=game_id, tournament_id=tournament_id)
        except TournamentGames.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('The specified game does not exist in this tournament.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate team_id matches team_a or team_b in the game
        if team_id != game.team_a and team_id != game.team_b:
            return Response({
                'status': 0,
                'message': _('The specified team is not part of this game.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the player is already in the lineup for this game and tournament with the same jersey number
        existing_lineup = Lineup.objects.filter(
            player_id=player.user_id,
            game_id=game,
            tournament_id=tournament,
          
        ).exists()

        if existing_lineup:
            return Response({
                'status': 0,
                'message': _('This player is already added to the lineup for this game and tournament with the same jersey number.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Count the number of players already in the lineup for this team and game
        existing_players = Lineup.objects.filter(team_id=team, game_id=game)
        player_count = existing_players.count()

        # Set status based on the number of players
        if player_count >= 11:
            lineup_status = Lineup.SUBSTITUTE  # If there are already 11 players, status is SUBSTITUTE
        else:
            lineup_status = Lineup.ADDED  # Otherwise, status is ADDED (for the first 11 players)

        # Attempt to create the Lineup
        try:
            lineup = Lineup.objects.create(
                team_id=team,
                player_id=player.user_id,
                game_id=game,
                tournament_id=tournament,
                lineup_status=lineup_status
            )
        except IntegrityError:
            return Response({
                'status': 0,
                'message': _('This player is already added to the lineup for this game and tournament with the same jersey number.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Return success response
        return Response({
            'status': 1,
            'message': _('Player added to lineup successfully.'),
            'data': {
                'team_id': team.id,
                'team_name': team.team_name,
                'player_id': player.user_id.id,
                'player_name': player.user_id.username,  # Adjust field if different
                'tournament_id': tournament.id,
                'tournament_name': tournament.tournament_name,
                'game_id': game.id,
                'game_number': game.game_number,
                'status': 'ADDED' if lineup_status == Lineup.ADDED else 'SUBSTITUTE'
            }
        }, status=status.HTTP_200_OK)
    
################## Added Players ###############

class LineupPlayers(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    ################## Added Players lIST ###############

    def get(self, request, *args, **kwargs):
            language = request.headers.get('Language', 'en')
            if language in ['en', 'ar']:
                activate(language)

            team_id = request.query_params.get('team_id')
            game_id = request.query_params.get('game_id')
            tournament_id = request.query_params.get('tournament_id')

            if not team_id or not game_id or not tournament_id:
                return Response({
                    'status': 0,
                    'message': _('team_id, game_id, and tournament_id are required.'),
                    'data': []
                }, status=status.HTTP_400_BAD_REQUEST)

            # Filter players in Lineup by team, game, and tournament, separating by status
            added_lineups = Lineup.objects.filter(
                team_id=team_id,
                game_id=game_id,
                tournament_id=tournament_id,
                lineup_status=Lineup.ADDED
            )
            substitute_lineups = Lineup.objects.filter(
                team_id=team_id,
                game_id=game_id,
                tournament_id=tournament_id,
                lineup_status=Lineup.SUBSTITUTE
            )
            already_added_lineups = Lineup.objects.filter(
                team_id=team_id,
                game_id=game_id,
                tournament_id=tournament_id,
                lineup_status=Lineup.ALREADY_IN_LINEUP
            )

            # Prepare response data for added players
            added_data = [{
                'id': lineup.player_id.id,
                'username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'position_2': lineup.position_2
            } for lineup in added_lineups]

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
                    'added': added_data,
                    'substitute': substitute_data,
                    'player_added_in_lineup':already_added_data,
                }
            }, status=status.HTTP_200_OK)
    
    ################## Added Players TO STARTING 11 Drag n Drop ###############


    def patch(self, request, *args, **kwargs):
    # Retrieve fields from the request data
        player_id = request.data.get('player_id')
        position_1 = request.data.get('position_1')
        position_2 = request.data.get('position_2')
        team_id = request.data.get('team_id')
        tournament_id = request.data.get('tournament_id')
        game_id = request.data.get('game_id')

        # Validate that all necessary fields are provided
        if not player_id or not position_1 or not position_2 or not team_id or not tournament_id or not game_id:
            return Response({
                'status': 0,
                'message': _('player_id, position_1, position_2, team_id, tournament_id, and game_id are required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch lineup by player_id, team_id, tournament_id, and game_id
            lineup = Lineup.objects.get(
                player_id=player_id,
                team_id=team_id,
                tournament_id=tournament_id,
                game_id=game_id
            )
            
            # Update lineup details
            lineup.lineup_status = Lineup.ALREADY_IN_LINEUP  # Set status to ALREADY_IN_LINEUP
            lineup.position_1 = position_1
            lineup.position_2 = position_2
            lineup.save()

            # Fetch all players in the team that are already added to the lineup for the same tournament and game
            already_added_lineups = Lineup.objects.filter(
                team_id=team_id,
                tournament_id=tournament_id,
                game_id=game_id,
                lineup_status=Lineup.ALREADY_IN_LINEUP
            )

            # Prepare response data for players already added in the lineup
            already_added_data = [{
                'id': player.player_id.id,
                'username': player.player_id.username,
                'profile_picture': player.player_id.profile_picture.url if player.player_id.profile_picture else None,
                'position_1': player.position_1,
                'position_2': player.position_2
            } for player in already_added_lineups]

            return Response({
                'status': 1,
                'message': _('Lineup updated successfully.'),
                'data': {
                    'already_added': already_added_data
                }
            }, status=status.HTTP_200_OK)

        except Lineup.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Lineup not found for the given player_id, team_id, tournament_id, and game_id.'),
            }, status=status.HTTP_404_NOT_FOUND)
  
    ################## Remove Players TO STARTING 11 map Drag n Drop ###############

    def post(self, request, *args, **kwargs):
    # Retrieve fields from the request data
        player_id = request.data.get('player_id')
        team_id = request.data.get('team_id')
        tournament_id = request.data.get('tournament_id')
        game_id = request.data.get('game_id')

        # Validate that all necessary fields are provided
        if not player_id or not team_id or not tournament_id or not game_id:
            return Response({
                'status': 0,
                'message': _('player_id, team_id, tournament_id, and game_id are required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch lineup by player_id, team_id, tournament_id, and game_id
            lineup = Lineup.objects.get(
                player_id=player_id,
                team_id=team_id,
                tournament_id=tournament_id,
                game_id=game_id
            )
            
            # Reset lineup details
            lineup.lineup_status = Lineup.ADDED  # Set status back to ADDED
            lineup.position_1 = None
            lineup.position_2 = None
            lineup.save()

            # Fetch all players already added to the lineup for the same team, tournament, and game
            already_added_lineups = Lineup.objects.filter(
                team_id=team_id,
                tournament_id=tournament_id,
                game_id=game_id,
                lineup_status=Lineup.ALREADY_IN_LINEUP
            )

            # Prepare response data for players already added in the lineup
            already_added_data = [{
                'id': player.player_id.id,
                'username': player.player_id.username,
                'profile_picture': player.player_id.profile_picture.url if player.player_id.profile_picture else None,
                'position_1': player.position_1,
                'position_2': player.position_2
            } for player in already_added_lineups]

            return Response({
                'status': 1,
                'message': _('Lineup reset successfully.'),
                'data': {
                    'already_added': already_added_data
                }
            }, status=status.HTTP_200_OK)

        except Lineup.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Lineup not found for the given player_id, team_id, tournament_id, and game_id.'),
            }, status=status.HTTP_404_NOT_FOUND)

################## Add player jersey of particular team of particular games in particular tournament ###############
        
class AddPlayerJerseyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        # Set language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        # Get player_id, team_id, tournament_id, game_id, and jersey_number from request data
        player_id = request.data.get('player_id')
        team_id = request.data.get('team_id')
        tournament_id = request.data.get('tournament_id')
        game_id = request.data.get('game_id')
        jersey_number = request.data.get('jersey_number')
        
        # Ensure all required fields are provided
        if not player_id or not team_id or not tournament_id or not game_id or not jersey_number:
            return Response({
                'status': 0,
                'message': _('player_id, team_id, tournament_id, game_id, and jersey_number are required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the player exists in the Lineup model for the given team_id, tournament_id, and game_id
        try:
            lineup = Lineup.objects.get(player_id=player_id, team_id=team_id, tournament_id=tournament_id, game_id=game_id)
        except Lineup.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('The specified player does not exist in the lineup for the given team, tournament, and game.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if a jersey number is already assigned for the given combination
        if PlayerJersey.objects.filter(
            lineup_players=lineup,
            lineup_players__team_id=team_id,
            lineup_players__tournament_id=tournament_id,
            lineup_players__game_id=game_id,
            jersey_number=jersey_number
        ).exists():
            return Response({
                'status': 0,
                'message': _('This jersey number is already assigned to another player in the lineup for the specified team, game, and tournament.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create and save the PlayerJersey entry
        player_jersey = PlayerJersey.objects.create(
            lineup_players=lineup,
            jersey_number=jersey_number
        )
        
        # Return success response with player and jersey details
        return Response({
            'status': 1,
            'message': _('Jersey number added successfully for the player.'),
            'data': {
                'player_id': lineup.player_id.id,
                'team_id': lineup.team_id.id,
                'game_id': lineup.game_id.id,
                'tournament_id': lineup.tournament_id.id,
                'jersey_number': player_jersey.jersey_number
            }
        }, status=status.HTTP_201_CREATED)

################## Remove Players from Added player List  ###############
class DeleteLineupView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    
    def delete(self, request, *args, **kwargs):
        # Get player_id, team_id, tournament_id, and game_id from request data
        player_id =request.query_params.get('player_id')
        team_id = request.query_params.get('team_id')
        tournament_id =request.query_params.get('tournament_id')
        game_id =request.query_params.get('game_id')

        # Ensure all required fields are provided
        if not player_id or not team_id or not tournament_id or not game_id:
            return Response({
                'status': 0,
                'message': _('player_id, team_id, tournament_id, and game_id are required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Try to retrieve the lineup entry with provided criteria
        lineup = Lineup.objects.filter(
            player_id=player_id,
            team_id=team_id,
            tournament_id=tournament_id,
            game_id=game_id,
            lineup_status=Lineup.ADDED  # Only consider entries that are currently added
        ).first()

        # Check if the lineup entry exists
        if lineup is None:
            return Response({
                'status': 0,
                'message': _('No matching active lineup entries found.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        # Update the lineup status to REMOVED (0)
        lineup.lineup_status = 0  # 0 represents "REMOVED"
        lineup.save()

        # Prepare the response data with lineup details
        response_data = {
            'player_id': lineup.player_id.id,
            'team_id': lineup.team_id.id,
            'tournament_id': lineup.tournament_id.id,
            'game_id': lineup.game_id.id,
            'lineup_status': lineup.lineup_status  # This will now be 0 (REMOVED)
        }

        return Response({
            'status': 1,
            'message': _('Lineup entries removed successfully.'),
            'data': response_data
        }, status=status.HTTP_200_OK)
class GameStatsLineupPlayers(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    def get(self, request, *args, **kwargs):
            language = request.headers.get('Language', 'en')
            if language in ['en', 'ar']:
                activate(language)

            team_id = request.query_params.get('team_id')
            game_id = request.query_params.get('game_id')
            tournament_id = request.query_params.get('tournament_id')

            if not team_id or not game_id or not tournament_id:
                return Response({
                    'status': 0,
                    'message': _('team_id, game_id, and tournament_id are required.'),
                    'data': []
                }, status=status.HTTP_400_BAD_REQUEST)

            # Filter players in Lineup by team, game, and tournament, separating by status
            # added_lineups = Lineup.objects.filter(
            #     team_id=team_id,
            #     game_id=game_id,
            #     tournament_id=tournament_id,
            #     lineup_status=Lineup.ADDED
            # )
            substitute_lineups = Lineup.objects.filter(
                team_id=team_id,
                game_id=game_id,
                tournament_id=tournament_id,
                lineup_status=Lineup.SUBSTITUTE
            )
            already_added_lineups = Lineup.objects.filter(
                team_id=team_id,
                game_id=game_id,
                tournament_id=tournament_id,
                lineup_status=Lineup.ALREADY_IN_LINEUP
            )

            # Prepare response data for added players
            # added_data = [{
            #     'id': lineup.player_id.id,
            #     'username': lineup.player_id.username,
            #     'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
            #     'position_1': lineup.position_1,
            #     'position_2': lineup.position_2
            # } for lineup in added_lineups]

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
                   
                    'player_added_in_lineup':already_added_data,
                    'substitute': substitute_data,
                }
            }, status=status.HTTP_200_OK)

###### Game Official Types API Views ######
class GameOficialTypesList(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    serializer_class = GameOficialTypeSerializer

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Get all official types
        official_types = OfficialsType.objects.all()

        # Serialize the official types with language in context
        serializer = self.serializer_class(official_types, many=True, context={'language': language})
        # Prepare the response
        return Response({
           'status': 1,
           'message': _('official types retrieved successfully.'),
           'data': serializer.data
        }, status=status.HTTP_200_OK)
    



################### Game Officilals API Views ###################

class GameOfficialsAPIView(APIView):
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
        game = get_object_or_404(TournamentGames, id=game_id)

        # Fetch all officials for the given game, grouped by officials type
        game_officials = GameOfficials.objects.filter(game_id=game_id)
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
            type_serializer = GameOficialTypeSerializer(official.officials_type_id, context={'language': language})
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
        game = get_object_or_404(TournamentGames, id=game_id)
        official = get_object_or_404(User, id=official_id)
        officials_type = get_object_or_404(OfficialsType, id=officials_type_id)

        # Check if the official is already assigned to this game with the same type
        if GameOfficials.objects.filter(game_id=game, official_id=official).exists():
            return Response({
                'status': 0,
                'message': _('This official is already assigned to this game.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create the new GameOfficial entry
        game_official = GameOfficials.objects.create(
            game_id=game,
            official_id=official,
            officials_type_id=officials_type
        )

        # Serialize the official type for the response
        type_serializer = GameOficialTypeSerializer(officials_type, context={'language': language})

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
        game_official = GameOfficials.objects.filter(game_id=game_id, official_id=official_id)
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
