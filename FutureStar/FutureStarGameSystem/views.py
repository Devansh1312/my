from django.shortcuts import get_object_or_404
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
from django.db.models import Sum,Count,Q
from django.core.exceptions import ObjectDoesNotExist




################## participates players of particular team for particular tournament ###############
class TeamPlayersAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, team_id):
        """
        Check if the user has the required role and valid membership in the team.
        """
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
    def get(self, request):
            language = request.headers.get('Language', 'en')
            if language in ['en', 'ar']:
                activate(language)

            team_id = request.query_params.get('team_id')
            game_id = request.query_params.get('game_id')  # Added game_id to filter
            tournament_id = request.query_params.get('tournament_id')  # Added tournament_id to filter

            if not team_id:
                return Response({
                    'status': 0,
                    'message': _('Team id is required.'),
                    'data': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            # Separate validation for game_id
            if not game_id:
                return Response({
                    'status': 0,
                    'message': _('Game id is required.'),
                    'data': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            # Separate validation for tournament_id
            if not tournament_id:
                return Response({
                    'status': 0,
                    'message': _('Tournament id is required.'),
                    'data': {}
                }, status=status.HTTP_400_BAD_REQUEST)


            try:
                team_name = TeamBranch.objects.get(id=team_id)
            except TeamBranch.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Team not found.'),
                    'data': {}
                }, status=status.HTTP_404_NOT_FOUND)

            # Fetch players in the specified team
            players = JoinBranch.objects.filter(
                branch_id__id=team_id,
                joinning_type=JoinBranch.PLAYER_TYPE
            )

            if not players.exists():
                return Response({
                    'status': 0,
                    'message': _('No players found for the provided team.'),
                    'data': {}
                }, status=status.HTTP_404_NOT_FOUND)

            # Get user_ids of players in JoinBranch
            player_user_ids = [player.user_id.id for player in players]

            # Fetch all players excluding those already in the Lineup model
            excluded_player_ids = Lineup.objects.filter(
                team_id=team_id,
                player_id__in=player_user_ids,
                lineup_status__in=[
                    Lineup.ADDED,
                    Lineup.ALREADY_IN_LINEUP
                ]
            ).values_list('player_id', flat=True)


            # Get player details excluding those in the Lineup
            lineups = User.objects.filter(id__in=player_user_ids).exclude(id__in=excluded_player_ids)

            response_data = []
            for player in lineups:
                # Fetch player's lineup entry for the game and tournament
                lineup_entry = Lineup.objects.filter(
                    player_id=player.id,
                    game_id=game_id,
                    tournament_id=tournament_id
                ).first()

                # Fetch lineup status and jersey number from Lineup and PlayerJersey
                lineup_status = None
                jersey_number = None
                if lineup_entry:
                    lineup_status = lineup_entry.lineup_status
                    jersey_entry = PlayerJersey.objects.filter(lineup_players=lineup_entry).first()
                    jersey_number = jersey_entry.jersey_number if jersey_entry else None

                response_data.append({
                    "id": player.id,
                    "team_id": team_id,
                    "team_name": team_name.team_name,
                    "player_id": player.id,
                    "player_name": player.username,
                    "player_profile_picture": player.profile_picture.url if player.profile_picture else None,
                    "jersey_number": jersey_number,  # Jersey number from PlayerJersey
                    "lineup_status": lineup_status,  # Include lineup status
                    "created_at": player.created_at,
                    "updated_at": player.updated_at,
                })


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

        team_id = int(team_id)

        # Validate permissions
        if not self._has_access(request.user, team_id):
            return Response({
                'status': 0,
                'message': _('You do not have permission to access this team.'),
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Validate team existence
        try:
            team = TeamBranch.objects.get(id=team_id)
        except TeamBranch.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('The specified team does not exist.'),
                'data': {}
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
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate tournament existence
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('The specified tournament does not exist.'),
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate game existence for the given tournament
        try:
            game = TournamentGames.objects.get(id=game_id, tournament_id=tournament_id)
        except TournamentGames.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('The specified game does not exist in this tournament.'),
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate team_id matches team_a or team_b in the game
        if team_id != game.team_a.id and team_id != game.team_b.id:
            return Response({
                'status': 0,
                'message': _('The specified team is not part of this game.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the player already exists in the lineup
        try:
            lineup = Lineup.objects.get(
                player_id=player.user_id,
                game_id=game,
                tournament_id=tournament,
                team_id=team
            )
        except Lineup.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('The player has not been assigned a jersey number yet.'),
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Update lineup status based on current lineup size
        existing_players = Lineup.objects.filter(team_id=team, game_id=game)
        
        # Count players with ADDED or ALREADY_IN_LINEUP status
        added_or_in_lineup_count = existing_players.filter(
            lineup_status__in=[Lineup.ADDED, Lineup.ALREADY_IN_LINEUP]
        ).count()

        # If the player is already in the lineup as ALREADY_IN_LINEUP, keep their status
        if lineup.lineup_status == Lineup.ALREADY_IN_LINEUP:
            lineup_status = lineup.lineup_status
        else:
            # If combined count >= 11, mark as SUBSTITUTE, otherwise ADD player to lineup
            lineup_status = Lineup.SUBSTITUTE if added_or_in_lineup_count >= 11 else Lineup.ADDED

        # Determine if reload is needed
        reload = added_or_in_lineup_count >= 11  # Reload if there are 11 or more players

        # Update the lineup entry
        lineup.lineup_status = lineup_status
        lineup.save()

        # Return success response
        return Response({
            'status': 1,
            'message': _('Lineup updated successfully.'),
            'data': {
                'team_id': team.id,
                'team_name': team.team_name,
                'player_id': player.user_id.id,
                'player_name': player.user_id.username,  # Adjust field if different
                'tournament_id': tournament.id,
                'tournament_name': tournament.tournament_name,
                'game_id': game.id,
                'game_number': game.game_number,
                'lineup_status': 'ADDED' if lineup_status == Lineup.ADDED else 'SUBSTITUTE',
                'count': added_or_in_lineup_count + 1,
                'reload': reload
            }
        }, status=status.HTTP_200_OK)



    

################## Remove players of particular team for particular tournament for particular games ###############
    
    def delete(self, request, *args, **kwargs):
        # Get player_id, team_id, tournament_id, and game_id from request data
        team_id = request.query_params.get('team_id')
        player_id = request.query_params.get('player_id')
        game_id = request.query_params.get('game_id')
        tournament_id = request.query_params.get('tournament_id')


        # Ensure all required fields are provided
        if not team_id:
            return Response({
                'status': 0,
                'message': _('Team id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        if not tournament_id:
            return Response({
                'status': 0,
                'message': _('Tournament id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        if not game_id:
            return Response({
                'status': 0,
                'message': _('Game id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        if not player_id:
            return Response({
                'status': 0,
                'message': _('Player id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        
        if not self._has_access(request.user, team_id):
            return Response({
                'status': 0,
                'message': _('You do not have permission to access this team.'),
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)

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
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Update the lineup status to REMOVED (0)
        lineup.lineup_status = 0  # 0 represents "REMOVED"
        lineup.created_by_id = request.user.id  # Add created_by_id when deleting
   
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

    
################## Added Players ###############

class LineupPlayers(APIView):
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
            tournament_id = request.query_params.get('tournament_id')

            user = request.user
            if not self._has_access(user, team_id):
                return Response({
                    'status': 0,
                    'message': _('You do not have the required permissions to perform this action.'),
                }, status=status.HTTP_403_FORBIDDEN)

            # Validate team_id
            if not team_id:
                return Response({
                    'status': 0,
                    'message': _('Team id is required.'),
                    'data': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate game_id
            if not game_id:
                return Response({
                    'status': 0,
                    'message': _('Game id is required.'),
                    'data': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate tournament_id
            if not tournament_id:
                return Response({
                    'status': 0,
                    'message': _('Tournament id is required.'),
                    'data': {}
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
                'id':lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'jersey_number': PlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if PlayerJersey.objects.filter(lineup_players=lineup).exists() else None
            } for lineup in added_lineups]

            # Prepare response data for substitute players
            substitute_data = [{
                'id':lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'jersey_number': PlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if PlayerJersey.objects.filter(lineup_players=lineup).exists() else None
            } for lineup in substitute_lineups]

            already_added_data = [{
                'id':lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'jersey_number': PlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if PlayerJersey.objects.filter(lineup_players=lineup).exists() else None
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
        team_id = request.data.get('team_id')
        tournament_id = request.data.get('tournament_id')
        game_id = request.data.get('game_id')
        positions = request.data.get('positions', [])  # List of {player_id, position_1}

        # Check if the user has the required permissions
        user = request.user
        if not self._has_access(user, team_id):
            return Response({
                'status': 0,
                'message': _('You do not have the required permissions to perform this action.'),
            }, status=status.HTTP_403_FORBIDDEN)

        # Validate team_id, tournament_id, and game_id
        if not team_id:
            return Response({
                'status': 0,
                'message': _('Team ID is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        if not tournament_id:
            return Response({
                'status': 0,
                'message': _('Tournament ID is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        if not game_id:
            return Response({
                'status': 0,
                'message': _('Game ID is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate positions data
        if not positions or not isinstance(positions, list):
            return Response({
                'status': 0,
                'message': _('Positions data must be a list of player details.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        errors = []  # To store errors for specific players

        for position_data in positions:
            player_id = position_data.get('player_id')
            position_1 = position_data.get('position_1')

            if not player_id or position_1 is None:  # Allow position_1 to be 0
                errors.append({
                    'player_id': player_id,
                    'message': _('Both player_id and position_1 are required.'),
                })
                continue

            try:
                # Fetch lineup by player_id, team_id, tournament_id, and game_id
                lineup = Lineup.objects.get(
                    player_id=player_id,
                    team_id=team_id,
                    tournament_id=tournament_id,
                    game_id=game_id
                )

                # Update lineup details based on position_1 value
                if position_1 == "0":
                    lineup.position_1 = None  # Set position_1 to NULL
                    lineup.lineup_status = Lineup.ADDED  # Set status to ADDED
                else:
                    lineup.position_1 = position_1
                    lineup.lineup_status = Lineup.ALREADY_IN_LINEUP  # Set status to ALREADY_IN_LINEUP

                lineup.created_by_id = user.id  # Set the updated user
                lineup.save()

            except Lineup.DoesNotExist:
                errors.append({
                    'player_id': player_id,
                    'message': _('Lineup not found for this player.')
                })

        # Fetch updated data for the response
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

        # Prepare data for response
        def prepare_lineup_data(lineups):
            return [{
                'id': lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'jersey_number': PlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if PlayerJersey.objects.filter(lineup_players=lineup).exists() else None
            } for lineup in lineups]

        added_data = prepare_lineup_data(added_lineups)
        substitute_data = prepare_lineup_data(substitute_lineups)
        already_added_data = prepare_lineup_data(already_added_lineups)

        # Prepare final response
        return Response({
            'status': 1 if not errors else 0,
            'message': _('Playing 11 Updated Sucessfully ') if not errors else _('Some players could not be updated.'),
            'data': {
                'added': added_data,
                'substitute': substitute_data,
                'player_added_in_lineup': already_added_data,
            }
        }, status=status.HTTP_200_OK if not errors else status.HTTP_400_BAD_REQUEST)


  
    ################## Remove Players TO STARTING 11 map Drag n Drop ###############

    def post(self, request, *args, **kwargs):
    # Retrieve fields from the request data
        player_id = request.data.get('player_id')
        team_id = request.data.get('team_id')
        tournament_id = request.data.get('tournament_id')
        game_id = request.data.get('game_id')

        # Validate player_id
        if not player_id:
            return Response({
                'status': 0,
                'message': _('Player id is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate team_id
        if not team_id:
            return Response({
                'status': 0,
                'message': _('Team id is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate tournament_id
        if not tournament_id:
            return Response({
                'status': 0,
                'message': _('Tournament id is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate game_id
        if not game_id:
            return Response({
                'status': 0,
                'message': _('Game id is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

          
        if not self._has_access(request.user, team_id):
            return Response({
                'status': 0,
                'message': _('You do not have the required permissions to perform this action.'),
            }, status=status.HTTP_403_FORBIDDEN)

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
            lineup.created_by_id = request.user.id  # Reset created_by_id when resetting the lineup

            lineup.save()

            # Fetch all players already added to the lineup for the same team, tournament, and game
            already_added_lineups = Lineup.objects.filter(
                team_id=team_id,
                tournament_id=tournament_id,
                game_id=game_id,
                lineup_status=Lineup.ALREADY_IN_LINEUP
            )
            substitute_lineups = Lineup.objects.filter(
                team_id=team_id,
                game_id=game_id,
                tournament_id=tournament_id,
                lineup_status=Lineup.SUBSTITUTE
            )

            # Prepare response data for players already added in the lineup
            already_added_data = [{
                'id':player.id,
                'player_id': player.player_id.id,
                'username': player.player_id.username,
                'profile_picture': player.player_id.profile_picture.url if player.player_id.profile_picture else None,
                'position_1': player.position_1,
                'jersey_number': PlayerJersey.objects.filter(lineup_players=player).first().jersey_number if PlayerJersey.objects.filter(lineup_players=player).exists() else None
            } for player in already_added_lineups]

            substitute_data = [{
                'id':lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'jersey_number': PlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if PlayerJersey.objects.filter(lineup_players=lineup).exists() else None
            } for lineup in substitute_lineups]

            return Response({
                'status': 1,
                'message': _('Lineup reset successfully.'),
                'data': {
                    'already_added': already_added_data,
                    'substitute': substitute_data

                }
            }, status=status.HTTP_200_OK)

        except Lineup.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Lineup not found.'),
            }, status=status.HTTP_404_NOT_FOUND)

################## Add player jersey of particular team of particular games in particular tournament ###############
        
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

        # Extract required fields
        team_id = request.data.get('team_id')
        game_id = request.data.get('game_id')
        tournament_id = request.data.get('tournament_id')
        players_data = request.data.get('players', [])  # Expecting a list of {player_id, jersey_number}

        # Initialize response data for validations
        validation_errors = []

        # Validate team_id
        if not team_id:
            validation_errors.append({
                'field': 'team_id',
                'message': _('Team id is required.')
            })

        # Validate game_id
        if not game_id:
            validation_errors.append({
                'field': 'game_id',
                'message': _('Game id is required.')
            })

        # Validate tournament_id
        if not tournament_id:
            validation_errors.append({
                'field': 'tournament_id',
                'message': _('Tournament id is required.')
            })

        # Validate players_data
        if not isinstance(players_data, list) or len(players_data) == 0:
            validation_errors.append({
                'field': 'players',
                'message': _('Players Details Must Required.')
            })

        # If there are validation errors, return them
        if validation_errors:
            return Response({
                'status': 0,
                'message': _('Validation errors occurred.'),
                'errors': validation_errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check user access to the team
        if not self._has_access(request.user, team_id):
            return Response({
                'status': 0,
                'message': _('You do not have permission to access this team.'),
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Process players
        response_data = []

        for player in players_data:
            player_id = player.get('player_id')
            jersey_number = player.get('jersey_number', 0)  # Default to 0 if not provided

            if not player_id:
                response_data.append({
                    'player_id': None,
                    'status': 0,
                    'message': _('Player id is required.')
                })
                continue

            # Validate team, player, tournament, and game existence
            try:
                team = TeamBranch.objects.get(id=team_id)
            except TeamBranch.DoesNotExist:
                response_data.append({
                    'player_id': player_id,
                    'status': 0,
                    'message': _('The specified team does not exist.')
                })
                continue

            try:
                tournament = Tournament.objects.get(id=tournament_id)
            except Tournament.DoesNotExist:
                response_data.append({
                    'player_id': player_id,
                    'status': 0,
                    'message': _('The specified tournament does not exist.')
                })
                continue

            try:
                game = TournamentGames.objects.get(id=game_id, tournament_id=tournament_id)
            except TournamentGames.DoesNotExist:
                response_data.append({
                    'player_id': player_id,
                    'status': 0,
                    'message': _('The specified game does not exist in this tournament.')
                })
                continue

            # Validate that the team is part of the game
            if team_id != game.team_a.id and team_id != game.team_b.id:
                response_data.append({
                    'player_id': player_id,
                    'status': 0,
                    'message': _('The specified team is not part of this game.')
                })
                continue

            # Validate the player is part of the team
            try:
                player = JoinBranch.objects.get(
                    branch_id=team_id,
                    joinning_type=JoinBranch.PLAYER_TYPE,
                    user_id=player_id
                )
            except JoinBranch.DoesNotExist:
                response_data.append({
                    'player_id': player_id,
                    'status': 0,
                    'message': _('The specified player is not part of this team.')
                })
                continue

            # Check if jersey number is already assigned in the current lineup
            if jersey_number != 0:
                existing_jersey = PlayerJersey.objects.filter(
                    lineup_players__team_id=team,
                    lineup_players__game_id=game,
                    jersey_number=jersey_number
                ).first()

                if existing_jersey:
                    # Set the existing jersey number to null before assigning it to the new player
                    existing_jersey.jersey_number = None
                    existing_jersey.save()

                # Create or update lineup entry
                try:
                    lineup, created = Lineup.objects.update_or_create(
                        player_id=player.user_id,
                        team_id=team,
                        game_id=game,
                        tournament_id=tournament,
                        defaults={
                            'player_ready': False,  # Player is not ready
                            'created_by_id': request.user.id,
                        }
                    )

                    # Now, create or update the PlayerJersey instance
                    if jersey_number != 0:
                        player_jersey, created_jersey = PlayerJersey.objects.update_or_create(
                            lineup_players=lineup,
                            defaults={
                                'jersey_number': jersey_number,
                                'created_by_id': request.user.id
                            }
                        )

                    response_data.append({
                        'player_id': player.user_id.id,
                        'team_id': team.id,
                        'game_id': game.id,
                        'tournament_id': tournament.id,
                        'jersey_number': jersey_number,  # Return the jersey number
                        'status': 1,
                        'message': _('Jersey Number added Successfully')
                    })

                except IntegrityError:
                    response_data.append({
                        'player_id': player_id,
                        'status': 0,
                        'message': _('An error occurred while adding the player to the lineup.')
                    })
            else:
                # Handle case where jersey_number is 0 by setting it to null
                try:
                    lineup, created = Lineup.objects.update_or_create(
                        player_id=player.user_id,
                        team_id=team,
                        game_id=game,
                        tournament_id=tournament,
                        defaults={
                            'player_ready': False,  # Player is not ready
                            'created_by_id': request.user.id,
                        }
                    )

                    # Set jersey number to null
                    player_jersey, created_jersey = PlayerJersey.objects.update_or_create(
                        lineup_players=lineup,
                        defaults={
                            'jersey_number': None,  # Explicitly set to null
                            'created_by_id': request.user.id
                        }
                    )

                    response_data.append({
                        'player_id': player.user_id.id,
                        'team_id': team.id,
                        'game_id': game.id,
                        'tournament_id': tournament.id,
                        'jersey_number': None,  # Indicate null jersey number in the response
                        'status': 1,
                        'message': _('Jersey number Deleted')
                    })

                except IntegrityError:
                    response_data.append({
                        'player_id': player_id,
                        'status': 0,
                        'message': _('An error occurred while adding the player to the lineup.')
                    })

        # Return response
        return Response({
            'status': 1,
            'message': _('Jersey Numbers Updated Successfully'),
            'data': response_data
        }, status=status.HTTP_200_OK)

################## Players games stats in tournament ###############

class GameStatsLineupPlayers(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, game_id=None, tournament_id=None):
        # Same access check code as before
        if game_id and tournament_id:
            try:
                game = TournamentGames.objects.get(id=game_id, tournament_id_id=tournament_id)
                if game.game_statistics_handler == user:
                    return True
            except TournamentGames.DoesNotExist:
                pass

        return False   

    # Function to get the last update for a player
    def get_last_update(self, player_id, game_id, tournament_id):  # Add self to the method definition
        last_stat = PlayerGameStats.objects.filter(
            Q(player_id_id=player_id) | Q(in_player_id=player_id) | Q(out_player_id=player_id),
            game_id=game_id,
            tournament_id=tournament_id
        ).order_by('-updated_at').first()  # Fetch the most recent update

        if last_stat:
            # Determine the type of the last update
            if last_stat.goals > 0:
                return 'goal'
            elif last_stat.assists > 0:
                return None
            elif last_stat.own_goals > 0:
                return None
            elif last_stat.yellow_cards > 0:
                return 'yellow_card'
            elif last_stat.red_cards > 0:
                return 'red_card'
            elif last_stat.in_player_id == player_id:
                return 'substituted'
            elif last_stat.out_player_id == player_id:
                return 'substituted'
        return None  # No relevant update found

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        team_a_id = request.query_params.get('team_a_id')
        team_b_id = request.query_params.get('team_b_id')
        game_id = request.query_params.get('game_id')
        tournament_id = request.query_params.get('tournament_id')

        # Validate team_a_id, team_b_id, game_id, tournament_id as before...

        if not self._has_access(request.user, game_id=game_id, tournament_id=tournament_id):
            return Response({
                'status': 0,
                'message': _('You do not have access to this resource.'),
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)
        
           # Calculate team goals
    
        tournament_game = TournamentGames.objects.select_related('team_a', 'team_b').get(id=game_id, tournament_id=tournament_id)
        team_a_goals = PlayerGameStats.objects.filter(
            team_id=team_a_id, game_id=game_id, tournament_id=tournament_id
        ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

        team_b_goals = PlayerGameStats.objects.filter(
            team_id=team_b_id, game_id=game_id, tournament_id=tournament_id
        ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

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

            substitute_data = [{
                'id': lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'jersey_number': PlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if PlayerJersey.objects.filter(lineup_players=lineup).exists() else None,
                'lastupdate': self.get_last_update(lineup.player_id.id, game_id, tournament_id)  # Use self to call the method
            } for lineup in substitute_lineups]

            already_added_data = [{
                'id': lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'jersey_number': PlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if PlayerJersey.objects.filter(lineup_players=lineup).exists() else None,
                'lastupdate': self.get_last_update(lineup.player_id.id, game_id, tournament_id)  # Use self to call the method
            } for lineup in already_added_lineups]

            managerial_staff = JoinBranch.objects.filter(
                branch_id=team_id,
                joinning_type=JoinBranch.MANAGERIAL_STAFF_TYPE
            ).select_related('user_id')

            managerial_staff_data = [{
                'id': staff.id,
                'staff_id': staff.user_id.id,
                'staff_username': staff.user_id.username,
                'profile_picture': staff.user_id.profile_picture.url if staff.user_id.profile_picture else None,
                'joining_type_id': staff.joinning_type,
                'joining_type_name': staff.get_joinning_type_display()
            } for staff in managerial_staff]

            lineup_data[team_key] = {
                'player_added_in_lineup': already_added_data,
                'substitute': substitute_data,
                'managerial_staff': managerial_staff_data
            }

        return Response({
            'status': 1,
            'message': _('Lineup players and manager fetched successfully for both teams.'),
            'data': {
                'game_id': game_id,
                'tournament_id': tournament_id,
                'goals': {
                    'team_a_id': tournament_game.team_a.id,
                    'team_a_name': tournament_game.team_a.team_name,
                    'team_a_total_goals': team_a_goals,
                    'team_a_logo': tournament_game.team_a.team_id.team_logo.url if tournament_game.team_a.team_id.team_logo else None,
                    'team_b_id': tournament_game.team_b.id,
                    'team_b_name': tournament_game.team_b.team_name,
                    'team_b_total_goals': team_b_goals,
                    'team_b_logo': tournament_game.team_b.team_id.team_logo.url if tournament_game.team_b.team_id.team_logo else None,
                },
                **lineup_data
            }
        }, status=status.HTTP_200_OK)


    

class LineupPlayerStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, game_id=None, tournament_id=None):
        """
        Check if the user has access to the game based on role and official type for a specific game in a specific tournament.
        """
        # Check if the user's role is 4
        if user.role.id != 4:
            return False

        if game_id and tournament_id:
            try:
                # Check if the game exists for the given tournament
                game = TournamentGames.objects.get(id=game_id, tournament_id_id=tournament_id)

                # Check if the user is associated with the game as an official with specific types
                official = GameOfficials.objects.filter(
                    game_id_id=game_id,
                    official_id=user,
                    officials_type_id__in=[2, 3, 4, 5]  # Allowed official types
                ).exists()

                if official:
                    return True

            except TournamentGames.DoesNotExist:
                pass  # Game not found or doesn't match; access denied
            except GameOfficials.DoesNotExist:
                pass  # Official entry not found or doesn't match; access denied

        # Default to denying access
        return False

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        # Retrieve tournament_id and game_id from query parameters
        tournament_id = request.query_params.get('tournament_id')
        game_id = request.query_params.get('game_id')

        # Check if both tournament_id and game_id are provided
        if not tournament_id:
            return Response({
                'status': 0,
                'message': _('Tournament id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        if not game_id:
            return Response({
                'status': 0,
                'message': _('Game id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user has access to this game (can be simplified depending on access logic)
        if not self._has_access(request.user, game_id, tournament_id):
            return Response({
                'status': 0,
                'message': _('Access denied. You do not have permission to view this game.'),
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            # Retrieve the game details from TournamentGames
            game = TournamentGames.objects.get(id=game_id, tournament_id=tournament_id)
        except TournamentGames.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Game not found for the given tournament.'),
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Fetch all lineup entries based on game_id and tournament_id
        lineup_entries = Lineup.objects.filter(
            game_id=game_id,
            tournament_id=tournament_id,
            lineup_status__in=[Lineup.SUBSTITUTE, Lineup.ALREADY_IN_LINEUP]
        )

        if not lineup_entries.exists():
            return Response({
                'status': 1,
                'message': _('No players found for the specified criteria.'),
                'data': {
                    'team_a': {
                    'added_players': [],
                    'substitute_players': [],
                },
                'team_b': {
                    'added_players': [],
                    'substitute_players': [],
                }
                }
            }, status=status.HTTP_200_OK)

        # Classify players based on team_a and team_b, and further classify by lineup_status
        team_a_added_players = []
        team_a_substitute_players = []
        team_b_added_players = []
        team_b_substitute_players = []

        for lineup in lineup_entries:
            player = lineup.player_id
            player_data = {
                'player_id': player.id,
                'player_username': player.username,
                'player_profile_picture': player.profile_picture.url if player.profile_picture else None,
                'position_1': lineup.position_1,
                'player_ready': lineup.player_ready,
                'created_at': lineup.created_at,
                'updated_at': lineup.updated_at,
            }

            # Classify the player based on the team
            if lineup.team_id == game.team_a:
                # Further classify by lineup status
                if lineup.lineup_status == Lineup.ALREADY_IN_LINEUP:
                    team_a_added_players.append({
                        **player_data,
                        'team_id': game.team_a.id,
                        'team_name': game.team_a.team_name,  # Assuming `team_name` field exists in `TeamBranch`
                    })
                elif lineup.lineup_status == Lineup.SUBSTITUTE:
                    team_a_substitute_players.append({
                        **player_data,
                        'team_id': game.team_a.id,
                        'team_name': game.team_a.team_name,  # Assuming `team_name` field exists in `TeamBranch`
                    })

            elif lineup.team_id == game.team_b:
                # Further classify by lineup status
                if lineup.lineup_status == Lineup.ALREADY_IN_LINEUP:
                    team_b_added_players.append({
                        **player_data,
                        'team_id': game.team_b.id,
                        'team_name': game.team_b.team_name,  # Assuming `team_name` field exists in `TeamBranch`
                    })
                elif lineup.lineup_status == Lineup.SUBSTITUTE:
                    team_b_substitute_players.append({
                        **player_data,
                        'team_id': game.team_b.id,
                        'team_name': game.team_b.team_name,  # Assuming `team_name` field exists in `TeamBranch`
                    })

        # Return the response with players classified into team_a and team_b and also by lineup status
        return Response({
            'status': 1,
            'message': _('Players fetched successfully.'),
            'data': {
                'team_a': {
                    'team_id': game.team_a.id,
                    'team_name': game.team_a.team_name, 
                    'added_players': team_a_added_players,
                    'substitute_players': team_a_substitute_players,
                },
                'team_b': {
                    'team_id': game.team_b.id,
                    'team_name': game.team_b.team_name, 
                    'added_players': team_b_added_players,
                    'substitute_players': team_b_substitute_players,
                }
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

        # Validate player_id
        if not player_id:
            return Response({
                'status': 0,
                'message': _('Player id is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate team_id
        if not team_id:
            return Response({
                'status': 0,
                'message': _('Team id is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate tournament_id
        if not tournament_id:
            return Response({
                'status': 0,
                'message': _('Tournament id is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate game_id
        if not game_id:
            return Response({
                'status': 0,
                'message': _('Game id is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        if not self._has_access(request.user, game_id, tournament_id):
                return Response({
                    'status': 0,
                    'message': _('Access denied. You do not have permission to view this game.'),
                    'data': {}
                }, status=status.HTTP_403_FORBIDDEN)

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
        lineup_entry.created_by_id = request.user.id
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
    


############################### Game Officilas Search API #########################

############ Custom User Search Pagination ##############
class OfflicialSearchPaggination(PageNumberPagination):
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
                'data': {}
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
                'data': {}
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
class OfficialSearchView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = OfflicialSearchPaggination  # Set the pagination class

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        # Get search_type and phone from query parameters
        search_type = request.query_params.get('search_type')
        phone = request.query_params.get('phone')
        game_id = request.query_params.get('game_id')  # Get game_id from request

        # Validate search_type: must be between 1 and 10
        if not search_type or not search_type.isdigit() or int(search_type) not in range(1, 11):
            return Response({
                'status': 0, 
                'message': _('Invalid search type.')
                }, status=status.HTTP_400_BAD_REQUEST)

        search_type = int(search_type)  # Convert search_type to an integer for logic
        users = User.objects.none()  # Initialize an empty queryset

        # Apply logic based on search_type
        if search_type == 1:
            users = User.objects.filter(role_id=5, is_deleted=False)  # Role 5 for search_type 1
        elif search_type in [2, 3, 4, 5]:
            users = User.objects.filter(role_id=4, is_deleted=False)  # Role 4 for search_type 2-5
        elif search_type in [6, 7, 8, 9, 10]:
            users = User.objects.filter(role_id=5, is_deleted=False)  # Role 5 for search_type 6-10

        # Filter by phone if provided
        if phone:
            users = users.filter(phone__icontains=phone)

        # Exclude users who have already joined the specified game
        if game_id:
            joined_users = GameOfficials.objects.filter(game_id=game_id).values_list('official_id', flat=True)
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
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the game exists
        game = get_object_or_404(TournamentGames, id=game_id)

        # Fetch all official types
        all_official_types = OfficialsType.objects.all()

        # Fetch assigned officials for the given game
        assigned_game_officials = GameOfficials.objects.filter(game_id=game_id)

        # Prepare the response data, grouping by official type
        officials_by_type = {}
        for official_type in all_official_types:
            # Serialize the official type
            type_serializer = GameOficialTypeSerializer(official_type, context={'language': language})
            type_name = type_serializer.data['name']

            # Filter assigned officials for the current official type
            assigned_officials = assigned_game_officials.filter(officials_type_id=official_type)

            # Prepare list of assigned officials or an empty list if none
            officials_by_type[type_name] = [
                {
                    'official_id': official.official_id.id,
                    'official_name': official.official_id.username,
                    'profile_picture': official.official_id.profile_picture.url if official.official_id.profile_picture else None,
                    'officials_type_id': official.officials_type_id.id,
                }
                for official in assigned_officials
            ]

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

        # Validate game_id
        if not game_id:
            return Response({
                'status': 0,
                'message': _('Game id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate official_id
        if not official_id:
            return Response({
                'status': 0,
                'message': _('official_id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate officials_type_id
        if not officials_type_id:
            return Response({
                'status': 0,
                'message': _('officials_type_id is required.'),
                'data': {}
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
                'data': {}
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
        # Validate game_id
        if not game_id:
            return Response({
                'status': 0,
                'message': _('Game id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate official_id
        if not official_id:
            return Response({
                'status': 0,
                'message': _('Official is required.'),
                'data': {}
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
                'message': _('No Official Found.'),
            }, status=status.HTTP_404_NOT_FOUND)



class PlayerGameStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, game_id=None, tournament_id=None):
        """
        Check if the user is the game_statistics_handler for the specified game and tournament.
        """
        # Check if the user is the game_statistics_handler for the given game and tournament
        if game_id and tournament_id:
            try:
                game = TournamentGames.objects.get(id=game_id, tournament_id_id=tournament_id)
                if game.game_statistics_handler == user:
                    return True
            except TournamentGames.DoesNotExist:
                pass  # Game not found or doesn't match; access denied

        return False

    def post(self, request, *args, **kwargs):
        # Set language based on the request headers
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        player_id = request.data.get('player_id')
        team_id = request.data.get('team_id')
        tournament_id = request.data.get('tournament_id')
        game_id = request.data.get('game_id')
        game_time = request.data.get('game_time')

        # Validate all required fields
        if not all([player_id, team_id, tournament_id, game_id, game_time]):
            return Response({'status': 0, 'message': _('All fields are required.')}, status=status.HTTP_400_BAD_REQUEST)

        if not self._has_access(request.user, game_id=game_id, tournament_id=tournament_id):
            return Response({'status': 0, 'message': _('You do not have access to this resource.')}, status=status.HTTP_403_FORBIDDEN)

        team_instance = get_object_or_404(TeamBranch, id=team_id)
        player_instance = get_object_or_404(User, id=player_id)
        tournament_instance = get_object_or_404(Tournament, id=tournament_id)
        game_instance = get_object_or_404(TournamentGames, id=game_id)

        if game_instance.finish:
            return Response({'status': 0, 'message': _('Cannot modify stats for a finished game.')}, status=status.HTTP_400_BAD_REQUEST)

        stats_keys = ['goals', 'assists', 'own_goals', 'yellow_cards', 'red_cards']
        for stat in stats_keys:
            stat_value = request.data.get(stat)

            if stat_value is not None:
                stat_value = int(stat_value)

                if stat_value == 1:
                    PlayerGameStats.objects.create(
                        player_id=player_instance,
                        team_id=team_instance,
                        tournament_id=tournament_instance,
                        game_id=game_instance,
                        game_time=game_time,
                        **{stat: 1},
                        created_by_id=request.user.id
                    )
                    self._update_team_goals(game_instance)
                    return Response({'status': 1, 'message': _(f'{stat.capitalize()} incremented successfully.'), 'data': {}}, status=status.HTTP_201_CREATED)

                elif stat_value == -1:
                    stat_count = PlayerGameStats.objects.filter(
                        player_id=player_instance,
                        team_id=team_instance,
                        tournament_id=tournament_instance,
                        game_id=game_instance,
                        **{stat: 1}
                    ).count()

                    if stat_count > 0:
                        latest_stat = PlayerGameStats.objects.filter(
                            player_id=player_instance,
                            team_id=team_instance,
                            tournament_id=tournament_instance,
                            game_id=game_instance,
                            **{stat: 1}
                        ).order_by('-created_at').first()
                        latest_stat.delete()
                        self._update_team_goals(game_instance)  # Update team goals after deletion
                        return Response({'status': 1, 'message': _(f'{stat.capitalize()} decremented successfully.'), 'data': {}}, status=status.HTTP_200_OK)
                    else:
                        return Response({'status': 0, 'message': _(f'Cannot decrement {stat.capitalize()} as it cannot go below zero.')}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 0, 'message': _('Invalid request data.')}, status=status.HTTP_400_BAD_REQUEST)

    def _update_team_goals(self, game_instance):
        """
        Updates the total goals for both teams in a game instance.
        """
        game_instance.team_a_goal = PlayerGameStats.objects.filter(
            team_id=game_instance.team_a.id,
            game_id=game_instance.id
        ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

        game_instance.team_b_goal = PlayerGameStats.objects.filter(
            team_id=game_instance.team_b.id,
            game_id=game_instance.id
        ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

        game_instance.save()

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

        # Validate required parameters
        required_params = {
            'player_id': player_id,
            'team_id': team_id,
            'tournament_id': tournament_id,
            'game_id': game_id
        }
        
        for key, value in required_params.items():
            if not value:
                return Response({
                    'status': 0,
                    'message': _(f'{key} is required.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Check access rights
        if not self._has_access(request.user, game_id=game_id, tournament_id=tournament_id):
            return Response({
                'status': 0,
                'message': _('You do not have access to this resource.'),
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            # Retrieve all matching player stats
            stats = PlayerGameStats.objects.filter(
                player_id=player_id,
                team_id=team_id,
                tournament_id=tournament_id,
                game_id=game_id
            )

            if not stats.exists():
                return Response({
                    'status': 0,
                    'message': _('Player stats not found for the specified criteria.')
                }, status=status.HTTP_404_NOT_FOUND)

            # Calculate totals
            totals = stats.aggregate(
                total_goals=Sum('goals'),
                total_assists=Sum('assists'),
                total_own_goals=Sum('own_goals'),  # Added own_goals calculation
                total_yellow_cards=Sum('yellow_cards'),
                total_red_cards=Sum('red_cards')
            )

            # Format the response data
            total_stats = {
                'id': stats.first().id,  # Assuming IDs are uniform for aggregated data
                'team_id': stats.first().team_id.id,
                'player_id': stats.first().player_id.id,
                'game_id': stats.first().game_id.id,
                'tournament_id': stats.first().tournament_id.id,
                'goals': totals['total_goals'] or 0,
                'assists': totals['total_assists'] or 0,
                'own_goals': totals['total_own_goals'] or 0,  # Added own_goals to response
                'yellow_cards': totals['total_yellow_cards'] or 0,
                'red_cards': totals['total_red_cards'] or 0
            }

            # Respond with the formatted data
            return Response({
                'status': 1,
                'message': _('Player stats fetched successfully.'),
                'data': [total_stats]
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': 0,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


######################### team game timeline #####################
class TeamGameStatsTimelineAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, game_id=None, tournament_id=None):
        """
        Check if the user is the game_statistics_handler for the specified game and tournament.
        """
        # Check if the user is the game_statistics_handler for the given game and tournament
        if game_id and tournament_id:
            try:
                game = TournamentGames.objects.get(id=game_id, tournament_id_id=tournament_id)
                if game.game_statistics_handler == user:
                    return True
            except TournamentGames.DoesNotExist:
                pass  # Game not found or doesn't match; access denied

        return False

    
    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        game_id = request.query_params.get('game_id')
        tournament_id = request.query_params.get('tournament_id')
        
        if not game_id:
            return Response({'status': 0, 'message': _('Game id is required.')}, status=status.HTTP_400_BAD_REQUEST)

        if not tournament_id:
            return Response({'status': 0, 'message': _('Tournament id is required.')}, status=status.HTTP_400_BAD_REQUEST)

        if not self._has_access(request.user, game_id=game_id, tournament_id=tournament_id):
            return Response({'status': 0, 'message': _('You do not have access to this resource.'), 'data': {}}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Fetch game and calculate total goals for both teams
            tournament_game = TournamentGames.objects.get(id=game_id, tournament_id=tournament_id)
            team_a_goals = PlayerGameStats.objects.filter(
                team_id=tournament_game.team_a.id, game_id=game_id, tournament_id=tournament_id
            ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0
            team_b_goals = PlayerGameStats.objects.filter(
                team_id=tournament_game.team_b.id, game_id=game_id, tournament_id=tournament_id
            ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

            # Fetch all stats for the game and order by updated_at descending
            # Fetch all stats for the game and order by game_time descending
            team_stats = PlayerGameStats.objects.filter(
                game_id=game_id, tournament_id=tournament_id
            ).select_related('player_id', 'team_id', 'in_player', 'out_player').order_by('-game_time')

            timeline = []

            for stat in team_stats:
                stat_info = {
                    'id': stat.id,
                    'player_id': stat.player_id.id if stat.player_id else None,
                    'player_name': stat.player_id.username if stat.player_id else None,
                    'team_id': stat.team_id.id,
                    'team_name': stat.team_id.team_name,
                    'goals': stat.goals if stat.goals != 0 else None,
                    'assists': stat.assists if stat.assists != 0 else None,
                    'own_goals': stat.own_goals if stat.own_goals != 0 else None,
                    'yellow_cards': stat.yellow_cards if stat.yellow_cards != 0 else None,
                    'red_cards': stat.red_cards if stat.red_cards != 0 else None,
                    'created_at': stat.created_at,
                    'updated_at': stat.updated_at,
                    'substitution_in_player': stat.in_player.id if stat.in_player else None,
                    'substitution_in_player_name': stat.in_player.username if stat.in_player else None,
                    'substitution_out_player': stat.out_player.id if stat.out_player else None,
                    'substitution_out_player_name': stat.out_player.username if stat.out_player else None,
                    'game_time': stat.game_time if stat.game_time else None
                }
                timeline.append(stat_info)

            return Response({
                'status': 1,
                'message': _('Team stats timeline fetched successfully.'),
                'data': {
                    'game_id': game_id,
                    'tournament_id': tournament_id,
                    'goals': {
                        'team_a_id': tournament_game.team_a.id,
                        'team_a_name': tournament_game.team_a.team_name,
                        'team_a_total_goals': team_a_goals,
                        'team_a_logo': tournament_game.team_a.team_id.team_logo.url if tournament_game.team_a.team_id.team_logo else None,
                        'team_b_id': tournament_game.team_b.id,
                        'team_b_name': tournament_game.team_b.team_name,
                        'team_b_total_goals': team_b_goals,
                        'team_b_logo': tournament_game.team_b.team_id.team_logo.url if tournament_game.team_b.team_id.team_logo else None,
                    },
                    'timeline': timeline
                }
            }, status=status.HTTP_200_OK)

        except TournamentGames.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Game not found.'),
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)


#################### player substitute ######################
class PlayerSubstitutionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, game_id=None, tournament_id=None):
        """
        Check if the user is the game_statistics_handler for the specified game and tournament.
        """
        # Check if the user is the game_statistics_handler for the given game and tournament
        if game_id and tournament_id:
            try:
                game = TournamentGames.objects.get(id=game_id, tournament_id_id=tournament_id)
                if game.game_statistics_handler == user:
                    return True
            except TournamentGames.DoesNotExist:
                pass  # Game not found or doesn't match; access denied

        return False
    def post(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        team_id = request.data.get("team_id")
        tournament_id = request.data.get("tournament_id")
        game_id = request.data.get("game_id")
        player_a_id = request.data.get("player_a_id")
        player_b_id = request.data.get("player_b_id")

        # Validate each field individually
        if not team_id:
            return Response({
                'status': 0,
                'message': _('Team id is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if not tournament_id:
            return Response({
                'status': 0,
                'message': _('Tournament id is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if not game_id:
            return Response({
                'status': 0,
                'message': _('Game id is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if not player_a_id:
            return Response({
                'status': 0,
                'message': _('Player A id is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if not player_b_id:
            return Response({
                'status': 0,
                'message': _('Player B id is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        
        if not self._has_access(request.user, game_id=game_id, tournament_id=tournament_id):
            return Response({
                'status': 0,
                'message': _('You do not have access to this resource.'),
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)

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
           return Response({"error": _("Player A not found or not in the correct lineup status.")})

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
            return Response({"error": _("Player B not found or not in the correct lineup status.")})

        # Swap positions and update statuses
        player_b.position_1 = player_a.position_1
        player_a.position_1 = None

        # Update player_ready and lineup_status
        player_a.player_ready = False
        player_b.player_ready = True

        player_a.lineup_status = Lineup.SUBSTITUTE
        player_b.lineup_status = Lineup.ALREADY_IN_LINEUP

        # Save the updated players

        user_a = get_object_or_404(User, id=player_a.player_id.id)  # Get User instance for player_a
        user_b = get_object_or_404(User, id=player_b.player_id.id)  # Get User instance for player_b
        print(user_a)
        print(user_b)
        # Get other related instances
        team_branch = get_object_or_404(TeamBranch, id=team_id)
        print(team_branch)
        tournament_instance = get_object_or_404(Tournament, id=tournament_id)
        print(tournament_instance)
        game_instance = get_object_or_404(TournamentGames, id=game_id)
        print(game_instance)
        try:
            # Create a new PlayerGameStats record to log the substitution
            player_game_stat = PlayerGameStats.objects.create(
                team_id=team_branch,
                game_id=game_instance,
                tournament_id=tournament_instance,
                player_id=user_b if user_b else user_a,
                in_player=user_b,  # Corrected to use the ID of player_b
                out_player=user_a,  # Corrected to use the ID of player_a
                created_by_id=request.user.id
            )
        except IntegrityError as e:
                return Response({
                    "error": _("Failed to log player substitution."),
                    "details": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        player_a.save()
        player_b.save()
        print(player_a)
        print(player_b)
        return Response({
            "message": _("Player substitution successful"),
            "player_a": {
                "id": player_a_id,
                "position_1": player_a.position_1,
                "player_ready": player_a.player_ready,
                "lineup_status": player_a.lineup_status,
            },
            "player_b": {
                "id": player_b_id,
                "position_1": player_b.position_1,
                "player_ready": player_b.player_ready,
                "lineup_status": player_b.lineup_status,
            }
        }, status=status.HTTP_200_OK)
   

    def get(self, request, *args, **kwargs):   
        permission_classes = [IsAuthenticated]
        parser_classes = (JSONParser, MultiPartParser, FormParser)

        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        team_id = request.query_params.get('team_id')
        game_id = request.query_params.get('game_id')
        tournament_id = request.query_params.get('tournament_id')

        # Validate each field individually
        if not team_id:
            return Response({
                'status': 0,
                'message': _('Team id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        if not game_id:
            return Response({
                'status': 0,
                'message': _('Game id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        if not tournament_id:
            return Response({
                'status': 0,
                'message': _('Tournament id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        
        if not self._has_access(request.user, game_id=game_id, tournament_id=tournament_id):
            return Response({
                'status': 0,
                'message': _('You do not have access to this resource.'),
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)

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
        } for lineup in substitute_lineups]

        
        # Return the response with the status and message
        return Response({
            'status': 1,
            'message': _('Lineup players fetched successfully with status "ADDED".'),
            'data': {
                
                'substitute_players': substitute_data,
                
            }
        }, status=status.HTTP_200_OK)

##################### Swap Position ######################
class SwapPositionView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    
    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Get data from request
        player_id = request.data.get('player_id')  # ID of the player to swap
        target_position = request.data.get('target_position')  # The target position to swap with
        team_id = request.data.get('team_id')  # Team ID of the player
        game_id = request.data.get('game_id')  # Game ID for the context
        
        if not player_id or target_position is None or not team_id or not game_id:
            return Response(
                {
                    "status": 0,
                    "message": _("Player ID, target position, team ID, and game ID are required."),
                    "data": {}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        # Get the player's lineup entry, ensuring that it belongs to the correct team and game
        player_lineup = get_object_or_404(Lineup, player_id=player_id, team_id=team_id, game_id=game_id)
        
        # Check if the player's lineup status is ALREADY_IN_LINEUP (status = 3)
        if player_lineup.lineup_status != Lineup.ALREADY_IN_LINEUP:
                return Response(
                    {
                        "status": 0,
                        "message": _("Player must have in starting 11 lineup to swap positions."),
                        "data": {}
                    },
                    status=status.HTTP_400_BAD_REQUEST
    )
        # Check if there's already a player in the target position within the same game and team
        target_lineup = Lineup.objects.filter(game_id=game_id, team_id=team_id, position_1=target_position).first()
        
        if target_lineup:
            if target_lineup.lineup_status != Lineup.ALREADY_IN_LINEUP:
                return Response({
                    'status': 0,
                    'message': _('The player in the target position must also be in the starting 11 lineup to swap positions.'),
                    'data': {}
                }, status=status.HTTP_400_BAD_REQUEST)
            # Swap positions between the two players
            original_position = player_lineup.position_1
            player_lineup.position_1 = target_position
            target_lineup.position_1 = original_position
            
            # Save both updated lineups
            player_lineup.save()
            target_lineup.save()

            return Response({
                'status': 1,
                'message': _('Positions swapped successfully.'),
                'data': {
                    "player_1": SwapPositionSerializer(player_lineup).data,
                    "player_2": SwapPositionSerializer(target_lineup).data
                }
            }, status=status.HTTP_200_OK)

        else:
            # If no player exists at the target position, just update the player's position
            player_lineup.position_1 = target_position
            player_lineup.save()
            
            return Response({
                'status': 1,
                'message': _('Player position updated successfully.'),
                'data': {
                    "player": SwapPositionSerializer(player_lineup).data
                }
            }, status=status.HTTP_200_OK)

        
       
    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Get team_id and game_id from request
        team_id = request.query_params.get('team_id')
        game_id = request.query_params.get('game_id')
        
        # Validate that team_id and game_id are provided
        if not team_id or not game_id:
            return Response(
                {
                    "status": 0,
                    "message": _("Team ID and Game ID are required."),
                    "data": {}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
                
        # Filter lineups based on team_id and game_id
        lineups = Lineup.objects.filter(team_id=team_id, game_id=game_id, lineup_status=Lineup.ALREADY_IN_LINEUP)
        
        # If no lineups are found, return an appropriate message
        if not lineups.exists():
            return Response(
                {
                    "status": 0,
                    "message": _("No lineups found for the provided team and game."),
                    "data": {}
                },
                status=status.HTTP_404_NOT_FOUND
            )        
        # Serialize the lineups
        serializer = SwapPositionSerializer(lineups, many=True)
        
        return Response({
            'status': 1,
            'message': _('Lineups retrieved successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


################### Tournament Satustics for top Goal and all ###########################
class TopPlayerStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Any logged-in user can access
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        tournament_id = request.query_params.get('tournament_id')

        if not tournament_id:
            return Response({
                'status': 0,
                'message': _('Tournament id is required.'),
                'data': {}
            }, status=400)

        try:
            # Fetch stats for goals, assists, yellow cards, and red cards
            stats = PlayerGameStats.objects.filter(tournament_id=tournament_id)

            top_goals = stats.values('player_id', 'team_id').annotate(total_goals=Sum('goals')).order_by('-total_goals')[:5]
            top_assists = stats.values('player_id', 'team_id').annotate(total_assists=Sum('assists')).order_by('-total_assists')[:5]
            top_yellow_cards = stats.values('player_id', 'team_id').annotate(total_yellow_cards=Sum('yellow_cards')).order_by('-total_yellow_cards')[:5]
            top_red_cards = stats.values('player_id', 'team_id').annotate(total_red_cards=Sum('red_cards')).order_by('-total_red_cards')[:5]

            # Fetch top 5 players based on appearances where lineup_status=3
            top_appearances = (
                Lineup.objects.filter(tournament_id=tournament_id, lineup_status=3)
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
