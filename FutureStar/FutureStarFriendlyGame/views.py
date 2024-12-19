from collections import defaultdict
import logging
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
from django.db.models import Q ,Sum 
from itertools import chain
from operator import attrgetter
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
import re
from datetime import date
from FutureStar.firebase_config import send_push_notification


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
                'message': _('User Dose Not Found'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        if request.user.role.id != 6:
            return Response({
                'status': 0,
                'message': _('You do not have the required role to access this resource'),
                'data': []
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            join_branch = JoinBranch.objects.get(
                Q(joinning_type=JoinBranch.MANAGERIAL_STAFF_TYPE) | Q(joinning_type=JoinBranch.COACH_STAFF_TYPE),
                user_id=user_id
            )
            team_branch = TeamBranch.objects.get(id=join_branch.branch_id.id)
            
            data = [{
                'id': team_branch.id,
                'name': team_branch.team_name
            }]

            return Response({
                'status': 1,
                'message': _('Teams fetched successfully.'),
                'data': data
            })

        except JoinBranch.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('You are not a manager of any team.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)
        except TeamBranch.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Team not found.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)


class CreateFriendlyGame(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Check if user has the correct role
        if request.user.role.id not in [3, 6]:
            return Response({
                'status': 0,
                'message': _('User does not have the required role.'),
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Validate game_field_id
        game_field_id = request.data.get('game_field_id', None)
        if not game_field_id:
            return Response({
                'status': 0,
                'message': _('Game field id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            game_field = Field.objects.get(id=game_field_id)
        except Field.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Game field not found.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate and create FriendlyGame
        serializer = FriendlyGameSerializer(data=request.data)
        if serializer.is_valid():
            team_a_id = request.data.get('team_a')
            if not team_a_id:
                return Response({
                    'status': 0,
                    'message': _('Team A is required.'),
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

            try:
                # Save the friendly game instance
                friendly_game = serializer.save(
                    team_a_id=team_a_id, 
                    team_b_id=team_b_id, 
                    game_field_id=game_field,
                    created_by=request.user
                )

                # Process requested referees
                referees_data = request.data.get('referees', [])
                for referee_data in referees_data:
                    user_id = referee_data.get('user_id')
                    fees = referee_data.get('fees', 0)

                    if fees and int(fees) > 0:  # Only create entry if fees > 0
                        try:
                            RequestedReferee.objects.create(
                                game_id=friendly_game,
                                user_id_id=user_id,
                                fees=fees,
                                status=RequestedReferee.REQUESTED
                            )
                        except Exception as e:
                            # Log or handle any specific errors (like invalid user_id)
                            print(e)
                            continue

                # Notify eligible team members (coaches and managers)
                team_a_name = friendly_game.team_a.team_name
                team_b_name = friendly_game.team_b.team_name if team_b_id else None
                game_field_name=friendly_game.game_field_id.field_name
                start_time = friendly_game.game_start_time.strftime('%H:%M')
                date=friendly_game.game_date.strftime('%d-%m')
              


                # Notify eligible team members (coaches and managers)
                self.notify_team_members(team_a_id, request.user, team_b_id, team_a_name, team_b_name, game_field_name, date,start_time)


                return Response({
                    'status': 1,
                    'message': _('Friendly game created successfully.'),
                    'data': FriendlyGameSerializer(friendly_game).data
                }, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response({
                    'status': 0,
                    'message': _('A game with these details already exists.'),
                    'data': {}
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 0,
            'message': _('Invalid data.'),
            'data': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def notify_team_members(self, team_id, creator_user, team_b_id=None, opponent_team_name=None, team_b_name=None, game_field_name=None, game_date=None, start_time=None,game_id=None):
        """
        Notify eligible team members (coaches and managers) about a new friendly game.
        """
        # Notify Team B Members
        if team_b_id:
            team_b_members = JoinBranch.objects.filter(
                branch_id=team_b_id,  # Filter users by role (Coach or Manager)
                joinning_type__in=[JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE]  # Staff types only
            )
            for member in team_b_members:
                user = member.user_id
                notification_language = user.current_language
                if notification_language in ['ar', 'en']:
                    activate(notification_language)

                # Prepare and send push notification
                device_token = user.device_token  # Assuming `device_token` is stored in the User model
                device_type = user.device_type    # Assuming `device_type` is stored in the User model (1 for Android, 2 for iOS)
                title = _("Your Game is Scheduled")
                body = _("You have a Friendly Game against {opponent_team_name} at {game_date} {start_time} at {game_field_name}").format(
                    opponent_team_name=opponent_team_name,  # Dynamically added opponent team name
                    game_date=game_date,
                    start_time=start_time,
                    game_field_name=game_field_name
                )
                push_data = {
              
                "game_id": game_id,  # Team ID to associate with the notification
                "game_type": "friendly",  # Specify that this is a friendly game
              
                    
            
                }
                if device_token:
                    send_push_notification(
                        device_token=device_token,
                        title=title,
                        body=body,
                        device_type=device_type,
                        data=push_data  # Optionally include game-related data

                    )




        else:       
            user_datas = User.objects.filter(Q(role__id=3) | Q(role__id=6))
            for user_data in user_datas:
                # print(user_datas)
            
            
            
            
                team_members = JoinBranch.objects.filter(
                    user_id=user_data.id,  # Filter users by role (Coach or Manager)
                    joinning_type__in=[JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE]  # Staff types only
                ).exclude(user_id=creator_user.id)  # Optimize query by prefetching related user data
                # print("fghfgh",team_members)

            

            # Iterate through the filtered users and send notifications
                for member in team_members:
                    print(member.id)
                    print(member)
                
                    user = member.user_id
                    notification_language = user.current_language
                    if notification_language in ['ar', 'en']:
                        activate(notification_language)

                    # Prepare and send push notification
                    device_token = user.device_token  # Assuming `device_token` is stored in the User model
                    device_type = user.device_type    # Assuming `device_type` is stored in the User model (1 for Android, 2 for iOS)
                    title = _("A new friendly game has been created!")
                    body = _("Make sure to check it out.")

                    push_data = {
                            "game_id": game_id,  # Include the game ID
                            "game_type": "friendly",  # Specify that this is a friendly game
                            
                    }

                    if device_token:
                        send_push_notification(
                            device_token=device_token,
                            title=title,
                            body=body,
                            device_type=device_type,
                            data=push_data  # Optionally include game-related data
                        )



    
    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get the game_id from query parameters
        game_id = request.query_params.get('game_id')
        if not game_id:
            return Response({
                'status': 0,
                'message': _('Game ID is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the friendly game using the game_id
            friendly_game = FriendlyGame.objects.select_related('team_a', 'team_b', 'game_field_id').get(id=game_id)
        except FriendlyGame.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Friendly game not found.'),
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Prepare custom response data
        data = {
            "game_id":friendly_game.id,
            "game_name":friendly_game.game_name,
            "game_number":friendly_game.game_number,
            "team_a_id": friendly_game.team_a.id if friendly_game.team_a else None,
            "team_a_name": friendly_game.team_a.team_name if friendly_game.team_a else None,
            "team_b_id": friendly_game.team_b.id if friendly_game.team_b else None,
            "team_b_name": friendly_game.team_b.team_name if friendly_game.team_b else None,
            "start_time": str(friendly_game.game_start_time) if friendly_game.game_start_time else None,
            "end_time": str(friendly_game.game_end_time) if friendly_game.game_end_time else None,
            "start_date": str(friendly_game.game_date) if friendly_game.game_date else None,
            "game_field_id": friendly_game.game_field_id.id,
            "game_field_name": friendly_game.game_field_id.field_name,
        }

        return Response({
            'status': 1,
            'message': _('Friendly game fetched successfully.'),
            'data': data
        }, status=status.HTTP_200_OK)
    
################## Request Referee ##################
########## Add fee #################
class RefereeFeeCreateUpdateView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        game_id = data.get('game_id')
        officials_data = data.get('officials')
        
        if not game_id or not officials_data:
            return Response({
                'status': 0,
                'message': _('Game ID and officials are required.'),
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the game exists
        try:
            game = FriendlyGame.objects.get(id=game_id)
        except FriendlyGame.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Game not exists'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create or update referees for the game in a transaction to ensure atomicity
        try:
            updated_referees = []
            with transaction.atomic():
                for official in officials_data:
                    user_id = official.get('user_id')
                    fees = official.get('fees')
                    
                    # Try to get or update the RequestedReferee entry
                    referee, created = RequestedReferee.objects.update_or_create(
                        game_id_id=game_id,  # ForeignKey, hence game_id_id is used here
                        user_id_id=user_id,  # ForeignKey, hence user_id_id is used here
                        defaults={'fees': fees, 'status': RequestedReferee.REQUESTED}
                    )
                    
                    # Append the updated or created referee details
                    updated_referees.append({
                        'user_id': user_id,
                        'fees': fees
                    })
            
            return Response({
                'status': 1,
                'message': _('Referees requested successfully.'),
                'data': [{
                    'game_id': game_id,
                    'officials': updated_referees
                }]
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'status': 0,
                'message': str(e),
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)


################ Raferee status update ############


    def patch(self, request, *args, **kwargs):
        # Extract the game_id, user_id, and status from the request data
        game_id = request.data.get('game_id')
        user_id = request.data.get('user_id')
        status_value = request.data.get('status')
        status_value=int(status_value)
        game_id=int(game_id)
        user_id=int(user_id)

        # Validate the input
        if not game_id or not user_id or not status_value:
            return Response({
                'status': 0,
                'message': _('game_id, user_id, and status are required'),
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate the status value to ensure it is only APPROVED (1) or REJECT (2)
        if status_value not in [1, 2]:
            return Response({
                'status': 0,
                'message': _('Invalid status value. Only APPROVED or REJECT are allowed'),
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Try to get the RequestedReferee object based on game_id and user_id
        try:
            referee = RequestedReferee.objects.get(game_id_id=game_id, user_id_id=user_id)
        except RequestedReferee.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Requested Referee not found for the provided game_id and user_id'),
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
        if referee.fees is None:
            return Response({
                'status': 0,
                'message': _('Referee must have a fee assigned to be approved'),
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update the status field
        referee.status = status_value
        referee.save()
        if status_value == 1:
            game = referee.game_id
            user = referee.user_id

            # Activate the user's notification language
            notification_language = user.current_language
            if notification_language in ['ar', 'en']:
                activate(notification_language)

            # Notification message (assumes translated strings are available in locale files)
            notification_title = _("You have been selected as a referee!")
            notification_body = _(
                "You have been selected as a referee for the friendly game {game_name} "
                "of {team_a_name} and {team_b_name} on {date} "
                "at {start_time} in {field_name}. Check it out!"
            ).format(
                game_name=game.game_name,
                team_a_name=game.team_a.team_name,
                team_b_name=game.team_b.team_name,
                date=game.game_date,
                start_time=game.game_start_time,
                field_name=game.game_field_id.field_name
            )

            # Fetch device token and type
            device_token = user.device_token
            device_type = user.device_type  # ANDROID or IOS

            # Send push notification
            push_data = {
                "game_id": game_id,
                "game_type": "friendly",  # Specify that this is a friendly game
                "user_id": user_id  # Add user_id to the push data
            }
            try:
                send_push_notification(
                    device_token=device_token,
                    title=notification_title,
                    body=notification_body,
                    device_type=device_type,
                    data=push_data,
                
                )
            except Exception as e:
                return Response({
                    'status': 0,
                    'message': _('Failed to send notification: ') + str(e),
                    'data': None
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'status': 1,
            'message': _('Referee status updated successfully'),
            'data': {
                'game_id': game_id,
                'user_id': user_id,
                'status': referee.status
            }
        }, status=status.HTTP_200_OK)



########### search referee ############


class OfficialListView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser,)

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        role_id = 4  # Role 4 for referees
        
        # Only include users who are referees (role_id=4) and not deleted
        users = User.objects.filter(role_id=role_id, is_deleted=False).order_by('id')

        # Prepare the data to be returned in the response
        user_data = [
            {
                'id': user.id,
                'name': user.username,
                'fees':None,
                # 'phone': user.phone,
                # 'profile_picture': user.profile_picture.url if user.profile_picture else None,
                # 'country_id': user.country.id if user.country else None,
                # 'country_name': user.country.name if user.country else None,
                # 'country_flag': user.country.flag.url if user.country else None,
            }
            for user in users
        ]

        # Return the list of users
        return Response({
            'status': 1, 
            'message': _('Referee list fetched successfully'), 
            'data': user_data
        }, status=status.HTTP_200_OK)

############### Update Friendly Game ################
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
                'message': _('Invalid id of Team B.'),
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


            team_a_id=game.team_a_id
            team_b_name = game.team_b.team_name if team_b_id else None
            game_field_name=game.game_field_id.field_name
            start_time = game.game_start_time.strftime('%H:%M')
            date=game.game_date.strftime('%d-%m')
            game_id=game.id
            
        

            # Notify team_a's coach and manager
            self.notify_team_a_coach_and_manager(team_a_id,team_b_id,team_b_name, date, start_time, game_field_name)

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

    def notify_team_a_coach_and_manager(self,team_a_id,team_b_id, team_b_name, game_date, start_time, game_field_name,game_id):
        """
        Notify coach and manager of team A when team B is assigned.
        """
        team_a_members = JoinBranch.objects.filter(
            branch_id=team_a_id,  # Filter users by role (Coach or Manager)
            joinning_type__in=[JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE]  # Staff types only
        )

        for member in team_a_members:
            user = member.user_id
            notification_language = user.current_language
            if notification_language in ['ar', 'en']:
                activate(notification_language)

            # Prepare and send push notification
            device_token = user.device_token  # Assuming `device_token` is stored in the User model
            device_type = user.device_type    # Assuming `device_type` is stored in the User model (1 for Android, 2 for iOS)
            title = _("Your Game is Scheduled")
            body = _("You have a Friendly Game against {opponent_team_name} at {game_date} {start_time} at {game_field_name}").format(
                opponent_team_name=team_b_name,  # Dynamically added opponent team name (team B)
                game_date=game_date,
                start_time=start_time,
                game_field_name=game_field_name
            )
            push_data = {
               
                "game_type": "friendly",  # Specify that this is a friendly game
                "team_b_id": team_b_id  # Add team_b_name to give more context in the notification
            }
            if device_token:
                send_push_notification(
                    device_token=device_token,
                    title=title,
                    body=body,
                    device_type=device_type,
                    data=push_data  # Optionally include game-related data
                )


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
                'message': _('Cannot delete a game that has already Started.'),
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
        return Response({
            'status': 1,
            'message': _('Data fetched successfully.'),
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

        # Filter games where game_date is in the future and team_b is None
        games = FriendlyGame.objects.filter(game_date__gte=date.today(), team_b=None)

        # Initialize pagination
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(games, request, view=self)

        # If paginated queryset exists, serialize the data and return paginated response
        if paginated_queryset is not None:
            serializer = FriendlyGameSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Fallback response if no pagination
        serializer = FriendlyGameSerializer(games, many=True)
        return Response({
            'status': 1,
            'message': _('Data fetched successfully.'),
            'data': serializer.data
        })
    
######################### List of all Teams for Team B  ###################
class TeamBranchListView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        team_a_id = request.query_params.get('team_a_id', None)  # ID to exclude
        search_key = request.query_params.get('search', '')  # Search key for team_name

        # Get all branches
        queryset = TeamBranch.objects.all()

        # Exclude team_a if provided
        if team_a_id:
            queryset = queryset.exclude(id=team_a_id)

        # Filter by team_name if search_key is provided
        if search_key:
            queryset = queryset.filter(team_name__icontains=search_key)

        # Order by team_name alphabetically
        queryset = queryset.order_by('team_name')

        # Serialize data
        serializer = TeamBranchSearchSerializer(queryset, many=True, context={'request': request})

        # Return response
        return Response({
            "status": 1,
            "message": _("Teams fetched successfully."),
            "data": serializer.data
        }, status=status.HTTP_200_OK)

####################### Fetch Friendly Games Detail #####################

class FriendlyGameDetailAPIView(APIView):
    def get(self, request, *args, **kwargs):
        game_id = request.query_params.get('game_id')

        # Validate required parameters
        if not game_id:
            return Response({
                "status": 0,
                "message": "Game ID is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the game details
            game = FriendlyGame.objects.get(id=game_id)
        except FriendlyGame.DoesNotExist:
            return Response({
                "status": 0,
                "message": "Game not found for the given Game ID."
            }, status=status.HTTP_404_NOT_FOUND)

        # Calculate game duration
        if game.game_start_time and game.game_end_time:
            start_time = datetime.combine(game.game_date, game.game_start_time)
            end_time = datetime.combine(game.game_date, game.game_end_time)
            duration = end_time - start_time
            game_duration = str(duration)  # Convert timedelta to string
        else:
            game_duration = None  # If either time is missing

        # Construct response data
        game_data = {
            "id": game.id,
            "tournament_name": "Friendly Game",
            "team_a_id": game.team_a.id if game.team_a else None,
            "team_a_name": game.team_a.team_name if game.team_a else None,
            "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a and game.team_a.team_id and game.team_a.team_id.team_logo else None,
            "team_b_id": game.team_b.id if game.team_b else None,
            "team_b_name": game.team_b.team_name if game.team_b else None,
            "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b and game.team_b.team_id and game.team_b.team_id.team_logo else None,
            "game_field_id": game.game_field_id.id if game.game_field_id else None,
            "game_field_name": game.game_field_id.field_name if game.game_field_id else None,
            "filed_location":{
                    "latitude": game.game_field_id.latitude if game.game_field_id.latitude else 0.0,
                    "longitude": game.game_field_id.longitude if game.game_field_id.longitude else 0.0,
                    "address": game.game_field_id.address if game.game_field_id.address else "",
                    "house_no": game.game_field_id.house_no if game.game_field_id.house_no else "",
                    "premises": game.game_field_id.premises if game.game_field_id.premises else "",
                    "street": game.game_field_id.street if game.game_field_id.street else "",
                    "city": game.game_field_id.city if game.game_field_id.city else "",
                    "state": game.game_field_id.state if game.game_field_id.state else "",
                    "country_name": game.game_field_id.country_name if game.game_field_id.country_name else "",
                    "postalCode": game.game_field_id.postalCode if game.game_field_id.postalCode else "",
                    "country_code": game.game_field_id.country_code if game.game_field_id.country_code else "",
                },
            "game_date": game.game_date,
            "game_start_time": game.game_start_time,
            "game_end_time": game.game_end_time,
            "game_duration": game_duration,  # Include game duration
            "created_by": game.created_by.id,
        }

        return Response({
            "status": 1,
            "message": "Game details fetched successfully.",
            "data": game_data
        }, status=status.HTTP_200_OK)


################## participates players of particular team for particular tournament ###############

class FriendlyGameTeamPlayersAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, team_id):
        """
        Check if the user has the required role and valid membership in the team.
        """
        if user.role.id not in [3, 6]:
            return False

        try:
            # Check if the user is part of the team with managerial or coach staff type
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
        game_id = request.query_params.get('game_id')  # Game ID to filter
        
        if not team_id:
            return Response({
                'status': 0,
                'message': _('team_id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate `game_id`
        if not game_id:
            return Response({
                'status': 0,
                'message': _('game_id is required.'),
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

        # Fetch players belonging to the specified team
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

        # Get the IDs of all players
        player_user_ids = [player.user_id.id for player in players]

        # Exclude players already added to the lineup for the specified game
        excluded_player_ids = FriendlyGameLineup.objects.filter(
            team_id=team_id,
            player_id__in=player_user_ids,
            game_id=game_id,
            lineup_status__in=[
                FriendlyGameLineup.ADDED,
                FriendlyGameLineup.ALREADY_IN_LINEUP
            ]
        ).values_list('player_id', flat=True)

        # Fetch player details excluding those in the lineup
        lineups = User.objects.filter(id__in=player_user_ids).exclude(id__in=excluded_player_ids)

        response_data = []
        for player in lineups:
            # Fetch player's lineup entry for the game
            lineup_entry = FriendlyGameLineup.objects.filter(
                player_id=player.id,
                game_id=game_id
            ).first()

            # Fetch lineup status and jersey number from FriendlyGameLineup and FriendlyGamePlayerJersey
            lineup_status = None
            jersey_number = None
            if lineup_entry:
                lineup_status = lineup_entry.lineup_status
                jersey_entry = FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup_entry).first()
                jersey_number = jersey_entry.jersey_number if jersey_entry else None

            response_data.append({
                "id": player.id,
                "team_id": team_id,
                "team_name": team_name.team_name,
                "player_id": player.id,
                "player_name": player.username,
                "player_profile_picture": player.profile_picture.url if player.profile_picture else None,
                "jersey_number": jersey_number,  # Jersey number from FriendlyPlayerJersey
                "lineup_status": lineup_status,  # Include lineup status
                "created_at": player.created_at,
                "updated_at": player.updated_at,
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

        # Convert team_id to integer if necessary
        try:
            team_id = int(team_id)
        except (ValueError, TypeError):
            return Response({
                'status': 0,
                'message': _('Invalid team_id.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

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

        # Validate game existence
        try:
            game = FriendlyGame.objects.get(id=game_id)
        except FriendlyGame.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('The specified game does not exist.'),
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
            lineup = FriendlyGameLineup.objects.get(
                player_id=player.user_id,
                game_id=game,
                team_id=team
            )
        except FriendlyGameLineup.DoesNotExist:
            lineup = None

        # Update lineup status based on current lineup size
        existing_players = FriendlyGameLineup.objects.filter(team_id=team, game_id=game)
        added_or_in_lineup_count = existing_players.filter(
            lineup_status__in=[FriendlyGameLineup.ADDED, FriendlyGameLineup.ALREADY_IN_LINEUP]
        ).count()

        if lineup:
            # If the player is already in the lineup, update their status
            if lineup.lineup_status == FriendlyGameLineup.ALREADY_IN_LINEUP:
                lineup_status = lineup.lineup_status  # Keep the status as ALREADY_IN_LINEUP
            else:
                lineup_status = FriendlyGameLineup.SUBSTITUTE if added_or_in_lineup_count >= 11 else FriendlyGameLineup.ADDED
            lineup.lineup_status = lineup_status
            lineup.save()
        else:
            # Add a new player to the lineup
            lineup_status = FriendlyGameLineup.SUBSTITUTE if added_or_in_lineup_count >= 11 else FriendlyGameLineup.ADDED
            lineup = FriendlyGameLineup.objects.create(
                player_id=player.user_id,
                game_id=game,
                team_id=team,
                lineup_status=lineup_status
            )

        # Determine if reload is needed
        reload = added_or_in_lineup_count >= 11  # Reload if there are 11 or more players

        message = _('Lineup updated successfully.')
        if lineup_status == FriendlyGameLineup.SUBSTITUTE:
            message = _('Player Substituted.')
        else:
            message = _('Player Added')

        # Return success response
       

        # Return success response
        return Response({
            'status': 1,
            'message': message,
            'data': {
                'team_id': team.id,
                'team_name': team.team_name,
                'player_id': player.user_id.id,
                'player_name': player.user_id.username,  # Adjust field if necessary
                'game_id': game.id,
                'game_name': game.game_name,  # Adjust field if necessary
                'lineup_status': 'ADDED' if lineup_status == FriendlyGameLineup.ADDED else 'SUBSTITUTE',
                'reload': reload,
                'count': added_or_in_lineup_count + 1  # Include the current player in the count
            }
        }, status=status.HTTP_200_OK)



    def delete(self, request, *args, **kwargs):
        # Extract parameters from query string
        team_id = request.query_params.get('team_id')
        player_id = request.query_params.get('player_id')
        game_id = request.query_params.get('game_id')

        # Ensure all required fields are provided
        if not team_id:
            return Response({
                'status': 0,
                'message': _('team_id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        if not player_id:
            return Response({
                'status': 0,
                'message': _('player_id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        if not game_id:
            return Response({
                'status': 0,
                'message': _('game_id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate user access to the team
        if not self._has_access(request.user, team_id):
            return Response({
                'status': 0,
                'message': _('You do not have permission to access this team.'),
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Try to retrieve the lineup entry based on provided criteria
        lineup = FriendlyGameLineup.objects.filter(
            player_id=player_id,
            team_id=team_id,
            game_id=game_id,
            lineup_status=FriendlyGameLineup.ADDED  # Only consider entries that are currently added
        ).first()

        # Check if the lineup entry exists
        if lineup is None:
            return Response({
                'status': 0,
                'message': _('No entries found.'),
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Update the lineup status to REMOVED (0)
        lineup.lineup_status = 0  # 0 represents "REMOVED"
        lineup.created_by_id = request.user.id  # Add created_by_id when deleting
        lineup.save()

        # Prepare response data with lineup details
        response_data = {
            'player_id': lineup.player_id.id,
            'team_id': lineup.team_id.id,
            'game_id': lineup.game_id.id,
            'lineup_status': lineup.lineup_status  # This will now be 0 (REMOVED)
        }

        # Return success response
        return Response({
            'status': 1,
            'message': _('Lineup Player Removed successfully.'),
            'data': response_data
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
                    'data': {}
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
                'jersey_number': FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).exists() else None

            } for lineup in added_lineups]

            # Prepare response data for substitute players
            substitute_data = [{
                'id':lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'jersey_number': FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).exists() else None
            } for lineup in substitute_lineups]

            already_added_data = [{
                'id':lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'jersey_number': FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).exists() else None
            } for lineup in already_added_lineups]

            # Return the response with the status and message
            return Response({
                'status': 1,
                'message': _('Lineup players fetched successfully.'),
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
        game_id = request.data.get('game_id')
        positions = request.data.get('positions', [])  # List of {player_id, position_1}

        # Check if the user has the required permissions
        user = request.user
        if not self._has_access(user, team_id):
            return Response({
                'status': 0,
                'message': _('You do not have the required permissions to perform this action.'),
            }, status=status.HTTP_403_FORBIDDEN)

        # Validate team_id and game_id
        if not team_id:
            return Response({
                'status': 0,
                'message': _('Team ID is required.'),
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
                # Fetch lineup by player_id, team_id, and game_id
                lineup = FriendlyGameLineup.objects.get(
                    player_id=player_id,
                    team_id=team_id,
                    game_id=game_id
                )

                # Update lineup details based on position_1 value
                if position_1 == "0":
                    lineup.position_1 = None  # Set position_1 to NULL
                    lineup.lineup_status = FriendlyGameLineup.ADDED  # Set status to ADDED
                else:
                    lineup.position_1 = position_1
                    lineup.lineup_status = FriendlyGameLineup.ALREADY_IN_LINEUP  # Set status to ALREADY_IN_LINEUP

                lineup.created_by_id = user.id  # Set the updated user
                lineup.save()

                  
                game = FriendlyGame.objects.get(id=game_id)
           
                opponent_team = game.team_b if game.team_a.id == team_id else game.team_a

                # Get the user's current language for notification
                notification_language = lineup.player_id.current_language
                if notification_language in ['ar', 'en']:
                    activate(notification_language)

                # Send notification to the player
                send_push_notification(
                    device_token=lineup.player_id.device_token,
                    title=_("You have been added to a game"),
                    body=_(
                        "You have been added to a game of {game_name} against {opponent_team}"
                    ).format(
                        game_name=game.game_name,
                
                       
                     
                        opponent_team=opponent_team.team_name
                    ),
                    device_type=lineup.player_id.device_type,
                    data={"game_id": game.id, "team_id": team_id, "opponent_team_id": opponent_team.id,"game_type":"friendly"}
                )



            except FriendlyGameLineup.DoesNotExist:
                errors.append({
                    'player_id': player_id,
                    'message': _('Lineup not found for this player.')
                })

        # Fetch updated data for the response
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

        # Prepare data for response
        def prepare_lineup_data(lineups):
            return [{
                'id': lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'jersey_number': FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).exists() else None
            } for lineup in lineups]

        added_data = prepare_lineup_data(added_lineups)
        substitute_data = prepare_lineup_data(substitute_lineups)
        already_added_data = prepare_lineup_data(already_added_lineups)

        # Prepare final response
        return Response({
            'status': 1 if not errors else 0,
            'message': _('Playing 11 Updated Successfully') if not errors else _('Some players could not be updated.'),
            'data': {
                'added': added_data,
                'substitute': substitute_data,
                'player_added_in_lineup': already_added_data,
            }
        }, status=status.HTTP_200_OK if not errors else status.HTTP_400_BAD_REQUEST)

  
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
                'jersey_number': FriendlyGamePlayerJersey.objects.filter(lineup_players=player).first().jersey_number if FriendlyGamePlayerJersey.objects.filter(lineup_players=player).exists() else None
            } for player in already_added_lineups]

            substitute_data = [{
                'id':lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'jersey_number': FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).exists() else None
            } for lineup in substitute_lineups]

            return Response({
                'status': 1,
                'message': _('Player Removed From Playing 11.'),
                'data': {
                    'already_added': already_added_data,
                    'substitute': substitute_data

                }
            }, status=status.HTTP_200_OK)

        except FriendlyGameLineup.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Lineup not found'),
            }, status=status.HTTP_404_NOT_FOUND)

# ################## Add player jersey of particular team of particular games in particular tournament ###############
class FriendlyAddPlayerJerseyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, team_id):

        if user.role.id not in [3, 6]:
            return False

        try:
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
        players_data = request.data.get('players', [])  # Expecting a list of {player_id, jersey_number}

        # Initialize response data for validations
        validation_errors = []

        # Validate team_id
        if not team_id:
            validation_errors.append({
                'field': 'team_id',
                'message': _('team_id is required.')
            })

        # Validate game_id
        if not game_id:
            validation_errors.append({
                'field': 'game_id',
                'message': _('game_id is required.')
            })

        # Validate players_data
        if not isinstance(players_data, list) or len(players_data) == 0:
            validation_errors.append({
                'field': 'players',
                'message': _('Players details are required.')
            })

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
                    'message': _('player_id is required.')
                })
                continue

            # Validate team and player existence
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
                game = FriendlyGame.objects.get(id=game_id)
            except FriendlyGame.DoesNotExist:
                response_data.append({
                    'player_id': player_id,
                    'status': 0,
                    'message': _('The specified friendly game does not exist.')
                })
                continue

            # Validate that the team is part of the friendly game
            if team_id != game.team_a.id and team_id != game.team_b.id:
                response_data.append({
                    'player_id': player_id,
                    'status': 0,
                    'message': _('The specified team is not part of this friendly game.')
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
                existing_jersey = FriendlyGamePlayerJersey.objects.filter(
                    lineup_players__team_id=team,
                    lineup_players__game_id=game,
                    jersey_number=jersey_number
                ).first()

                if existing_jersey:
                    # Set the existing jersey number to null before assigning it to the new player
                    existing_jersey.jersey_number = None
                    existing_jersey.save()

                try:
                    lineup, created = FriendlyGameLineup.objects.update_or_create(
                        player_id=player.user_id,
                        team_id=team,
                        game_id=game,
                        defaults={
                            'player_ready': False,
                            'created_by_id': request.user.id,
                        }
                    )

                    # Now, create or update the PlayerJersey instance
                    player_jersey, created_jersey = FriendlyGamePlayerJersey.objects.update_or_create(
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
                        'jersey_number': jersey_number,
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
                try:
                    lineup, created = FriendlyGameLineup.objects.update_or_create(
                        player_id=player.user_id,
                        team_id=team,
                        game_id=game,
                        defaults={
                            'player_ready': False,
                            'created_by_id': request.user.id,
                        }
                    )

                    player_jersey, created_jersey = FriendlyGamePlayerJersey.objects.update_or_create(
                        lineup_players=lineup,
                        defaults={
                            'jersey_number': None,
                            'created_by_id': request.user.id
                        }
                    )

                    response_data.append({
                        'player_id': player.user_id.id,
                        'team_id': team.id,
                        'game_id': game.id,
                        'jersey_number': None,
                        'status': 1,
                        'message': _('Jersey number deleted.')
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


################## Players games stats lineup in Friendly ###############

class FriendlyGameStatsLineupPlayers(APIView):
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
        last_stat = FriendlyGamesPlayerGameStats.objects.filter(
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

        # Validate team_a_id, team_b_id, game_id, tournament_id as before...

        if not self._has_access(request.user, game_id=game_id):
            return Response({
                'status': 0,
                'message': _('You do not have access to this resource.'),
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)
        
           # Calculate team goals
    
        friendly_game = FriendlyGame.objects.select_related('team_a', 'team_b').get(id=game_id)
        team_a_goals = FriendlyGamesPlayerGameStats.objects.filter(
            team_id=team_a_id, game_id=game_id
        ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

        team_b_goals = FriendlyGamesPlayerGameStats.objects.filter(
            team_id=team_b_id, game_id=game_id
        ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

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

            substitute_data = [{
                'id': lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'jersey_number': FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).exists() else None,
                'lastupdate': self.get_last_update(lineup.player_id.id, game_id)  # Use self to call the method
            } for lineup in substitute_lineups]

            already_added_data = [{
                'id': lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'jersey_number': FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).exists() else None,
                'lastupdate': self.get_last_update(lineup.player_id.id, game_id)  # Use self to call the method
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
                'tournament_logo':None,
                'tournament_name':"Friendly Game",
                'goals': {
                    'team_a_id': friendly_game.team_a.id,
                    'team_a_name': friendly_game.team_a.team_name,
                    'team_a_total_goals': team_a_goals,
                    'team_a_logo': friendly_game.team_a.team_id.team_logo.url if friendly_game.team_a.team_id.team_logo else None,
                    'team_b_id': friendly_game.team_b.id,
                    'team_b_name': friendly_game.team_b.team_name,
                    'team_b_total_goals': team_b_goals,
                    'team_b_logo': friendly_game.team_b.team_id.team_logo.url if friendly_game.team_b.team_id.team_logo else None,
                },
                'lineup': lineup_data
            }
        }, status=status.HTTP_200_OK)


    


class FriendlyGameLineupPlayerStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, game_id=None):
        """
        Check if the user has access to the game based on role and official type.
        """
        # Check if the user's role is 4
        if user.role.id != 4:
            return False

        if game_id:
            try:
                # Check if the game exists for the friendly game
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

        # Retrieve game_id from query parameters
        game_id = request.query_params.get('game_id')

        # Check if game_id is provided
        if not game_id:
            return Response({
                'status': 0,
                'message': _('game_id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user has access to this game
        if not self._has_access(request.user, game_id):
            return Response({
                'status': 0,
                'message': _('Access denied. You do not have permission to view this game.'),
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            # Retrieve the game details from FriendlyGame
            game = FriendlyGame.objects.get(id=game_id)
        except FriendlyGame.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Game not found.'),
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Fetch all lineup entries based on game_id
        lineup_entries = FriendlyGameLineup.objects.filter(
            game_id=game_id,
            lineup_status__in=[FriendlyGameLineup.SUBSTITUTE, FriendlyGameLineup.ALREADY_IN_LINEUP]
        )

        if not lineup_entries.exists():
            return Response({
                'status': 1,
                'message': _('No players found.'),
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
                if lineup.lineup_status == FriendlyGameLineup.ALREADY_IN_LINEUP:
                    team_a_added_players.append({
                        **player_data,
                        'team_id': game.team_a.id,
                        'team_name': game.team_a.team_name,  # Assuming `team_name` field exists in `TeamBranch`
                    })
                elif lineup.lineup_status == FriendlyGameLineup.SUBSTITUTE:
                    team_a_substitute_players.append({
                        **player_data,
                        'team_id': game.team_a.id,
                        'team_name': game.team_a.team_name,  # Assuming `team_name` field exists in `TeamBranch`
                    })

            elif lineup.team_id == game.team_b:
                # Further classify by lineup status
                if lineup.lineup_status == FriendlyGameLineup.ALREADY_IN_LINEUP:
                    team_b_added_players.append({
                        **player_data,
                        'team_id': game.team_b.id,
                        'team_name': game.team_b.team_name,  # Assuming `team_name` field exists in `TeamBranch`
                    })
                elif lineup.lineup_status == FriendlyGameLineup.SUBSTITUTE:
                    team_b_substitute_players.append({
                        **player_data,
                        'team_id': game.team_b.id,
                        'team_name': game.team_b.team_name,  # Assuming `team_name` field exists in `TeamBranch`
                    })


        team_a_ready_count = FriendlyGameLineup.objects.filter(
            team_id=game.team_a,
          
            game_id=game_id,
            lineup_status=3,
            player_ready=True
        ).count()

        team_b_ready_count = FriendlyGameLineup.objects.filter(
            team_id=game.team_b,
           
            game_id=game_id,
            lineup_status=3,
            player_ready=True
        ).count()
        print(team_b_ready_count)

        # Send notifications to team_a coaches and managers if they have 11 players ready
        if team_a_ready_count == 11:
            team_a_name = game.team_a.team_name
            team_a_coaches_and_managers = JoinBranch.objects.filter(
                branch_id=game.team_a,
                joinning_type__in=[JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE]
            )
            for join in team_a_coaches_and_managers:
                user = join.user_id
                notification_language = user.current_language
                if notification_language in ['ar', 'en']:
                    activate(notification_language)

                send_push_notification(
                    device_token=user.device_token,
                    title=_("Let's Go"),
                    body=_("Your {team_name} team is ready to play!").format(team_name=team_a_name),
                    device_type=user.device_type,
                    data={"game_id":game.id,"team_id": game.team_a.id,"game_type":"friendly"}
                )

        # Send notifications to team_b coaches and managers if they have 11 players ready
        print(team_b_ready_count == 11)
        if team_b_ready_count == 11:
            team_b_name = game.team_b.team_name
            team_b_coaches_and_managers = JoinBranch.objects.filter(
                branch_id=game.team_b,
                joinning_type__in=[JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE]
            )
            for join in team_b_coaches_and_managers:
                user = join.user_id
                notification_language = user.current_language
                if notification_language in ['ar', 'en']:
                    activate(notification_language)

                send_push_notification(
                    device_token=user.device_token,
                    title=_("Let's Go"),
                    body=_("Your {team_name} team is ready to play!").format(team_name=team_b_name),
                    device_type=user.device_type,
                    data={"game_id":game.id,"team_id": game.team_b.id,"game_type":"friendly"}
                )

        # If both teams are ready, send a notification to coaches and managers of both teams
        if team_a_ready_count == 11 and team_b_ready_count == 11:
            team_a_coaches_and_managers = JoinBranch.objects.filter(
                branch_id=game.team_a,
                joinning_type__in=[JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE]
            )
            team_b_coaches_and_managers = JoinBranch.objects.filter(
                branch_id=game.team_b,
                joinning_type__in=[JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE]
            )

            for join in team_a_coaches_and_managers:
                user = join.user_id
                notification_language = user.current_language
                if notification_language in ['ar', 'en']:
                    activate(notification_language)

                send_push_notification(
                    device_token=user.device_token,
                    title=_("Let's Go"),
                    body=_("Both teams are ready to play! Let's Go"),
                    device_type=user.device_type,
                    data={"game_id":game.id,"team_id": game.team_a.id,"game_type":"friendly"}
                )

            for join in team_b_coaches_and_managers:
                user = join.user_id
                notification_language = user.current_language
                if notification_language in ['ar', 'en']:
                    activate(notification_language)

                send_push_notification(
                    device_token=user.device_token,
                    title=_("Let's Go"),
                    body=_("Both teams are ready to play! Let's Go"),
                    device_type=user.device_type,
                    data={"game_id":game.id,"team_id": game.team_b.id,"game_type":"friendly"}
                )


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

        # Retrieve player_id, team_id, and game_id from request data
        player_id = request.data.get('player_id')
        team_id = request.data.get('team_id')
        game_id = request.data.get('game_id')

        # Validate player_id
        if not player_id:
            return Response({
                'status': 0,
                'message': _('player_id is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate team_id
        if not team_id:
            return Response({
                'status': 0,
                'message': _('team_id is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate game_id
        if not game_id:
            return Response({
                'status': 0,
                'message': _('game_id is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user has access to the game
        if not self._has_access(request.user, game_id):
            return Response({
                'status': 0,
                'message': _('Access denied. You do not have permission to view this game.'),
                'data': {}
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
                'message': _('Lineup entry not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Toggle the player_ready status
        lineup_entry.player_ready = not lineup_entry.player_ready
        lineup_entry.created_by_id = request.user.id
        lineup_entry.save()

        return Response({
            'status': 1,
            'message': _('Player status updated successfully.'),
            'data': {
                'player_id': player_id,
                'team_id': team_id,
                'game_id': game_id,
                'player_ready': lineup_entry.player_ready
            }
        }, status=status.HTTP_200_OK)







############################### Game Officilas Search API #########################

############ Custom User Search Pagination ##############
class FriendlyOfflicialSearchPaggination(PageNumberPagination):
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
class FriendlyOfficialSearchView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = FriendlyOfflicialSearchPaggination  # Set the pagination class

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
            joined_users = FriendlyGameGameOfficials.objects.filter(game_id=game_id).values_list('official_id', flat=True)
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
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the game exists
        game = get_object_or_404(FriendlyGame, id=game_id)

        # Fetch all official types
        all_official_types = FriendlyGameOfficialsType.objects.all()

        # Fetch assigned officials for the given game
        assigned_game_officials = FriendlyGameGameOfficials.objects.filter(game_id=game_id)

        # Prepare the response data, grouping by official type
        officials_by_type = {}
        for official_type in all_official_types:
            # Serialize the official type
            type_serializer = FriendlyGameOficialTypeSerializer(official_type, context={'language': language})
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

        # Ensure required fields are provided
        if not game_id or not official_id or not officials_type_id:
            return Response({
                'status': 0,
                'message': _('game_id, official_id, and officials_type_id are required.'),
                'data': {}
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
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create the new GameOfficial entry
        game_official = FriendlyGameGameOfficials.objects.create(
            game_id=game,
            official_id=official,
            officials_type_id=officials_type
        )

        # Serialize the official type for the response
        type_serializer = FriendlyGameOficialTypeSerializer(officials_type, context={'language': language})
        try:
        # Retrieve the official's device token and language preference
            device_token = official.device_token  # Assuming User model has `device_token` field
            notification_language = official.current_language  # Assuming User model has `current_language` field

            # Activate the official's preferred language
            if notification_language in ['ar', 'en']:
                activate(notification_language)

            if device_token:
                title = _('You have been appointed to officiate a friendly game.')

                # Include detailed information in the body
                body = _(
                    'You have been appointed as {officials_type} to the friendly game between {team_a} and {team_b} on {date} {time} at {location} .'
                ).format(
                    team_a=game.team_a.team_name,  # Assuming `team_a_name` is a field in the `game` object
                    team_b=game.team_b.team_name,  # Assuming `team_b_name` is a field in the `game` object
                    date=game.game_date.strftime('%d-%b'),  # Format the date and time
                    time=game.game_start_time.strftime('%H:%M'),
                    location=game.game_field_id.field_name,  # Assuming `location` is a field in the `game` object
                    officials_type=type_serializer.data['name']
                )
                push_data={
                    "game_id": game.id,  # The game ID
                }


                # Send the push notification to the official
                send_push_notification(device_token, title, body, device_type=official.device_type,data=push_data)  # device_type: 1 for Android, 2 for iOS
        except Exception as e:
            logging.error(f"Error sending push notification: {str(e)}", exc_info=True)

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
                'data': {}
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
                'message': _('No official found for the given game.'),
            }, status=status.HTTP_404_NOT_FOUND)


class FriendlyPlayerGameStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, game_id=None):
        # Check if the user is the game_statistics_handler for the specified friendly game.
        if game_id:
            try:
                game = FriendlyGame.objects.get(id=game_id)
                if game.game_statistics_handler == user:
                    return True
            except FriendlyGame.DoesNotExist:
                pass  # Game not found or doesn't match; access denied
        return False

    def get_last_update(self, player_id, game_id): 
        # Fetch the most recent update for the player
        last_stat = FriendlyGamesPlayerGameStats.objects.filter(
            Q(player_id_id=player_id) | Q(in_player_id=player_id) | Q(out_player_id=player_id),
            game_id=game_id
        ).order_by('-updated_at').first()

        if last_stat:
            if last_stat.goals > 0:
                return 'goal'
            elif last_stat.yellow_cards > 0:
                return 'yellow_card'
            elif last_stat.red_cards > 0:
                return 'red_card'
            elif last_stat.in_player_id == player_id:
                return 'substituted'
            elif last_stat.out_player_id == player_id:
                return 'substituted'
        return None

    def _update_team_goals(self, game_instance):
        # Updates the total goals for both teams in a friendly game instance.
        game_instance.team_a_goal = FriendlyGamesPlayerGameStats.objects.filter(
            team_id=game_instance.team_a.id,
            game_id=game_instance.id
        ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

        game_instance.team_b_goal = FriendlyGamesPlayerGameStats.objects.filter(
            team_id=game_instance.team_b.id,
            game_id=game_instance.id
        ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

        game_instance.save()

    def _get_game_stats_response(self, game_instance, team_id, player_id, game_id):
        # Returns stats, goals, and lineup details for friendly games.
        team_a_goals = FriendlyGamesPlayerGameStats.objects.filter(
            team_id=game_instance.team_a.id,
            game_id=game_instance.id
        ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

        team_b_goals = FriendlyGamesPlayerGameStats.objects.filter(
            team_id=game_instance.team_b.id,
            game_id=game_instance.id
        ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

        lineup_data = {}
        for team_id, team_key in [(game_instance.team_a.id, 'team_a'), (game_instance.team_b.id, 'team_b')]:
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

            substitute_data = [{
                'id': lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'jersey_number': FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).exists() else None,
                'lastupdate': self.get_last_update(lineup.player_id.id, game_id)
            } for lineup in substitute_lineups]

            already_added_data = [{
                'id': lineup.id,
                'player_id': lineup.player_id.id,
                'player_username': lineup.player_id.username,
                'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
                'position_1': lineup.position_1,
                'jersey_number': FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).exists() else None,
                'lastupdate': self.get_last_update(lineup.player_id.id, game_id)
            } for lineup in already_added_lineups]

            lineup_data[team_key] = {
                'player_added_in_lineup': already_added_data,
                'substitute': substitute_data
            }

        return Response({
            'status': 1,
            'message': _('Stats updated and lineup fetched successfully.'),
            'data': {
                'game_id': game_instance.id,
                'tournament_logo':None,
                'tournament_name':"Friendly Game",
                'goals': {
                    'team_a_id': game_instance.team_a.id,
                    'team_a_name': game_instance.team_a.team_name,
                    'team_a_total_goals': team_a_goals,
                    'team_a_logo': game_instance.team_a.team_id.team_logo.url if game_instance.team_a.team_id.team_logo else None,
                    'team_b_id': game_instance.team_b.id,
                    'team_b_name': game_instance.team_b.team_name,
                    'team_b_total_goals': team_b_goals,
                    'team_b_logo': game_instance.team_b.team_id.team_logo.url if game_instance.team_b.team_id.team_logo else None,
                },
                **lineup_data
            }
        }, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        # Set language based on the request headers
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Retrieve required identifiers from the request data
        player_id = request.data.get('player_id')
        team_id = request.data.get('team_id')
        game_id = request.data.get('game_id')
        game_time = request.data.get('game_time')

        time_format_regex = r"^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$"

        if not game_time or not re.match(time_format_regex, game_time):
            return Response(
                {
                    'status': 0,
                    'message': _('Game time is required and must be in hh:mm:ss format (00:00:00 to 23:59:59).')
                },status=status.HTTP_400_BAD_REQUEST
            )

        # Validate required fields
        if not all([player_id, team_id, game_id, game_time]):
            return Response({'status': 0, 'message': _('All fields are required.')}, status=status.HTTP_400_BAD_REQUEST)

        # Check access
        if not self._has_access(request.user, game_id=game_id):
            return Response({'status': 0, 'message': _('You do not have access to this resource.')}, status=status.HTTP_403_FORBIDDEN)

        # Retrieve model instances
        team_instance = get_object_or_404(TeamBranch, id=team_id)
        player_instance = get_object_or_404(User, id=player_id)
        game_instance = get_object_or_404(FriendlyGame, id=game_id)

        if game_instance.finish:
            return Response({'status': 0, 'message': _('Cannot modify stats for a finished game.')}, status=status.HTTP_400_BAD_REQUEST)

        # Process statistics
        stats_keys = ['goals', 'assists', 'own_goals', 'yellow_cards', 'red_cards']
        for stat in stats_keys:
            stat_value = request.data.get(stat)

            if stat_value is not None:  # Check if the stat is included in the request
                stat_value = int(stat_value)

                if stat_value == 1:
                    # Increment: Create a new entry
                    FriendlyGamesPlayerGameStats.objects.create(
                        player_id=player_instance,
                        team_id=team_instance,
                        game_id=game_instance,
                        game_time=game_time,
                        **{stat: 1},  # Set the specific stat to 1
                        created_by_id=request.user.id
                    )

                    # Send push notification
                    self._send_stat_notification(player_instance, stat, game_instance)

                    # Update team goals
                    self._update_team_goals(game_instance)
                    return self._get_game_stats_response(game_instance, team_id, player_id, game_instance.id)

                elif stat_value == -1:
                    # Decrement: Find and delete the most recent entry for this stat
                    stat_count = FriendlyGamesPlayerGameStats.objects.filter(
                        player_id=player_instance,
                        team_id=team_instance,
                        game_id=game_instance,
                        **{stat: 1}
                    ).count()

                    if stat_count > 0:
                        latest_stat = FriendlyGamesPlayerGameStats.objects.filter(
                            player_id=player_instance,
                            team_id=team_instance,
                            game_id=game_instance,
                            **{stat: 1}
                        ).order_by('-created_at').first()
                        latest_stat.delete()
                        self._update_team_goals(game_instance)
                        return self._get_game_stats_response(game_instance, team_id, player_id)
                    else:
                        return Response({'status': 0, 'message': _(f'Cannot decrement {stat.capitalize()} as it cannot go below zero.')}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 0, 'message': _('Invalid request data.')}, status=status.HTTP_400_BAD_REQUEST)

    def _send_stat_notification(self, player_instance, stat, game_instance):
        """
        Sends a push notification when a player's statistics are updated in a friendly game.
        """
        # Define the notification content with translations
        stat_messages = {
            'goals': _('You just scored a goal!'),
            'assists': _('You just made an assist!'),
            'own_goals': _('You just scored an own goal!'),
            'yellow_cards': _('You just received a yellow card!'),
            'red_cards': _('You just received a red card!'),
        }

        # Customize the message based on the stat type
        message = stat_messages.get(stat, _('Your statistics have been updated!'))

        # Set the language based on player's current_language
        print(f"Player's preferred language: {player_instance.current_language}")
        notification_language = player_instance.current_language  # Use player's preferred language

        if notification_language in ['en', 'ar']:
            activate(notification_language)  # Activate language for notification
            print(f"Language activated: {notification_language}")
            print(_('You just scored a goal!'))  # Check translation

        # Translate each part of the notification message
        translated_message = _(message)
        translated_game_number = _(f"Game Number {game_instance.game_number}")

        # Construct the notification body
        notification_body = f"{translated_message} in Friendly Game - {translated_game_number}"

        # Print the notification details to verify the message content
        print(f"Notification title: {_('Statistics Updated!')}")
        print(f"Notification body: {notification_body}")

        # Send the notification to the player
        if player_instance.device_token:
            push_data = {'type': 'player_stat', 'player_id': player_instance.id, 'game_id': game_instance.id}
            send_push_notification(player_instance.device_token, _('Statistics Updated!'), notification_body, player_instance.device_type, data=push_data)


    def get(self, request, *args, **kwargs):
        # Set language based on the request headers
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Retrieve query parameters for filtering
        player_id = request.query_params.get('player_id')
        team_id = request.query_params.get('team_id')
        game_id = request.query_params.get('game_id')

        # Validate required parameters
        required_params = {
            'player_id': player_id,
            'team_id': team_id,
            'game_id': game_id
        }
        
        for key, value in required_params.items():
            if not value:
                return Response({
                    'status': 0,
                    'message': _(f'{key} is required.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Check access rights
        if not self._has_access(request.user, game_id=game_id):
            return Response({
                'status': 0,
                'message': _('You do not have access to this resource.'),
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            # Retrieve all matching player stats
            stats = FriendlyGamesPlayerGameStats.objects.filter(
                player_id=player_id,
                team_id=team_id,
                game_id=game_id
            )

            # If no stats found, return 0 for all stats
            if not stats.exists():
                total_stats = {
                    'id': None,  # or an appropriate default value
                    'team_id': team_id,
                    'player_id': player_id,
                    'game_id': game_id,
                    'goals': 0,
                    'assists': 0,
                    'yellow_cards': 0,
                    'red_cards': 0,
                    'own_goals': 0
                }

                return Response({
                    'status': 1,
                    'message': _('Player stats fetched successfully.'),
                    'data': [total_stats]
                }, status=status.HTTP_200_OK)

            # Calculate totals
            totals = stats.aggregate(
                total_goals=Sum('goals'),
                total_assists=Sum('assists'),
                total_yellow_cards=Sum('yellow_cards'),
                total_red_cards=Sum('red_cards'),
                total_own_goals=Sum('own_goals')
            )

            # Format the response data
            total_stats = {
                'id': stats.first().id,  # Assuming IDs are uniform for aggregated data
                'team_id': stats.first().team_id.id,
                'player_id': stats.first().player_id.id,
                'game_id': stats.first().game_id.id,
                'goals': totals['total_goals'] or 0,
                'assists': totals['total_assists'] or 0,
                'yellow_cards': totals['total_yellow_cards'] or 0,
                'red_cards': totals['total_red_cards'] or 0,
                'own_goals': totals['total_own_goals'] or 0
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



class FriendlyPlayerGameStatsTimelineAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, game_id=None):
        """
        Check if the user is the game_statistics_handler for the specified game.
        """
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

        game_id = request.query_params.get('game_id')

        if not game_id:
            return Response({'status': 0, 'message': _('game_id is required.')}, status=status.HTTP_400_BAD_REQUEST)

        if not self._has_access(request.user, game_id=game_id):
            return Response({'status': 0, 'message': _('You do not have access to this resource.'), 'data': {}}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Fetch game and calculate total goals for both teams
            friendly_game = FriendlyGame.objects.get(id=game_id)
            team_a_goals = FriendlyGamesPlayerGameStats.objects.filter(
                team_id=friendly_game.team_a.id, game_id=game_id
            ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0
            team_b_goals = FriendlyGamesPlayerGameStats.objects.filter(
                team_id=friendly_game.team_b.id, game_id=game_id
            ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

            # Fetch all stats for the game and order by game_time descending
            team_stats = FriendlyGamesPlayerGameStats.objects.filter(
                game_id=game_id
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
                    'tournament_logo':None,
                    'tournament_name':"Friendly Game",
                    'goals': {
                        'team_a_id': friendly_game.team_a.id,
                        'team_a_name': friendly_game.team_a.team_name,
                        'team_a_total_goals': team_a_goals,
                        'team_a_logo': friendly_game.team_a.team_id.team_logo.url if friendly_game.team_a.team_id.team_logo else None,
                        'team_b_id': friendly_game.team_b.id,
                        'team_b_name': friendly_game.team_b.team_name,
                        'team_b_total_goals': team_b_goals,
                        'team_b_logo': friendly_game.team_b.team_id.team_logo.url if friendly_game.team_b.team_id.team_logo else None,
                    },
                    'timeline': timeline
                }
            }, status=status.HTTP_200_OK)

        except FriendlyGame.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Game not found.'),
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

    
####################  player substitute #####################
class FriendlyPlayerSubstitutionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, game_id=None):
        if game_id:
            try:
                game = FriendlyGame.objects.get(id=game_id)
                if game.game_statistics_handler == user:
                    return True
            except FriendlyGame.DoesNotExist:
                pass
        return False

    def get_last_update(self, player_id, game_id):  # Simplified for friendly games
        last_stat = FriendlyGamesPlayerGameStats.objects.filter(
            Q(player_id_id=player_id) | Q(in_player_id=player_id) | Q(out_player_id=player_id),
            game_id=game_id
        ).order_by('-updated_at').first()

        if last_stat:
            if last_stat.goals > 0:
                return 'goal'
            elif last_stat.yellow_cards > 0:
                return 'yellow_card'
            elif last_stat.red_cards > 0:
                return 'red_card'
            elif last_stat.in_player_id == player_id or last_stat.out_player_id == player_id:
                return 'substituted'
        return None

    def _format_lineup_data(self, lineup, game_id):
        return {
            'id': lineup.id,
            'player_id': lineup.player_id.id,
            'player_username': lineup.player_id.username,
            'profile_picture': lineup.player_id.profile_picture.url if lineup.player_id.profile_picture else None,
            'position_1': lineup.position_1,
            'jersey_number': FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).first().jersey_number if FriendlyGamePlayerJersey.objects.filter(lineup_players=lineup).exists() else None,
            'lastupdate': self.get_last_update(lineup.player_id.id, game_id)
        }

    def _format_managerial_staff(self, staff):
        return {
            'id': staff.id,
            'staff_id': staff.user_id.id,
            'staff_username': staff.user_id.username,
            'profile_picture': staff.user_id.profile_picture.url if staff.user_id.profile_picture else None,
            'joining_type_id': staff.joinning_type,
            'joining_type_name': staff.get_joinning_type_display()
        }

    def post(self, request):
        # Handle language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract inputs
        team_id = request.data.get("team_id")
        game_id = request.data.get("game_id")
        player_a_id = request.data.get("player_a_id")
        player_b_id = request.data.get("player_b_id")
        game_time = request.data.get("game_time")

        time_format_regex = r"^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$"

        if not game_time or not re.match(time_format_regex, game_time):
            return Response(
                {
                    'status': 0,
                    'message': _('Game time is required and must be in hh:mm:ss format (00:00:00 to 23:59:59).')
                },status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate inputs
        if not team_id or not game_id or not player_a_id or not player_b_id:
            return Response({'status': 0, 'message': _('All fields (team_id, game_id, player_a_id, player_b_id) are required.')}, status=status.HTTP_400_BAD_REQUEST)

        # Access check
        if not self._has_access(request.user, game_id=game_id):
            return Response({'status': 0, 'message': _('You do not have access to this resource.')}, status=status.HTTP_403_FORBIDDEN)

        # Retrieve players
        try:
            player_a = FriendlyGameLineup.objects.get(team_id=team_id, game_id=game_id, player_id=player_a_id, lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP)
            player_b = FriendlyGameLineup.objects.get(team_id=team_id, game_id=game_id, player_id=player_b_id, lineup_status=FriendlyGameLineup.SUBSTITUTE)
        except FriendlyGameLineup.DoesNotExist as e:
            return Response({'status': 0, 'message': _('Player not found or not in correct lineup status.'), 'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Swap positions and statuses
        player_b.position_1 = player_a.position_1
        player_a.position_1 = None
        player_a.player_ready = False
        player_b.player_ready = True
        player_a.lineup_status = FriendlyGameLineup.SUBSTITUTE
        player_b.lineup_status = FriendlyGameLineup.ALREADY_IN_LINEUP
        player_a.save()
        player_b.save()

        # Log substitution
        try:
            player_game_stat = FriendlyGamesPlayerGameStats.objects.create(
                team_id=get_object_or_404(TeamBranch, id=team_id),
                game_id=get_object_or_404(FriendlyGame, id=game_id),
                player_id=player_b.player_id,
                in_player=player_b.player_id,
                out_player=player_a.player_id,
                game_time=game_time,
                created_by_id=request.user.id
            )
        except IntegrityError as e:
            return Response({'status': 0, 'message': _('Failed to log substitution.'), 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Goals aggregation
        game_instance = get_object_or_404(FriendlyGame, id=game_id)
        team_a_goals = FriendlyGamesPlayerGameStats.objects.filter(team_id=game_instance.team_a.id, game_id=game_id).aggregate(total_goals=Sum('goals'))['total_goals'] or 0
        team_b_goals = FriendlyGamesPlayerGameStats.objects.filter(team_id=game_instance.team_b.id, game_id=game_id).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

        # Fetch lineup data
        lineup_data = {}
        for team, team_key in [(game_instance.team_a, 'team_a'), (game_instance.team_b, 'team_b')]:
            substitute_lineups = FriendlyGameLineup.objects.filter(team_id=team.id, game_id=game_id, lineup_status=FriendlyGameLineup.SUBSTITUTE)
            already_added_lineups = FriendlyGameLineup.objects.filter(team_id=team.id, game_id=game_id, lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP)

            lineup_data[team_key] = {
                'player_added_in_lineup': [self._format_lineup_data(lineup, game_id) for lineup in already_added_lineups],
                'substitute': [self._format_lineup_data(lineup, game_id) for lineup in substitute_lineups],
                'managerial_staff': [self._format_managerial_staff(staff) for staff in JoinBranch.objects.filter(branch_id=team.id, joinning_type=JoinBranch.MANAGERIAL_STAFF_TYPE).select_related('user_id')]
            }

        # Response
        return Response({
            'status': 1,
            'message': _('Player substitution successful.'),
            'data': {
                'game_id': game_id,
                'tournament_logo':None,
                'tournament_name':"Friendly Game",
                'goals': {
                    'team_a_id': game_instance.team_a.id,
                    'team_a_name': game_instance.team_a.team_name,
                    'team_a_total_goals': team_a_goals,
                    'team_a_logo': game_instance.team_a.team_id.team_logo.url if game_instance.team_a.team_id.team_logo else None,
                    'team_b_id': game_instance.team_b.id,
                    'team_b_name': game_instance.team_b.team_name,
                    'team_b_total_goals': team_b_goals,
                    'team_b_logo': game_instance.team_b.team_id.team_logo.url if game_instance.team_b.team_id.team_logo else None,
                },
                **lineup_data
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
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not self._has_access(request.user, game_id=game_id):
            return Response({
                'status': 0,
                'message': _('You do not have access to this resource.'),
                'data': {}
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
        } for lineup in substitute_lineups]

        
        # Return the response with the status and message
        return Response({
            'status': 1,
            'message': _('Lineup players fetched successfully with status "ADDED".'),
            'data': {
                
                'substitute_players': substitute_data,
                
            }
        }, status=status.HTTP_200_OK)

################# player Swap position ########################
class FriendlyGameSwapPositionView(APIView):
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
            return Response({
                'status': 0,
                'message': _('Player ID, target position, team ID, and game ID are required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the player's lineup entry, ensuring that it belongs to the correct team and game
        player_lineup = get_object_or_404(FriendlyGameLineup, player_id=player_id, team_id=team_id, game_id=game_id)

        # Check if the player's lineup status is ALREADY_IN_LINEUP (status = 3)
        if player_lineup.lineup_status != FriendlyGameLineup.ALREADY_IN_LINEUP:
            return Response({
                'status': 0,
                'message': _('The player in the target position must also be in the starting 11 lineup to swap positions.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        
        # Check if there's already a player in the target position within the same game and team
        target_lineup = FriendlyGameLineup.objects.filter(game_id=game_id, team_id=team_id, position_1=target_position).first()
        
        if target_lineup:
            if target_lineup.lineup_status != FriendlyGameLineup.ALREADY_IN_LINEUP:
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
                    "player_1": FriendlyGameSwapPositionSerializer(player_lineup).data,
                    "player_2": FriendlyGameSwapPositionSerializer(target_lineup).data
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
                    "player": FriendlyGameSwapPositionSerializer(player_lineup).data
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
            return Response({
                'status': 0,
                'message': _('Team ID and Game ID are required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Filter lineups based on team_id and game_id
        lineups = FriendlyGameLineup.objects.filter(team_id=team_id, game_id=game_id, lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP)

        # If no lineups are found, return an appropriate message
        if not lineups.exists():
            return Response({
                'status': 0,
                'message': _('No lineups found for the provided team and game.'),
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        
        # Serialize the lineups
        serializer = FriendlyGameSwapPositionSerializer(lineups, many=True)
        
        return Response({
            'status': 1,
            'message': _('Lineups retrieved successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


############################# Frindly Game H2H With Recent Meetings With Game Stats ################################################
class FriendlyGamesh2hCompleteAPIView(APIView):
    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        team_a_id = request.query_params.get('team_a', None)
        team_b_id = request.query_params.get('team_b', None)

        if not team_a_id or not team_b_id:
            return Response({
                'status': 0,
                'message': _('Both Team A and Team B IDs are required'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Query all games from both tables
        tournament_games = TournamentGames.objects.filter(
            Q(team_a_id=team_a_id) | Q(team_b_id=team_a_id) |
            Q(team_a_id=team_b_id) | Q(team_b_id=team_b_id)
        )

        friendly_games = FriendlyGame.objects.filter(
            Q(team_a_id=team_a_id) | Q(team_b_id=team_a_id) |
            Q(team_a_id=team_b_id) | Q(team_b_id=team_b_id)
        )

        # Combine games for statistics
        all_games = chain(tournament_games, friendly_games)

        # Calculate stats
        team_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0})

        for game in all_games:
            if game.is_draw:
                if game.team_a and game.team_b:
                    team_stats[game.team_a.id]['draws'] += 1
                    team_stats[game.team_b.id]['draws'] += 1
            else:
                if game.winner_id and game.loser_id:
                    team_stats[int(game.winner_id)]['wins'] += 1
                    team_stats[int(game.loser_id)]['losses'] += 1

        # Stats output
        team_a_stats = team_stats.get(int(team_a_id), {'wins': 0, 'losses': 0, 'draws': 0})
        team_b_stats = team_stats.get(int(team_b_id), {'wins': 0, 'losses': 0, 'draws': 0})

        stats = {
            "team_a_win": team_a_stats['wins'],
            "team_b_win": team_b_stats['wins'],
            "team_a_lose": team_a_stats['losses'],
            "team_b_lose": team_b_stats['losses'],
            "team_a_draw": team_a_stats['draws'],
            "team_b_draw": team_b_stats['draws'],
            "team_a_Duel_success_rate" : 0,
            "team_b_Duel_success_rate" : 0,
            "team_a_Total_Long_passes" : 0,
            "team_b_Total_Long_passes" : 0,
            "team_a_Aerial_duels_success_rate" : 0,
            "team_b_Aerial_duels_success_rate" : 0,
        }

        # Query recent meetings
        recent_tournament_games = TournamentGames.objects.filter(
            (Q(team_a_id=team_a_id) & Q(team_b_id=team_b_id)) |
            (Q(team_a_id=team_b_id) & Q(team_b_id=team_a_id)),
             finish=True
        ).order_by('-game_start_time')

        recent_friendly_games = FriendlyGame.objects.filter(
            (Q(team_a_id=team_a_id) & Q(team_b_id=team_b_id)) |
            (Q(team_a_id=team_b_id) & Q(team_b_id=team_a_id)),
            finish=True
        ).order_by('-game_start_time')

        # Combine and sort by start time
        recent_games = sorted(
            chain(recent_tournament_games, recent_friendly_games),
            key=attrgetter('game_start_time'), reverse=True
        )[:5]

        # Serialize recent games
        recent_meetings = []
        for game in recent_games:
            game_data = {
                'id': game.id,
                'team_a_name': game.team_a.team_name if game.team_a else None,
                'team_b_name': game.team_b.team_name if game.team_b else None,
                'team_a_goal': game.team_a_goal,
                'team_b_goal': game.team_b_goal,
                'game_date': game.game_date,
                'game_field_name': game.game_field_id.field_name if game.game_field_id else None,
                'type': 'Tournament' if isinstance(game, TournamentGames) else 'Friendly'
            }
            recent_meetings.append(game_data)

        return Response({
            'status': 1,
            'message': _('H2H Fetch Successfully'),
            'data': {
                "stats": stats,
                "recent_meetings": recent_meetings
            }
        }, status=status.HTTP_200_OK)




############################ FriendlyGame Game Stats  API ########################################
class FriendlyTeamGameDetailStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        try:
            # Activate language settings based on header
            language = request.headers.get('Language', 'en')
            if language in ['en', 'ar']:
                activate(language)

            # Extract and validate query parameters
            game_id = request.query_params.get('game_id')

            if not game_id:
                return Response({
                    'status': 0, 
                    'message': _('game_id is required.')
                    },status=status.HTTP_400_BAD_REQUEST
                )

            # Fetch the friendly game object
            game = FriendlyGame.objects.filter(id=game_id).select_related('team_a', 'team_b').first()

            if not game:
                return Response({
                    'status': 0, 
                    'message': _('Game not found with the given criteria.')
                    },status=status.HTTP_404_NOT_FOUND
                )

            # Prepare response data
            def format_team_data(team, prefix):
                return {
                    f"{prefix}_id": team.id if team else None,
                    f"{prefix}_name": team.team_name if team else None
                }

            def format_stats(prefix, game):
                return {
                    "possession": getattr(game, f"{prefix}_possession", 0.0),
                    "interception": getattr(game, f"{prefix}_interception", 0),
                    "offside": getattr(game, f"{prefix}_offside", 0),
                    "corner": getattr(game, f"{prefix}_corner", 0),
                }

            response_data = {
                **format_team_data(game.team_a, "team_a"),
                **format_team_data(game.team_b, "team_b"),
                "General": {
                    "team_a": format_stats("general_team_a", game),
                    "team_b": format_stats("general_team_b", game)
                },
                "Defence": {
                    "team_a": format_stats("defence_team_a", game),
                    "team_b": format_stats("defence_team_b", game)
                },
                "Distribution": {
                    "team_a": format_stats("distribution_team_a", game),
                    "team_b": format_stats("distribution_team_b", game)
                },
                "Attack": {
                    "team_a": format_stats("attack_team_a", game),
                    "team_b": format_stats("attack_team_b", game)
                },
                "Discipline": {
                    "team_a": format_stats("discipline_team_a", game),
                    "team_b": format_stats("discipline_team_b", game)
                }
            }

            # Return success response
            return Response(
                {
                    "status": 1,
                    "message": _("Game detail stats fetched successfully."),
                    "data": response_data,
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    "status": 0,
                    "message": _("An unexpected error occurred. Please try again later."),
                    "error": str(e),  # Optional: Remove in production for security
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

############### Friendly Game Detail API for Both Team LineUp See ####################
class FriendlyGamesDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        # Set language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get parameters from request query
        game_id = request.query_params.get('game_id')

        if not game_id:
            return Response({
                'status': 0,
                'message': _('game_id is required.'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the friendly game
            game = FriendlyGame.objects.get(id=game_id)
        except FriendlyGame.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Friendly game not found.'),
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Helper function to fetch team data
        def fetch_team_data(team):
            if not team:
                return None

            # Filter players in Lineup by team and game, separating by status
            substitute_lineups = FriendlyGameLineup.objects.filter(
                team_id=team.id,
                game_id=game_id,
                lineup_status=FriendlyGameLineup.SUBSTITUTE
            )
            already_added_lineups = FriendlyGameLineup.objects.filter(
                team_id=team.id,
                game_id=game_id,
                lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP
            )

            # Fetch the staff types for the given team_id
            staff_types = JoinBranch.objects.filter(branch_id=team.id).select_related('user_id', 'user_id__country')

            staff_data = {
                'managerial_staff': [],
                'coach_staff': [],
                'medical_staff': []
            }

            def get_user_country_data(user):
                """Helper to get country name and flag."""
                return {
                    'country_name': user.country.name if user.country else None,
                    'country_flag': user.country.flag.url if user.country and user.country.flag else None
                }

            for staff in staff_types:
                user = staff.user_id
                country_data = get_user_country_data(user)

                staff_info = {
                    'id': user.id,
                    'username': user.username,
                    'profile_picture': user.profile_picture.url if user.profile_picture else None,
                    'joining_type_id': staff.joinning_type,
                    'joining_type_name': staff.get_joinning_type_display(),
                    **country_data
                }

                if staff.joinning_type == JoinBranch.MANAGERIAL_STAFF_TYPE:
                    staff_data['managerial_staff'].append(staff_info)
                elif staff.joinning_type == JoinBranch.COACH_STAFF_TYPE:
                    staff_data['coach_staff'].append(staff_info)
                elif staff.joinning_type == JoinBranch.MEDICAL_STAFF_TYPE:
                    staff_data['medical_staff'].append(staff_info)

            # Prepare response data for players
            def get_player_data(lineup):
                user = lineup.player_id
                country_data = get_user_country_data(user)
                return {
                    'id': user.id,
                    'username': user.username,
                    'profile_picture': user.profile_picture.url if user.profile_picture else None,
                    'position_1': lineup.position_1,
                    **country_data
                }

            substitute_data = [get_player_data(lineup) for lineup in substitute_lineups]
            already_added_data = [get_player_data(lineup) for lineup in already_added_lineups]

            return {
                'team_id': team.id,
                'team_name': team.team_name,
                'player_added_in_lineup': already_added_data,
                'substitute': substitute_data,
                **staff_data
            }

        # Fetch data for team A and team B
        team_a_data = fetch_team_data(game.team_a)
        team_b_data = fetch_team_data(game.team_b)

        # Return the response
        return Response({
            'status': 1,
            'message': _('Lineup players fetched successfully.'),
            'data': {
                'team_a': team_a_data,
                'team_b': team_b_data
            }
        }, status=status.HTTP_200_OK)


################################ Get Uniform API when first Screen Call by manager ######################
class FriendlyGameUniformAPIView(APIView):
    def get(self, request, *args, **kwargs):
        team_id = request.query_params.get('team_id')
        game_id = request.query_params.get('game_id')
        user_role = request.user.role.id
        if user_role not in [3, 6]:
            return Response({
            'status': 0,
            'message': _('Access denied. You do not have the necessary role for this action.'),
            'data': None,
        }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            game = FriendlyGame.objects.get(id=game_id)
        except FriendlyGame.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('The specified game does not exist.'),
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

        data = {}

        if game.team_a.id == int(team_id):
            data = {
                "primary_color_player": game.team_a_primary_color_player,
                "secondary_color_player": game.team_a_secondary_color_player,
                "primary_color_goalkeeper": game.team_a_primary_color_goalkeeper,
                "secondary_color_goalkeeper": game.team_a_secondary_color_goalkeeper
            }
        elif game.team_b.id == int(team_id):
            data = {
                "primary_color_player": game.team_b_primary_color_player,
                "secondary_color_player": game.team_b_secondary_color_player,
                "primary_color_goalkeeper": game.team_b_primary_color_goalkeeper,
                "secondary_color_goalkeeper": game.team_b_secondary_color_goalkeeper
            }
        else:
            return Response({
                'status': 0,
                'message': _('The specified team_id does not match any team in this game.'),
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 1,
            'message': _('Colors retrieved successfully.'),
            'data': data
        }, status=status.HTTP_200_OK)
    
######################################### Create Uniform API by Manager #############################

class FriendlyGameUniformColorAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, team_id):
        if user.role.id not in [3, 6]:  # Restrict to roles Manager/Coach
            return False

        try:
            JoinBranch.objects.get(
                branch_id_id=team_id,
                user_id=user,
                joinning_type__in=[JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE],
            )
            return True
        except ObjectDoesNotExist:
            return False

    def post(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        serializer = FriendlyTeamUniformColorSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            game_id = validated_data['game_id']
            team_id = validated_data['team_id']
            primary_color_player = validated_data['primary_color_player']
            secondary_color_player = validated_data['secondary_color_player']
            primary_color_goalkeeper = validated_data['primary_color_goalkeeper']
            secondary_color_goalkeeper = validated_data['secondary_color_goalkeeper']
            if not self._has_access(request.user, team_id):
                return Response({
                    'status': 0,
                    'message': _('Access denied. You do not have permission for this team.'),
                    'data': None,
                }, status=status.HTTP_403_FORBIDDEN)

            try:
                game = FriendlyGame.objects.get(id=game_id)
            except FriendlyGame.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Game not found.'),
                    'data': None,
                }, status=status.HTTP_404_NOT_FOUND)
            
            team_id = int(team_id)
            # Update uniform colors for the matched team
            if team_id == game.team_a.id:
                game.team_a_primary_color_player = primary_color_player
                game.team_a_secondary_color_player = secondary_color_player
                game.team_a_primary_color_goalkeeper = primary_color_goalkeeper
                game.team_a_secondary_color_goalkeeper = secondary_color_goalkeeper
            elif team_id == game.team_b.id:
                game.team_b_primary_color_player = primary_color_player
                game.team_b_secondary_color_player = secondary_color_player
                game.team_b_primary_color_goalkeeper = primary_color_goalkeeper
                game.team_b_secondary_color_goalkeeper = secondary_color_goalkeeper
            else:
                return Response({
                    'status': 0,
                    'message': _('The specified team_id does not match any team in this game.'),
                    'data': None,
                }, status=status.HTTP_400_BAD_REQUEST)

            game.save()

            return Response({
                'status': 1,
                'message': _('Uniform Added Successfully'),
                'data': serializer.validated_data,
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 0,
            'message': _('Invalid data.'),
            'data': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    

######## Refree Uniform Fetch API #####################    
class FetchFriendlyGameUniformColorAPIView(APIView):
    def _has_access(self, user, game_id=None):
        if user.role.id != 4:  # Restrict to Referee role
            return False

        if game_id:
            try:
                # Check if the user is associated with the game as an official with specific types
                official = FriendlyGameGameOfficials.objects.filter(
                    game_id_id=game_id,
                    official_id=user,
                    officials_type_id__in=[2, 3, 4, 5]  # Allowed official types
                ).exists()

                if official:
                    return True

            except FriendlyGame.DoesNotExist:
                pass  # Game not found; access denied

        return False

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        game_id = request.query_params.get('game_id')

        if not game_id:
            return Response({
                'status': 0,
                'message': _('game_id is required.'),
                'data': None,
            }, status=status.HTTP_400_BAD_REQUEST)

        if not self._has_access(request.user, game_id=game_id):
            return Response({
                'status': 0,
                'message': _('Access denied. You do not have permission for this game.'),
                'data': None,
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            game = FriendlyGame.objects.get(id=game_id)
        except FriendlyGame.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Game not found.'),
                'data': None,
            }, status=status.HTTP_404_NOT_FOUND)

        team_a_data = {
            "team_id": game.team_a.id,
            "team_name": game.team_a.team_name,
            "primary_color_player": game.team_a_primary_color_player,
            "secondary_color_player": game.team_a_secondary_color_player,
            "primary_color_goalkeeper": game.team_a_primary_color_goalkeeper,
            "secondary_color_goalkeeper": game.team_a_secondary_color_goalkeeper,
        }

        team_b_data = {
            "team_id": game.team_b.id,
            "team_name": game.team_b.team_name,
            "primary_color_player": game.team_b_primary_color_player,
            "secondary_color_player": game.team_b_secondary_color_player,
            "primary_color_goalkeeper": game.team_b_primary_color_goalkeeper,
            "secondary_color_goalkeeper": game.team_b_secondary_color_goalkeeper,
        }

        return Response({
            'status': 1,
            'message': _('Uniform information fetched successfully.'),
            'data': {
                'team_a': team_a_data,
                'team_b': team_b_data
            },
        }, status=status.HTTP_200_OK)



class FriendlyGameResult(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def patch(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
 
        game_id = request.data.get('game_id')  # Extract game_id from URL parameters
         # Get tournament_id from the request data

        try:
            # Get the game by game_id and tournament_id
            game = FriendlyGame.objects.get(id=game_id)
        except FriendlyGame.DoesNotExist:
            return Response({
                "status": 0,
                "message": _("Game not found for the given tournament.")
            }, status=status.HTTP_404_NOT_FOUND)

        # Retrieve the goals scored by each team in the game
        team_a_goals = FriendlyGamesPlayerGameStats.objects.filter(
            team_id=game.team_a.id,
            game_id=game.id,
            tournament_id=game.tournament_id.id
        ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

        team_b_goals = FriendlyGamesPlayerGameStats.objects.filter(
            team_id=game.team_b.id,
            game_id=game.id,
            tournament_id=game.tournament_id.id
        ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

        # Check if the finish status is provided and is true
        finish = request.data.get('finish', 'false').lower() == 'true'

        if finish:
            # If the game is finished, determine the result
            if team_a_goals == 0 and team_b_goals == 0:
                # If both teams have 0-0, set is_draw to True
                game.is_draw = True
            else:
                # If one team wins, set is_draw to False
                game.is_draw = False
                if team_a_goals > team_b_goals:
                    game.winner_id = game.team_a.id
                    game.loser_id = game.team_b.id
                else:
                    game.winner_id = game.team_b.id
                    game.loser_id = game.team_a.id

            # Set the finish status to True and update the scores
            game.finish = True
            game.team_a_goal = team_a_goals
            game.team_b_goal = team_b_goals
            game.save()

            return Response({
                "status": 1,
                "message": _("Game updated successfully."),
                "data": {
                    "id": game.id,
                    "tournament_id": game.tournament_id.id,
                    "is_draw": game.is_draw,
                    "finish": game.finish,
                    "team_a_goal": game.team_a_goal,
                    "team_b_goal": game.team_b_goal,
                    "winner_id": game.winner_id,
                    "loser_id": game.loser_id,
                }
            }, status=status.HTTP_200_OK)

        else:
            # If finish is not true, return the current game state with null values for is_draw and finish
            return Response({
                "status": 1,
                "message": _("Match is still running."),
                "data": {
                    "id": game.id,
                    "tournament_id": game.tournament_id.id,
                    "is_draw": game.is_draw if game.is_draw is not None else None,
                    "finish": game.finish if game.finish is not None else None,
                    "team_a_goal": game.team_a_goal,
                    "team_b_goal": game.team_b_goal,
                    "winner_id": game.winner_id,
                    "loser_id": game.loser_id,
                }
            }, status=status.HTTP_200_OK)
