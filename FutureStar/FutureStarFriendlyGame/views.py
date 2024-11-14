from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.utils.translation import activate
from FutureStarTrainingGroupApp.serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from FutureStarFriendlyGame.serializers import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from FutureStar_App.models import *
from FutureStarAPI.models import *
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
from django.db import transaction
import string
from rest_framework.exceptions import ValidationError
import re
import logging
from django.utils.crypto import get_random_string
from django.utils.timezone import now



class ManagerBranchDetail(APIView):
    def get(self, request, *args, **kwargs):
        user_id = request.user.id
        if not user_id:
            return Response({
                'status': 0,
                'message': 'User ID is required.',
                
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            join_branch = JoinBranch.objects.get(user_id=user_id, joinning_type=JoinBranch.MANAGERIAL_STAFF_TYPE)
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
                'total_records': 1,
                'total_pages': 1,
                'current_page': 1,
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
    def post(self, request, *args, **kwargs):
        user_id = request.user.id
        if request.user.role.id != 6:  # Ensure the user has the required role
            return Response({
                'status': 0,
                'message': 'User does not have the required role.',
                
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Ensure the required fields are in the request data
        game_field_id = request.data.get('game_field_id', None)
        if not game_field_id:
            return Response({
                'status': 0,
                'message': 'Game field ID is required.',
                
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the Field instance using the game_field_id
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
                    'total_records': 0,
                    'total_pages': 0,
                    'current_page': 1,
                    'data': {}
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Check that the user is managerial staff for Team A
                join_branch = JoinBranch.objects.get(
                    user_id=user_id, 
                    branch_id=team_a_id, 
                    joinning_type=JoinBranch.MANAGERIAL_STAFF_TYPE
                )

                team_b_id = request.data.get('team_b', None)
                # Save the game with both teams and the correct game field instance
                friendly_game = serializer.save(team_a_id=team_a_id, team_b_id=team_b_id, game_field_id=game_field,created_by=request.user)

                
                return Response({
                    'status': 1,
                    'message': 'Friendly game created successfully.',
                    'total_records': 1,
                    'total_pages': 1,
                    'current_page': 1,
                    'data': FriendlyGameSerializer(friendly_game).data
                }, status=status.HTTP_201_CREATED)
            except JoinBranch.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': 'User is not a Managerial Staff for Team A.',
                    'total_records': 0,
                    'total_pages': 0,
                    'current_page': 1,
                    'data': {}
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 0,
            'message': 'Invalid data.',
            'total_records': 0,
            'total_pages': 0,
            'current_page': 1,
            'data': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class UpdateFriendlyGame(APIView):
    def put(self, request, *args, **kwargs):
        user_id = request.user.id
        if request.user.role.id != 6:  # Ensure the user has the required role
            return Response({
                'status': 0,
                'message': _('User does not have the required role.'),
                
                'data': {}
            }, status=status.HTTP_403_FORBIDDEN)

        game_id = request.data.get('game_id')

        try:
            game = FriendlyGame.objects.get(id=game_id)

            # Check if the user is a managerial staff member of any branch
            try:
                join_branch = JoinBranch.objects.get(
                    user_id=user_id, 
                    joinning_type=JoinBranch.MANAGERIAL_STAFF_TYPE
                )
                
                # Check if `team_b` is empty
                if game.team_b is None:
                    # Assign the manager's branch to `team_b` and update game status
                    game.team_b = join_branch.branch_id
                    game.game_status = 1  # Set status to started
                    game.save()
                    data = FriendlyGameSerializer(game).data
                    return Response({
                        'status': 1,
                        'message': _('Game updated successfully with manager\'s branch as Team B.'),
                        'total_records': 1,
                        'total_pages': 1,
                        'current_page': 1,
                        'data': data
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': 0,
                        'message': _('Team B is already assigned.'),
                        'total_records': 0,
                        'total_pages': 0,
                        'current_page': 1,
                        'data': {}
                    }, status=status.HTTP_400_BAD_REQUEST)

            except JoinBranch.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('User is not a Managerial Staff for any branch.'),
                    'total_records': 0,
                    'total_pages': 0,
                    'current_page': 1,
                    'data': {}
                }, status=status.HTTP_404_NOT_FOUND)
        
        except FriendlyGame.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Game not found.'),
                
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

class DeleteFriendlyGame(APIView):
    def delete(self, request, *args, **kwargs):
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