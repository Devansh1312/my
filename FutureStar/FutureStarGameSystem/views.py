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
from django.db.models import Sum


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
            lineup_status__in=[0, None],
            player_id__is_deleted=False  # Exclude deleted players
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
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
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

        team_a_id = request.query_params.get('team_a_id')
        team_b_id = request.query_params.get('team_b_id')
        game_id = request.query_params.get('game_id')
        tournament_id = request.query_params.get('tournament_id')

        if not team_a_id or not team_b_id or not game_id or not tournament_id:
            return Response({
                'status': 0,
                'message': _('team_a_id, team_b_id, game_id, and tournament_id are required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch lineup data for both teams
        lineup_data = {}
        for team_id, team_key in [(team_a_id, 'team_a'), (team_b_id, 'team_b')]:
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

            # Prepare response data for substitute and already added players
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

            # Retrieve managerial staff related to the given team
            managerial_staff = JoinBranch.objects.filter(
                branch_id=team_id,
                joinning_type=JoinBranch.MANAGERIAL_STAFF_TYPE  # Assuming this is the constant for managerial staff type
            ).select_related('user_id')

            managerial_staff_data = [{
                'id': staff.user_id.id,
                'username': staff.user_id.username,
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
class LineupPlayerStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        # Retrieve team_id, tournament_id, and game_id from query parameters
        team_id = request.query_params.get('team_id')
        tournament_id = request.query_params.get('tournament_id')
        game_id = request.query_params.get('game_id')

        # Check if all required query parameters are provided
        if not team_id or not tournament_id or not game_id:
            return Response({
                'status': 0,
                'message': _('team_id, tournament_id, and game_id are required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Filter lineup entries by team_id, tournament_id, game_id, and specific statuses
        lineup_entries = Lineup.objects.filter(
            lineup_status__in=[Lineup.SUBSTITUTE, Lineup.ALREADY_IN_LINEUP],
            team_id=team_id,
            tournament_id=tournament_id,
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
            if lineup.lineup_status == Lineup.ALREADY_IN_LINEUP:
                added_players.append(player_data)
            elif lineup.lineup_status == Lineup.SUBSTITUTE:
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
        tournament_id = request.data.get('tournament_id')
        game_id = request.data.get('game_id')

        # Ensure all required fields are provided
        if not player_id or not team_id or not tournament_id or not game_id:
            return Response({
                'status': 0,
                'message': _('player_id, team_id, tournament_id, and game_id are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Try to retrieve the lineup entry
        try:
            lineup_entry = Lineup.objects.get(
                player_id=player_id,
                team_id=team_id,
                tournament_id=tournament_id,
                game_id=game_id
            )
        except Lineup.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Lineup entry not found with the specified criteria.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Toggle the player_ready status
        lineup_entry.player_ready = not lineup_entry.player_ready
        lineup_entry.save()

        return Response({
            'status': 1,
            'message': _('Player ready status updated successfully.'),
            'data': {
                'player_id': player_id,
                'team_id': team_id,
                'tournament_id': tournament_id,
                'game_id': game_id,
                'player_ready': lineup_entry.player_ready
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



class PlayerGameStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
         # Set language based on the request headers
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        # Retrieve required identifiers from the request data
        player_id = request.data.get('player_id')
        team_id = request.data.get('team_id')
        tournament_id = request.data.get('tournament_id')
        game_id = request.data.get('game_id')
        
        # Validate that all necessary fields are provided
        if not all([player_id, team_id, tournament_id, game_id]):
            return Response({
                'status': 0,
                'message': _('player_id, team_id, tournament_id, and game_id are required.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Retrieve related model instances
        team_instance = get_object_or_404(TeamBranch, id=team_id)
        player_instance = get_object_or_404(User, id=player_id)
        tournament_instance = get_object_or_404(Tournament, id=tournament_id)
        game_instance = get_object_or_404(TournamentGames, id=game_id)
        
        # Retrieve stats values from request data
        goals = int(request.data.get('goals', 0) or 0)
        assists = int(request.data.get('assists', 0) or 0)
        own_goals = int(request.data.get('own_goals', 0) or 0)
        yellow_cards = int(request.data.get('yellow_cards', 0) or 0)
        red_cards = int(request.data.get('red_cards', 0) or 0)
        
        # Create a new entry for each submission
        new_stat = PlayerGameStats.objects.create(
            player_id=player_instance,
            team_id=team_instance,
            tournament_id=tournament_instance,
            game_id=game_instance,
            goals=goals,
            assists=assists,
            own_goals=own_goals,
            yellow_cards=yellow_cards,
            red_cards=red_cards,
        )
        
        # Aggregate totals for this player, team, game, and tournament combination
        total_stats = PlayerGameStats.objects.filter(
            player_id=player_instance,
            team_id=team_instance,
            tournament_id=tournament_instance,
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
            'tournament_id': tournament_instance.id,
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
        tournament_id = request.query_params.get('tournament_id')
        game_id = request.query_params.get('game_id')

        # Validate that all necessary fields are provided
        if not player_id or not team_id or not tournament_id or not game_id:
            return Response({
                'status': 0,
                'message': _('player_id, team_id, tournament_id, and game_id are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Try to retrieve the player's stats entry
        try:
            stats = PlayerGameStats.objects.get(
                player_id=player_id,
                team_id=team_id,
                tournament_id=tournament_id,
                game_id=game_id
            )
        except PlayerGameStats.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Player stats not found for the specified criteria.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Prepare the stats data
        stats_data = {
            'id': stats.id,
            'team_id': stats.team_id.id,
            'player_id': stats.player_id.id,
            'game_id': stats.game_id.id,
            'tournament_id': stats.tournament_id.id,
            'goals': stats.goals,
            'assists': stats.assists,
            'own_goals': stats.own_goals,
            'yellow_cards': stats.yellow_cards,
            'red_cards': stats.red_cards,
            'created_at': stats.created_at,
            'updated_at': stats.updated_at
        }

        # Respond with the retrieved data
        return Response({
            'status': 1,
            'message': _('Player stats fetched successfully.'),
            'data': stats_data
        }, status=status.HTTP_200_OK)
    


class TeamGameStatsTimelineAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    
    def get(self, request, *args, **kwargs):
        # Retrieve query parameters
        game_id = request.query_params.get('game_id')
        tournament_id = request.query_params.get('tournament_id')
        include_game_time = request.query_params.get('game_time')  # Check if game_time is provided

        # Validate query parameters
        if not game_id or not tournament_id:
            return Response({
                'status': 0,
                'message': _('game_id and tournament_id are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve all relevant stats related to the given game and tournament
        team_stats = PlayerGameStats.objects.filter(
            game_id=game_id,
            tournament_id=tournament_id
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
class PlayerSubstitutionAPIView(APIView):
    def post(self, request):
            team_id = request.data.get("team_id")
            tournament_id = request.data.get("tournament_id")
            game_id = request.data.get("game_id")
            player_a_id = request.data.get("player_a_id")
            player_b_id = request.data.get("player_b_id")

            if not all([team_id, tournament_id, game_id, player_a_id, player_b_id]):
                return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Retrieve player A (must have status ALREADY_IN_LINEUP)
                player_a = Lineup.objects.get(
                    team_id=team_id,
                    tournament_id=tournament_id,
                    game_id=game_id,
                    player_id=player_a_id,
                    lineup_status=Lineup.ALREADY_IN_LINEUP
                )
            except Lineup.DoesNotExist:
                return Response ({"error": "Player A not found or not in the correct lineup status."})

            try:
                # Retrieve player B (must have status SUBSTITUTE)
                player_b = Lineup.objects.get(
                    team_id=team_id,
                    tournament_id=tournament_id,
                    game_id=game_id,
                    player_id=player_b_id,
                    lineup_status=Lineup.SUBSTITUTE
                )
            except Lineup.DoesNotExist:
                return Response({"error": "Player B not found or not in the correct lineup status."})

            # Swap positions and update statuses
            player_b.position_1, player_b.position_2 = player_a.position_1, player_a.position_2
            player_a.position_1, player_a.position_2 = None, None

            # Update player_ready and lineup_status
            player_a.player_ready = False
            player_b.player_ready = True

            player_a.lineup_status = Lineup.SUBSTITUTE
            player_b.lineup_status = Lineup.ALREADY_IN_LINEUP

            # Save the updated players

            user_a = get_object_or_404(User, id=player_a.player_id.id)  # Get User instance for player_a
            user_b = get_object_or_404(User, id=player_b.player_id.id)  # Get User instance for player_b
            print(player_a.player_id)
            print(user_b)
            # Get other related instances
            team_branch = get_object_or_404(TeamBranch, id=team_id)
            tournament_instance = get_object_or_404(Tournament, id=tournament_id)
            game_instance = get_object_or_404(TournamentGames, id=game_id)

            # Create a new PlayerGameStats record to log the substitution
            player_game_stat = PlayerGameStats.objects.create(
                team_id=team_branch,
                game_id=game_instance,
                tournament_id=tournament_instance,
                in_player=user_b,  # Corrected to use the ID of player_b
                out_player=user_a,  # Corrected to use the ID of player_a
            )
            print(player_game_stat)
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
            tournament_id = request.query_params.get('tournament_id')

            if not team_id or not game_id or not tournament_id:
                return Response({
                    'status': 0,
                    'message': _('team_id, game_id, and tournament_id are required.'),
                    'data': []
                }, status=status.HTTP_400_BAD_REQUEST)

            # Filter players in Lineup by team, game, and tournament, separating by status
            
            substitute_lineups = Lineup.objects.filter(
                team_id=team_id,
                game_id=game_id,
                tournament_id=tournament_id,
                lineup_status=Lineup.SUBSTITUTE
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
    

class TeamGameGoalCountAPIView(APIView):
        def get(self, request):
                # Activate language if specified in the header
                language = request.headers.get('Language', 'en')
                if language in ['en', 'ar']:
                    activate(language)

                    
                team_id = request.query_params.get('team_id')
                game_id = request.query_params.get('game_id')
                tournament_id = request.query_params.get('tournament_id')

                # Validate required URL parameters (team_id, game_id, tournament_id)
                if not (team_id and game_id and tournament_id):
                    return Response({
                        'status': 0,
                        'message': _('team_id, game_id, and tournament_id are required.'),
                        'data': []
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Filter PlayerGameStats entries for the specified team, game, and tournament
                goal_stats = PlayerGameStats.objects.filter(
                    team_id=team_id,
                    game_id=game_id,
                    tournament_id=tournament_id
                )
                
                # Calculate the total goals
                total_goals = goal_stats.aggregate(total_goals=Sum('goals'))['total_goals'] or 0

                try:
                    # Fetch the TournamentGames entry
                    tournament_game = TournamentGames.objects.get(id=game_id, tournament_id=tournament_id)
                    
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
                        'team_id': team_id,
                        'game_id': game_id,
                        'tournament_id': tournament_id,
                        'total_goals': total_goals,
                        # 'message': _('Goal count updated successfully.')
                    }, status=status.HTTP_200_OK)

                except TournamentGames.DoesNotExist:
                    return Response({'error': _('Game not found')}, status=status.HTTP_404_NOT_FOUND)