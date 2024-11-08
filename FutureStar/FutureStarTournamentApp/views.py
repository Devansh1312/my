from collections import defaultdict,OrderedDict
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.utils.translation import activate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from FutureStarAPI.serializers import *
from FutureStarTeamApp.serializers import *
from FutureStarTournamentApp.serializers import *




from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from FutureStar_App.models import *
from FutureStarTeamApp.models import *
from FutureStarAPI.models import *
from FutureStarTournamentApp.models import *


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
from django.db import transaction
import string
from rest_framework.exceptions import ValidationError
import re
import logging
from django.utils.crypto import get_random_string
from django.utils.timezone import now

class CustomTournamentPagination(PageNumberPagination):
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    page_size = 10
    page_query_param = 'page'
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        try:
            page_number = request.data.get(self.page_query_param, 1)
            self.page = int(page_number)
            if self.page < 1:
                raise ValidationError("Page number must be a positive integer.")
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

############################# GET TOURNAMENTS ###########################

class TournamentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        paginator = CustomTournamentPagination()
        tournaments = Tournament.objects.all()

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

            # Handle logo upload
            if 'tournament_banner' in request.FILES:
                logo = request.FILES['tournament_banner']
                file_extension = logo.name.split('.')[-1]
                unique_suffix = get_random_string(8)
                file_name = f"tournament_banner/{tournament_instance.id}_{unique_suffix}.{file_extension}"
                logo_path = default_storage.save(file_name, logo)
                tournament_instance.tournament_banner = logo_path
                tournament_instance.save()

            serializer.save()
            return Response({
                'status': 1,
                'message': _('Tournament created successfully.'),
                'data': TournamentSerializer(tournament_instance).data
            }, status=status.HTTP_201_CREATED)
        
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

    def delete(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        tournament_id = request.query_params.get('tournament_id')
        try:
            tournament_instance = Tournament.objects.get(id=tournament_id)
            tournament_instance.delete()
            return Response({
                'status': 1,
                'message': _('Tournament deleted successfully.')
            }, status=status.HTTP_204_NO_CONTENT)
        except Tournament.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Tournament not found.')
            }, status=status.HTTP_404_NOT_FOUND)


############################# TOURNAMENT DETAIL WITH ID ###########################
class TournamentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
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


class TournamentGroupTeamListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    # Handle GET request to list TournamentGroupTeam instances
    def get(self, request, *args, **kwargs):
        tournament_id = request.query_params.get('tournament_id')  # Get tournament ID from query params

        if not tournament_id:
            return Response({
                'status': 0,
                'message': _('Tournament ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Filter and order TournamentGroupTeam instances by tournament_id and group_name
        tournament_group_teams = TournamentGroupTeam.objects.filter(
            tournament_id=tournament_id
        ).select_related('group_id').order_by('group_id__group_name')

        # Check if any teams were found for the given tournament
        if not tournament_group_teams.exists():
            return Response({
                'status': 0,
                'message': _('No Tournament Group Teams found for the specified tournament.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Group teams by group_id, maintaining alphabetical order
        grouped_teams = defaultdict(list)
        for team in tournament_group_teams:
            group_name = team.group_id.group_name if team.group_id else 'Unknown Group'
            grouped_teams[group_name].append(team)

        # Use OrderedDict to ensure groups are ordered alphabetically in the response
        grouped_data = OrderedDict()
        for group_name in sorted(grouped_teams.keys()):
            teams = grouped_teams[group_name]
            serializer = TournamentGroupTeamSerializer(teams, many=True)
            grouped_data[group_name] = serializer.data

        return Response({
            'status': 1,
            'message': _('Tournament Group Teams fetched successfully.'),
            'data': grouped_data
        }, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):

        team_branch_id = request.data.get('team_branch_id')

        group_id = request.data.get('group_id')

        tournament_id = request.data.get('tournament_id')

        

        # Check if tournament exists and get its capacity

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



        # Check if the team is already in this group

        if TournamentGroupTeam.objects.filter(

            team_branch_id=team_branch_id, group_id=group_id, tournament_id=tournament_id

        ).exists():

            return Response({

                'status': 0,

                'message': _('The team is already added to this group.'),

            }, status=status.HTTP_400_BAD_REQUEST)

        

        # Check if the team is already in another group in the same tournament

        existing_team = TournamentGroupTeam.objects.filter(

            team_branch_id=team_branch_id, tournament_id=tournament_id

        ).first()

        

        # Retrieve the GroupTable instance for the given group_id

        group_instance = get_object_or_404(GroupTable, id=group_id)

        

        if existing_team:

            # Update the existing record with new data if needed

            existing_team.group_id = group_instance

            existing_team.status = 1

            existing_team.save()



            serializer = TournamentGroupTeamSerializer(existing_team)

            return Response({

                'status': 1,

                'message': _('Tournament Group Team updated successfully.'),

                'data': serializer.data

            }, status=status.HTTP_200_OK)

        

        # If no existing team, create a new one

        serializer = TournamentGroupTeamSerializer(data=request.data)

        if serializer.is_valid():

            serializer.save(group_id=group_instance, status=1)  # Set group_id and status when creating a new entry

            return Response({

                'status': 1,

                'message': _('Tournament Group Team added successfully.'),

                'data': serializer.data

            }, status=status.HTTP_201_CREATED)



        return Response({

            'status': 0,

            'message': _('Failed to create Tournament Group Team.'),

            'errors': serializer.errors

        }, status=status.HTTP_400_BAD_REQUEST)
    
############################# REQUEST TO JOIN TEAM ###########################

class TeamJoiningRequest(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def post(self, request, *args, **kwargs):
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
        
        # Create a new TournamentGroupTeam entry with group_id as None and status as 0
        tournament_group_team = TournamentGroupTeam.objects.create(
            group_id=None,          # set group_id to null
            team_branch_id=team_branch,
            tournament_id=tournament,
            status=0                 # set status to 0
        )
        
        # Serialize and return the created object
        serializer = TournamentGroupTeamSerializer(tournament_group_team)
        return Response({
            'status': 1,
            'message': _('Team joining request created successfully.'),
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


############################# FETCH TEAM LISTS APPROVED,REQUESTED AND REJECTED ###########################

class TournamentGroupTeamListView(APIView):

    def get(self, request):
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
                    tournament_id=tournament_id, status__in=[0, 3]
                )
        else:
            return Response(
                {"error": "Invalid team_list parameter. Use 1 for active teams, 2 for inactive teams."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Serialize the filtered teams
        serializer = TournamentGroupTeamSerializer(teams, many=True)
        return Response({
            'status': 1,
            'message': _('Team Fetched successfully.'),
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

############################# REJECT TEAM OF GROUP ###########################

class TeamRejectRequest(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def post(self, request, *args, **kwargs):
        team_id = request.data.get('team_id')
        tournament_id = request.data.get('tournament_id')
        
        # Check if the tournament and team exist
        try:
            tournament = Tournament.objects.get(id=tournament_id)
            team_branch = TeamBranch.objects.get(id=team_id)
            print(team_branch)
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
        tournament_group_team.status = 3  # Status 3 for rejected
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
        # Extract parameters from the request
        tournament_id = request.query_params.get('tournament_id')
        search_key = request.query_params.get('search', '').strip()

        # Validate and fetch the tournament
        tournament = get_object_or_404(Tournament, id=tournament_id)
        age_group = tournament.age_group

        # Get group_id from the query (if provided)
        group_id = request.query_params.get('group_id')

        # Filter teams by age_group and search term (if provided)
        queryset = TeamBranch.objects.filter(age_group_id=age_group)

        if search_key:
            queryset = queryset.filter(team_name__icontains=search_key)

        if group_id:
            # Exclude teams that are already associated with the given group in this tournament
            queryset = queryset.exclude(id__in=TournamentGroupTeam.objects.filter(
                tournament_id=tournament_id, group_id=group_id
            ).values_list('team_branch_id', flat=True))

        # Paginate the results
        paginator = self.pagination_class()
        paginated_data = paginator.paginate_queryset(queryset, request, view=self)

        # Format the paginated data to include branch_id, team_name, and team_logo
        formatted_data = [
            {
                "branch_id": branch.id,
                "team_name": branch.team_name,
                "team_logo": branch.upload_image.url if branch.upload_image else None
            }
            for branch in paginated_data
        ]

        # Create response with formatted paginated data
        return paginator.get_paginated_response(formatted_data)