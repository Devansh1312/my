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
                file_name = f"tournament_logo/{tournament_instance.tournament_name}_{tournament_instance.id}.{file_extension}"
                logo_path = default_storage.save(file_name, logo)
                tournament_instance.logo = logo_path
                tournament_instance.save()

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


class GroupTableAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        group_table=GroupTable.objects.all()
        group_table_data = GroupTableSerializer(group_table, many=True).data
        
        return Response({
            'status': 1,
            'message': _('Group table retrieved successfully.'),
            'data': group_table_data

        })
    


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

        # Filter TournamentGroupTeam instances by tournament_id
        tournament_group_teams = TournamentGroupTeam.objects.filter(tournament_id=tournament_id)

        # Check if any teams were found for the given tournament
        if not tournament_group_teams.exists():
            return Response({
                'status': 0,
                'message': _('No Tournament Group Teams found for the specified tournament.')
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TournamentGroupTeamSerializer(tournament_group_teams, many=True)

        return Response({
            'status': 1,
            'message': _('Tournament Group Teams fetched successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    # Handle POST request to create a new TournamentGroupTeam instance
    def post(self, request, *args, **kwargs):
        # Check if the team is already added to the same group
        team_branch_id = request.data.get('team_branch_id')  # Assuming the team ID is in the request body
        group_id = request.data.get('group_id')  # Assuming the group ID is in the request body

        if TournamentGroupTeam.objects.filter(team_branch_id=team_branch_id, group_id=group_id).exists():
            return Response({
                'status': 0,
                'message': _('The team is already added to this group.'),
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the team is already added to another group in the same tournament
        tournament_id = request.data.get('tournament_id')  # Assuming the tournament ID is in the request body

        if TournamentGroupTeam.objects.filter(team_branch_id=team_branch_id, tournament_id=tournament_id).exists():
            return Response({
                'status': 0,
                'message': _('The team is already added to another group in this tournament.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # If validation passes, proceed to create the team-group association
        serializer = TournamentGroupTeamSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 1,
                'message': _('Tournament Group Team Added successfully.'),
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'status': 0,
            'message': _('Failed to create Tournament Group Team.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

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