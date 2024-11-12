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




# Create your views here.
class TeamPlayersAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
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
        excluded_player_ids = Lineup.objects.filter(
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
                "player_playing_position": lineup.main_playing_position.name_en if lineup.main_playing_position else None,
                "created_at": lineup.created_at,
                "updated_at": lineup.updated_at,
            })

        return Response({
            'status': 1,
            'message': _('Players fetched successfully.'),
            'data': response_data
        }, status=status.HTTP_200_OK)

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
    

class LineupPlayers(APIView):
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

    def patch(self, request, *args, **kwargs):
        player_id = request.data.get('player_id')
        position_1 = request.data.get('position_1')
        position_2 = request.data.get('position_2')
        team_id = request.data.get('team_id')

        if not player_id or not position_1 or not position_2 or not team_id:
            return Response({
                'status': 0,
                'message': _('player_id, position_1, position_2, and team_id are required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch lineup by player_id and team_id
            lineup = Lineup.objects.get(player_id=player_id, team_id=team_id)
            lineup.lineup_status = Lineup.ALREADY_IN_LINEUP  # Set status to ALREADY_IN_LINEUP
            lineup.position_1 = position_1
            lineup.position_2 = position_2
            lineup.save()

            # Fetch all players in the team that are added to the lineup
            already_added_lineups = Lineup.objects.filter(team_id=team_id, lineup_status=Lineup.ALREADY_IN_LINEUP)

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
                'message': _('Lineup not found for the given player_id and team_id.'),
            }, status=status.HTTP_404_NOT_FOUND)
    # Method to reset status to 1 and clear positions
  

    def post(self, request, *args, **kwargs):
        player_id = request.data.get('player_id')

        if not player_id:
            return Response({
                'status': 0,
                'message': _('player_id is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            lineup = Lineup.objects.get(player_id=player_id)
            lineup.lineup_status = Lineup.ADDED  # Set status back to 1
            lineup.position_1 = None
            lineup.position_2 = None
            lineup.save()

            return Response({
                'status': 1,
                'message': _('Lineup reset successfully.'),
            }, status=status.HTTP_200_OK)

        except Lineup.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Lineup not found for the given player_id.'),
            }, status=status.HTTP_404_NOT_FOUND)
    
class AddPlayerJerseyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    def post(self, request, *args, **kwargs):
        # Set language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        # Get player_id, team_id, and jersey_number from request data
        player_id = request.data.get('player_id')
        team_id = request.data.get('team_id')
        jersey_number = request.data.get('jersey_number')
        
        # Ensure player_id, team_id, and jersey_number are provided
        if not player_id or not team_id or not jersey_number:
            return Response({
                'status': 0,
                'message': _('player_id, team_id, and jersey_number are required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the player exists in the Lineup model for the given team_id
        try:
            lineup = Lineup.objects.get(player_id=player_id, team_id=team_id)
        except Lineup.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('The specified player does not exist in the lineup for the given team.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if a jersey number is already assigned to the player in the PlayerJersey model
        if PlayerJersey.objects.filter(lineup_players=lineup).exists():
            return Response({
                'status': 0,
                'message': _('Jersey number already assigned to this player.'),
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
    
class DeleteLineupView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
  
    def delete(self, request, *args, **kwargs):
        # Get player_id and team_id from request data
        player_id = request.data.get('player_id')
        team_id = request.data.get('team_id')

        # Ensure both player_id and team_id are provided
        if not player_id or not team_id:
            return Response({
                'status': 0,
                'message': _('Both player_id and team_id are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update the lineup status to REMOVED instead of deleting
        updated_count = Lineup.objects.filter(
            player_id=player_id,
            team_id=team_id,
            lineup_status=Lineup.ADDED  # Only update entries that are currently added
        ).update(lineup_status=0)

        # Return response based on the update status
        if updated_count > 0:
            return Response({
                'status': 1,
                'message': _('Lineup entries removed successfully.')
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 0,
                'message': _('No matching active lineup entries found.')
            }, status=status.HTTP_404_NOT_FOUND)
        

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