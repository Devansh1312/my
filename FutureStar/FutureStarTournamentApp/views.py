from collections import defaultdict,OrderedDict
from itertools import chain
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.utils.translation import activate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from FutureStarAPI.serializers import *
from FutureStarTeamApp.serializers import *
from FutureStarTournamentApp.serializers import *


from django.core.exceptions import ObjectDoesNotExist

from django.db.models import Sum,Case,When

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from FutureStarGameSystem.models import *
from FutureStar_App.models import *
from FutureStarTeamApp.models import *
from FutureStarAPI.models import *
from FutureStarTournamentApp.models import *
from FutureStarFriendlyGame.models import *


from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
import random
from django.utils import timezone
import os
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.utils.translation import gettext as _
from django.db import IntegrityError, transaction
import string
from rest_framework.exceptions import ValidationError
import re
import logging
from django.utils.crypto import get_random_string
from django.utils.timezone import now



from datetime import date, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from django.db.models import Q

from FutureStar.firebase_config import send_push_notification



class CustomTournamentPagination(PageNumberPagination):
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
            page_number = request.data.get(self.page_query_param, 1)
            self.page = int(page_number)
            if self.page < 1:
                raise ValidationError(_("Page number must be a positive integer."))
        except (ValueError, TypeError):
            return Response({
                'status': 0,
                'message': _('Page not found.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        paginator = self.django_paginator_class(queryset, self.get_page_size(request))
        self.total_pages = paginator.num_pages

        if self.page > self.total_pages:
            return Response({
                'status': 0,
                'message': _('Page not found.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        return super().paginate_queryset(queryset, request, view)




###################### POST LIKE ##################################
class TournamentLikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        tournament_id = request.data.get('tournament_id')

        if not tournament_id:
            return Response({
                'status': 0,
                'message': _('Tournament ID is required.')
            }, status=400)

        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Tournament not found.')
            }, status=404)

        # Toggle like/unlike
        creator_type = request.data.get('creator_type')
        created_by_id = request.data.get('created_by_id', request.user.id)  # Default to logged-in user ID

        tournament_like, created = TournamentLike.objects.get_or_create(created_by_id=created_by_id, tournament=tournament, creator_type=creator_type)
        
        if not created:
            # If the user already liked the tournament, unlike it (delete the like)
            tournament_like.delete()
            message = _('Tournament unliked successfully.')
        else:
            message = _('Tournament liked successfully.')

        # Serialize the tournament data with comments set to empty
        serializer = TournamentSerializer(tournament, context={'request': request})
        
        # Return the full tournament data with an empty comment list
        return Response({
            'status': 1,
            'message': message,
            'data': serializer.data
        }, status=200)


################################ Get comment API #############################
class TournamentCommentPagination(CustomTournamentPagination):
    def paginate_queryset(self, queryset, request, view=None):
        return super().paginate_queryset(queryset, request, view)

class TournamentCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Validate tournament_id from request data
        tournament_id = request.data.get('tournament_id')
        if not tournament_id:
            return Response({
                'status': 0,
                'message': _('Tournament ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Tournament not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Get only top-level comments (parent=None) for the tournament
        top_level_comments = Tournament_comment.objects.filter(tournament=tournament, parent=None).order_by('-date_created')

        # Paginate the comments
        paginator = TournamentCommentPagination()
        paginated_comments = paginator.paginate_queryset(top_level_comments, request)

        # If pagination fails or no comments are found
        if paginated_comments is None:
            return Response({
                'status': 1,
                'message': _('No comments found for this tournament.'),
                'data': {
                    'total_records': 0,
                    'total_pages': 0,
                    'current_page': 1,
                    'results': []
                }
            }, status=status.HTTP_200_OK)

        # Serialize the paginated comments
        serializer = TournamentCommentSerializer(paginated_comments, many=True, context={'request': request})

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
class TournamentCommentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        data = request.data
        tournament_id = data.get('tournament_id')
        comment_text = data.get('comment')
        parent_id = data.get('parent_id')
        created_by_id = data.get('created_by_id')
        creator_type = data.get('creator_type')

        # Validate the required fields
        if not tournament_id or not comment_text or not created_by_id or not creator_type:
            return Response({
                'status': 0,
                'message': _('tournament_id, comment, created_by_id and creator_type are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Tournament not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate parent comment if provided
        parent_comment = None
        if parent_id:
            try:
                parent_comment = Tournament_comment.objects.get(id=parent_id)
            except Tournament_comment.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Parent comment not found.')
                }, status=status.HTTP_404_NOT_FOUND)

        # Create the comment using the new fields
        comment = Tournament_comment.objects.create(
            created_by_id=created_by_id,
            creator_type=creator_type,
            tournament=tournament,
            comment=comment_text,
            parent=parent_comment
        )

        return Response({
            'status': 1,
            'message': _('Comment created successfully.'),
            'data': TournamentCommentSerializer(comment).data
        }, status=status.HTTP_200_OK)



############################# GET TOURNAMENTS ###########################

class TournamentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        paginator = CustomTournamentPagination()
        tournaments = Tournament.objects.all().order_by('-created_at')

        paginated_tournaments = paginator.paginate_queryset(tournaments, request, view=self)
        if paginated_tournaments is None:
            return paginator.get_paginated_response([])

        serializer = TournamentSerializer(paginated_tournaments, many=True, context={'request': request})

        return Response({
            'status': 1,
            'message': _('Tournaments fetched successfully.'),
            'data': serializer.data,
            'total_records': paginator.page.paginator.count,
            'total_pages': paginator.total_pages,
            'current_page': paginator.page.number
        }, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        serializer = TournamentSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            # Save the tournament instance
            tournament_instance = serializer.save()

            # Handle logo upload
            if 'logo' in request.FILES:
                logo = request.FILES['logo']
                file_extension = logo.name.split('.')[-1]
                unique_suffix = get_random_string(8)
                file_name = f"tournament_logo/{tournament_instance.id}_{unique_suffix}.{file_extension}"
                logo_path = default_storage.save(file_name, logo)
                tournament_instance.logo = logo_path
                tournament_instance.save()

            if 'tournament_banner' in request.FILES:
                banner = request.FILES['tournament_banner']
                file_extension = banner.name.split('.')[-1]
                unique_suffix = get_random_string(8)
                file_name = f"tournament_banner/{tournament_instance.id}_{unique_suffix}.{file_extension}"
                banner_path = default_storage.save(file_name, banner)
                tournament_instance.tournament_banner = banner_path
                tournament_instance.save()

            # Assign the team_id correctly
            team_id = request.data.get('created_by_id')
            try:
                team_instance = Team.objects.get(id=team_id)  # Fetch the Team instance
                tournament_instance.team_id = team_instance
                tournament_instance.save()
            except Team.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Invalid team ID. Team not found.')
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'status': 1,
                'message': _('Tournament created successfully.'),
                'data': TournamentSerializer(tournament_instance).data
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 0,
            'message': _('Tournament creation failed.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    ############################# EDIT AND DELETE###################

    def patch(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        tournament_id = request.data.get('tournament_id')
        try:
            tournament_instance = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Tournament not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TournamentSerializer(tournament_instance, data=request.data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            tournament_instance = serializer.save()

            # Handle logo update if provided
            if 'logo' in request.FILES:
                logo = request.FILES['logo']
                file_extension = logo.name.split('.')[-1]
                unique_suffix = get_random_string(8)
                file_name = f"tournament_logo/{tournament_instance.id}_{unique_suffix}.{file_extension}"
                logo_path = default_storage.save(file_name, logo)
                tournament_instance.logo = logo_path
                tournament_instance.save()
            # Handle logo upload
            if 'tournament_banner' in request.FILES:
                logo = request.FILES['tournament_banner']
                file_extension = logo.name.split('.')[-1]
                unique_suffix = get_random_string(8)
                file_name = f"tournament_banner/{tournament_instance.id}_{unique_suffix}.{file_extension}"
                logo_path = default_storage.save(file_name, logo)
                tournament_instance.tournament_banner = logo_path
                tournament_instance.save()

            
            # Assign the team_id correctly
            team_id = request.data.get('created_by_id')
            try:
                team_instance = Team.objects.get(id=team_id)  # Fetch the Team instance
                tournament_instance.team_id = team_instance
                tournament_instance.save()
            except Team.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Invalid team ID. Team not found.')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()

            return Response({
                'status': 1,
                'message': _('Tournament updated successfully.'),
                'data': TournamentSerializer(tournament_instance).data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'status': 0,
            'message': _('Tournament update failed.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



class TournmanetDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        tournament_id = request.data.get('tournament_id')
        if tournament_id is None:
            return Response({
                'status': 0,
                'message': _('Tournament ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)
        tournament_id = int(tournament_id)
        try:
            tournament_instance = Tournament.objects.get(id=tournament_id)
            tournament_instance.delete()
            return Response({
                'status': 1,
                'message': _('Tournament deleted successfully.')
            }, status=status.HTTP_200_OK)
        except Tournament.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Tournament not found.')
            }, status=status.HTTP_404_NOT_FOUND)



####################### Get My Tournamnets For team Profile  #######################
class MyTournamentsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomTournamentPagination

    def get(self, request, *args, **kwargs):
        # Extract parameters from request
        creator_type = request.query_params.get('creator_type', None)
        created_by_id = request.query_params.get('created_by_id', None)

        # Check creator_type and created_by_id validity
        if creator_type is None or int(creator_type) != 2:
            return Response({
                'status': 0,
                'message': _('You do not have access.')
            }, status=status.HTTP_403_FORBIDDEN)

        if not created_by_id:
            return Response({
                'status': 0,
                'message': _('Invalid creator details.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Filter tournaments where team_id matches created_by_id
        tournaments = Tournament.objects.filter(team_id=created_by_id).order_by('-created_at')

        if not tournaments.exists():
            return Response({
                'status': 1,
                'message': _('You have not created any tournament yet...'),
                'data': []
            }, status=status.HTTP_200_OK)

        # Initialize paginator
        paginator = self.pagination_class()
        paginated_tournaments = paginator.paginate_queryset(tournaments, request, view=self)

        # Serialize the data
        serializer = TournamentSerializer(paginated_tournaments, many=True, context={'request': request})

        # Return paginated response
        return Response({
            'status': 1,
            'message': _('Tournaments fetched successfully.'),
            'data': serializer.data,
            'total_records': paginator.page.paginator.count,
            'total_pages': paginator.total_pages,
            'current_page': paginator.page.number
        }, status=status.HTTP_200_OK)

############################# TOURNAMENT DETAIL WITH ID ###########################
class TournamentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Fetch the tournament using the tournament_id from the query parameters
        tournament_id = request.query_params.get('tournament_id')

        if not tournament_id:
            return Response({
                'status': 0,
                'message': _('Tournament ID is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the tournament object using the provided tournament_id
            tournament = Tournament.objects.get(id=tournament_id)
            
            # Serialize the tournament data
            serializer = TournamentSerializer(tournament, context={'request': request})

            # Format the response as required
            return Response({
                'status': 1,
                'message': _('Tournament details fetched successfully.'),
                'data':  serializer.data,
               
            }, status=status.HTTP_200_OK)

        except Tournament.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Tournament not found.'),
            }, status=status.HTTP_404_NOT_FOUND)
        
############################# FETCH ONLY GROUP TABLE WITHOUT TEAM ###########################

class GroupTableAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        tournament_id = request.query_params.get('tournament_id') 

        group_table=GroupTable.objects.filter(tournament_id=tournament_id)
        group_table_data = GroupTableSerializer(group_table, many=True).data
        
        return Response({
            'status': 1,
            'message': _('Group table retrieved successfully.'),
            'data': group_table_data

        })
    


############################# FETCH AND CREATE GROUP TEAM WITH ADDING OR UPDATING TEAM ###########################


# class TournamentGroupTeamListCreateAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = (JSONParser, MultiPartParser, FormParser)

#     def get(self, request, *args, **kwargs):
#             language = request.headers.get('Language', 'en')
#             if language in ['en', 'ar']:
#                 activate(language)

#             tournament_id = request.query_params.get('tournament_id')

#             if not tournament_id:
#                 return Response({
#                     'status': 0,
#                     'message': _('Tournament ID is required.')
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             # Fetch all groups associated with the tournament
#             groups = GroupTable.objects.filter(tournament_id=tournament_id).order_by('group_name')

#             if not groups.exists():
#                 return Response({
#                     'status': 0,
#                     'message': _('No groups found for the specified tournament.')
#                 }, status=status.HTTP_404_NOT_FOUND)

#             # Prepare the response data
#             grouped_data = []
#             for group in groups:
#                 # Get all teams in the current group
#                 teams = TournamentGroupTeam.objects.filter(
#                     group_id=group.id,
#                     tournament_id=tournament_id
#                 ).select_related('group_id', 'team_branch_id')

#                 # Serialize team data if available, otherwise an empty list
#                 if teams.exists():
#                     serializer = TournamentGroupTeamSerializer(teams, many=True)
#                     group_teams = serializer.data
#                 else:
#                     group_teams = []  # Empty list for groups without teams

#                 # Add group data with ID and teams
#                 grouped_data.append({
#                     "id": group.id,
#                     "name": group.group_name,
#                     "teams": group_teams
#                 })

#             return Response({
#                 'status': 1,
#                 'message': _('Tournament Group Teams fetched successfully.'),
#                 'data': grouped_data
#             }, status=status.HTTP_200_OK)

# ########### Join Team In Group Via Add Button ##############
#     def post(self, request, *args, **kwargs):
#         language = request.headers.get('Language', 'en')
#         if language in ['en', 'ar']:
#             activate(language)

#         team_branch_id = request.data.get('team_id')
#         group_id = request.data.get('group_id')
#         tournament_id = request.data.get('tournament_id')

#         if not (team_branch_id and group_id and tournament_id):
#             return Response({
#                 'status': 0,
#                 'message': _('team_id, group_id, and tournament_id are required.'),
#             }, status=status.HTTP_400_BAD_REQUEST)

#         # Validate tournament existence
#         try:
#             tournament = Tournament.objects.get(id=tournament_id)
#         except Tournament.DoesNotExist:
#             return Response({
#                 'status': 0,
#                 'message': _('Tournament does not exist.'),
#             }, status=status.HTTP_400_BAD_REQUEST)

#         # Validate group existence and its relation to the tournament
#         try:
#             group_instance = GroupTable.objects.get(id=group_id, tournament_id=tournament_id)
#         except GroupTable.DoesNotExist:
#             return Response({
#                 'status': 0,
#                 'message': _('The provided group does not belong to the specified tournament.'),
#             }, status=status.HTTP_400_BAD_REQUEST)

#         with transaction.atomic():
#             # Check if the team already exists in the tournament
#             existing_assignment = TournamentGroupTeam.objects.filter(
#                 team_branch_id=team_branch_id, tournament_id=tournament_id
#             ).first()

#             if existing_assignment:
#                 # If the team already has a group assigned (not NULL), show an error message
#                 if existing_assignment.group_id:
#                     return Response({
#                         'status': 0,
#                         'message': _('The team is already assigned to another group in this tournament.'),
#                     }, status=status.HTTP_400_BAD_REQUEST)

#                 # If group_id is NULL, update the record
#                 existing_assignment.group_id = group_instance
#                 existing_assignment.status = 1  # Update the status if required
#                 existing_assignment.save(update_fields=['group_id', 'status', 'updated_at'])
#                 return Response({
#                     'status': 1,
#                     'message': _('Tournament Group Team updated successfully.'),
#                     'data': TournamentGroupTeamSerializer(existing_assignment).data
#                 }, status=status.HTTP_200_OK)

#             # If no existing assignment, return an error
#             return Response({
#                 'status': 0,
#                 'message': _('No existing assignment found to update.'),
#             }, status=status.HTTP_400_BAD_REQUEST)




class TeamJoiningRequest(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        user = request.user
        if request.user.role_id in [6, 3]:  # Managers (6) or Coaches (3)
        # Determine joinning_type based on role
            joinning_type = (
                JoinBranch.MANAGERIAL_STAFF_TYPE if request.user.role_id == 6
                else JoinBranch.COACH_STAFF_TYPE
            )
          
            try:
                user_branch = JoinBranch.objects.filter(
                    user_id=request.user,
                    joinning_type=joinning_type
                )
               
            except JoinBranch.DoesNotExist:
                role_message = (
                    _('You are not assigned as a manager to any Team.')
                    if request.user.role_id == 6
                    else _('You are not assigned as a coach to any Team.')
                )
                return Response({
                    'status': 0,
                    'message': role_message,
                }, status=status.HTTP_400_BAD_REQUEST)
        
        elif TeamBranch.objects.filter(team_id__team_founder=request.user).exists():  # Check if user is a team founder
            try:
                # Retrieve the first branch associated with the team where the user is the founder
                team_branch = TeamBranch.objects.filter(team_id__team_founder=request.user).first()
                if not team_branch:
                    return Response({
                        'status': 0,
                        'message': _('No Team Exists'),
                    }, status=status.HTTP_400_BAD_REQUEST)
                
               
            except TeamBranch.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('You are not associated with any team as a founder.'),
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'status': 0,
                'message': _('Only managers, coaches, or team founders can perform this action.'),
            }, status=status.HTTP_403_FORBIDDEN)

        # Initialize classification dictionaries
       
        teams_data=[]

        # Retrieve tournament (assuming tournament_id is provided in the request)
        tournament_id = request.query_params.get('tournament_id')
        if not tournament_id:
            return Response({
                'status': 0,
                'message': _('Tournament ID is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Tournament does not exist.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Filter teams by age group
        tournament_age_group = tournament.age_group
     
        # Retrieve founder teams
        if TeamBranch.objects.filter(team_id__team_founder=user).exists():
            founder_team_branches = TeamBranch.objects.filter(team_id__team_founder=user, age_group_id=tournament_age_group)
            teams_data.extend(founder_team_branches)

        # Retrieve manager teams
      
        if user.role_id == 6:  # Assuming role_id == 6 indicates a manager
            manager_branches = TeamBranch.objects.filter(
                id__in=JoinBranch.objects.filter(
                    user_id=user,
                    joinning_type=JoinBranch.MANAGERIAL_STAFF_TYPE  # Managerial staff
                ).values_list('branch_id', flat=True),
                age_group_id=tournament_age_group  # Filter by tournament age group
            )
            teams_data.extend(manager_branches)
        # Retrieve coach teams
        if user.role_id == 3:  # Assuming role_id == 3 indicates a coach
            coach_branches = TeamBranch.objects.filter(
                id__in=JoinBranch.objects.filter(
                    user_id=user,
                    joinning_type=JoinBranch.COACH_STAFF_TYPE  # Coach staff
                ).values_list('branch_id', flat=True),
                age_group_id=tournament_age_group  # Filter by tournament age group
            )
            teams_data.extend(coach_branches)
        unique_teams = list((teams_data))
        serialized_data = TeamBranchSerializer(unique_teams, many=True, context={'request': request}).data
        return Response({
            'status': 1,
            'message': _('Teams retrieved successfully.'),
            'data': serialized_data
               
            
        }, status=status.HTTP_200_OK)
        
    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Proceed with the tournament joining request flow
        tournament_id = request.data.get('tournament_id')
        team_id = request.data.get('team_id')
        
        # Check if the tournament and team exist
        try:
            tournament = Tournament.objects.get(id=tournament_id)
            team_branch = TeamBranch.objects.get(id=team_id)
        except Tournament.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Tournament does not exist.'),
            }, status=status.HTTP_400_BAD_REQUEST)
        except TeamBranch.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Team does not exist.'),
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if team_branch.age_group_id != tournament.age_group:
            return Response({
                'status': 0,
                'message': _('The team age group does not match the tournament age group.'),
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check for an existing request (either REQUESTED or ACCEPTED)
        existing_request = TournamentGroupTeam.objects.filter(
            team_branch_id=team_branch,
            tournament_id=tournament
        ).first()  # Get the first matching record (if any)
        
        if existing_request:
            # If the request is rejected, we can either update or create a new one
            if existing_request.status == TournamentGroupTeam.REJECTED:
                existing_request.status = TournamentGroupTeam.REQUESTED  # Revert to requested status
                existing_request.save()  # Save the updated request
                tournament_group_team = existing_request
            else:
                return Response({
                    'status': 0,
                    'message': _('This team has already requested or is already accepted into the tournament.'),
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # If no existing request found, create a new one
            tournament_group_team = TournamentGroupTeam.objects.create(
                team_branch_id=team_branch,
                tournament_id=tournament,
                status=TournamentGroupTeam.REQUESTED  # Set status to REQUESTED (0)
            )
        
        # Serialize and return the created or updated object
        serializer = TournamentGroupTeamSerializer(tournament_group_team)
        team_founder = tournament.team_id.team_founder
        if team_founder:
            device_token = team_founder.device_token  # Ensure the `device_token` is available
            if device_token:
                notification_language = team_founder.current_language  # Retrieve the user's current language
                if notification_language in ['ar', 'en']:
                    activate(notification_language)  # Activate the user's preferred language
                
                title = _("Tournament Joining Request")  # Use the translation function
                body = _("Team {team_name} has sent a request to join the tournament {tournament_name}.").format(
                    team_name=team_branch.team_name,
                    tournament_name=tournament.tournament_name
                )
                  # Include tournament_id in the push data
                push_data = {
                    "tournament_id": tournament.id,  # Assuming `tournament.id` is the correct attribute for the ID
                    "team_brach_id": team_branch.id,
                    "notifier_id":tournament.team_id.id , # Assuming `team_branch.id` is the correct attribute for the ID
                    "type": "team_joining_request",  # Assuming `type` is the correct attribute for the type of notification
                }
                send_push_notification(device_token, title, body, device_type=team_founder.device_type, data=push_data)
                notification = Notifictions.objects.create(
                    created_by_id=request.user.id,
                    creator_type=1,  # Assuming 1 is for user
                    targeted_id=team_founder.id,
                    targeted_type=1,  # Assuming 1 is for user
                    title=title,
                    content=body
                )
                notification.save()

        return Response({
            'status': 1,
            'message': _('Team joining request created successfully.' if not existing_request else _('Team joining request updated successfully.')),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

   
class TeamRequestApproved(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract parameters from the request
        team_branch_id = request.data.get('team_id')
        tournament_id = request.data.get('tournament_id')

        # Validate tournament existence and capacity
        try:
            tournament = Tournament.objects.get(id=tournament_id)
            tournament_capacity = int(tournament.number_of_team)
        except Tournament.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Tournament does not exist.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Count all teams in the tournament with status 1
        current_team_count = TournamentGroupTeam.objects.filter(
            tournament_id=tournament_id, status=1
        ).count()

        # Check if tournament team slots are full
        if current_team_count >= tournament_capacity:
            return Response({
                'status': 0,
                'message': _('All team slots in this tournament are filled.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch all groups associated with the tournament
        groups = GroupTable.objects.filter(tournament_id=tournament_id)

        # Check if the team already exists in the tournament
        existing_team = TournamentGroupTeam.objects.filter(
            team_branch_id=team_branch_id, tournament_id=tournament_id
        ).first()

        if existing_team:
            # Update the team's status to accepted
            existing_team.status = 1

            # If the tournament has only one group, assign that group ID
            if groups.count() == 1:
                existing_team.group_id = groups.first()
            
            existing_team.save()

            team_members = JoinBranch.objects.filter(
                branch_id=team_branch_id,
                joinning_type__in=[JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE]
            )

            for member in team_members:
                user = member.user_id  # Assuming JoinBranch.user_id is a ForeignKey to the User model
                device_token = user.device_token  # Assuming User model has a `device_token` field
                device_type = user.device_type  # Assuming User model has a `device_type` field

                # Check and activate the user's preferred notification language
                notification_language = user.current_language  # Assuming User model has a `current_language` field
                if notification_language in ['ar', 'en']:
                    activate(notification_language)

                if device_token and device_type:
                    # Send push notification with translated content
                    push_data = {
                        "tournament_id": tournament.id,  # Assuming `tournament.id` is the correct attribute for the ID
                        "team_branch_id": team_branch_id, 
                        "notifier_id":tournament.team_id.id, # Include the branch_id
                        "type": "team_approved",  # Assuming `type` is the correct attribute for the type of notification
                        "team_list":"1",
                    }
                    send_push_notification(
                        device_token=device_token,
                        title=_("Team Approved"),
                        body=_("Your team has been accepted to join the {} tournament.").format(tournament.tournament_name),
                        device_type=device_type,
                        data=push_data,
                    )
                    notification = Notifictions.objects.create(
                        created_by_id=request.user.id,
                        creator_type=1,  # Assuming 1 is for user
                        targeted_id=user.id,
                        targeted_type=1,  # Assuming 1 is for user
                        title=_("Team Approved"),
                        content=_("Your team has been accepted to join the {} tournament.").format(tournament.tournament_name),
                    )
                    notification.save()
            return Response({
                'status': 1,
                'message': _('Tournament Group Team status updated to accepted.'),
                'data': {
                    'team_branch_id': existing_team.team_branch_id.id if existing_team.team_branch_id else None,
                    'tournament_id': existing_team.tournament_id.id if existing_team.tournament_id else None,
                    'group_id': existing_team.group_id.id if existing_team.group_id else None,
                    'status': existing_team.status,
                }
            }, status=status.HTTP_200_OK)
        # Handle cases where the team does not already exist in the tournament
        return Response({
            'status': 0,
            'message': _('The team does not exist in the tournament. Please ensure the team is already added.'),
        }, status=status.HTTP_400_BAD_REQUEST)



############################# FETCH TEAM LISTS APPROVED,REQUESTED AND REJECTED ###########################

class TournamentGroupTeamListView(APIView):
    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Get the value of the 'team_list' query parameter
        team_list = request.query_params.get('team_list')
        tournament_id = request.query_params.get('tournament_id')


        if team_list == '1':
            # Show teams with status 1
            teams = TournamentGroupTeam.objects.filter(
                tournament_id=tournament_id, status=1
            )
        elif team_list == '2':
            # Show teams with status 0
              teams = TournamentGroupTeam.objects.filter(
                    tournament_id=tournament_id, status__in=[0, 2] 
                )
        else:
            return Response(
                {"error": _("Invalid team_list parameter. Use 1 for active teams, 2 for inactive teams.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Serialize the filtered teams
        serializer = TournamentGroupTeamSerializer(teams, many=True)
        return Response({
            'status': 1,
            'message': _('Team Fetched successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

############################# REJECT TEAM OF GROUP ###########################

class TeamRejectRequest(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        team_id = request.data.get('team_id')
        tournament_id = request.data.get('tournament_id')
        
        # Check if the tournament and team exist
        try:
            tournament = Tournament.objects.get(id=tournament_id)
            team_branch = TeamBranch.objects.get(id=team_id)
        except Tournament.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Tournament does not exist.'),
            }, status=status.HTTP_400_BAD_REQUEST)
        except TeamBranch.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Team does not exist.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Find the existing TournamentGroupTeam entry based on tournament_id and team_branch_id
        try:
            tournament_group_team = TournamentGroupTeam.objects.get(
                tournament_id=tournament,
                team_branch_id=team_branch
            )
        except TournamentGroupTeam.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Team is not part of the tournament or the request does not exist.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update the existing entry: set group_id to None and status to 3 (rejected)
        tournament_group_team.status = 2  # Status 2 for rejected
        tournament_group_team.group_id = None  # Set group_id to None
        tournament_group_team.save()

        # Serialize and return the updated object
        serializer = TournamentGroupTeamSerializer(tournament_group_team)
        return Response({
            'status': 1,
            'message': _('Team rejected successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

############### Custom Pagination ###############
class CustomBranchSearchPagination(PageNumberPagination): 
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
                raise ValidationError(_("Page number must be a positive integer."))
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
            'message': _('Data fetched successfully.'),
            'total_records': self.total_records,
            'total_pages': self.total_pages,
            'current_page': self.page,
            'data': data
        })

################################# Branch Search API ####################################################


class TeamBranchSearchView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomBranchSearchPagination

    def get(self, request):
        # Get the preferred language from headers
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract parameters from the request
        tournament_id = request.query_params.get('tournament_id')
        search_key = request.query_params.get('search', '').strip()

        # Validate and fetch the tournament
        tournament = get_object_or_404(Tournament, id=tournament_id)
        if tournament is None:
            return Response({
                'status': 0,
                'message': _('Tournament does not exist.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Base queryset to filter team branches associated with the tournament
        queryset = TeamBranch.objects.filter(
            id__in=TournamentGroupTeam.objects.filter(
                tournament_id=tournament_id,
                group_id__isnull=True,  # Include only teams not assigned to any group
                status=TournamentGroupTeam.ACCEPTED  # Status = ACCEPTED
            ).values_list('team_branch_id', flat=True)
        )

        # Apply search filter if `search_key` is provided
        if search_key:
            queryset = queryset.filter(team_name__icontains=search_key)

        # Paginate the results
        paginator = self.pagination_class()
        paginated_data = paginator.paginate_queryset(queryset, request, view=self)

        # Format the paginated data to include branch_id, team_name, and team_logo
        formatted_data = [
            {
                "id": branch.id,
                "team_name": branch.team_name,
                "team_logo": branch.upload_image.url if branch.upload_image else None,
                "country_name": branch.team_id.country_id.name if branch.team_id.country_id else None
            }
            for branch in paginated_data
        ]

        # Create response with formatted paginated data
        return paginator.get_paginated_response(formatted_data)


class TournamentGamesOptionsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        tournament_id = request.query_params.get('tournament_id')
        group_id = request.query_params.get('group_id')
        team_a_id = request.query_params.get('team_a')

        # Validate tournament_id
        if not tournament_id:
            return Response({
                'status': 0,
                'error': "Please provide a valid tournament_id."
            }, status=400)

        # Convert parameters to integers or handle blank/null cases
        try:
            tournament_id = int(tournament_id)
        except ValueError:
            return Response({
                'status': 0,
                'error': "Invalid tournament_id provided."
            }, status=400)

        try:
            group_id = int(group_id) if group_id else None
        except ValueError:
            return Response({
                'status': 0,
                'error': "Invalid group_id provided."
            }, status=400)

        try:
            team_a_id = int(team_a_id) if team_a_id else None
        except ValueError:
            team_a_id = None  # If invalid, treat as not provided

        # Query accepted teams
        if group_id:
            # Case 2: Both tournament_id and group_id provided
            accepted_teams = TournamentGroupTeam.objects.filter(
                tournament_id=tournament_id,
                group_id=group_id,
                status=TournamentGroupTeam.ACCEPTED
            ).select_related('team_branch_id')
        else:
            # Case 1: Only tournament_id provided
            accepted_teams = TournamentGroupTeam.objects.filter(
                tournament_id=tournament_id,
                status=TournamentGroupTeam.ACCEPTED
            ).select_related('team_branch_id')

        # Prepare team options excluding team_a_id
        team_a_options = [
            {'id': team.team_branch_id.id, 'name': team.team_branch_id.team_name}
            for team in accepted_teams.exclude(team_branch_id__id=team_a_id)
        ]

        team_b_options = team_a_options  # Same options for team B

        return Response({
            'status': 1,
            'message': _('Options Fetched Successfully'),
            'data': {
                "team_a_options": team_a_options,
                "team_b_options": team_b_options
            }
        })

############### Custom Pagination ###############
class CustomGameListPagination(PageNumberPagination): 
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
                raise ValidationError(_("Page number must be a positive integer."))
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
            'message': _('Games fetched successfully.'),
            'total_records': self.total_records,
            'total_pages': self.total_pages,
            'current_page': self.page,
            'data': data
        })

######### Single game Detail API ##################
class GameDetailsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        tournament_id = request.query_params.get('tournament_id')
        game_id = request.query_params.get('game_id')

        # Validate required parameters
        if not tournament_id or not game_id:
            return Response({
                "status": 0,
                "message": "Tournament ID and Game ID are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the game details based on tournament_id and game_id
            game = TournamentGames.objects.get(tournament_id=tournament_id, id=game_id)
        except TournamentGames.DoesNotExist:
            return Response({
                "status": 0,
                "message": "Game not found for the given Tournament ID and Game ID."
            }, status=status.HTTP_404_NOT_FOUND)

        # Calculate game duration
        if game.game_start_time and game.game_end_time:
            start_time = datetime.combine(datetime.today(), game.game_start_time)
            end_time = datetime.combine(datetime.today(), game.game_end_time)
            duration = end_time - start_time
            game_duration = str(duration)  # Convert timedelta to string
        else:
            game_duration = None  # If either time is missing

        # Construct response data
        game_data = {
            "id": game.id,
            "tournament_id": game.tournament_id.id if game.tournament_id else None,
            "tournament_name": game.tournament_id.tournament_name if game.tournament_id else None,
            "age_group_name": game.tournament_id.age_group.name_en if language == 'en' else game.tournament_id.age_group.name_ar,
            "team_id": game.tournament_id.team_id.id,
            "game_number": game.game_number,
            "game_date": game.game_date,
            "game_start_time": game.game_start_time,
            "game_end_time": game.game_end_time,
            "game_duration": game_duration,  # Include game duration
            "group_id": game.group_id.id if game.group_id else None,
            "group_name": game.group_id.group_name if game.group_id else None,
            "team_a_name": game.team_a.team_name if game.team_a and game.team_a.team_id else None,
            "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a and game.team_a.team_id and game.team_a.team_id.team_logo else None,
            "team_b_name": game.team_b.team_name if game.team_b and game.team_b.team_id else None,
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
            "finish": game.finish,
            "winner_id": game.winner_id,
            "loser_id": game.loser_id,
            "is_draw": game.is_draw,
            "created_at": game.created_at,
            "updated_at": game.updated_at,
        }

        return Response({
            "status": 1,
            "message": "Game details fetched successfully.",
            "data": game_data
        }, status=status.HTTP_200_OK)


######################### Update Tournamnet game API #########################
class UpdateTournamentGameDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def patch(self, request, *args, **kwargs):
        # Set language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract the game ID from the URL
        game_id = kwargs.get("game_id")
        if not game_id:
            return Response({
                'status': 0,
                'message': _('Game ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the game object
            game = TournamentGames.objects.get(id=game_id)
        except TournamentGames.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Game not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TournamentGamesSerializer(game, data=request.data, partial=True)
        try:
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': 1,
                    'message': _('Game details updated successfully.'),
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 0,
                    'message': _('Failed to update game details.'),
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 0,
                'message': _('An unexpected error occurred.'),
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, *args, **kwargs):
        # Extract the game ID from the URL
        game_id =request.query_params.get('game_id')
        if not game_id:
            return Response({
                'status': 0,
                'message': _('Game ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch and delete the game object
            game = TournamentGames.objects.get(id=game_id)
            game.delete()
            return Response({
                'status': 1,
                'message': _('Game deleted successfully.')
            }, status=status.HTTP_200_OK)
        except TournamentGames.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Game not found.')
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 0,
                'message': _('An unexpected error occurred.'),
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

######################### Create Tournamnet Game API #######################################################
class TournamentGamesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def generate_game_number(self, tournament_id):
        """Generate the game number in the format #TSYYNNNGGG."""
        # Get the last two digits of the current year (e.g., 2025 -> 25)
        current_year = timezone.now().year % 100  # Extract last 2 digits
        
        # Pad tournament_id to 3 digits (e.g., 001 for ID 1)
        tournament_id_str = str(tournament_id).zfill(3)

        # Find the last game number for the given tournament
        last_game = TournamentGames.objects.filter(tournament_id=tournament_id).order_by('-game_number').first()

        # Determine the next game number
        if last_game:
            # Extract the numeric part of the game number and increment
            last_game_number = int(last_game.game_number[-3:])  # Extract last 3 digits
            game_number = last_game_number + 1
        else:
            # Start from 1 if no games exist
            game_number = 1  

        # Pad the game number to 3 digits (e.g., 001)
        game_number_str = str(game_number).zfill(3)

        # Format game number as #TSYYNNNGGG
        game_number_final = f"#TS{current_year:02d}{tournament_id_str}{game_number_str}"
        
        return game_number_final

    def post(self, request, *args, **kwargs):
        # Set language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract data from the request
        tournament_id = request.data.get("tournament_id")
        game_number = self.generate_game_number(tournament_id)  # Generate game number
        team_a = request.data.get("team_a")  # Team A ID
        team_b = request.data.get("team_b")  # Team B ID
        group_id = request.data.get("group_id")  # Optional field

        if not tournament_id or not team_a or not team_b:
            return Response({
                'status': 0,
                'message': _('All tournament_id, team_a, and team_b are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if TournamentGames.objects.filter(Q(tournament_id=tournament_id) & Q(game_number=game_number)).exists():
            return Response({
                'status': 0,
                'message': _('This game number already exists for the specified tournament. Please choose a different game number.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if group_id == 0 or group_id == "0":
            request.data["group_id"] = None

        # Add generated game number to the request data
        request.data["game_number"] = game_number

        serializer = TournamentGamesSerializer(data=request.data)
        try:
            if serializer.is_valid():
                game = serializer.save()

                # Notify coaches and managers of both teams
                self.notify_team_members(team_a, tournament_id, game, "team_a")
                self.notify_team_members(team_b, tournament_id, game, "team_b")

                return Response({
                    'status': 1,
                    'message': _('Game created successfully.'),
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 0,
                    'message': _('Failed to create game.'),
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': 0,
                'message': _('An unexpected error occurred.'),
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def notify_team_members(self, team_branch_id, tournament_id, game,team_type):
        """
        Send notifications to the coaches and managers of the given team.
        """
        try:
            tournament = Tournament.objects.get(id=tournament_id)
            team_members = JoinBranch.objects.filter(
                branch_id=team_branch_id,
                joinning_type__in=[JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE]
            )
 

            if team_type == "team_a":
                team_name = game.team_a.team_name
                opponent_team_name = game.team_b.team_name
            else:
                team_name = game.team_b.team_name
                opponent_team_name = game.team_a.team_name

            # Create the notification message
            notification_message = _("Your team ({}), has been scheduled to a match in {} against {} on {} at {}.").format(
                team_name,
                tournament.tournament_name,
                opponent_team_name,
                game.game_date.strftime("%Y-%m-%d") if game.game_date else _("TBD"),
                game.game_start_time.strftime("%H:%M") if game.game_start_time else _("TBD"),
            )
            push_data = {
                    "tournament_id": tournament.id,  # The tournament ID
                    "game_id": game.id,  # The game ID
                    "team_branch_id": team_branch_id,  # The team branch ID
                    "type": "game_scheduled",  # The notification type
                }
            # Send notification to each team member
            for member in team_members:
                user = member.user_id  # Assuming JoinBranch.user_id is a ForeignKey to User
                device_token = user.device_token  # Assuming User model has `device_token` field
                device_type = user.device_type  # Assuming User model has `device_type` field
                notification_language = user.current_language  # Assuming User model has `current_language` field

                if notification_language in ['ar', 'en']:
                    activate(notification_language)

                if device_token and device_type:
                    send_push_notification(
                        device_token=device_token,
                        title=_("Game Scheduled"),
                        body=notification_message,
                        device_type=device_type,
                        data=push_data
                    )
                    notification = Notifictions.objects.create(
                        created_by_id=self.request.user.id,  # Requestor ID (could be dynamically set, e.g., the admin or the user making the change)
                        creator_type=2,      # Creator type (admin or system)
                        targeted_id=user.id,    # Targeted user ID (team member)
                        targeted_type=1,                # Assuming target is always a user
                        title=_("Game Scheduled"),
                        content=notification_message
                    )
                    notification.save()
                    
        except Tournament.DoesNotExist:
            logging.error(f"Tournament with ID {tournament_id} does not exist.")
        except Exception as e:
            logging.error(f"Error sending notification: {str(e)}", exc_info=True)


    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        tournament_id = request.query_params.get('tournament_id')
        games_query = TournamentGames.objects.all().order_by('-game_date', '-game_start_time')

        if tournament_id:
            games_query = games_query.filter(tournament_id=tournament_id)

        paginator = CustomGameListPagination()
        paginated_games = paginator.paginate_queryset(games_query, request)

        grouped_data = defaultdict(list)
        for game in paginated_games:
            game_date = game.game_date

            day_name = game_date.strftime('%A') if game_date else "Unknown"
            formatted_date = game_date.strftime('%Y-%m-%d') if game_date else "Unknown-Date"

            # Calculate team goals even if the game is not finished
            team_a_goals = PlayerGameStats.objects.filter(
                team_id=game.team_a.id,
                game_id=game.id,
                tournament_id=game.tournament_id.id
            ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

            team_b_goals = PlayerGameStats.objects.filter(
                team_id=game.team_b.id,
                game_id=game.id,
                tournament_id=game.tournament_id.id
            ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

            team_a_branch = game.team_a
            team_b_branch = game.team_b

            team_a_name = team_a_branch.team_name if team_a_branch else None
            team_b_name = team_b_branch.team_name if team_b_branch else None

            team_a_logo = team_a_branch.team_id.team_logo if team_a_branch and team_a_branch.team_id else None
            team_b_logo = team_b_branch.team_id.team_logo if team_b_branch and team_b_branch.team_id else None

            team_a_logo_path = f"/media/{team_a_logo}" if team_a_logo else None
            team_b_logo_path = f"/media/{team_b_logo}" if team_b_logo else None

            game_data = {
                "id": game.id,
                "tournament_id": game.tournament_id.id if game.tournament_id else None,
                "tournament_name": game.tournament_id.tournament_name if game.tournament_id else None,
                "tournament_banner" :game.tournament_id.tournament_banner.url if game.tournament_id.tournament_banner else None,
                "game_number": game.game_number,
                "game_date": game.game_date.strftime('%Y-%m-%d') if game.game_date else None,
                "game_start_time": game.game_start_time,
                "game_end_time": game.game_end_time,
                "group_id": game.group_id.id if game.group_id else None,
                "group_id_name": game.group_id.group_name if game.group_id else None,
                "team_a": game.team_a.id if game.team_a else None,
                "team_a_name": team_a_name,
                "team_a_logo": team_a_logo_path,
                "team_a_goal": team_a_goals,
                "team_b": game.team_b.id if game.team_b else None,
                "team_b_name": team_b_name,
                "team_b_logo": team_b_logo_path,
                "team_b_goal": team_b_goals,
                "game_field_id": game.game_field_id.id if game.game_field_id else None,
                "game_field_id_name": game.game_field_id.field_name if game.game_field_id else None,
                "game_field_id": game.game_field_id.id if game.game_field_id else None,
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
                "finish": game.finish,
                "winner": game.winner_id,
                "loser_id": game.loser_id,
                "is_draw": game.is_draw,
                "created_at": game.created_at,
                "updated_at": game.updated_at,
            }

            grouped_data[f"{day_name},{formatted_date}"].append(game_data)

        formatted_data = [
            {"date": date, "games": games}
            for date, games in grouped_data.items() if games
        ]

        return paginator.get_paginated_response(formatted_data)

            
    def patch(self, request, *args, **kwargs):
 
        game_id = request.data.get('game_id')  # Extract game_id from URL parameters
        tournament_id = request.data.get('tournament_id')  # Get tournament_id from the request data

        try:
            # Get the game by game_id and tournament_id
            game = TournamentGames.objects.get(id=game_id, tournament_id=tournament_id)
        except TournamentGames.DoesNotExist:
            return Response({
                "status": 0,
                "message": _("Game not found for the given tournament.")
            }, status=status.HTTP_404_NOT_FOUND)

        # Retrieve the goals scored by each team in the game
        team_a_goals = PlayerGameStats.objects.filter(
            team_id=game.team_a.id,
            game_id=game.id,
            tournament_id=game.tournament_id.id
        ).aggregate(total_goals=Sum('goals'))['total_goals'] or 0

        team_b_goals = PlayerGameStats.objects.filter(
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

################## Tournament Games Detail API for Lineup Of Both Team ################################
class TournamentGamesDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        # Set language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get parameters from request query
        game_id = request.query_params.get('game_id')
        tournament_id = request.query_params.get('tournament_id')

        if not game_id or not tournament_id:
            return Response({
                'status': 0,
                'message': _('game_id and tournament_id are required.'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the tournament game
            game = TournamentGames.objects.get(id=game_id, tournament_id=tournament_id)
        except TournamentGames.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Tournament game not found.'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        # Helper function to fetch team data
        def fetch_team_data(team):
            if not team:
                return None

            # Filter players in Lineup by team, game, and tournament, separating by status
            substitute_lineups = Lineup.objects.filter(
                team_id=team.id,
                game_id=game_id,
                tournament_id=tournament_id,
                lineup_status=Lineup.SUBSTITUTE
            )
            already_added_lineups = Lineup.objects.filter(
                team_id=team.id,
                game_id=game_id,
                tournament_id=tournament_id,
                lineup_status=Lineup.ALREADY_IN_LINEUP
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



################################ Get Uniform API when first Screen Call ######################
class GameUniformColorAPIView(APIView):
    def get(self, request, *args, **kwargs):
        team_id = request.query_params.get('team_id')
        tournament_id = request.query_params.get('tournament_id')
        game_id = request.query_params.get('game_id')
        user_role = request.user.role.id
        if user_role not in [3, 6]:
            return Response({
            'status': 0,
            'message': _('Access denied. You do not have the necessary role for this action.'),
            'data': None,
        }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            game = TournamentGames.objects.get(id=game_id, tournament_id=tournament_id)
        except TournamentGames.DoesNotExist:
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
                "third_color_player": game.team_a_third_color_player,
                "primary_color_goalkeeper": game.team_a_primary_color_goalkeeper,
                "secondary_color_goalkeeper": game.team_a_secondary_color_goalkeeper,
                "third_color_goalkeeper": game.team_a_third_color_goalkeeper
            }
        elif game.team_b.id == int(team_id):
            data = {
                "primary_color_player": game.team_b_primary_color_player,
                "secondary_color_player": game.team_b_secondary_color_player,
                "third_color_player": game.team_b_third_color_player,
                "primary_color_goalkeeper": game.team_b_primary_color_goalkeeper,
                "secondary_color_goalkeeper": game.team_b_secondary_color_goalkeeper,
                "third_color_goalkeeper": game.team_b_third_color_goalkeeper
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

############################### Uniform Color APIS #########################################
####### Uniform Color Set Post APi ##############

class TeamUniformColorAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, user, team_id):
        """
        Check if the user has the required role and valid membership in the team.
        """
        if user.role.id not in [3, 6]:  # Restrict roles
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
        # Activate language preference
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        serializer = TeamUniformColorSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            game_id = validated_data['game_id']
            tournament_id = validated_data['tournament_id']
            team_id = validated_data['team_id']
            primary_color_player = validated_data['primary_color_player']
            secondary_color_player = validated_data['secondary_color_player']
            third_color_player = validated_data['third_color_player']
            primary_color_goalkeeper = validated_data['primary_color_goalkeeper']
            secondary_color_goalkeeper = validated_data['secondary_color_goalkeeper']
            third_color_goalkeeper = validated_data['third_color_goalkeeper']

            if not self._has_access(request.user, team_id):
                return Response({
                    'status': 0,
                    'message': _('Access denied. You do not have permission for this team.'),
                    'data': None,
                }, status=status.HTTP_403_FORBIDDEN)

            try:
                game = TournamentGames.objects.get(id=game_id, tournament_id=tournament_id)
            except TournamentGames.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Game not found.'),
                    'data': None,
                }, status=status.HTTP_404_NOT_FOUND)

            # Update uniform colors for the matched team
            if team_id == game.team_a.id:
                game.team_a_primary_color_player = primary_color_player
                game.team_a_secondary_color_player = secondary_color_player
                game.team_a_third_color_player = third_color_player
                game.team_a_primary_color_goalkeeper = primary_color_goalkeeper
                game.team_a_secondary_color_goalkeeper = secondary_color_goalkeeper
                game.team_a_third_color_goalkeeper = third_color_goalkeeper
            elif team_id == game.team_b.id:
                game.team_b_primary_color_player = primary_color_player
                game.team_b_secondary_color_player = secondary_color_player
                game.team_b_third_color_player = third_color_player
                game.team_b_primary_color_goalkeeper = primary_color_goalkeeper
                game.team_b_secondary_color_goalkeeper = secondary_color_goalkeeper
                game.team_b_third_color_goalkeeper = third_color_goalkeeper
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

############ Fetch both team uniform using refree #######################
class FetchTeamUniformColorAPIView(APIView):
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

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        game_id = request.query_params.get('game_id')
        tournament_id = request.query_params.get('tournament_id')

        if not game_id or not tournament_id:
            return Response({
                'status': 0,
                'message': _('game_id and tournament_id are required.'),
                'data': None,
            }, status=status.HTTP_400_BAD_REQUEST)
        if not self._has_access(request.user, game_id=game_id, tournament_id=tournament_id):
            return Response({
                'status': 0,
                'message': _('Access denied. You do not have permission for this game.'),
                'data': None,
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            # Fetch the game based on the tournament and game ID
            game = TournamentGames.objects.get(id=game_id, tournament_id=tournament_id)
        except TournamentGames.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Game not found.'),
                'data': None,
            }, status=status.HTTP_404_NOT_FOUND)

        # Retrieve the team information for team_a and team_b
        team_a_data = {
            "team_id": game.team_a.id,
            "team_name": game.team_a.team_name,  # Assuming the `TeamBranch` model has a `name` field
            "primary_color_player": game.team_a_primary_color_player,
            "secondary_color_player": game.team_a_secondary_color_player,
            "third_color_player": game.team_a_third_color_player,
            "primary_color_goalkeeper": game.team_a_primary_color_goalkeeper,
            "secondary_color_goalkeeper": game.team_a_secondary_color_goalkeeper,
            "third_color_goalkeeper": game.team_a_third_color_goalkeeper,
        }

        team_b_data = {
            "team_id": game.team_b.id,
            "team_name": game.team_b.team_name,  # Assuming the `TeamBranch` model has a `name` field
            "primary_color_player": game.team_b_primary_color_player,
            "secondary_color_player": game.team_b_secondary_color_player,
            "third_color_player": game.team_b_third_color_player,
            "primary_color_goalkeeper": game.team_b_primary_color_goalkeeper,
            "secondary_color_goalkeeper": game.team_b_secondary_color_goalkeeper,
            "third_color_goalkeeper": game.team_b_third_color_goalkeeper,
        }

        return Response({
            'status': 1,
            'message': _('Uniform information fetched successfully.'),
            'data': {
                'game_id': game.id,
                'tournament_id': game.tournament_id.id,
                'is_confirm': game.is_confirm,
                'team_a': team_a_data,
                'team_b': team_b_data
            },
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        game_id = request.data.get('game_id')
        tournament_id = request.data.get('tournament_id')
        is_confirm = request.data.get('is_confirm')

        # Validate required fields
        if not game_id or not tournament_id:
            return Response({
                'status': 0,
                'message': _('game_id and tournament_id are required.'),
                'data': None,
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate is_confirm input
        if is_confirm in [1, True, '1', 'true', 'True']:
            is_confirm = False
        elif is_confirm in [0, False, '0', 'false', 'False']:
            is_confirm = True
        else:
            return Response({
                'status': 0,
                'message': _('Invalid is_confirm value. It must be 1, 0, true, or false.'),
                'data': None,
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check access permissions
        if not self._has_access(request.user, game_id=game_id, tournament_id=tournament_id):
            return Response({
                'status': 0,
                'message': _('Access denied. You do not have permission to update this game.'),
                'data': None,
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            # Fetch the game record
            game = TournamentGames.objects.get(id=game_id, tournament_id=tournament_id)

            # If the uniform is rejected, set uniform colors to None (null)
            if not is_confirm:
                game.team_a_primary_color_player = None
                game.team_a_secondary_color_player = None
                game.team_a_third_color_player = None
                game.team_a_primary_color_goalkeeper = None
                game.team_a_secondary_color_goalkeeper = None
                game.team_a_third_color_goalkeeper = None
                game.team_b_primary_color_player = None
                game.team_b_secondary_color_player = None
                game.team_b_third_color_player = None
                game.team_b_primary_color_goalkeeper = None
                game.team_b_secondary_color_goalkeeper = None
                game.team_b_third_color_goalkeeper = None
                # Send rejection notification to both teams' managers
                self.notify_team_managers(game)


            # Save the game with updated uniform colors (if rejected)
            game.is_confirm = is_confirm
            game.save()

            # Prepare team data similar to the GET response
            team_a_data = {
                "team_id": game.team_a.id,
                "team_name": game.team_a.team_name,
                "primary_color_player": game.team_a_primary_color_player,
                "secondary_color_player": game.team_a_secondary_color_player,
                "third_color_player": game.team_a_third_color_player,
                "primary_color_goalkeeper": game.team_a_primary_color_goalkeeper,
                "secondary_color_goalkeeper": game.team_a_secondary_color_goalkeeper,
                "third_color_goalkeeper": game.team_a_third_color_goalkeeper,
            }

            team_b_data = {
                "team_id": game.team_b.id,
                "team_name": game.team_b.team_name,
                "primary_color_player": game.team_b_primary_color_player,
                "secondary_color_player": game.team_b_secondary_color_player,
                "third_color_player": game.team_b_third_color_player,
                "primary_color_goalkeeper": game.team_b_primary_color_goalkeeper,
                "secondary_color_goalkeeper": game.team_b_secondary_color_goalkeeper,
                "third_color_goalkeeper": game.team_b_third_color_goalkeeper,
            }

            # Dynamic success message based on is_confirm value
            success_message = _('Uniform confirmed successfully.') if is_confirm else _('Uniform rejected successfully. Please add new uniform ASAP.')

            # Return response matching GET
            return Response({
                'status': 1,
                'message': success_message,
                'data': {
                    'game_id': game.id,
                    'tournament_id': game.tournament_id.id,
                    'is_confirm': game.is_confirm,
                    'team_a': team_a_data,
                    'team_b': team_b_data
                },
            }, status=status.HTTP_200_OK)

        except TournamentGames.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Game not found.'),
                'data': None,
            }, status=status.HTTP_404_NOT_FOUND)

    def notify_team_managers(self, game):
        """
        Send notifications to both teams' managers that the uniform has been rejected.
        """
        try:
            # Fetch the managers for both teams
            team_a_managers = JoinBranch.objects.filter(
                branch_id=game.team_a, joinning_type__in=[JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE]
            )
            team_b_managers = JoinBranch.objects.filter(
                branch_id=game.team_b, joinning_type__in=[JoinBranch.MANAGERIAL_STAFF_TYPE, JoinBranch.COACH_STAFF_TYPE]
            )

            # Create the notification message
            notification_message = _("Your uniform has been rejected for the tournament {} by the referee. Please add a new uniform ASAP.").format(
                game.tournament_id.tournament_name
            )

            # Send notification to team A managers
            self.send_rejection_notification(team_a_managers, notification_message, game)

            # Send notification to team B managers
            self.send_rejection_notification(team_b_managers, notification_message, game)

        except Exception as e:
            logging.error(f"Error notifying team managers: {str(e)}", exc_info=True)

    def send_rejection_notification(self, team_managers, message, game):
        """
        Send rejection notification to each manager.
        """
        for manager in team_managers:
            user = manager.user_id  # Assuming JoinBranch.user_id is a ForeignKey to User
            device_token = user.device_token  # Assuming User model has `device_token` field
            device_type = user.device_type  # Assuming User model has `device_type` field
            notification_language = user.current_language  # Assuming User model has `current_language` field

            if notification_language in ['ar', 'en']:
                activate(notification_language)
            data={'type': "assign_handler"}

            if device_token and device_type:
                send_push_notification(
                    device_token=device_token,
                    title=_("Uniform Rejected"),
                    body=message,
                    device_type=device_type,
                    data=data
                )
                notification = Notifictions.objects.create(
                    created_by_id=self.request.user.id,  # Requestor ID (could be dynamically set, e.g., the admin or the user making the change)
                    creator_type=1,      # Creator type (admin or system)
                    targeted_id=user.id,    # Targeted user ID (team member)
                    targeted_type=1,                # Assuming target is always a user
                    title=_("Uniform Rejected"),
                    content=message
                )
                notification.save()

############### Tournament Games h2h  API View ####################
class TournamentGamesh2hCompleteAPIView(APIView):
    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        tournament_id = request.query_params.get('tournament_id', None)
        team_a_id = request.query_params.get('team_a', None)
        team_b_id = request.query_params.get('team_b', None)

        if not tournament_id:
            return Response({
                'status': 0,
                'message': _('Tournament ID is required'),
            }, status=status.HTTP_400_BAD_REQUEST)

        if not team_a_id or not team_b_id:
            return Response({
                'status': 0,
                'message': _('Both Team A and Team B IDs are required'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Query all completed games in the tournament (for stats)
        all_games = TournamentGames.objects.filter(
            tournament_id=tournament_id
        )

        if not all_games.exists():
            return Response({
                'status': 0,
                'message': _('No games found for this tournament'),
            }, status=status.HTTP_404_NOT_FOUND)

        # Calculate standings for all teams
        team_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0, 'points': 0})

        for game in all_games:
            if game.is_draw:
                if game.team_a and game.team_b:
                    team_stats[game.team_a.id]['draws'] += 1
                    team_stats[game.team_b.id]['draws'] += 1
            else:
                if game.winner_id and game.loser_id:
                    team_stats[int(game.winner_id)]['wins'] += 1
                    team_stats[int(game.winner_id)]['points'] += 1  # 1 point for a win
                    team_stats[int(game.loser_id)]['losses'] += 1

        standings = [
            {
                'team_id': team_id,
                'wins': stats['wins'],
                'losses': stats['losses'],
                'draws': stats['draws'],
                'points': stats['points']
            }
            for team_id, stats in team_stats.items()
        ]

        standings.sort(key=lambda x: x['points'], reverse=True)  # Sort by points descending
        team_positions = {team['team_id']: index + 1 for index, team in enumerate(standings)}

        # Query games for H2H view (recent meetings)
        h2h_games = TournamentGames.objects.filter(
            finish=True,  # Filter only by game_finish for recent meetings
            tournament_id=tournament_id
        ).filter(
            (Q(team_a__id=team_a_id) & Q(team_b__id=team_b_id)) |
            (Q(team_a__id=team_b_id) & Q(team_b__id=team_a_id))
        ).order_by('-game_start_time')[:5]  # Get the latest 5 games by game_start_time

        # Prepare stats
        team_a_stats = team_stats.get(int(team_a_id), {'wins': 0, 'losses': 0, 'draws': 0})
        team_b_stats = team_stats.get(int(team_b_id), {'wins': 0, 'losses': 0, 'draws': 0})

        stats = {
            "team_a_position": team_positions.get(int(team_a_id), None),
            "team_b_position": team_positions.get(int(team_b_id), None),
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

        # Serialize H2H games
        if h2h_games.exists():
            serializer = TournamentGamesHead2HeadSerializer(
                h2h_games, many=True, context={'tournament_id': tournament_id, 'team_positions': team_positions}
            )
            recent_meetings = serializer.data
        else:
            recent_meetings = []  # Return an empty list if no games are found

        return Response({
            'status': 1,
            'message': _('H2H Fetch Successfully'),
            'data': {
                "stats": stats,
                "recent_meetings": recent_meetings
            }
        }, status=status.HTTP_200_OK)

############################ FETCH AND CREATE GROUP TEAM WITH ADDING OR UPDATING TEAM ###########################

class TournamentGroupTeamListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        tournament_id = request.query_params.get('tournament_id')

        if not tournament_id:
            return Response({
                'status': 0,
                'message': _('Tournament ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch all groups associated with the tournament
        groups = GroupTable.objects.filter(tournament_id=tournament_id).order_by('group_name')

        if not groups.exists():
            return Response({
                'status': 0,
                'message': _('No groups found for the specified tournament.')
            }, status=status.HTTP_404_NOT_FOUND)

        grouped_data = []
        for group in groups:
            # Fetch teams in the current group
            teams = TournamentGroupTeam.objects.filter(
                group_id=group.id,
                tournament_id=tournament_id
            ).select_related('group_id', 'team_branch_id')

            team_stats = []
            for team in teams:
                team_id = team.team_branch_id.id if team.team_branch_id else None

                # Query games where the team is either team_a or team_b, and the game is finished
                games = TournamentGames.objects.filter(
                    (Q(team_a=team_id) | Q(team_b=team_id)),
                    group_id=group.id,
                    tournament_id=tournament_id,
                    finish=True
                )
                match_played = games.count()

                # Calculate total goals for the team (sum of goals scored in games where the team is involved)
                total_goals = games.aggregate(
                    total_goals_a=Sum('team_a_goal'),
                    total_goals_b=Sum('team_b_goal')
                )
                total_goals_scored = total_goals['total_goals_a'] or 0
                total_goals_conceded = total_goals['total_goals_b'] or 0
                total_goals = total_goals_scored 
                # Calculate conceded goals (goals scored by the opponent)
                conceded_goals = games.aggregate(
                    total_conceded=Sum(
                        Case(
                            When(team_a=team_id, then='team_b_goal'),
                            When(team_b=team_id, then='team_a_goal'),
                            default=0,
                            output_field=models.IntegerField()
                        )
                    )
                )['total_conceded'] or 0

                # Calculate "+/-" (difference between total goals scored and conceded)
                goal_difference = total_goals_scored - conceded_goals

                # Total wins, losses, and draws
                total_wins = games.filter(winner_id=team_id).count()
                total_losses = games.filter(loser_id=team_id).count()
                total_draws = games.filter(is_draw=True).count()
                # Points calculation: 1 point per win
                points = total_wins  # 1 point per win, 0 for draw and loss

                # Serialize the team data
                serializer = DetailedTournamentGroupTeamSerializer(team)
                team_data = serializer.data

                # Update the serialized data with additional statistics
                team_data.update({
                    "match_played": match_played,
                    "total_goals": total_goals,
                    "total_wins": total_wins,
                    "total_losses": total_losses,
                    "total_draws": total_draws,
                    "points": points,
                    "conceded_goals": conceded_goals,
                    "+/-": goal_difference  # Add the goal difference (total goals - conceded goals)
                })
                team_stats.append(team_data)

            # Sort teams by points (descending), and use total goals as a tie-breaker
            sorted_team_stats = sorted(team_stats, key=lambda x: (x['points'], x['total_goals']), reverse=True)

            grouped_data.append({
                "group_id": group.id,
                "group_name": group.group_name,
                "teams": sorted_team_stats
            })

        return Response({
            'status': 1,
            'message': _('Tournament Group Points Table fetched successfully.'),
            'data': grouped_data
        }, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        team_branch_id = request.data.get('team_id')
        group_id = request.data.get('group_id')
        tournament_id = request.data.get('tournament_id')

        if not (team_branch_id and group_id and tournament_id):
            return Response({
                'status': 0,
                'message': _('team_id, group_id, and tournament_id are required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate tournament existence
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Tournament does not exist.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate group existence and its relation to the tournament
        try:
            group_instance = GroupTable.objects.get(id=group_id, tournament_id=tournament_id)
        except GroupTable.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('The provided group does not belong to the specified tournament.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Check if the team already exists in the tournament
            existing_team = TournamentGroupTeam.objects.filter(
                team_branch_id=team_branch_id, tournament_id=tournament_id
            ).first()

            if existing_team:
                # If the team already has a group assigned (not NULL), show an error message
                if existing_team.group_id:
                    return Response({
                        'status': 0,
                        'message': _('The team is already assigned to another group in this tournament.'),
                    }, status=status.HTTP_400_BAD_REQUEST)

                # If group_id is NULL, update the record
                existing_team.group_id = group_instance
                existing_team.status = 1  # Update the status if required
                existing_team.save(update_fields=['group_id', 'status', 'updated_at'])
                return Response({
                    'status': 1,
                    'message': _('Tournament Group Team added successfully.'),
                    'data': TournamentGroupTeamSerializer(existing_team).data
                }, status=status.HTTP_200_OK)

            # If no existing assignment, return an error
            return Response({
                'status': 0,
                'message': _('No team found to add.'),
            }, status=status.HTTP_400_BAD_REQUEST)

class UpcomingGameView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        user = request.user
        user_id = user.id
        user_role = user.role.id  # Assuming `role` is a related field
        one_hour_ago = now() - timedelta(hours=1)
        current_time = now()

        all_games = []

        # Condition 1: Statistics Handler
        if user_role == 5:
            tournament_games = TournamentGames.objects.filter(
                Q(game_date__gt=current_time.date()) | 
                (Q(game_date=current_time.date()) & Q(game_start_time__gte=current_time.time())) | 
                (Q(game_date=current_time.date()) & Q(game_end_time__gte=one_hour_ago)),
                game_statistics_handler=user_id,
                finish=False
            ).order_by('game_date', 'game_start_time')

            friendly_games = FriendlyGame.objects.filter(
                Q(game_date__gt=current_time.date()) | 
                (Q(game_date=current_time.date()) & Q(game_start_time__gte=current_time.time())) | 
                (Q(game_date=current_time.date()) & Q(game_end_time__gte=one_hour_ago)),
                game_statistics_handler=user_id,
                finish=False
            ).order_by('game_date', 'game_start_time')

            all_games += list(tournament_games) + list(friendly_games)

        # Condition 2: Role 6/3 (Coach/Manager in a Branch)
        if user_role in [6, 3]:
            branches = JoinBranch.objects.filter(
                user_id=user_id,
                joinning_type__in=[JoinBranch.COACH_STAFF_TYPE, JoinBranch.MANAGERIAL_STAFF_TYPE]
            ).values_list('branch_id', flat=True)

            if branches:
                tournament_games = TournamentGames.objects.filter(
                    Q(game_date__gt=current_time.date()) | 
                    (Q(game_date=current_time.date()) & Q(game_start_time__gte=current_time.time())) | 
                    (Q(game_date=current_time.date()) & Q(game_end_time__gte=one_hour_ago)),
                    Q(team_a_id__in=branches) | Q(team_b_id__in=branches),
                    finish=False
                ).order_by('game_date', 'game_start_time')

                friendly_games = FriendlyGame.objects.filter(
                    Q(game_date__gt=current_time.date()) | 
                    (Q(game_date=current_time.date()) & Q(game_start_time__gte=current_time.time())) | 
                    (Q(game_date=current_time.date()) & Q(game_end_time__gte=one_hour_ago)),
                    Q(team_a_id__in=branches) | Q(team_b_id__in=branches),
                    finish=False
                ).order_by('game_date', 'game_start_time')

                all_games += list(tournament_games) + list(friendly_games)

        # Condition 3: Role 4 (Game Official)
        if user_role == 4:
            tournament_games = TournamentGames.objects.filter(
                Q(game_date__gt=current_time.date()) | 
                (Q(game_date=current_time.date()) & Q(game_start_time__gte=current_time.time())) | 
                (Q(game_date=current_time.date()) & Q(game_end_time__gte=one_hour_ago)),
                finish=False,
                gameofficials__official_id=user_id,
                gameofficials__officials_type_id__in=[2, 3, 4, 5]
            ).order_by('game_date', 'game_start_time')

            friendly_games = FriendlyGame.objects.filter(
                Q(game_date__gt=current_time.date()) | 
                (Q(game_date=current_time.date()) & Q(game_start_time__gte=current_time.time())) | 
                (Q(game_date=current_time.date()) & Q(game_end_time__gte=one_hour_ago)),
                finish=False,
                friendlygamegameofficials__official_id=user_id,
                friendlygamegameofficials__officials_type_id__in=[2, 3, 4, 5]
            ).order_by('game_date', 'game_start_time')

            all_games += list(tournament_games) + list(friendly_games)

        # Combine and sort all games
        all_games = sorted(all_games, key=lambda game: (game.game_date, game.game_start_time))

        # Response for the first game
        if all_games:
            first_game = all_games[0]

            # Role 6/3-specific response
            if user_role in [6, 3]:
                branches = list(branches)
                game_type = "Friendly" if isinstance(first_game, FriendlyGame) else "Tournament"
                team_id = (
                    first_game.team_a.id
                    if first_game.team_a.id in branches
                    else first_game.team_b.id
                )
                game_details = {
                    "game_id": first_game.id,
                    "team_name": (
                        first_game.team_a.team_name
                        if first_game.team_a.id in branches
                        else first_game.team_b.team_name
                    ),
                    "opponent_team_name": (
                        first_game.team_b.team_name
                        if first_game.team_a.id in branches
                        else first_game.team_a.team_name
                    ),
                    "game_date": first_game.game_date,
                    "game_start_time": first_game.game_start_time,
                    "game_end_time": first_game.game_end_time,
                    "user_role": user_role,
                    "extra_time":first_game.extra_time,
                    "status": "Upcoming",
                }
                if game_type == "Tournament":
                    game_details["tournament_id"] = (
                        first_game.tournament_id.id if first_game.tournament_id else None
                    )

                return Response(
                    {
                        "status": 1,
                        "message": "Upcoming game fetched successfully.",
                        "data": {
                            "game_type": game_type,
                            "team_id": team_id,
                            "game_details": game_details,
                        },
                    },
                    status=200,
                )

            # Default response for other roles
            game_type = "Tournament" if isinstance(first_game, TournamentGames) else "Friendly"

            response_data = {
                "status": 1,
                "message": "Upcoming {} game fetched successfully.".format(game_type),
                "data": {
                    "game_type": game_type,
                    "game_start_time": first_game.game_start_time,
                    "game_end_time": first_game.game_end_time,
                    "game_details": {
                        "game_id": first_game.id,
                        "team_a": {
                            "id": first_game.team_a.id if first_game.team_a else None,
                            "name": first_game.team_a.team_name if first_game.team_a else None,
                        },
                        "team_b": {
                            "id": first_game.team_b.id if first_game.team_b else None,
                            "name": first_game.team_b.team_name if first_game.team_b else None,
                        },
                        "user_role": user_role,
                        # Add "tournament_id" only if game_type is "Tournament"
                        **({"tournament_id": first_game.tournament_id.id} if game_type == "Tournament" and first_game.tournament_id else {}),
                        **({"tournament_name": first_game.tournament_id.tournament_name} if game_type == "Tournament" and first_game.tournament_id else {})
                    },
                },
            }
            return Response(response_data, status=200)

        return Response(
            {
                "status": 0,
                "message": _('No upcoming games found for the user.'),
            },
            status=200,
        )


################### Fetch My Games ################################

class FetchMyGamesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Determine the language for the response
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        created_by_id = request.GET.get('created_by_id', None)
        creator_type = str(request.GET.get('creator_type', 0))

        if creator_type == '2' and not created_by_id:
            return Response({"status": 0, "message": "created_by_id must be provided for creator_type 2."})

        creator_type = int(creator_type)
        created_by_id = int(created_by_id) if created_by_id else None

        user_teams = []
        teams_data = []

        # Fetch user teams based on creator type
        if creator_type == 1:
            user_teams = list(TeamBranch.objects.filter(joinbranch__user_id=created_by_id).values_list('id', flat=True))
        elif creator_type == 2 and created_by_id:
            teams_data = TeamBranch.objects.filter(team_id__id=created_by_id)

        # Fetch games based on teams
        tournament_games = []
        friendly_games = []

        if creator_type == 1:
            tournament_games = TournamentGames.objects.filter(
                Q(team_a__id__in=user_teams) | Q(team_b__id__in=user_teams)
            ).distinct()
            friendly_games = FriendlyGame.objects.filter(
                Q(team_a__id__in=user_teams) | Q(team_b__id__in=user_teams)
            ).distinct()

        if creator_type == 2 and teams_data:
            for team in teams_data:
                tournament_games += TournamentGames.objects.filter(
                    Q(team_a=team) | Q(team_b=team)
                ).distinct()
                friendly_games += FriendlyGame.objects.filter(
                    Q(team_a=team) | Q(team_b=team)
                ).distinct()

        # Use a set to avoid duplicates
        seen_game_ids = set()

        # Combine tournament games and friendly games
        all_games = []

        # Process tournament games
        for game in tournament_games:
            if game.id not in seen_game_ids:
                seen_game_ids.add(game.id)
                all_games.append({
                    "id": game.id,
                    "game_type": "Tournament",
                    "tournament_id": game.tournament_id.id if game.tournament_id else None,
                    "tournament_name": game.tournament_id.tournament_name if game.tournament_id else None,
                    "game_number": game.game_number,
                    "game_date": str(game.game_date),
                    "game_start_time": str(game.game_start_time),
                    "game_end_time": str(game.game_end_time),
                    "group_id": game.group_id.id if game.group_id else None,
                    "group_id_name": game.group_id.group_name if game.group_id else None,
                    "team_a": game.team_a.id if game.team_a else None,
                    "team_a_name": game.team_a.team_name if game.team_a else None,
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a and game.team_a.team_id and game.team_a.team_id.team_logo else None,
                    "team_a_goal": game.team_a_goal,
                    "team_b": game.team_b.id if game.team_b else None,
                    "team_b_name": game.team_b.team_name if game.team_b else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b and game.team_b.team_id and game.team_b.team_id.team_logo else None,
                    "team_b_goal": game.team_b_goal,
                    "game_field_id": game.game_field_id.id if game.game_field_id else None,
                    "game_field_id_name": game.game_field_id.field_name if game.game_field_id else None,
                    "finish": game.finish,
                    "winner": game.winner_id,
                    "loser_id": game.loser_id,
                    "is_draw": game.is_draw,
                    "created_by": game.tournament_id.team_id.id,
                })

        # Process friendly games
        for game in friendly_games:
            if game.id not in seen_game_ids:
                seen_game_ids.add(game.id)
                all_games.append({
                    "id": game.id,
                    "game_type": "Friendly",
                    "game_number": game.game_number,
                    "game_date": str(game.game_date),
                    "game_start_time": str(game.game_start_time),
                    "game_end_time": str(game.game_end_time),
                    "group_id": None,
                    "group_id_name": None,
                    "team_a": game.team_a.id if game.team_a else None,
                    "team_a_name": game.team_a.team_name if game.team_a else None,
                    "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a and game.team_a.team_id and game.team_a.team_id.team_logo else None,
                    "team_a_goal": game.team_a_goal,
                    "team_b": game.team_b.id if game.team_b else None,
                    "team_b_name": game.team_b.team_name if game.team_b else None,
                    "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b and game.team_b.team_id and game.team_b.team_id.team_logo else None,
                    "team_b_goal": game.team_b_goal,
                    "game_field_id": game.game_field_id.id if game.game_field_id else None,
                    "game_field_id_name": game.game_field_id.field_name if game.game_field_id else None,
                    "finish": game.finish,
                    "winner": game.winner_id,
                    "loser_id": game.loser_id,
                    "is_draw": game.is_draw,
                    "created_by":game.created_by.id,
                })

        # Sort all games by game_date and game_start_time
        all_games.sort(key=lambda x: (x["game_date"], x["game_start_time"]))

        # Implement Pagination
        page = int(request.GET.get("page", 1))
        page_size = 10
        total_records = len(all_games)
        total_pages = (total_records + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size

        # Paginate the games
        paginated_games = all_games[start:end]

        # Return the response
        return Response({
            "status": 1,
            "message": "Games fetched successfully.",
            "total_records": total_records,
            "total_pages": total_pages,
            "current_page": page,
            "data": paginated_games,
        })

class FetchAllGamesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        user = request.user
        creator_type = request.query_params.get('creator_type')
        created_by_id = request.query_params.get('created_by_id')
        notification_count = Notifictions.objects.filter(targeted_id=created_by_id, targeted_type=creator_type,read=False).count()


        if not user.is_authenticated:
            return Response({"status": 0, "message": "User is not authenticated."})

        tournament_games = TournamentGames.objects.all()
        friendly_games = FriendlyGame.objects.all()

        games_by_date = {}

        # Process tournament games
        for game in tournament_games:
            date_str = game.game_date.strftime('%A,%Y-%m-%d') if game.game_date else "Unknown"
            if date_str not in games_by_date:
                games_by_date[date_str] = {"tournament": []}

            tournament_name = game.tournament_id.tournament_name if game.tournament_id else "Unknown Tournament"
            
            tournament_entry = next(
                (entry for entry in games_by_date[date_str]["tournament"] if entry["tournament_name"] == tournament_name),
                None
            )
            if not tournament_entry:
                tournament_entry = {
                    "tournament_name": tournament_name,
                    "games": []
                }
                games_by_date[date_str]["tournament"].append(tournament_entry)

            tournament_entry["games"].append({
                "id": game.id,
                "tournament_id": game.tournament_id.id if game.tournament_id else None,
                "game_number": game.game_number,
                "game_date": str(game.game_date),
                "game_start_time": str(game.game_start_time),
                "game_end_time": str(game.game_end_time),
                "group_id": game.group_id.id if game.group_id else None,
                "group_id_name": game.group_id.group_name if game.group_id else None,
                "team_a": game.team_a.id if game.team_a else None,
                "team_a_name": game.team_a.team_name if game.team_a else None,
                "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a and game.team_a.team_id.team_logo else None,
                "team_a_goal": game.team_a_goal,
                "team_b": game.team_b.id if game.team_b else None,
                "team_b_name": game.team_b.team_name if game.team_b else None,
                "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b and game.team_b.team_id.team_logo else None,
                "team_b_goal": game.team_b_goal,
                "game_field_id": game.game_field_id.id if game.game_field_id else None,
                "game_field_id_name": game.game_field_id.field_name if game.game_field_id else None,
                "finish": game.finish,
                "winner": game.winner_id,
                "loser_id": game.loser_id,
                "is_draw": game.is_draw,
                "created_at": game.created_at,
                "updated_at": game.updated_at,
                "game_type": "Tournament",
            })

        # Process friendly games as a pseudo-tournament
        for game in friendly_games:
            date_str = game.game_date.strftime('%A,%Y-%m-%d') if game.game_date else "Unknown"
            if date_str not in games_by_date:
                games_by_date[date_str] = {"tournament": []}
            
            friendly_tournament_entry = next(
                (entry for entry in games_by_date[date_str]["tournament"] if entry["tournament_name"] == "Friendly Games"),
                None
            )
            if not friendly_tournament_entry:
                friendly_tournament_entry = {
                    "tournament_name": "Friendly Games",
                    "games": []
                }
                games_by_date[date_str]["tournament"].append(friendly_tournament_entry)

            friendly_tournament_entry["games"].append({
                "id": game.id,
                "game_number": game.game_number,
                "game_date": str(game.game_date),
                "game_start_time": str(game.game_start_time),
                "game_end_time": str(game.game_end_time),
                "group_id": None,
                "group_id_name": None,
                "team_a": game.team_a.id if game.team_a else None,
                "team_a_name": game.team_a.team_name if game.team_a else None,
                "team_a_logo": game.team_a.team_id.team_logo.url if game.team_a and game.team_a.team_id.team_logo else None,
                "team_a_goal": game.team_a_goal,
                "team_b": game.team_b.id if game.team_b else None,
                "team_b_name": game.team_b.team_name if game.team_b else None,
                "team_b_logo": game.team_b.team_id.team_logo.url if game.team_b and game.team_b.team_id.team_logo else None,
                "team_b_goal": game.team_b_goal,
                "game_field_id": game.game_field_id.id if game.game_field_id else None,
                "game_field_id_name": game.game_field_id.field_name if game.game_field_id else None,
                "finish": game.finish,
                "winner": game.winner_id,
                "loser_id": game.loser_id,
                "is_draw": game.is_draw,
                "created_at": game.created_at,
                "updated_at": game.updated_at,
                "game_type": "Friendly",
            })

        # Sort the games by date (latest first)
            sorted_games_by_date = dict(sorted(
                games_by_date.items(),
                key=lambda x: datetime.strptime(x[0], '%A,%Y-%m-%d') if x[0] != "Unknown" else datetime.min,
                reverse=True
            ))

        # Format the response
            response_data = [
                {
                    "date": date,
                    "tournament": games["tournament"],
                }
                for date, games in sorted_games_by_date.items()
            ]

            # Pagination
            page = int(request.GET.get("page", 1))
            page_size = 10  # Adjust as needed
            total_records = len(response_data)
            total_pages = (total_records + page_size - 1) // page_size
            start = (page - 1) * page_size
            end = start + page_size

            return Response({
                "status": 1,
                "message": "Games fetched successfully.",
                "total_records": total_records,
                "total_pages": total_pages,
                "current_page": page,
                "data": response_data[start:end],
                "notification_count": notification_count  # Include notification count here

            })

############################ Tournaments Game Stats  API ########################################
class TeamGameDetailStatsAPIView(APIView):
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
            tournament_id = request.query_params.get('tournament_id')

            if not tournament_id:
                return Response(
                    {'status': 0, 'message': _('tournament_id is required.')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not game_id:
                return Response(
                    {'status': 0, 'message': _('game_id is required.')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Fetch the game object
            game = TournamentGames.objects.filter(
                id=game_id,
                tournament_id=tournament_id
            ).select_related('team_a', 'team_b').first()

            if not game:
                return Response(
                    {'status': 0, 'message': _('Game not found with the given criteria.')},
                    status=status.HTTP_404_NOT_FOUND
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



class ExtraTimeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Getting data from the request
        game_type = request.data.get('game_type')  # Either "Tournament" or "Friendly"
        game_id = request.data.get('game_id')
        tournament_id = request.data.get('tournament_id')  # Only needed for Tournament games
        extra_time_value = request.data.get('extra_time')  # 1 to add, -1 to remove
   
        extra_time_value=int(extra_time_value)


        # Check if required fields are provided
        if not game_type or not game_id:
            return Response({
                "status": 0,
                "message": _("Game type and game ID are required.")
            }, status=400)

        # Ensure extra_time_value is provided and is either 1 or -1
        if extra_time_value not in [1, -1]:
            return Response({
                "status": 0,
                "message": _("Invalid value for 'extra_time'. It must be 1 (add) or -1 (remove).")
            }, status=400)

        # Handle "Tournament" game type
        if game_type == "Tournament":
            if not tournament_id:
                return Response({
                    "status": 0,
                    "message": _("Tournament ID is required for Tournament games.")
                }, status=400)

            # Find the Tournament game using both game_id and tournament_id
            game = TournamentGames.objects.filter(id=game_id, tournament_id=tournament_id).first()

        # Handle "Friendly" game type
        elif game_type == "Friendly":
            # Find the Friendly game using only game_id
            game = FriendlyGame.objects.filter(id=game_id).first()

        else:
            return Response({
                "status": 0,
                "message": _("Invalid game type. Must be either 'Tournament' or 'Friendly'.")
            }, status=400)

        if not game:
            return Response({
                "status": 0,
                "message": _("Game not found.")
            }, status=404)

        # If extra_time_value is 1, add 1 to extra_time
        if extra_time_value == 1:
            game.extra_time += 1

        # If extra_time_value is -1, remove 1 from extra_time but ensure it doesn't go below 0
        elif extra_time_value == -1:
            if game.extra_time > 0:
                game.extra_time -= 1
            else:
                return Response({
                    "status": 0,
                    "message": _("Extra time is already at 0, cannot remove further.")
                }, status=400)

        # Save the updated game
        game.save()

        return Response({
            "status": 1,
            "message": _("Extra time updated successfully."),
            "data": {
                "game_id": game.id,
                "extra_time": game.extra_time
            }
        }, status=200)
    




