# Django and Python Standard Library Imports
from datetime import date, timedelta
import os
import random
import re
import string
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db import transaction
from django.db.models import Case, When, F, Q, Sum
from django.utils.crypto import get_random_string
from django.core.files.storage import default_storage
from django.core.paginator import EmptyPage
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.utils.translation import activate

# Django REST Framework Imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError

# App-Specific Imports
from FutureStarAPI.models import *
from FutureStarFriendlyGame.models import FriendlyGame,FriendlyGameLineup,FriendlyGamesPlayerGameStats,FriendlyGameGameOfficials
from FutureStarGameSystem.models import PlayerGameStats,TournamentGames,Lineup,GameOfficials,JoinBranch
from FutureStarTrainingApp.models import Training
from FutureStarTournamentApp.serializers import TournamentGameSerializer
from FutureStarTeamApp.serializers import TeamSerializer
from FutureStarTrainingGroupApp.serializers import TrainingGroupSerializer
from FutureStarAPI.serializers import *
from FutureStar.firebase_config import send_push_notification

# JWT Token Imports
from rest_framework_simplejwt.tokens import RefreshToken
##################################################### User Current Type Switch API Z###############################################
class UpdateCurrentTypeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user  # Retrieve the authenticated user from the token
        
        # Deserialize and validate input data
        serializer = UpdateCurrentTypeSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # Updates the current_type for the authenticated user
            return Response({
                'status': 1,
                'message': _('Current type updated successfully.'),
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'status': 0,
            'message': _('Failed to update current type.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


#################################################### Get User data ##########################################################################################################
def get_user_data(user, request):
    created_by_id = request.query_params.get('created_by_id') or request.data.get('created_by_id', request.user.id)
    creator_type = request.query_params.get('creator_type') or request.data.get('creator_type', FollowRequest.USER_TYPE)
    

    # Counting followers for a user, team, or group
    followers_count = FollowRequest.objects.filter(target_id=user.id, target_type=FollowRequest.USER_TYPE).count()
    # Counting following for a user, team, or group
    following_count = FollowRequest.objects.filter(created_by_id=user.id, creator_type=FollowRequest.USER_TYPE).count()

    post_count = Post.objects.filter(created_by_id=user.id, creator_type=FollowRequest.USER_TYPE).count()
    
    # Check if the current user is following this user
    is_follow = FollowRequest.objects.filter(
        created_by_id=created_by_id,
        creator_type=creator_type,
        target_id=user.id,
        target_type=FollowRequest.USER_TYPE
    ).exists()
    
    gender_name = None
    if user.gender:
        serializer = UserGenderSerializer(user.gender, context={'request': request})
        gender_name = serializer.data['name']
    
    playing_foot =None
    if user.playing_foot:
        serializer = UserPlayingFootSerializer(user.playing_foot, context={'request': request})
        playing_foot = serializer.data['name']
    
    # Main and secondary playing positions with id and combined name-shortname fields
    main_playing_position_name = None
    main_playing_position_id = user.main_playing_position.id if user.main_playing_position else None
    secondary_playing_position_name = None
    secondary_playing_position_id = user.secondary_playing_position.id if user.secondary_playing_position else None

    if user.main_playing_position:
        main_playing_position_name = f"{user.main_playing_position.name_en} - {user.main_playing_position.shortname}"

    if user.secondary_playing_position:
        secondary_playing_position_name = f"{user.secondary_playing_position.name_en} - {user.secondary_playing_position.shortname}"

    return {
        'id': user.id,
        'created_by_id':user.id,
        'followers_count': followers_count,
        'following_count': following_count,
        'creator_type': 1,
        'post_count': post_count,
        'is_follow': is_follow,
        'user_role': user.role_id,
        'username': user.username,
        'phone': user.phone,
        'email': user.email,
        'fullname': user.fullname,
        'bio': user.bio,
        'date_of_birth': user.date_of_birth,
        'age': user.age,
        'gender_id': user.gender.id if user.gender else None,
        'gender_name': gender_name,
        'country_id': user.country.id if user.country else None,
        'country_name': user.country.name if user.country else None,
        'city_id': user.city.id if user.city else None,
        'city_name': user.city.name if user.city else None,
        'nationality': user.nationality,
        'weight': user.weight,
        'height': user.height,
        'main_playing_position_id': main_playing_position_id,
        'main_playing_position_name': main_playing_position_name,
        'secondary_playing_position_id': secondary_playing_position_id,
        'secondary_playing_position_name': secondary_playing_position_name,
        'playing_foot_id': user.playing_foot.id if user.playing_foot else None,
        'playing_foot_name': playing_foot,
        'favourite_local_team': user.favourite_local_team,
        'favourite_team': user.favourite_team,
        'favourite_local_player': user.favourite_local_player,
        'favourite_player': user.favourite_player,
        'profile_picture': user.profile_picture.url if user.profile_picture else None,
        'cover_photo': user.card_header.url if user.card_header else None,
        'device_type': user.device_type,
        'device_token': user.device_token,
        'current_language': user.current_language,
    }


######################################################################################### Get Team Data ###################################################################
def get_team_data(user, request):
    
    # Get the user's team (assuming only one team is allowed per user)
    try:
        team = Team.objects.get(team_founder=user)
    except Team.DoesNotExist:
        return None  # If no team exists, return None or empty dictionary as needed

    # Create the serializer with the team instance and request context
    serializer = TeamSerializer(team, context={'request': request})
    
    # Return serialized team data
    return serializer.data


############################################################################# Get Group Data ######################################################
def get_group_data(user, request):
    
    # Get the user's group (assuming only one group is allowed per user)
    try:
        group = TrainingGroups.objects.get(group_founder=user)
    except TrainingGroups.DoesNotExist:
        return None  # If no group exists, return None or empty dictionary as needed

    # Create the serializer with the group instance and request context
    serializer = TrainingGroupSerializer(group, context={'request': request})
    
    # Return serialized group data
    return serializer.data
###################################################### Send OTP API #############################################################################################################
              
# Generate a random 6-digit OTP
def generate_otp():
    return str(random.randint(100000, 999999))

class send_otp(APIView):
    permission_classes = [AllowAny]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def generate_random_password(self, length=8):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for i in range(length))
    
    def post(self, request, *args, **kwargs):        
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        registration_type = request.data.get('type')
        try:
            # Handle Registration Type 1 (Normal registration)
            if registration_type == 1:
                username = request.data.get('username')
                phone = request.data.get('phone')
                password = request.data.get('password')

                # Check if username or phone already exists, but allow for deleted users to register again
                if Team.objects.filter(team_username=username).exists() or User.objects.filter(username=username) or TrainingGroups.objects.filter(group_username=username).exists():
                    return Response({
                        'status': 0,
                        'message': _('Username already taken.')
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Check if phone exists and is deleted (soft deleted), allowing re-registration
                user = User.objects.filter(phone=phone).first()
                if user and user.is_deleted:
                    # User is soft deleted, proceed with registration
                    otp = generate_otp()
                    otp_record, created = OTPSave.objects.update_or_create(
                        phone=phone,
                        defaults={'phone': phone, 'OTP': otp}
                    )
                    return Response({
                        'status': 1,
                        'message': _('OTP sent successfully.'),
                        'data': otp  # For development, this is sent in the response.
                    }, status=status.HTTP_200_OK)

                elif User.objects.filter(phone=phone).exists():
                    return Response({
                        'status': 0,
                        'message': _('Phone number already in use.')
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Generate OTP and save it if no soft-deleted user is found
                otp = generate_otp()
                otp_record, created = OTPSave.objects.update_or_create(
                    phone=phone,
                    defaults={'phone': phone, 'OTP': otp}
                )

                return Response({
                    'status': 1,
                    'message': _('OTP sent successfully.'),
                    'data': otp  # For development, this is sent in the response.
                }, status=status.HTTP_200_OK)

            # Handle Registration Type 2/3 (Social registration via email)
            elif registration_type in [2, 3]:
                username = request.data.get('username')
                phone = request.data.get('phone')
                email = request.data.get('email')

                if not email:
                    return Response({
                        'status': 0,
                        'message': _('Email already in use.')
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Check email format using regex
                email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
                if not re.match(email_regex, email):
                    return Response({
                        'status': 0,
                        'message': _('Invalid email format.')
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Check if email exists in User table
                if User.objects.filter(email=email).exists():
                    return Response({
                        'status': 0,
                        'message': _('Email already in use.')
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Validate if username or phone already exists if provided
                if username and phone:
                    # Check if username or phone already exists
                    if Team.objects.filter(team_username=username).exists() or User.objects.filter(username=username) or TrainingGroups.objects.filter(group_username=username).exists():
                        return Response({
                            'status': 0,
                            'message': _('Username already taken.')
                        }, status=status.HTTP_400_BAD_REQUEST)

                    # Check if phone exists and is deleted (soft deleted), allowing re-registration
                    user = User.objects.filter(phone=phone).first()
                    if user and user.is_deleted:
                        # User is soft deleted, proceed with registration
                        otp = generate_otp()
                        random_password = self.generate_random_password()
                        otp_record, created = OTPSave.objects.update_or_create(
                            phone=phone,
                            defaults={'phone': phone, 'OTP': otp}
                        )

                        return Response({
                            'status': 1,
                            'message': _('OTP sent successfully.'),
                            'data': otp  # Send OTP in response for development.
                        }, status=status.HTTP_200_OK)

                    if User.objects.filter(phone=phone).exists():
                        return Response({
                            'status': 0,
                            'message': _('Phone number already in use.')
                        }, status=status.HTTP_400_BAD_REQUEST)

                    otp = generate_otp()
                    random_password = self.generate_random_password()
                    otp_record, created = OTPSave.objects.update_or_create(
                        phone=phone,
                        defaults={'phone': phone, 'OTP': otp}
                    )

                    return Response({
                        'status': 1,
                        'message': _('OTP sent successfully.'),
                        'data': otp  # Send OTP in response for development.
                    }, status=status.HTTP_200_OK)

                return Response({
                    'status': 1,
                    'message': _('User can proceed with registration.'),
                }, status=status.HTTP_200_OK)

            return Response({
                'status': 0,
                'message': _('Invalid registration type.')
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': 0,
                'message': _('An error occurred while sending OTP.'),
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

##################################################### Verify and Register API #############################################################################################################
class verify_and_register(APIView):
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        phone = request.data.get("phone")
        otp_input = request.data.get("otp")
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")
        device_type = request.data.get("device_type")
        device_token = request.data.get("device_token")

        # Check if phone, OTP, username, email, and password are provided
        if not phone:
            return Response({
                'status': 0,
                'message': _('Phone is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if not otp_input:
            return Response({
                'status': 0,
                'message': _('OTP is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if not username:
            return Response({
                'status': 0,
                'message': _('Username is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the OTP and phone exist in the OTPSave table
        try:
            otp_record = OTPSave.objects.get(phone=phone, OTP=otp_input)
        except OTPSave.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Invalid OTP or phone number.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if username already exists
        if Team.objects.filter(team_username=username).exists() or User.objects.filter(username=username) or TrainingGroups.objects.filter(group_username=username).exists():
            return Response({
                'status': 0,
                'message': _('Username already taken.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the phone already exists in the User table, and is not deleted
        user = User.objects.filter(phone=phone).first()
        if user:
            if user.is_deleted:
                # User is soft deleted, proceed with registration
                pass
            else:
                return Response({
                    'status': 0,
                    'message': _('Phone number already in use.')
                }, status=status.HTTP_400_BAD_REQUEST)

        if email : 
            # Check if the email already exists in the User table
            if User.objects.filter(email=email).exists():
                return Response({
                    'status': 0,
                    'message': _('Email already in use.')
                }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create the user within a transaction to ensure atomicity
            with transaction.atomic():
                # Create the user in the User table using details from the request body
                user = User.objects.create(
                    username=username,
                    phone=phone,
                    email = email if email else None ,
                    role_id=5,  # Assuming role_id 5 is for regular users
                    device_type=device_type,
                    device_token=device_token
                )
                user.set_password(password)
                user.save()

                # Delete OTP record after successful registration
                otp_record.delete()

                # Generate refresh and access tokens
                refresh = RefreshToken.for_user(user)
                return Response({
                    'status': 1,
                    'message': _('User registered successfully'),
                    'data': {
                        'refresh_token': str(refresh),
                        'access_token': str(refresh.access_token),
                        'user':get_user_data(user, request),
                        'team':get_team_data(user, request),
                        'group':get_group_data(user, request),
                        'current_type':user.current_type,
                    }
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'status': 0,
                'message': _('An error occurred while registering the user.'),
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        phone = request.data.get("phone")
        otp_input = request.data.get("otp")
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")
        device_type = request.data.get("device_type")
        device_token = request.data.get("device_token")

        # Check if phone, OTP, username, email, and password are provided
        if not phone:
            return Response({
                'status': 0,
                'message': _('Phone is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if not otp_input:
            return Response({
                'status': 0,
                'message': _('OTP is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if not username:
            return Response({
                'status': 0,
                'message': _('Username is required.')
            }, status=status.HTTP_400_BAD_REQUEST)


        # Check if the OTP and phone exist in the OTPSave table
        try:
            otp_record = OTPSave.objects.get(phone=phone, OTP=otp_input)
        except OTPSave.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Invalid OTP or phone number.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if username already exists
        if Team.objects.filter(team_username=username).exists() or User.objects.filter(username=username) or TrainingGroups.objects.filter(group_username=username).exists():
            return Response({
                'status': 0,
                'message': _('Username already taken.')
            }, status=status.HTTP_400_BAD_REQUEST)


        # Check if the phone already exists in the User table
        if User.objects.filter(phone=phone).exists():
            return Response({
                'status': 0,
                'message': _('Phone number already in use.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if email : 
        # Check if the email already exists in the User table
            if User.objects.filter(email=email).exists():
                return Response({
                    'status': 0,
                    'message': _('Email already in use.')
                }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create the user within a transaction to ensure atomicity
            with transaction.atomic():
                # Create the user in the User table using details from the request body
                user = User.objects.create(
                    username=username,
                    phone=phone,
                    email = email if email else None ,
                    role_id=5,  # Assuming role_id 5 is for regular users
                    device_type=device_type,
                    device_token=device_token
                )
                user.set_password(password)
                user.save()

                # Delete OTP record after successful registration
                otp_record.delete()

                # Generate refresh and access tokens
                refresh = RefreshToken.for_user(user)
                return Response({
                    'status': 1,
                    'message': _('User registered successfully'),
                    'data': {
                        'refresh_token': str(refresh),
                        'access_token': str(refresh.access_token),
                        'user':get_user_data(user, request),
                        'team':get_team_data(user, request),
                        'group':get_group_data(user, request),
                        'current_type':user.current_type,
                    }
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'status': 0,
                'message': _('An error occurred while registering the user.'),
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

##################################################### Login API ######################################################################
class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            login_type = serializer.validated_data['type']
            device_type = serializer.validated_data['device_type']
            device_token = serializer.validated_data['device_token']

            if login_type == 1:
                # Normal login with username_or_phone and password
                username_or_phone = serializer.validated_data['username']
                password = serializer.validated_data['password']

                # Check if the phone number is linked to a deleted user
                deleted_user = User.objects.filter(phone=username_or_phone, is_deleted=True).first()

                if deleted_user:
                    user = User.objects.filter(phone=username_or_phone, is_deleted=False).first()
                    if not user:
                        return Response({
                            'status': 0,
                            'message': _('This phone number is associated with a deleted account, you have to register again.'),
                        }, status=status.HTTP_400_BAD_REQUEST)

                # Now check if the phone number is linked to a normal (non-deleted) user
                user = User.objects.filter(phone=username_or_phone, is_deleted=False).first() or \
                       User.objects.filter(username=username_or_phone).first()

                if user:
                    if user.check_password(password):
                        if user.role.id == 1:
                            return Response({
                                'status': 0,
                                'message': _('You Cannot Login Here'),
                            }, status=status.HTTP_400_BAD_REQUEST)

                        elif user.is_active:
                            user.device_type = device_type
                            user.device_token = device_token
                            user.last_login = timezone.now()
                            user.save()

                            refresh = RefreshToken.for_user(user)
                            return Response({
                                'status': 1,
                                'message': _('Login successful'),
                                'data': {
                                    'refresh_token': str(refresh),
                                    'access_token': str(refresh.access_token),
                                    'user': get_user_data(user, request),
                                    'team': get_team_data(user, request),
                                    'group': get_group_data(user, request),
                                    'current_type': user.current_type,
                                }
                            }, status=status.HTTP_200_OK)
                    else:
                        return Response({
                            'status': 0,
                            'message': _('Invalid credentials'),
                        }, status=status.HTTP_400_BAD_REQUEST)

                else:
                    return Response({
                        'status': 0,
                        'message': _('User does not exist for the given username or phone.'),
                    }, status=status.HTTP_400_BAD_REQUEST)

            elif login_type in [2, 3]:
                # Login with email, no password provided
                email = serializer.validated_data['username']

                user = User.objects.filter(email=email, is_deleted=False).first()

                if user:
                    # If the user already exists and is not deleted, log them in
                    if user.is_deleted:
                        return Response({
                            'status': 0,
                            'message': _('Your account has been deleted. Please contact support.'),
                        }, status=status.HTTP_400_BAD_REQUEST)

                    if user.role.id == 1:
                        return Response({
                            'status': 0,
                            'message': _('You Cannot Login Here'),
                        }, status=status.HTTP_400_BAD_REQUEST)
                    elif user.is_active:
                        user.device_type = device_type
                        user.device_token = device_token
                        user.last_login = timezone.now()
                        user.save()

                        refresh = RefreshToken.for_user(user)
                        return Response({
                            'status': 1,
                            'message': _('Login successful'),
                            'data': {
                                'refresh_token': str(refresh),
                                'access_token': str(refresh.access_token),
                                'user': get_user_data(user, request),
                                'team': get_team_data(user, request),
                                'group': get_group_data(user, request),
                                'current_type': user.current_type,
                            }
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response({
                            'status': 0,
                            'message': _('Account is inactive'),
                        }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({
                        'status': 0,
                        'message': _('Email does not exist. Please register first.'),
                    }, status=status.HTTP_400_BAD_REQUEST)

        # Custom error handling
        error_message = serializer.errors.get('non_field_errors')
        if error_message:
            return Response({
                'status': 0,
                'message': _(error_message[0])  # Ensures translation is applied
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'status': 0,
                'message': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

##################################################### Logout API ###############################################################
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        try:
            # Fetch the user who is logging out
            user = request.user
            # Clear device_type and device_token
            user.device_type = None
            user.device_token = None
            user.save()
            return Response({
                'status': 1,
                'message': _('Logout successful'),
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': 0,
                'message': _('Logout failed'),
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

####################### User Acount Delete Reason LIST API ##############
class DeleteAccountReasonsListView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        # Order by 'name' field alphabetically
        reason = UserDeleteReason.objects.all().order_by('name_en')
        
        serializer = DeleteAccountReasonSerializer(reason, many=True, context={'request': request})
        
        return Response({
           'status': 1,
           'message': _('Reasons fetched successfully.'),
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

################ Delete User ####################
class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user  # Get the authenticated user
        deleted_reason_id = request.data.get('deleted_reason_id')
        deleted_reason_text = request.data.get('deleted_reason')

        try:
            # Convert deleted_reason_id to an integer if possible
            deleted_reason_id = int(deleted_reason_id)
        except (ValueError, TypeError):
            return Response({
                'status': 0,
                'message': _('Invalid deletion reason ID. It must be an integer.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the reason ID exists
        delete_reason = UserDeleteReason.objects.filter(id=deleted_reason_id).first()
        if not delete_reason:
            return Response({
                'status': 0,
                'message': _('Invalid deletion reason ID.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Mark the user as deleted and set the reason
        user.is_deleted = True
        user.deleted_reason_id = delete_reason  # Assign the UserDeleteReason instance to the foreign key
        user.deleted_reason = deleted_reason_text  # Assign the additional text reason
        user.is_active = False  # Optionally, deactivate the user as well
        user.save()

        return Response({
            'status': 2,
            'message': _('Your account has been deleted successfully.')
        }, status=status.HTTP_200_OK)

##################################################### Forgot Password API #############################################################################################################
class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            user = User.objects.filter(phone=phone).first()

            if user:
                otp = str(random.randint(100000, 999999))
                user.otp = otp
                user.save()

                return Response({
                    'status': 1,
                    'message': _('OTP sent to your phone number.'),
                    'data': otp,
                }, status=status.HTTP_200_OK)

            return Response({
                'status': 0,
                'message': _('User with this phone number does not exist.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 0,
            'message': _('Invalid data.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

##################################################### Verify OTP API #############################################################################################################
class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            otp = serializer.validated_data['otp']

            user = User.objects.filter(phone=phone).first()

            if user and user.otp == otp:
                return Response({
                    'status': 1,
                    'message': _('OTP verified successfully.'),
                }, status=status.HTTP_200_OK)

            return Response({
                'status': 0,
                'message': _('Invalid OTP.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 0,
            'message': _('Invalid data.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

##################################################### Change Password API #############################################################################################################
class ChangePasswordOtpAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        serializer = ChangePasswordOtpSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            new_password = serializer.validated_data['new_password']

            user = User.objects.filter(phone=phone).first()

            if user:
                user.set_password(new_password)
                user.otp = None
                user.save()

                return Response({
                    'status': 1,
                    'message': _('Password changed successfully.'),
                }, status=status.HTTP_200_OK)

            return Response({
                'status': 0,
                'message': _('User not found.'),
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'status': 0,
            'message': _('Invalid data.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


##################################################### Change Password API #############################################################################################################
class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        # Parse language from the headers
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Extract user from the request
        user = request.user
        
        # Get old and new passwords from request data
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        # Check if the old password is correct
        if not user.check_password(old_password):
            return Response({
                'status': 0,
                'message': _('Old password is incorrect.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate the new password
        if len(new_password) < 8:  # You can set your own validation logic
            return Response({
                'status': 0,
                'message': _('New password must be at least 8 characters long.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Set the new password and save the user
        user.set_password(new_password)
        user.save()

        return Response({
            'status': 1,
            'message': _('Password changed successfully.'),
        }, status=status.HTTP_200_OK)




############################################### Create Profile API ###################################
class UpdateProfilePictureAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user

        # Ensure profile picture is in the request
        if "profile_picture" not in request.FILES:
            return Response({
                'status': 2,
                'message': _('No profile picture provided.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        old_profile_picture = user.profile_picture
        
        # Handle profile picture update
        if "profile_picture" in request.FILES:
            profile_picture = request.FILES["profile_picture"]
            if old_profile_picture and os.path.isfile(os.path.join(settings.MEDIA_ROOT, str(old_profile_picture))):
                os.remove(os.path.join(settings.MEDIA_ROOT, str(old_profile_picture)))

            file_extension = profile_picture.name.split('.')[-1]
            unique_suffix = get_random_string(8)
            file_name = f"profile_pics/{user.id}_{unique_suffix}.{file_extension}"
            path = default_storage.save(file_name, profile_picture)
            user.profile_picture = path
        elif request.data.get("profile_picture") in [None, '']:  # Retain old picture if None/blank
            user.profile_picture = old_profile_picture
        # Save user details
        user.save()

        return Response({
            'status': 1,
            'message': _('Profile Picture updated successfully.'),
            'data': {
                'user':get_user_data(user, request),
                'team':get_team_data(user, request),
                'group':get_group_data(user, request),
                'current_type':user.current_type,
            }
        }, status=status.HTTP_200_OK)

############################################### Edit Profile API ###################################
class EditProfileAPIView(APIView):
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Handle language preference
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get 'created_by_id' from query parameters
        user_id = request.query_params.get('user_id')
        creator_type = request.query_params.get('creator_type')
        created_by_id = request.query_params.get('created_by_id')


        if not user_id:
            return Response({
                'status': 0,
                'message': _('user_id is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the user, return 0 if not found
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('User not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        notification_count = Notifictions.objects.filter(targeted_id=created_by_id, targeted_type=creator_type,read=False).count()


        # Return user details if found
        return Response({
            'status': 1,
            'message': _('Player Details.'),
            'data': {
                'user': get_user_data(user, request),
                'team': get_team_data(user, request),
                'group': get_group_data(user, request),
                'current_type': user.current_type,
            },
            "notification_count": notification_count  # Include notification count here
        }, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        user = request.user

        # Get old profile picture and card header
        old_profile_picture = user.profile_picture
        old_card_header = user.card_header

        # Fields that should be set to NULL if provided as blank or None
        null_fields = ['fullname', 'bio', 'nationality', 'weight', 'height',
                        'favourite_local_team', 'favourite_team',
                       'favourite_local_player', 'favourite_player']

        for field in null_fields:
            field_value = request.data.get(field)
            if field_value is None or field_value == '':
                setattr(user, field, None)  # Set the field to null if blank or None
            else:
                setattr(user, field, field_value)  # Otherwise, update with new value
        
        playing_foot = request.data.get('playing_foot')
        if playing_foot not in [None, '0', '', 'null']:
            try:
                # Convert the playing_foot_value to integer (if it's a string or other type)
                playing_foot_id = int(playing_foot)
                user.playing_foot = PlayingFoot.objects.get(id=playing_foot_id)  # Assign PlayingFoot instance
            except (ValueError, TypeError):
                return Response({
                    'status': 0,
                    'message': _('Invalid playing foot specified.')
                }, status=status.HTTP_400_BAD_REQUEST)
            except PlayingFoot.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('The specified playing foot does not exist.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Handle date_of_birth - retain old value if None or blank
        date_of_birth = request.data.get('date_of_birth')
        if date_of_birth not in [None, '', 'null']:
            try:
                user.date_of_birth = date_of_birth  # Assuming valid format
            except (ValueError, TypeError):
                return Response({
                    'status': 2,
                    'message': _('Invalid date format.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Handle age - retain old value if None or blank
        age = request.data.get('age')
        if age not in [None,'', 'null']:
            user.age = age
        
        # Handle main_playing_position - set to NULL if blank, zero, or 'null' is provided
        main_playing_position_id = request.data.get('main_playing_position')
        if main_playing_position_id in [None, '', '0', 'null']:
            user.main_playing_position = None
        else:
            try:
                user.main_playing_position = PlayingPosition.objects.get(id=main_playing_position_id)
            except PlayingPosition.DoesNotExist:
                return Response({
                    'status': 2,
                    'message': _('Invalid main playing position specified.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Handle secondary_playing_position - set to NULL if blank, zero, or 'null' is provided
        secondary_playing_position_id = request.data.get('secondary_playing_position')
        if secondary_playing_position_id in [None, '', '0', 'null']:
            user.secondary_playing_position = None
        else:
            try:
                user.secondary_playing_position = PlayingPosition.objects.get(id=secondary_playing_position_id)
            except PlayingPosition.DoesNotExist:
                return Response({
                    'status': 2,
                    'message': _('Invalid secondary playing position specified.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Handle gender - retain old value if None or blank
        gender_id = request.data.get('gender')
        if gender_id not in [None, '','0', 'null']:  # Ensure 'null' is also checked
            try:
                user.gender = UserGender.objects.get(id=gender_id)
            except UserGender.DoesNotExist:
                return Response({
                    'status': 2,
                    'message': _('Invalid gender specified.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Handle country - retain old value if None or blank
        country_id = request.data.get('country')
        if country_id not in [None,'0', '', 'null']:
            try:
                user.country = Country.objects.get(id=country_id)
            except Country.DoesNotExist:
                return Response({
                    'status': 2,
                    'message': _('Invalid country specified.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Handle city - retain old value if None or blank
        city_id = request.data.get('city')
        if city_id not in [None,'0', '', 'null']:
            if not user.country:
                return Response({
                    'status': 2,
                    'message': _('City cannot be set without a valid country.')
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                user.city = City.objects.get(id=city_id)
            except City.DoesNotExist:
                return Response({
                    'status': 2,
                    'message': _('Invalid city specified.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Handle profile picture update
        if "profile_picture" in request.FILES:
            profile_picture = request.FILES["profile_picture"]
            if old_profile_picture and os.path.isfile(os.path.join(settings.MEDIA_ROOT, str(old_profile_picture))):
                os.remove(os.path.join(settings.MEDIA_ROOT, str(old_profile_picture)))

            file_extension = profile_picture.name.split('.')[-1]
            unique_suffix = get_random_string(8)
            file_name = f"profile_pics/{user.id}_{unique_suffix}.{file_extension}"            
            path = default_storage.save(file_name, profile_picture)
            user.profile_picture = path
        elif request.data.get("profile_picture") in [None, '']:  # Retain old picture if None/blank
            user.profile_picture = old_profile_picture

        # Handle card header update
        if "cover_photo" in request.FILES:
            card_header = request.FILES["cover_photo"]
            if old_card_header and os.path.isfile(os.path.join(settings.MEDIA_ROOT, str(old_card_header))):
                os.remove(os.path.join(settings.MEDIA_ROOT, str(old_card_header)))

            file_extension = card_header.name.split('.')[-1]
            unique_suffix = get_random_string(8)
            file_name = f"card_header/{user.id}_{unique_suffix}.{file_extension}"
            path = default_storage.save(file_name, card_header)
            user.card_header = path
        elif request.data.get("cover_photo") in [None, '']:  # Retain old header if None/blank
            user.card_header = old_card_header

        # Save user details
        user.save()

        return Response({
            'status': 1,
            'message': _('Profile updated successfully.'),
            'data': {
                'user':get_user_data(user, request),
                'team':get_team_data(user, request),
                'group':get_group_data(user, request),
                'current_type':user.current_type,
            }
        }, status=status.HTTP_200_OK)

####################### POST API ###############################################################################
class CustomPostPagination(PageNumberPagination):
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    page_size = 10  # Number of records per page
    page_query_param = 'page'  # Custom page number param in the body
    page_size_query_param = 'page_size'
    max_page_size = 100  # Set max size if needed

    def paginate_queryset(self, queryset, request, view=None):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Get the page number from the body (default: 1)
        try:
            # Try to fetch and validate the page number
            page_number = request.data.get(self.page_query_param, 1)
            self.page = int(page_number)
            if self.page < 1:
                raise ValidationError(_("Page number must be positive."))
        except (ValueError, TypeError):
            # If the page number is invalid, return a custom error response
            return Response({
                'status': 0,
                'message': _('Page Not Found'),
                'data': []
            }, status=400)

        # Get total number of pages based on the queryset
        paginator = self.django_paginator_class(queryset, self.get_page_size(request))
        total_pages = paginator.num_pages

        # Check if the requested page number is out of range
        if self.page > total_pages:
            # Return custom response for an invalid page
            return Response({
                'status': 0,
                'message': _('Page Not Found'),
                'data': []
            }, status=400)

        # Perform standard pagination if the page is valid
        return super().paginate_queryset(queryset, request, view)

###################################################################################### POST MODULE ################################################################################

###################### POST LIKE ##################################
class PostLikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Set language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get post ID
        post_id = request.data.get('post_id')
        if not post_id:
            return Response({
                'status': 0,
                'message': _('Post ID is required.')
            }, status=400)

        # Validate post existence
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Post not found.')
            }, status=404)

        # Get liker information
        creator_type = request.data.get('creator_type')  # Who liked the post
        created_by_id = request.data.get('created_by_id', request.user.id)  # Default to logged-in user

        # Determine notifier name based on liker type
        if creator_type in [1, "1"]:  # User
            liker = User.objects.get(id=created_by_id)
            notifier_name = liker.username
        elif creator_type in [2, "2"]:  # Team
            liker = Team.objects.get(id=created_by_id)
            notifier_name = liker.team_username
        elif creator_type in [3, "3"]:  # Group
            liker = TrainingGroups.objects.get(id=created_by_id)
            notifier_name = liker.group_username
        else:
            return Response({
                'status': 0,
                'message': _('Invalid creator type.')
            }, status=400)

        # Toggle like/unlike
        post_like, created = PostLike.objects.get_or_create(
            created_by_id=created_by_id, post=post, creator_type=creator_type
        )

        if not created:
            # Unlike the post
            post_like.delete()
            message = _('Post unliked successfully.')
        else:
            # Like the post
            post_like.date_liked = timezone.now()
            post_like.save()
            message = _('Post liked successfully.')

            # Fetch post creator details for notification
            post_creator_type = post.creator_type
            post_created_by_id = post.created_by_id

            if post_creator_type in [1, "1"]:  # User
                recipient = User.objects.get(id=post_created_by_id)
            elif post_creator_type in [2, "2"]:  # Team
                team = Team.objects.get(id=post_created_by_id)
                recipient = team.team_founder
            elif post_creator_type in [3, "3"]:  # Group
                group = TrainingGroups.objects.get(id=post_created_by_id)
                recipient = group.group_founder
            else:
                return Response({
                    'status': 0,
                    'message': _('Invalid creator type for post.')
                }, status=400)

            # Create the notification record with target details
            notification = Notifictions.objects.create(
                created_by_id=created_by_id,  # Who liked the post
                creator_type=creator_type,   # Type of liker
                
                targeted_id=post_created_by_id,  # For whom the notification is created
                targeted_type=post_creator_type,  # Type of post creator
                
                title=_('Post Liked!'),
                content=_('{} liked your post.').format(notifier_name)
            )
            notification.save()

            # Notification settings
            device_token = recipient.device_token
            device_type = recipient.device_type
            notification_language = recipient.current_language

            # Set notification language
            if notification_language in ['ar', 'en']:
                activate(notification_language)

            # Send push notification
            if device_type in [1, 2, "1", "2"]:
                title = _('Post Liked!')
                body = _('{} liked your post.').format(notifier_name)
                push_data = {'type': 'post', 'notifier_id': post_id}
                send_push_notification(device_token, title, body, device_type, data=push_data)

        # Serialize and return post data
        serializer = PostSerializer(post, context={'request': request})
        return Response({
            'status': 1,
            'message': message,
            'data': serializer.data
        }, status=200)


############################# ALL POST LIST VIEW ##########################
class AllPostsListAPIView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = CustomPostPagination

    def get_queryset(self):
        return Post.objects.all().order_by('-date_created')

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        queryset = self.get_queryset()

        page = self.paginate_queryset(queryset)
        if page is None:
            return Response({
                'status': 0,
                'message': _('Page Not Found'),
                'data': []
            }, status=400)

        serializer = self.get_serializer(page, many=True, context={'request': request})
        total_records = queryset.count()
        total_pages = self.paginator.page.paginator.num_pages

        return Response({ 
            'status': 1,
            'message': _('All posts fetched successfully.'),
            'data': serializer.data,
            'total_records': total_records,
            'total_pages': total_pages,
            'current_page': self.paginator.page.number
        }, status=status.HTTP_200_OK)

##########  LIST OF POST BASED ON USER TEAM AND GROUP ################
class PostListAPIView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = CustomPostPagination

    def get_queryset(self):
        # Get created_by_id and creator_type from query_params
        creator_type = self.request.query_params.get('creator_type')
        created_by_id = self.request.query_params.get('created_by_id')

        # Set default values if either parameter is missing
        if not creator_type:
            return Response({
                    'status': 0,
                    'message': _('creator_type is required when creator_type is 2.')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if not created_by_id:
            return Response({
                    'status': 0,
                    'message': _('created_by_id is required when creator_type is 2.')
                }, status=status.HTTP_400_BAD_REQUEST)


        # Check creator_type and adjust the created_by_id accordingly
        if creator_type in [1,"1"]:  # If creator_type is 1, use user_id
            created_by_id = self.request.query_params.get('user_id', self.request.user.id)
        elif creator_type in [2,"2"]:  # If creator_type is 2, use team_id
            created_by_id = self.request.query_params.get('team_id')
            if not created_by_id:
                # Return an error if team_id is missing for creator_type 2
                return Response({
                    'status': 0,
                    'message': _('Team ID is required when creator_type is 2.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Filter posts based on created_by_id and creator_type
        return Post.objects.filter(
            created_by_id=created_by_id,
            creator_type=creator_type
        ).order_by('-date_created')

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        queryset = self.get_queryset()
        
        # Count posts for this created_by_id and creator_type
        post_count = queryset.count()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            total_records = queryset.count()
            total_pages = self.paginator.page.paginator.num_pages

            return Response({
                'status': 1,
                'message': _('Posts fetched successfully.'),
                'data': serializer.data,
                'post_count': post_count,  # Add post_count here
                'total_records': total_records,
                'total_pages': total_pages,
                'current_page': self.paginator.page.number
            }, status=status.HTTP_200_OK)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response({
            'status': 1,
            'message': _('Posts fetched successfully.'),
            'data': serializer.data,
            'post_count': post_count  # Add post_count here
        }, status=status.HTTP_200_OK)

######################## Post Media Delete #######################
class PostMediaDelete(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def delete(self, request, *args, **kwargs):
        media_id = request.query_params.get('media_id')
        if not media_id:
            return Response({
                'status': 0,
                'message': _('Media ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            post_media = PostMedia.objects.get(id=media_id)

            # Delete the file from the file system
            if post_media.file:
                file_path = post_media.file.path
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Delete the PostMedia instance
            post_media.delete()

            return Response({
                'status': 1,
                'message': _('Post Media deleted successfully.')
            }, status=status.HTTP_200_OK)

        except PostMedia.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Post Media not found.')
            }, status=status.HTTP_404_NOT_FOUND)

######################### POST CREATE API ###########################################
class PostCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get created_by_id, creator_type from request data
        created_by_id = request.data.get('created_by_id')
        creator_type = request.data.get('creator_type')

        if not created_by_id or not creator_type:
            return Response({
                'status': 0,
                'message': _('created_by_id and creator_type are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            post = serializer.save(created_by_id=created_by_id, creator_type=creator_type)

            # Handle multiple media files
            media_files = request.FILES.getlist('media_files')  # Expecting multiple files under 'media_files' key

            for media_file in media_files:
                # Determine file extension and media type
                file_extension = media_file.name.split('.')[-1].lower()
                media_type = PostMedia.IMAGE_TYPE if file_extension in ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "svg", "webp", "ico", "heic"] else PostMedia.VIDEO_TYPE

                # Generate unique file name
                unique_suffix = get_random_string(8)
                file_name = f"post_media/{post.id}_{created_by_id}_{creator_type}_{unique_suffix}.{file_extension}"

                # Save the file and create a PostMedia instance
                media_path = default_storage.save(file_name, media_file)
                PostMedia.objects.create(post=post, media_type=media_type, file=media_path)

            # Notify followers
            self.notify_followers(created_by_id, creator_type, post)

            post.refresh_from_db()

            return Response({
                'status': 1,
                'message': _('Post created successfully'),
                'data': PostSerializer(post).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 0,
            'message': _('Invalid data'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def notify_followers(self, created_by_id, creator_type, post):
        """
        Notify followers and create a notification record when a post is created.
        """
        # Fetch followers based on FollowRequest
        followers = FollowRequest.objects.filter(
            Q(target_id=created_by_id, target_type=creator_type)
        )

        # Retrieve creator name based on creator_type
        creator_name = None
        if creator_type in [1, "1"]:  # For individual user posts
            creator_name = User.objects.filter(id=created_by_id).values_list('username', flat=True).first()
        elif creator_type in [2, "2"]:  # For team posts
            creator_name = Team.objects.get(id=created_by_id).team_username
        elif creator_type in [3, "3"]:  # For group posts
            creator_name = TrainingGroups.objects.get(id=created_by_id).group_name

        # Notify followers
        for follower in followers:
            title = _('New Post Alert!')
            body = _('{} just added a new post.').format(creator_name)

            # Set notification target details
            targeted_id = follower.created_by_id  # Follower ID
            targeted_type = follower.creator_type  # Follower type (User, Team, Group)

            # Check follower type and send notification
            if targeted_type == 1:  # User
                follower_user = User.objects.get(id=targeted_id)

                # Set notification language based on the follower's preference
                notification_language = follower_user.current_language
                if notification_language in ['ar', 'en']:
                    activate(notification_language)

                # Send push notification
                push_data = {
                    'type': 'post',
                    'notifier_id': post.id
                }
                send_push_notification(
                    follower_user.device_token,
                    title,
                    body,
                    follower_user.device_type,
                    data=push_data
                )

                # **CREATE NOTIFICATION RECORD**
                Notifictions.objects.create(
                    created_by_id=created_by_id,  # Post creator
                    creator_type=creator_type,   # Creator type

                    targeted_id=targeted_id,     # Targeted follower
                    targeted_type=targeted_type, # Follower type

                    title=title,
                    content=body
                )

            elif targeted_type == 2:  # Team
                team = Team.objects.get(id=targeted_id)

                # Notify team founder
                send_push_notification(
                    team.team_founder.device_token,
                    title,
                    body,
                    team.team_founder.device_type,
                    data={'type': 'post', 'notifier_id': post.id}
                )

                # **CREATE NOTIFICATION RECORD**
                Notifictions.objects.create(
                    created_by_id=created_by_id,
                    creator_type=creator_type,

                    targeted_id=targeted_id,
                    targeted_type=targeted_type,

                    title=title,
                    content=body
                )

            elif targeted_type == 3:  # Group
                group = TrainingGroups.objects.get(id=targeted_id)

                # Notify group founder
                send_push_notification(
                    group.group_founder.device_token,
                    title,
                    body,
                    group.group_founder.device_type,
                    data={'type': 'post', 'notifier_id': post.id}
                )

                # **CREATE NOTIFICATION RECORD**
                Notifictions.objects.create(
                    created_by_id=created_by_id,
                    creator_type=creator_type,

                    targeted_id=targeted_id,
                    targeted_type=targeted_type,

                    title=title,
                    content=body
                )

##########################   EDIT POST API ##################################
class PostEditAPIView(generics.GenericAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
        # Get created_by_id and creator_type from request data
        created_by_id = self.request.data.get('created_by_id')
        creator_type = self.request.data.get('creator_type')

        # Ensure both parameters are provided and valid
        if not created_by_id or not creator_type:
            return Post.objects.none()

        return Post.objects.filter(created_by_id=created_by_id, creator_type=creator_type)

    def get_object(self, post_id):
        return get_object_or_404(self.get_queryset(), id=post_id)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        post_id = request.data.get('post_id')
        if not post_id:
            return Response({
                'status': 0,
                'message': _('Post ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        post = self.get_object(post_id)
        serializer = self.get_serializer(post)

        return Response({
            'status': 1,
            'message': _('Post fetched successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        created_by_id = request.data.get('created_by_id')
        creator_type = request.data.get('creator_type')
        post_id = request.data.get('post_id')

        if not post_id:
            return Response({
                'status': 0,
                'message': _('Post ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        post = self.get_object(post_id)
        serializer = self.get_serializer(post, data=request.data, partial=True)

        if serializer.is_valid():
            # Update the post details
            post = serializer.save()

            # Handle media file updates
            media_files = request.FILES.getlist('media_files')  # Accept multiple media files
            if media_files:
                for media_file in media_files:
                    # Determine file extension and media type
                    file_extension = media_file.name.split('.')[-1].lower()
                    media_type = (
                        PostMedia.IMAGE_TYPE 
                        if file_extension in ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "svg", "webp", "ico", "heic"]
                        else PostMedia.VIDEO_TYPE
                    )

                    # Generate unique file name
                    unique_suffix = get_random_string(8)
                    file_name = f"post_media/{post.id}_{created_by_id}_{creator_type}_{unique_suffix}.{file_extension}"

                    # Save the file and create a PostMedia instance
                    media_path = default_storage.save(file_name, media_file)
                    PostMedia.objects.create(post=post, media_type=media_type, file=media_path)

            # Refresh the post object with updated related data
            post.refresh_from_db()

            return Response({
                'status': 1,
                'message': _('Post updated successfully.'),
                'data': PostSerializer(post).data
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 0,
            'message': _('Failed to update the post.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


####################### POST DETAIL API ############################
class PostDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        # Activate the language based on the request headers
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get the data from the request
        post_id = request.data.get('post_id')

        # Validate the presence of post_id
        if not post_id:
            return Response({
                'status': 0,
                'message': _('Post ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Post not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Track the post view
        creator_type = request.data.get('creator_type')
        created_by_id = request.data.get('created_by_id')  # Default to logged-in user ID

        PostView.objects.get_or_create(created_by_id=created_by_id, post=post, creator_type=creator_type)

        # Retrieve the view count for the post
        view_count = PostView.objects.filter(post=post).count()

        # Serialize the post details with the paginated comments
        serializer = PostSerializer(post, context={'request': request})

        # Return the combined response with both post details and view count
        return Response({
            'status': 1,
            'message': _('Post details fetched successfully.'),
            'data': {
                **serializer.data,
                'view_count': view_count,  # Include view count in response
            },
        }, status=status.HTTP_200_OK)



################################ Get comment API #############################
class PostCommentPagination(CustomPostPagination):
    def paginate_queryset(self, queryset, request, view=None):
        return super().paginate_queryset(queryset, request, view)

class PostCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Validate post_id from request data
        post_id = request.data.get('post_id')
        if not post_id:
            return Response({
                'status': 0,
                'message': _('Post ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Post not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Get only top-level comments (parent=None) for the post
        top_level_comments = Post_comment.objects.filter(post=post, parent=None).order_by('-date_created')

        # Paginate the comments
        paginator = PostCommentPagination()
        paginated_comments = paginator.paginate_queryset(top_level_comments, request)

        # If pagination fails or no comments are found
        if paginated_comments is None:
            return Response({
                'status': 1,
                'message': _('No comments found for this post.'),
                'data': {
                    'total_records': 0,
                    'total_pages': 0,
                    'current_page': 1,
                    'results': []
                }
            }, status=status.HTTP_200_OK)

        # Serialize the paginated comments
        serializer = PostCommentSerializer(paginated_comments, many=True, context={'request': request})

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
class CommentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        # Set language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract input data
        data = request.data
        post_id = data.get('post_id')
        comment_text = data.get('comment')
        parent_id = data.get('parent_id')
        creator_type = data.get('creator_type')  # Can be 1 (User), 2 (Team), 3 (Group)
        created_by_id = data.get('created_by_id', request.user.id)  # Default to user ID if not provided

        # Validate required fields
        if not post_id or not comment_text:
            return Response({
                'status': 0,
                'message': _('post_id and comment are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate post existence
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Post not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate parent comment if provided
        parent_comment = None
        if parent_id:
            try:
                parent_comment = Post_comment.objects.get(id=parent_id)
            except Post_comment.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Parent comment not found.')
                }, status=status.HTTP_404_NOT_FOUND)

        # Determine notifier name based on creator type
        if creator_type in [1, "1"]:  # User
            commenter = User.objects.get(id=created_by_id)
            notifier_name = commenter.username
        elif creator_type in [2, "2"]:  # Team
            commenter = Team.objects.get(id=created_by_id)
            notifier_name = commenter.team_username
        elif creator_type in [3, "3"]:  # Group
            commenter = TrainingGroups.objects.get(id=created_by_id)
            notifier_name = commenter.group_username
        else:
            return Response({
                'status': 0,
                'message': _('Invalid creator type.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create the comment
        comment = Post_comment.objects.create(
            created_by_id=created_by_id,
            creator_type=creator_type,
            post=post,
            comment=comment_text,
            parent=parent_comment
        )

        # Determine notification recipient based on comment/reply case
        if parent_comment:
            # Notify parent comment creator (reply case)
            recipient_id = parent_comment.created_by_id
            recipient_type = parent_comment.creator_type
        else:
            # Notify post creator (new comment case)
            recipient_id = post.created_by_id
            recipient_type = post.creator_type

        # Fetch recipient details
        if recipient_type in [1, "1"]:  # User
            recipient = User.objects.get(id=recipient_id)
            device_token = recipient.device_token
            device_type = recipient.device_type
            notification_language = recipient.current_language
        elif recipient_type in [2, "2"]:  # Team
            recipient = Team.objects.get(id=recipient_id)
            user = recipient.team_founder
            device_token = user.device_token
            device_type = user.device_type
            notification_language = user.current_language
        elif recipient_type in [3, "3"]:  # Group
            recipient = TrainingGroups.objects.get(id=recipient_id)
            user = recipient.group_founder
            device_token = user.device_token
            device_type = user.device_type
            notification_language = user.current_language
        else:
            return Response({
                'status': 0,
                'message': _('Invalid creator type for recipient.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Set notification language
        if notification_language in ['ar', 'en']:
            activate(notification_language)

        # Create notification content
        if parent_comment:
            title = _('Someone replied to your comment')
            body = _('{} replied to your comment.').format(notifier_name)
            push_data = {'type': 'post', 'notifier_id': post_id}
        else:
            title = _('Someone commented on your post')
            body = _('{} commented on your Post.').format(notifier_name)
            push_data = {'type': 'post', 'notifier_id': post_id}

        # **Create Notification Record with Targeted ID and Type**
        notification = Notifictions.objects.create(
            created_by_id=created_by_id,      # Comment creator
            creator_type=creator_type,       # Creator type

            targeted_id=recipient_id,        # Recipient ID
            targeted_type=recipient_type,    # Recipient type

            title=title,
            content=body
        )
        notification.save()

        # **Send Push Notification**
        if device_type in [1, 2, "1", "2"]:
            send_push_notification(device_token, title, body, device_type, data=push_data)

        # **Return response**
        return Response({
            'status': 1,
            'message': _('Comment created successfully.'),
            'data': PostCommentSerializer(comment).data
        }, status=status.HTTP_201_CREATED)


############### POST DELETE API ##############################
class PostDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def delete(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        post_id = request.query_params.get('post_id')
        created_by_id = request.query_params.get('created_by_id')
        creator_type = request.query_params.get('creator_type')

        if not post_id or not created_by_id or not creator_type:
            return Response({
                'status': 0,
                'message': _('post_id, created_by_id, and creator_type are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            post = Post.objects.get(id=post_id, created_by_id=created_by_id, creator_type=creator_type)
            post.delete()
            return Response({
                'status': 1,
                'message': _('Post deleted successfully.')
            }, status=status.HTTP_200_OK)

        except Post.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Post not found.')
            }, status=status.HTTP_404_NOT_FOUND)


################################################################# CREATE NEW PROFILE API #########################################################################################

class ProfileTypeView(APIView):
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    @staticmethod
    def coach_directory_path(instance, filename):
        return f'certificates/coach/{instance.id}/{filename}'

    @staticmethod
    def referee_directory_path(instance, filename):
        return f'certificates/referee/{instance.id}/{filename}'

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Assuming the user is already authenticated and you have access to the user object
        user = request.user

        # Check if the user is already a coach or referee
        if user.is_coach:
            return Response({
                'status': 0,
                'message': _('You are already registered as a coach and cannot create a new coach profile.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if user.is_referee:
            return Response({
                'status': 0,
                'message': _('You are already registered as a referee and cannot create a new referee profile.')
            }, status=status.HTTP_400_BAD_REQUEST)
        # Get user roles with specific IDs
        user_roles = Role.objects.filter(id__in=[3, 4])  # Filter for roles with IDs 3, 4, or 6
        serializer = UserRoleSerializer(user_roles, many=True)

        # Prepare the response with roles directly under 'data'
        return Response({
            'status': 1,
            'message': _('User Profiles retrieved successfully.'),
            'data': serializer.data  # Directly include the serialized data
        }, status=status.HTTP_200_OK)
        
    def post(self, request):
        # Set language based on headers, default to English
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        if request.user.role.id != 5:
            return Response({
                'status': 0,
                'message': _('You do not have permission to perform this action.'),
            }, status=status.HTTP_403_FORBIDDEN)

        # Extract profile type and certificates from request
        profile_type = request.data.get('profile_type')
        certificates = request.FILES.getlist('certificates')  # Uploaded files
        user = request.user  # Assuming user is authenticated

        if user.is_coach:
            return Response({
                'status': 0,
                'message': _('You are already registered as a coach and cannot create a new coach profile.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if user.is_referee:
            return Response({
                'status': 0,
                'message': _('You are already registered as a referee and cannot create a new referee profile.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate profile type
        if profile_type not in ['3', '4']:
            return Response({
                'status': 0,
                'message': _('Invalid profile type.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check existing roles
        if user.is_coach and profile_type == '3':
            return Response({
                'status': 0,
                'message': _('You are already registered as a coach and cannot create a new coach profile.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        if user.is_referee and profile_type == '4':
            return Response({
                'status': 0,
                'message': _('You are already registered as a referee and cannot create a new referee profile.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Determine directory and profile type settings
        if profile_type == '3':  # Profile type for coach
            user.is_coach = True
            user.is_referee = False
            directory = 'coach_certificates'
            certificate_type = CertificateType.COACH
        elif profile_type == '4':  # Profile type for referee
            user.is_referee = True
            user.is_coach = False
            directory = 'referee_certificates'
            certificate_type = CertificateType.REFEREE

        # Save certificates with their original file names and extensions
        for cert in certificates:
            # Extract file extension
            file_extension = os.path.splitext(cert.name)[-1].lower()  # Get the file extension

            # Generate a unique 10-character string directly in the loop
            unique_str = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

            # Create a unique file name using the original name and the unique string
            file_name = f"{directory}/{request.user.role.id}/{unique_str}{file_extension}"  # Append unique string to the file name
            file_path = default_storage.save(file_name, cert)

            # Save the full file path (including the extension) in the database
            UserCertificate.objects.create(
                user=user,
                certificate_type=certificate_type,
                certificate_file=file_path,  # Store the full path (name + extension)
            )


        # Update user's profile and save changes
        user.updated_at = timezone.now()
        user.save()

        # Return success response
        return Response({
            'status': 1,
            'message': _('Profile type and certificates uploaded successfully.'),
            'data': {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'is_coach': user.is_coach,
                'is_referee': user.is_referee,
            }
        }, status=status.HTTP_201_CREATED)

################################ album and gallary ######################################################################################################################
class CustomMediaPagination(PageNumberPagination):
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    page_size = 30  # Number of records per page 
    page_query_param = 'page'  # Custom page number param in the body
    page_size_query_param = 'page_size'
    max_page_size = 100  # Set max size if needed

    def paginate_queryset(self, queryset, request, view=None):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Get the page number from the body (default: 1)
        try:
            # Try to fetch and validate the page number
            page_number = request.data.get(self.page_query_param, 1)
            self.page = int(page_number)
            if self.page < 1:
                raise ValidationError(_("Page number must be positive."))
        except (ValueError, TypeError):
            # If the page number is invalid, return a custom error response
            return Response({
                'status': 0,
                'message': _('Page Not Found'),
                'data': []
            }, status=400)

        # Get total number of pages based on the queryset
        paginator = self.django_paginator_class(queryset, self.get_page_size(request))
        total_pages = paginator.num_pages

        # Check if the requested page number is out of range
        if self.page > total_pages:
            # Return custom response for an invalid page
            return Response({
                'status': 0,
                'message': _('Page Not Found'),
                'data': []
            }, status=400)

        # Perform standard pagination if the page is valid
        return super().paginate_queryset(queryset, request, view)

        
###########detail album with id ################
class DetailAlbumListAPIView(generics.ListAPIView):
    serializer_class = DetailAlbumSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    pagination_class = CustomMediaPagination

    def get_queryset(self):
        album_id = self.request.data.get('album_id')
        if album_id:
            return Album.objects.filter(id=album_id)
        return Album.objects.none()

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({
                'status': 0,
                'message': _('Album Id is required or Album not found.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        album = queryset.first()
        gallary_items_queryset = Gallary.objects.filter(album=album).order_by('-created_at')
        
        page = self.paginate_queryset(gallary_items_queryset)
        if page is not None:
            gallary_items_serializer = GallarySerializer(page, many=True)
            total_records = gallary_items_queryset.count()
            total_pages = self.paginator.page.paginator.num_pages

            return Response({
                'status': 1,
                'message': _('Album Details fetched successfully.'),
                'data': gallary_items_serializer.data,
                'total_records': total_records,
                'total_pages': total_pages,
                'current_page': self.paginator.page.number
            }, status=status.HTTP_200_OK)

        # Return unpaginated data if pagination is not applied
        gallary_items_serializer = GallarySerializer(gallary_items_queryset, many=True)
        return Response({
            'status': 1,
            'message': _('Album Details fetched successfully.'),
            'data': gallary_items_serializer.data,
            'total_records': gallary_items_queryset.count()
        }, status=status.HTTP_200_OK)


################## Create Album API ##################        
class DetailAlbumCreateAPIView(generics.CreateAPIView):
    serializer_class = DetailAlbumSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract and process creator_type and created_by_id
        creator_type = request.data.get('creator_type')
        created_by_id = request.data.get('created_by_id')

        # Check if creator_type is provided
        if not creator_type:
            return Response({
                'status': 0,
                'message': _('creator_type is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convert creator_type to int and strip created_by_id if provided
        try:
            creator_type = int(creator_type.strip())
            created_by_id = int(created_by_id.strip()) if created_by_id else None
        except (ValueError, TypeError):
            return Response({
                'status': 0,
                'message': _('creator_type and created_by_id must be valid integers.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate created_by_id based on creator_type
        if creator_type == Album.USER_TYPE:
            created_by_id = request.user.id  # Set created_by_id to logged-in user's ID
        elif creator_type == Album.TEAM_TYPE:
            if not Team.objects.filter(id=created_by_id).exists():
                return Response({
                    'status': 0,
                    'message': _('For TEAM_TYPE, created_by_id must correspond to an existing Team.')
                }, status=status.HTTP_400_BAD_REQUEST)
        elif creator_type == Album.GROUP_TYPE:
            if not TrainingGroups.objects.filter(id=created_by_id).exists():
                return Response({
                    'status': 0,
                    'message': _('For GROUP_TYPE, created_by_id must correspond to an existing Group.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Proceed with serializer validation
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            album_instance = serializer.save(creator_type=creator_type, created_by_id=created_by_id)

            media_files = request.FILES.getlist('media_file')
            gallery_items = []

            if media_files:
                for media_file in media_files:
                    gallary_data = {
                        'creator_type': creator_type,
                        'created_by_id': created_by_id,
                        'media_file': media_file,
                        'album': album_instance.id,
                        'content_type': request.data.get('content_type'),
                    }
                    gallary_serializer = GallarySerializer(data=gallary_data)
                    if gallary_serializer.is_valid():
                        gallery_item = gallary_serializer.save()
                        gallery_items.append(gallery_item)
                    else:
                        album_instance.delete()  # Clean up the album if any media fails
                        return Response({
                            'status': 0,
                            'message':_('Gallery entry creation failed.'),
                            'errors': gallary_serializer.errors
                        }, status=status.HTTP_400_BAD_REQUEST)

            album_data = DetailAlbumSerializer(album_instance).data
            return Response({
                'status': 1,
                'message': _('Detailed Albums added successfully.'),
                'data': [album_data]
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 0,
            'message': _('Album creation failed.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


########### only album list ################
class AlbumListAPIView(generics.ListAPIView):
    serializer_class = AlbumSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = CustomMediaPagination 

    def get_queryset(self):
        language = self.request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        creator_type = self.request.query_params.get('creator_type', None)
        created_by_id = self.request.query_params.get('created_by_id', None)

        queryset = Album.objects.all().order_by('-created_at')

        # Validate creator_type and created_by_id
        if creator_type is not None:
            try:
                creator_type = int(creator_type)
                if creator_type not in [Album.USER_TYPE, Album.TEAM_TYPE, Album.GROUP_TYPE]:
                    raise ValueError(_("Invalid creator_type."))
            except (ValueError, TypeError):
                raise Exception(_("creator_type must be a valid integer."))
            
            queryset = queryset.filter(creator_type=creator_type)

        if created_by_id is not None:
            try:
                created_by_id = int(created_by_id)
                if creator_type == Album.TEAM_TYPE:
                    if not Team.objects.filter(id=created_by_id).exists():
                        raise Exception(_("For TEAM_TYPE, created_by_id must correspond to an existing Team."))
                elif creator_type == Album.GROUP_TYPE:
                    if not TrainingGroups.objects.filter(id=created_by_id).exists():
                        raise Exception(_("For GROUP_TYPE, created_by_id must correspond to an existing Group."))
                # For USER_TYPE, you can check if created_by_id is the logged-in user
                elif creator_type == Album.USER_TYPE and created_by_id != self.request.user.id:
                    raise Exception(_("For USER_TYPE, created_by_id must match the logged-in user."))
            except (ValueError, TypeError):
                raise Exception(_("created_by_id must be a valid integer."))

            queryset = queryset.filter(created_by_id=created_by_id)

        return queryset.order_by('-created_at')

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        try:
            queryset = self.get_queryset()
        except Exception as e:
            return Response({
                'status': 0,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        page = self.paginate_queryset(queryset) 
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            total_records = queryset.count()
            total_pages = self.paginator.page.paginator.num_pages

            return Response({
                'status': 1,
                'message': _('Albums fetched successfully.'),
                'data': [
                    {
                        **album_data,
                        # 'user': request.user.id,
                        # 'team_id': album_data['created_by_id'] if album_data['creator_type'] == Album.TEAM_TYPE else None,
                        # 'group_id': album_data['created_by_id'] if album_data['creator_type'] == Album.GROUP_TYPE else None,
                    }
                    for album_data in serializer.data
                ],
                'total_records': total_records,
                'total_pages': total_pages,
                'current_page': self.paginator.page.number
            }, status=status.HTTP_200_OK)

        albums = self.get_queryset()
        serializer = self.get_serializer(albums, many=True)

        return Response({
            'status': 1,
            'message': _('Album entries fetched successfully.'),
            'data': [
                {
                    **album_data,
                    # 'user': request.user.id,
                    # 'team_id': album_data['created_by_id'] if album_data['creator_type'] == Album.TEAM_TYPE else None,
                    # 'group_id': album_data['created_by_id'] if album_data['creator_type'] == Album.GROUP_TYPE else None,
                }
                for album_data in serializer.data
            ]
        }, status=status.HTTP_200_OK)
###########detail gallary with id with diffrentiatee ################
class ImageGallaryListAPIView(generics.ListAPIView):
    serializer_class = GetGallarySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = CustomMediaPagination

    def get_queryset(self):
        language = self.request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        content_type = self.request.query_params.get('content_type', 1)  # Default to images if not specified

        # Base queryset for images with album_id as null and content_type for images
        queryset = Gallary.objects.filter(album_id__isnull=True, content_type=content_type)

        # Get query parameters for filtering
        creator_type = self.request.query_params.get('creator_type', None)
        created_by_id = self.request.query_params.get('created_by_id', None)

        # Filter the queryset based on creator_type and created_by_id
        if created_by_id is not None:
            queryset = queryset.filter(created_by_id=created_by_id)

        if creator_type is not None:
            queryset = queryset.filter(creator_type=creator_type)

        return queryset.order_by('-created_at')

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            total_pages = self.paginator.page.paginator.num_pages
            current_page = self.paginator.page.number
        else:
            serializer = self.get_serializer(queryset, many=True)
            total_pages = 1
            current_page = 1

        # Modify the response to include user, team_id, and group_id
        response_data = []
        for gallary_data in serializer.data:
            response_data.append({
                **gallary_data,
                # 'user': request.user.id,
                # 'team_id': gallary_data['created_by_id'] if gallary_data['creator_type'] == Gallary.TEAM_TYPE else None,
                # 'group_id': gallary_data['created_by_id'] if gallary_data['creator_type'] == Gallary.GROUP_TYPE else None,
            })

        return Response({
            'status': 1,
            'message': _('Image gallary entries fetched successfully.'),
            'data': response_data,
            'total_records': queryset.count(),
            'total_pages': total_pages,
            'current_page': current_page
        }, status=status.HTTP_200_OK)


class VideoGallaryListAPIView(generics.ListAPIView):
    serializer_class = GetGallarySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = CustomMediaPagination

    def get_queryset(self):
        language = self.request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        content_type = self.request.query_params.get('content_type', 2)  # Default to videos if not specified
        
        # Base queryset for videos with album_id as null and content_type=2 for videos
        queryset = Gallary.objects.filter(album_id__isnull=True, content_type=content_type)

        # Get query parameters for filtering
        creator_type = self.request.query_params.get('creator_type', None)
        created_by_id = self.request.query_params.get('created_by_id', None)

        # Filter the queryset based on creator_type and created_by_id
        if created_by_id is not None:
            queryset = queryset.filter(created_by_id=created_by_id)

        if creator_type is not None:
            queryset = queryset.filter(creator_type=creator_type)

        return queryset.order_by('-created_at')

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            total_pages = self.paginator.page.paginator.num_pages
            current_page = self.paginator.page.number
        else:
            serializer = self.get_serializer(queryset, many=True)
            total_pages = 1
            current_page = 1

        # Modify the response to include user, team_id, and group_id
        response_data = []
        for gallary_data in serializer.data:
            response_data.append({
                'id': gallary_data.get('id'),
                'album': gallary_data.get('album'),
                'content_type': gallary_data.get('content_type'),
                'media_file': gallary_data.get('media_file'),
                'created_at': gallary_data.get('created_at'),
                'updated_at': gallary_data.get('updated_at'),
                # 'user': request.user.id,
                # 'team_id': gallary_data['created_by_id'] if gallary_data['creator_type'] == Gallary.TEAM_TYPE else None,
                # 'group_id': gallary_data['created_by_id'] if gallary_data['creator_type'] == Gallary.GROUP_TYPE else None,
                'creator_type': gallary_data.get('creator_type'),  # Add creator_type
                'created_by_id': gallary_data.get('created_by_id')  # Add created_by_id
            })

        return Response({
            'status': 1,
            'message': _('Video gallary entries fetched successfully.'),
            'data': response_data,
            'total_records': queryset.count(),
            'total_pages': total_pages,
            'current_page': current_page
        }, status=status.HTTP_200_OK)


###############create gallary###################
class GallaryCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get album_id, creator_type, and created_by_id from request data
        album_id = request.data.get('album_id')
        created_by_id = request.data.get('created_by_id', request.user.id)
        creator_type = request.data.get('creator_type')
        if album_id in [None, '0', '']:
            album_id = None
        if not creator_type:
            return Response({
                'status': 0,
                'message': _('creator_type is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = GetGallarySerializer(data=request.data)
        if serializer.is_valid():
            # Validate the creator_type
            creator_type = int(creator_type)
            if creator_type not in [Gallary.USER_TYPE, Gallary.TEAM_TYPE, Gallary.GROUP_TYPE]:
                return Response({
                    'status': 0,
                    'message': _('Invalid creator type.'),
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check permissions based on creator type
            if creator_type == Gallary.TEAM_TYPE:
                if not Team.objects.filter(id=created_by_id).exists():
                    return Response({
                        'status': 0,
                        'message': _('Invalid team ID.'),
                    }, status=status.HTTP_400_BAD_REQUEST)

            elif creator_type == Gallary.GROUP_TYPE:
                if not TrainingGroups.objects.filter(id=created_by_id).exists():
                    return Response({
                        'status': 0,
                        'message': _('Invalid group ID.'),
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Fetch album instance if album_id is provided
            album_instance = None
            if album_id:
                try:
                    album_instance = Album.objects.get(id=album_id)
                except Album.DoesNotExist:
                    return Response({
                        'status': 0,
                        'message': _('Album not found.'),
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Handle the media_file if it is provided
            if "media_file" in request.FILES:
                image = request.FILES["media_file"]
                file_extension = image.name.split('.')[-1]
                unique_suffix = get_random_string(8)
                file_name = f"media_file/{creator_type}_{created_by_id}_{unique_suffix}.{file_extension}"
                logo = default_storage.save(file_name, image)
                serializer.validated_data["media_file"] = logo  # Save the file path in the serializer

            # Save the gallery entry
            gallary = serializer.save(
                created_by_id=created_by_id,
                creator_type=creator_type,
                album_id=album_instance.id if album_instance else None  # Pass the ID or None
            )

            return Response({
                'status': 1,
                'message': _('Gallery entry created successfully.'),
                'data': GetGallarySerializer(gallary).data,
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 0,
            'message': _('Failed to create gallery entry.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

###########gallary list latest 9 ################

class LatestGallaryListAPIView(generics.ListCreateAPIView):
    serializer_class = GetGallarySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
        language = self.request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        creator_type = self.request.query_params.get('creator_type')
        created_by_id = self.request.query_params.get('created_by_id', self.request.user.id)

        queryset = Gallary.objects.filter(album_id__isnull=True).order_by('-created_at')
        if creator_type == str(Gallary.TEAM_TYPE):
            queryset = queryset.filter(creator_type=Gallary.TEAM_TYPE, created_by_id=created_by_id)
        elif creator_type == str(Gallary.GROUP_TYPE):
            queryset = queryset.filter(creator_type=Gallary.GROUP_TYPE, created_by_id=created_by_id)
        elif creator_type == str(Gallary.USER_TYPE):
            queryset = queryset.filter(creator_type=Gallary.USER_TYPE, created_by_id=created_by_id)
        else:
            queryset = queryset.filter(created_by_id=self.request.user.id)

        return queryset

    def get_latest_albums(self):

        creator_type = self.request.query_params.get('creator_type')
        created_by_id = self.request.query_params.get('created_by_id', self.request.user.id)

        queryset = Album.objects.all().order_by('-created_at')
        if creator_type == str(Gallary.TEAM_TYPE):
            queryset = queryset.filter(creator_type=Gallary.TEAM_TYPE, created_by_id=created_by_id)
        elif creator_type == str(Gallary.GROUP_TYPE):
            queryset = queryset.filter(creator_type=Gallary.GROUP_TYPE, created_by_id=created_by_id)
        elif creator_type == str(Gallary.USER_TYPE):
            queryset = queryset.filter(creator_type=Gallary.USER_TYPE, created_by_id=created_by_id)
        else:
            queryset = queryset.filter(creator_type=Gallary.USER_TYPE, created_by_id=self.request.user.id)

        return queryset

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        queryset = self.get_queryset()
        images = queryset.filter(content_type=1)[:9]
        videos = queryset.filter(content_type=2)[:9]

        # Serialize images and videos
        image_serializer = self.get_serializer(images, many=True)
        video_serializer = self.get_serializer(videos, many=True)

        # Fetch and serialize the latest 9 albums
        latest_albums = self.get_latest_albums()[:9]
        album_serializer = AlbumSerializer(latest_albums, many=True)

        # Retrieve creator type from the request data
        creator_type = request.query_params.get('creator_type')

        # Format images, videos, and albums response data with specific fields
        def format_response_data(gallary_data):
            return {
                'id': gallary_data.get('id'),
                'album': gallary_data.get('album'),
                'content_type': gallary_data.get('content_type'),
                'media_file': gallary_data.get('media_file'),
                'created_at': gallary_data.get('created_at'),
                'updated_at': gallary_data.get('updated_at'),
                'creator_type': gallary_data.get('creator_type'),  # Include creator_type
                'created_by_id': gallary_data.get('created_by_id')
            }

        # Apply formatting based on creator type to each image, video, and album entry
        formatted_images = [
            format_response_data(data) for data in image_serializer.data
            if (creator_type == str(Gallary.TEAM_TYPE) and data['creator_type'] == Gallary.TEAM_TYPE) or
               (creator_type == str(Gallary.GROUP_TYPE) and data['creator_type'] == Gallary.GROUP_TYPE) or
               (creator_type == str(Gallary.USER_TYPE) and data['creator_type'] == Gallary.USER_TYPE)
        ]
        formatted_videos = [
            format_response_data(data) for data in video_serializer.data
            if (creator_type == str(Gallary.TEAM_TYPE) and data['creator_type'] == Gallary.TEAM_TYPE) or
               (creator_type == str(Gallary.GROUP_TYPE) and data['creator_type'] == Gallary.GROUP_TYPE) or
               (creator_type == str(Gallary.USER_TYPE) and data['creator_type'] == Gallary.USER_TYPE)
        ]
        formatted_albums = [
            {
                'id': album.get('id'),
                'name': album.get('name'),
                'thumbnail': album.get('thumbnail'),
                'creator_type': album.get('creator_type'),  # Use album object here
                'created_by_id': album.get('created_by_id'),
                'created_at': album.get('created_at'),
                'updated_at': album.get('updated_at'),
            }
            for album in album_serializer.data
            if (creator_type == str(Album.TEAM_TYPE) and album['creator_type'] == Album.TEAM_TYPE) or
               (creator_type == str(Album.GROUP_TYPE) and album['creator_type'] == Album.GROUP_TYPE) or
               (creator_type == str(Album.USER_TYPE) and album['creator_type'] == Album.USER_TYPE)
        ]

        return Response({
            'status': 1,
            'message': _('gallery entries and latest albums fetched successfully.'),
            'data': {
                'images': formatted_images,
                'videos': formatted_videos,
                'albums': formatted_albums,
            },
        }, status=status.HTTP_200_OK)


###########  gallary list delete ################


class GallaryDeleteAPIView(generics.DestroyAPIView):
    queryset = Gallary.objects.all().order_by('-created_at')
    serializer_class = GallarySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_object(self):
        language = self.request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Fetch the 'id' from the request body
        id = self.request.query_params.get('gallary_id')
        if not id:
                return Response({
                'status': 0,
                'message': _({"gallary_id": _("This field is required.")}),
            }, status=status.HTTP_400_BAD_REQUEST)
                

        
        try:
            return Gallary.objects.get(id=id)
        except Gallary.DoesNotExist:
            raise ({"message": _("gallery entry not found.")})

    def delete(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        try:
            # Retrieve the Gallary object by ID from the body
            gallary_instance = self.get_object()

            # Optionally delete the media file from storage if needed
            if gallary_instance.media_file:
                gallary_instance.media_file.delete(save=False)  # Deletes the file from storage
            
            # Perform the deletion
            gallary_instance.delete()

            return Response({
                'status': 1,
                'message': _('gallery entry deleted successfully.')
            }, status=status.HTTP_200_OK)

        except Gallary.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('gallery entry not found.')
            }, status=status.HTTP_404_NOT_FOUND)
        
###########  album list delete ################

class AlbumDeleteAPIView(generics.DestroyAPIView):
    queryset = Album.objects.all().order_by('-created_at')
    serializer_class = AlbumSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    permission_classes = [IsAuthenticated]

    def get_object(self):
        language = self.request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Fetch the 'id' from the request body
        id = self.request.query_params.get('album_id')
        if not id:
                return Response({
                'status': 0,
                'message': _({"album_id": _("This field is required.")}),
            }, status=status.HTTP_400_BAD_REQUEST)
                

          
        try:
            return Album.objects.get(id=id)
        except Album.DoesNotExist:
            raise ({"message": _("Album not found.")})

    def delete(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        try:
            # Retrieve the Album object by ID from the body
            album_instance = self.get_object()

            # Perform the deletion
            album_instance.delete()

            return Response({
                'status': 1,
                'message': _('Album deleted successfully.')
            }, status=status.HTTP_200_OK)

        except Album.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Album not found.')
            }, status=status.HTTP_404_NOT_FOUND)

########################################################################  Sponsor API ################################################################
class SponsorAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        creator_type = request.query_params.get('creator_type')
        created_by_id = request.query_params.get('created_by_id')

        if not creator_type or not created_by_id:
            return Response({
                "status": 0,
                "message": _("Please provide both creator_type and created_by_id"),
            }, status=status.HTTP_400_BAD_REQUEST)

        sponsors = Sponsor.objects.filter(
            creator_type=creator_type,
            created_by_id=created_by_id
        ).order_by('-created_at')

        sponsor_list = [
            {
                "id": sponsor.id,
                "name": sponsor.name,
                "logo": sponsor.logo.url if sponsor.logo else None,
                "url": sponsor.url,
                "creator_type": sponsor.creator_type,
                "created_by_id": sponsor.created_by_id,
                "created_at": sponsor.created_at,
                "updated_at": sponsor.updated_at
            } for sponsor in sponsors
        ]

        return Response({
            "status": 1,
            "message": _("Sponsors list found successfully"),
            "data": sponsor_list
        }, status=status.HTTP_200_OK)

    def post(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        data = request.data
        name = data.get('name')
        url = data.get('url')
        creator_type = data.get('creator_type')
        created_by_id = data.get('created_by_id')

        if not creator_type or not created_by_id:
            return Response({
                "status": 0,
                "message": _("Please provide both creator_type and created_by_id")
            }, status=status.HTTP_400_BAD_REQUEST)

        max_sponsors = 6
        existing_sponsors_count = Sponsor.objects.filter(
            creator_type=creator_type,
            created_by_id=created_by_id
        ).count()

        if existing_sponsors_count >= max_sponsors:
            return Response({
                "status": 0,
                "message": _("Maximum limit of sponsors reached for this creator.")
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            logo = None
            if "logo" in request.FILES:
                image = request.FILES["logo"]
                file_extension = image.name.split('.')[-1]
                unique_suffix = get_random_string(8)
                file_name = f"sponsors_images/{creator_type}_{created_by_id}_{unique_suffix}.{file_extension}"
                logo = default_storage.save(file_name, image)

            sponsor = Sponsor.objects.create(
                name=name,
                logo=logo,
                url=url,
                creator_type=creator_type,
                created_by_id=created_by_id
            )

            return Response({
                "status": 1,
                "message": _("Sponsor created successfully"),
                "data": {
                    "id": sponsor.id,
                    "name": sponsor.name,
                    "logo": sponsor.logo.url if sponsor.logo else None,
                    "url": sponsor.url,
                    "creator_type": sponsor.creator_type,
                    "created_by_id": sponsor.created_by_id,
                    "created_at": sponsor.created_at,
                    "updated_at": sponsor.updated_at
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": 0,
                "message": _("Failed to create sponsor"),
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SponsorDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        sponsor_id = request.query_params.get('sponsor_id')

        if not sponsor_id:
            return Response({
                "status": 0,
                "message": _("Please provide sponsor_id"),
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            sponsor = Sponsor.objects.get(id=sponsor_id)
        except Sponsor.DoesNotExist:
            return Response({
                "status": 0,
                "message": _("Sponsor not found"),
            }, status=status.HTTP_404_NOT_FOUND)

        sponsor_data = {
            "id": sponsor.id,
            "name": sponsor.name,
            "logo": sponsor.logo.url if sponsor.logo else None,
            "url": sponsor.url,
            "creator_type": sponsor.creator_type,
            "created_by_id": sponsor.created_by_id,
            "created_at": sponsor.created_at,
            "updated_at": sponsor.updated_at
        }

        return Response({
            "status": 1,
            "message": _("Sponsor details fetched successfully"),
            "data": sponsor_data
        }, status=status.HTTP_200_OK)

    def put(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        sponsor_id = request.data.get('sponsor_id')
        creator_type = request.data.get('creator_type')
        created_by_id = request.data.get('created_by_id')

        if not sponsor_id:
            return Response({
                "status": 0,
                "message": _("Please provide sponsor_id"),
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            sponsor = Sponsor.objects.get(id=sponsor_id)
        except Sponsor.DoesNotExist:
            return Response({
                "status": 0,
                "message": _("Sponsor not found"),
            }, status=status.HTTP_404_NOT_FOUND)

        name = request.data.get('name', sponsor.name)
        url = request.data.get('url', sponsor.url)
        logo = sponsor.logo
        if "logo" in request.FILES:
            if logo:
                default_storage.delete(logo.name)
            image = request.FILES["logo"]
            file_extension = image.name.split('.')[-1]
            unique_suffix = get_random_string(8)
            file_name = f"sponsors_images/{creator_type}_{created_by_id}_{unique_suffix}.{file_extension}"
            logo = default_storage.save(file_name, image)

        sponsor.name = name
        sponsor.logo = logo
        sponsor.url = url
        sponsor.save()

        return Response({
            "status": 1,
            "message": _("Sponsor updated successfully"),
            "data": {
                "id": sponsor.id,
                "name": sponsor.name,
                "logo": sponsor.logo.url if sponsor.logo else None,
                "url": sponsor.url,
                "creator_type": sponsor.creator_type,
                "created_by_id": sponsor.created_by_id,
                "created_at": sponsor.created_at,
                "updated_at": sponsor.updated_at
            }
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        sponsor_id = request.query_params.get('sponsor_id')

        if not sponsor_id:
            return Response({
                "status": 0,
                "message": _("Please provide sponsor_id"),
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            sponsor = Sponsor.objects.get(id=sponsor_id)
            if sponsor.logo:
                default_storage.delete(sponsor.logo.name)
            sponsor.delete()

            return Response({
                "status": 1,
                "message": _("Sponsor deleted successfully"),
            }, status=status.HTTP_200_OK)

        except Sponsor.DoesNotExist:
            return Response({
                "status": 0,
                "message": _("Sponsor not found"),
            }, status=status.HTTP_404_NOT_FOUND)


######################################################################## Report API View ###################################################################################
class ReportListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Report.objects.all().order_by('title_en')
    serializer_class = ReportSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Get all genders
        user_report = self.get_queryset()
        serializer = self.get_serializer(user_report, many=True)

        # Prepare the response with genders directly under 'data'
        return Response({
            'status': 1,
            'message': _('Reports retrieved successfully.'),
            'data': serializer.data  # Directly include the serialized data
        }, status=status.HTTP_200_OK)

class PostReportCreateView(generics.CreateAPIView):
    queryset = PostReport.objects.all().order_by('-created_at')
    serializer_class = PostReportSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def perform_create(self, serializer):
        # Automatically associate the report with the logged-in user's team or group information
        creator_type = self.request.data.get('creator_type')
        created_by_id = self.request.data.get('created_by_id')

        if not creator_type or not created_by_id:
            raise serializers.ValidationError(_("Please provide both creator_type and created_by_id"))

        serializer.save(creator_type=creator_type, created_by_id=created_by_id)

    def create(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Overriding the create method to return a custom response
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)  # Saving the report

        return Response({
            'status': 1,
            'message': _('Post Report Submitted Successfully.'),
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

################################################################################## Field API View ##################################################################################
class FieldAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # To handle file uploads

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Fetch all field capacities and ground types
        field_capacity = FieldCapacity.objects.all()
        ground_type = GroundMaterial.objects.all().order_by('name_en')

        # Serialize the data and pass the request context for language-based translation
        field_capacity_serializer = FieldCapacitySerializer(field_capacity, many=True)
        ground_type_serializer = GroundMaterialSerializer(ground_type, many=True, context={'request': request})
        
        return Response({
            'status': 1,
            'message': _('Fields retrieved successfully.'),
            'data': {
                'field_capacity': field_capacity_serializer.data,
                'ground_type': ground_type_serializer.data
            }
        }, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Handle field creation with image upload
        serializer = FieldSerializer(data=request.data, context={'request': request})
        user = request.user.id
        
        if serializer.is_valid():
            field_instance = serializer.save()

            # Handle image upload
            if 'image' in request.FILES:
                image = request.FILES['image']
                # Save the new image with a structured filename
                file_extension = image.name.split('.')[-1]
                unique_suffix = get_random_string(8)
                file_name = f"fields_images/{user}_{field_instance.id}_{unique_suffix}.{file_extension}"
                # Save the image and update the instance
                image_path = default_storage.save(file_name, image)
                field_instance.image = image_path
                field_instance.save()

            return Response({
                'status': 1,
                'message': _('Field created successfully.'),
                'data': FieldSerializer(field_instance).data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'status': 0,
                'message': _('Field creation failed.'),
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class ListFieldsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        # Set language from request headers
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Fetch all fields ordered by the latest creation date
        fields_queryset = Field.objects.all().order_by('-created_at')

        # Serialize the data
        serializer = FieldDetailSerializer(fields_queryset, many=True)

        # Return the serialized data
        return Response({
            'status': 1,
            'message': _('Fields fetched successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)




##################################################################### User Gender List API View ##############################################################################
class UserGenderListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserGender.objects.all().order_by('name_en')
    serializer_class = UserGenderSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        # Get the 'type' parameter from the query string (defaults to '2' if not provided)
        gender_type = request.query_params.get('type', '2')

        # If type is 1, get only the first 2 rows, else get all rows
        if gender_type == '1':
            user_genders = self.get_queryset()[:2]  # Limit to first 2 rows
        else:
            user_genders = self.get_queryset()  # Get all rows

        # Serialize the data
        serializer = self.get_serializer(user_genders, many=True)

        # Prepare the response with genders directly under 'data'
        return Response({
            'status': 1,
            'message': _('Gender retrieved successfully.'),
            'data': serializer.data  # Directly include the serialized data
        }, status=status.HTTP_200_OK)



############################################################## Playing Position API List View ################################################################################
class PlayingPositionListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = PlayingPosition.objects.all().order_by('name_en')
    serializer_class = PlayingPositionSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Get all playing positions
        playing_positions = self.get_queryset()
        serializer = self.get_serializer(playing_positions, many=True)

        # Prepare the response with playing positions directly under 'data'
        return Response({
            'status': 1,
            'message': _('Playing positions retrieved successfully.'),
            'data': serializer.data  # Directly include the serialized data
        }, status=status.HTTP_200_OK)

####################### Playing Foot API ############

class PlayingFootAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = PlayingFoot.objects.all().order_by('name_en')
    serializer_class = UserPlayingFootSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Get all playing positions
        playing_foot = self.get_queryset()
        serializer = self.get_serializer(playing_foot, many=True)

        # Prepare the response with playing positions directly under 'data'
        return Response({
            'status': 1,
            'message': _('Playing foot retrieved successfully.'),
            'data': serializer.data  # Directly include the serialized data
        }, status=status.HTTP_200_OK)


#######################################################  USER ROLE API LIST VIEW #############################################################################################

class UserRoleListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Role.objects.all().order_by('name_en')
    serializer_class = UserRoleSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Get all genders
        user_role = self.get_queryset()
        serializer = self.get_serializer(user_role, many=True)

        # Prepare the response with genders directly under 'data'
        return Response({
            'status': 1,
            'message': _('user role retrieved successfully.'),
            'data': serializer.data  # Directly include the serialized data
        }, status=status.HTTP_200_OK)

class LocationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        country_id = request.query_params.get('country_id')

        # If country_id is not provided, return all active countries
        if not country_id:
            countries = Country.objects.filter(status=True)
            country_data = [{'id': country.id, 'name': country.name} for country in countries]

            return Response({
                'status': 1,
                'message': _('Countries fetched successfully.'),
                'data': country_data
            }, status=status.HTTP_200_OK)

        # If country_id is provided, return cities for that country
        try:
            country = Country.objects.get(id=country_id, status=True)
        except Country.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Country not found or inactive.')
            }, status=status.HTTP_404_NOT_FOUND)

        cities = City.objects.filter(country=country, status=True)
        city_data = [{'id': city.id, 'name': city.name} for city in cities]

        return Response({
            'status': 1,
            'message': _('Cities fetched successfully.'),
            'data': city_data
        }, status=status.HTTP_200_OK)


####################################### FOLLOW USER ############################################
class FollowUnfollowAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request):
        # Set language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract input data
        creator_type = request.data.get('creator_type')
        created_by_id = request.data.get('created_by_id', request.user.id)  # Default to current user
        target_id = request.data.get('target_id')
        target_type = request.data.get('target_type')

        # Handle Follow/Unfollow Logic
        try:
            follow_request = FollowRequest.objects.get(
                created_by_id=created_by_id,
                creator_type=creator_type,
                target_id=target_id,
                target_type=target_type
            )
            # **Unfollow** case
            follow_request.delete()
            followers_count = FollowRequest.objects.filter(target_id=created_by_id, target_type=creator_type).count()
            following_count = FollowRequest.objects.filter(created_by_id=created_by_id, creator_type=creator_type).count()

            # Return response for unfollowing
            return Response({
                'status': 1,
                'message': _('Unfollowed successfully.'),
                'data': {
                    'followers_count': followers_count,
                    'following_count': following_count,
                    'is_follow': False,
                }
            }, status=status.HTTP_200_OK)

        except FollowRequest.DoesNotExist:
            # **Follow** case
            follow_request = FollowRequest.objects.create(
                created_by_id=created_by_id,
                creator_type=creator_type,
                target_id=target_id,
                target_type=target_type
            )
            followers_count = FollowRequest.objects.filter(target_id=created_by_id, target_type=creator_type).count()
            following_count = FollowRequest.objects.filter(created_by_id=created_by_id, creator_type=creator_type).count()

            # **Determine Follower Name (Creator)**
            if creator_type in [1, "1"]:  # User
                follower = User.objects.get(id=created_by_id)
                notifier_name = follower.username
            elif creator_type in [2, "2"]:  # Team
                follower = Team.objects.get(id=created_by_id)
                notifier_name = follower.team_username
            elif creator_type in [3, "3"]:  # Training Group
                follower = TrainingGroups.objects.get(id=created_by_id)
                notifier_name = follower.group_name
            else:
                return Response({
                    'status': 0,
                    'message': _('Invalid creator type.')
                }, status=400)

            # **Determine Target Name (Recipient)**
            if target_type in [1, "1"]:  # User
                target = User.objects.get(id=target_id)
                device_token = target.device_token
                device_type = target.device_type
                notification_language = target.current_language
            elif target_type in [2, "2"]:  # Team
                target = Team.objects.get(id=target_id)
                owner = target.team_founder
                device_token = owner.device_token
                device_type = owner.device_type
                notification_language = owner.current_language
            elif target_type in [3, "3"]:  # Training Group
                target = TrainingGroups.objects.get(id=target_id)
                owner = target.group_founder
                device_token = owner.device_token
                device_type = owner.device_type
                notification_language = owner.current_language
            else:
                return Response({
                    'status': 0,
                    'message': _('Invalid target type.')
                }, status=400)

            # **Set Notification Language**
            if notification_language in ['ar', 'en']:
                activate(notification_language)

            # **Send Push Notification**
            if device_type in [1, 2, "1", "2"]:
                title = _('New Follower!')
                body = _('{} started following you.').format(notifier_name)
                push_data = {'type': 'follow', 'notifier_id': created_by_id, 'target_type': creator_type}
                send_push_notification(device_token, title, body, device_type, data=push_data)

            # **Create Notification Record with Targeted ID and Type**
            notification = Notifictions.objects.create(
                created_by_id=created_by_id,      # Follower ID
                creator_type=creator_type,       # Follower Type

                targeted_id=target_id,           # Target ID
                targeted_type=target_type,       # Target Type

                title=_('New Follower!'),
                content = _('{} started following you.').format(notifier_name)
            )
            notification.save()

            # Return response for following
            return Response({
                'status': 1,
                'message': _('Followed successfully.'),
                'data': {
                    'followers_count': followers_count,
                    'following_count': following_count,
                    'is_follow': True,
                }
            }, status=status.HTTP_201_CREATED)

################ Pagination ##################
# Custom Pagination class with fixed paginate_queryset
class CustomFollowRequestPagination(PageNumberPagination):
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
            'message': _('Data fetched successfully.'),
            'total_records': self.total_records,
            'total_pages': self.total_pages,
            'current_page': self.page,
            'data': data
        })


####################################### LIST OF FOLLOWERS #######################################
class ListFollowersAPI(generics.ListAPIView):
    pagination_class = CustomFollowRequestPagination
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
        language = self.request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        creator_type = self.request.query_params.get('creator_type')
        created_by_id = self.request.query_params.get('created_by_id')
        search_key = self.request.query_params.get('search_key', '')  # Get search key if provided

        # Filter followers based on target_id and target_type
        queryset = FollowRequest.objects.filter(target_type=creator_type, target_id=created_by_id)

        if search_key:
            # Separate filtering for each type
            user_ids = User.objects.filter(username__icontains=search_key).values_list('id', flat=True)
            team_ids = Team.objects.filter(team_username__icontains=search_key).values_list('id', flat=True)
            group_ids = TrainingGroups.objects.filter(group_username__icontains=search_key).values_list('id', flat=True)

            # Filter queryset by matching IDs in each creator type
            queryset = queryset.filter(
                Q(creator_type=FollowRequest.USER_TYPE, created_by_id__in=user_ids) |
                Q(creator_type=FollowRequest.TEAM_TYPE, created_by_id__in=team_ids) |
                Q(creator_type=FollowRequest.GROUP_TYPE, created_by_id__in=group_ids)
            )

        return queryset

    def list(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get the target ID and type for the is_follow check
        created_by_id = self.request.query_params.get('created_by_id')
        creator_type = self.request.query_params.get('creator_type')

        # Get the paginated page object
        page = self.paginate_queryset(self.get_queryset())
        followers = []

        # Loop through the paginated results and build the response data
        for follow in page:
            is_follow = FollowRequest.objects.filter(
                created_by_id=created_by_id,
                creator_type=creator_type,
                target_id=follow.created_by_id,
                target_type=follow.creator_type
            ).exists()

            try:
                if follow.creator_type == FollowRequest.USER_TYPE:
                    user = User.objects.get(id=follow.created_by_id)
                    followers.append({
                        'creator_type': 1,
                        'creator_id': user.id,
                        'username': user.username,
                        'role': user.role.id,
                        'profile': user.profile_picture.url if user.profile_picture else None,
                        'is_follow': is_follow
                    })
                elif follow.creator_type == FollowRequest.TEAM_TYPE:
                    team = Team.objects.get(id=follow.created_by_id)
                    followers.append({
                        'creator_type': 2,
                        'creator_id': team.id,
                        'username': team.team_username,
                        'role': 7,
                        'profile': team.team_logo.url if team.team_logo else None,
                        'is_follow': is_follow
                    })
                elif follow.creator_type == FollowRequest.GROUP_TYPE:
                    group = TrainingGroups.objects.get(id=follow.created_by_id)
                    followers.append({
                        'creator_type': 3,
                        'creator_id': group.id,
                        'username': group.group_username,
                        'role': 8,
                        'profile': group.group_logo.url if group.group_logo else None,
                        'is_follow': is_follow
                    })
            except ObjectDoesNotExist:
                continue  # If any object is not found, skip this iteration

        # Use the paginated response method
        return self.get_paginated_response(followers)



##################################### LIST OF FOLLOWING #######################################
class ListFollowingAPI(generics.ListAPIView):
    pagination_class = CustomFollowRequestPagination
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
        language = self.request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        creator_type = self.request.query_params.get('creator_type')
        created_by_id = self.request.query_params.get('created_by_id')
        search_key = self.request.query_params.get('search_key', '')  # Get search key if provided

        queryset = FollowRequest.objects.filter(creator_type=creator_type, created_by_id=created_by_id)

        if search_key:
            # Separate filtering for each type
            user_ids = User.objects.filter(username__icontains=search_key).values_list('id', flat=True)
            team_ids = Team.objects.filter(team_username__icontains=search_key).values_list('id', flat=True)
            group_ids = TrainingGroups.objects.filter(group_username__icontains=search_key).values_list('id', flat=True)

            # Filter queryset by matching IDs in each target type
            queryset = queryset.filter(
                Q(target_type=FollowRequest.USER_TYPE, target_id__in=user_ids) |
                Q(target_type=FollowRequest.TEAM_TYPE, target_id__in=team_ids) |
                Q(target_type=FollowRequest.GROUP_TYPE, target_id__in=group_ids)
            )

        return queryset

    def list(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Get the paginated page object
        page = self.paginate_queryset(self.get_queryset())
        following = []

        # Loop through the paginated results and build the response data
        for follow in page:
            if follow.target_type == FollowRequest.USER_TYPE:
                user = User.objects.get(id=follow.target_id)
                following.append({
                    'creator_type': 1,
                    'creator_id': user.id,
                    'username': user.username,
                    'role': user.role.id,
                    'profile': user.profile_picture.url if user.profile_picture else None
                })
            elif follow.target_type == FollowRequest.TEAM_TYPE:
                team = Team.objects.get(id=follow.target_id)
                following.append({
                    'creator_type': 2,
                    'creator_id': team.id,
                    'username': team.team_username,
                    'role': 7,
                    'profile': team.team_logo.url if team.team_logo else None
                })
            elif follow.target_type == FollowRequest.GROUP_TYPE:
                group = TrainingGroups.objects.get(id=follow.target_id)
                following.append({
                    'creator_type': 3,
                    'creator_id': group.id,
                    'username': group.group_username,
                    'role': 8,
                    'profile': group.group_logo.url if group.group_logo else None
                })

        # Use the paginated response method
        return self.get_paginated_response(following)

##################################### Mobile Dashboard Image #######################################

class DashboardAPI(APIView):
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated
    parser_classes = (JSONParser, MultiPartParser, FormParser)  # Handle various parsers (for file uploads, if needed)

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract created_by_id and creator_type from query parameters
        created_by_id = request.query_params.get('created_by_id')
        creator_type = request.query_params.get('creator_type')

        if not created_by_id or not creator_type:
            return Response({
                'status': 0,
                'message': _('Both created_by_id and creator_type are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convert created_by_id and creator_type to integers
        created_by_id = int(created_by_id)
        creator_type = int(creator_type)

        # Filter notifications where targeted_id matches created_by_id and targeted_type matches creator_type
        notification_count = Notifictions.objects.filter(targeted_id=created_by_id, targeted_type=creator_type,read=False).count()

        # Fetch banners
        banners = MobileDashboardBanner.objects.all().order_by('-created_at')
        banner_serializer = MobileDashboardBannerSerializer(banners, many=True)

        # Fetch latest post
        latest_post = Post.objects.order_by('-created_at').first()
        latest_post_serializer = PostSerializer(latest_post, context={'request': request}) if latest_post else None

        # Fetch latest event
        latest_event = Event.objects.order_by('-created_at').first()
        latest_event_serializer = EventSerializer(latest_event, context={'request': request}) if latest_event else None

        # Fetch latest game
        latest_game = TournamentGames.objects.order_by('-game_date', '-game_start_time').first()
        latest_game_serializer = TournamentGameSerializer(latest_game, context={'request': request}) if latest_game else None

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

            # Get the first (most recent) date
            latest_date = next(iter(sorted_games_by_date))

            # Format the response for only the latest date
            response_data = {}
            if latest_date:
                response_data = {
                    "date": latest_date,
                    "tournament": sorted_games_by_date[latest_date]["tournament"]
                }

        return Response({
            "status": 1,
            "message": _("Dashboard banner list fetched successfully."),
            "data": {
                "banners": banner_serializer.data,
                "latest_post": latest_post_serializer.data if latest_post_serializer else None,
                "latest_event": latest_event_serializer.data if latest_event_serializer else None,
                "latest_game": latest_game_serializer.data if latest_game_serializer else None,
                "latest_by_date" : response_data,
            },
            "notification_count": notification_count if notification_count else 0,
        }, status=status.HTTP_200_OK)
     
    
    

####################################################################### Event Moodule #############################################################################################

###################### Event LIKE ######################
class EventLikeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        # Set language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract input data
        event_id = request.data.get('event_id')
        creator_type = request.data.get('creator_type', EventLike.USER_TYPE)  # Default: User
        created_by_id = request.data.get('created_by_id', request.user.id)  # Default: Logged-in user

        # Validate required data
        if not event_id:
            return Response({
                'status': 0,
                'message': _('Event ID is required.')
            }, status=400)

        # Validate event existence
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Event not found.')
            }, status=404)

        # Determine notifier name based on liker type
        if creator_type in [1, "1"]:  # User
            liker = User.objects.get(id=created_by_id)
            notifier_name = liker.username
        elif creator_type in [2, "2"]:  # Team
            liker = Team.objects.get(id=created_by_id)
            notifier_name = liker.team_username
        elif creator_type in [3, "3"]:  # Group
            liker = TrainingGroups.objects.get(id=created_by_id)
            notifier_name = liker.group_name
        else:
            return Response({
                'status': 0,
                'message': _('Invalid creator type.')
            }, status=400)

        # Toggle like/unlike functionality
        event_like, created = EventLike.objects.get_or_create(
            created_by_id=created_by_id,
            event=event,
            creator_type=creator_type
        )

        if not created:
            # **Unlike the event**
            event_like.delete()
            message = _('Event unliked successfully.')
        else:
            # **Like the event**
            message = _('Event liked successfully.')

            # **Fetch event organizer details for notification**
            organizer = event.event_organizer  # Organizer object
            recipient = organizer

            # Notification recipient details
            device_token = recipient.device_token
            device_type = recipient.device_type
            notification_language = recipient.current_language

            # Set notification language
            if notification_language in ['ar', 'en']:
                activate(notification_language)
            
            # Default values
            title = _('Event Liked!')
            body = _('{} liked your event.').format(notifier_name)

            # Send push notification
            if device_type in [1, 2, "1", "2"]:
                title = _('Event Liked!')
                body = _('{} liked your event.').format(notifier_name)
                push_data = {'type': 'event_list', 'notifier_id': event_id}
                send_push_notification(device_token, title, body, device_type, data=push_data)

            # **CREATE NOTIFICATION RECORD WITH TARGETED ID AND TYPE**
            Notifictions.objects.create(
                created_by_id=created_by_id,      # Liker ID
                creator_type=creator_type,       # Liker type
                
                targeted_id=event.created_by_id,  # Organizer ID
                targeted_type=event.creator_type, # Organizer type

                title=title,
                content=body,
            )

        # Serialize the event data with updated like status
        serializer = EventSerializer(event, context={'request': request})

        # Return response with updated event data
        return Response({
            'status': 1,
            'message': _(message),
            'data': serializer.data
        }, status=200)

###################### Get Comment of EVENT API ######################
class EventCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        event_id = request.data.get('event_id')
        if not event_id:
            return Response({
                'status': 0,
                'message': _('Event ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Event not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Get top-level comments
        comments = Event_comment.objects.filter(event=event, parent=None).order_by('-date_created')

        # Paginate comments
        paginator = PostCommentPagination()
        paginated_comments = paginator.paginate_queryset(comments, request)

        # If no paginated comments
        if paginated_comments is None:
            return Response({
                'status': 1,
                'message': _('No comments found for this Event.'),
                'data': {
                    'total_records': 0,
                    'total_pages': 0,
                    'current_page': 1,
                    'data': []
                }
            }, status=status.HTTP_200_OK)

        # Serialize paginated comments
        serializer = EventCommentSerializer(paginated_comments, many=True)

        return Response({
            'status': 1,
            'message': _('Comments fetched successfully.'),
            'data': serializer.data,
            'total_records': comments.count(),
            'total_pages': paginator.page.paginator.num_pages,
            'current_page': paginator.page.number,
        }, status=status.HTTP_200_OK)

###################### COMMENT CREATE API ######################
class EventCommentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        # Set language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract input data
        data = request.data
        event_id = data.get('event_id')
        comment_text = data.get('comment')
        parent_id = data.get('parent_id')
        creator_type = data.get('creator_type', Event_comment.USER_TYPE)  # Default: User type
        created_by_id = data.get('created_by_id', request.user.id)  # Default: Logged-in user

        # Validate required fields
        if not event_id or not comment_text:
            return Response({
                'status': 0,
                'message': _('event_id and comment are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate event existence
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Event not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate parent comment if provided
        parent_comment = None
        if parent_id:
            try:
                parent_comment = Event_comment.objects.get(id=parent_id)
            except Event_comment.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Parent comment not found.')
                }, status=status.HTTP_404_NOT_FOUND)

        # Determine notifier name based on creator type
        if creator_type in [1, "1"]:  # User
            commenter = User.objects.get(id=created_by_id)
            notifier_name = commenter.username
        elif creator_type in [2, "2"]:  # Team
            commenter = Team.objects.get(id=created_by_id)
            notifier_name = commenter.team_username
        elif creator_type in [3, "3"]:  # Group
            commenter = TrainingGroups.objects.get(id=created_by_id)
            notifier_name = commenter.group_name
        else:
            return Response({
                'status': 0,
                'message': _('Invalid creator type.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create the comment
        comment = Event_comment.objects.create(
            created_by_id=created_by_id,
            creator_type=creator_type,
            event=event,
            comment=comment_text,
            parent=parent_comment
        )

        # Determine recipient based on comment or reply
        if parent_comment:
            # Notify parent comment creator (reply case)
            recipient_id = parent_comment.created_by_id
            recipient_type = parent_comment.creator_type
        else:
            # Notify event organizer (new comment case)
            recipient_id = event.created_by_id
            recipient_type = event.creator_type

        # Fetch recipient details
        if recipient_type in [1, "1"]:  # User
            recipient = User.objects.get(id=recipient_id)
            recipient_name = recipient.username
            device_token = recipient.device_token
            device_type = recipient.device_type
            notification_language = recipient.current_language
        elif recipient_type in [2, "2"]:  # Team
            recipient = Team.objects.get(id=recipient_id)
            user = recipient.team_founder
            recipient_name = recipient.team_username
            device_token = user.device_token
            device_type = user.device_type
            notification_language = user.current_language
        elif recipient_type in [3, "3"]:  # Group
            recipient = TrainingGroups.objects.get(id=recipient_id)
            user = recipient.group_founder
            recipient_name = recipient.group_name
            device_token = user.device_token
            device_type = user.device_type
            notification_language = user.current_language
        else:
            return Response({
                'status': 0,
                'message': _('Invalid recipient type.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Set notification language
        if notification_language in ['ar', 'en']:
            activate(notification_language)

        # Notification Title and Body
        if parent_comment:
            title = _('New Reply on Your Comment!')
            body = _('{} replied to your comment.').format(notifier_name)
            push_data = {'type': 'event_comment_reply', 'event_id': event_id}
        else:
            title = _('New Comment on Your Event!')
            body = _('{} commented on your event.').format(notifier_name)
            push_data = {'type': 'event_comment', 'event_id': event_id}

        # Send push notification
        if device_type in [1, 2, "1", "2"]:
            send_push_notification(device_token, title, body, device_type, data=push_data)

        # **CREATE NOTIFICATION RECORD WITH TARGETED ID AND TYPE**
        Notifictions.objects.create(
            created_by_id=created_by_id,      # Commenter ID
            creator_type=creator_type,       # Commenter type
            
            targeted_id=recipient_id,        # Recipient ID (Organizer/Parent Commenter)
            targeted_type=recipient_type,    # Recipient type

            title=title,
            content=body,
        )

        # Return response with comment data
        return Response({
            'status': 1,
            'message': _('Comment created successfully.'),
            'data': EventCommentSerializer(comment).data
        }, status=status.HTTP_201_CREATED)




###################### Event Pagination ######################

class CustomEventPagination(PageNumberPagination):
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
            }, status=400)

        paginator = self.django_paginator_class(queryset, self.get_page_size(request))
        self.total_pages = paginator.num_pages

        if self.page > self.total_pages or self.page < 1:
            return Response({
                'status': 0,
                'message': _('Page not found.'),
                'data': []
            }, status=400)  # Use HTTP 400 for invalid page requests

        return super().paginate_queryset(queryset, request, view)


###################### All Events and my events ######################
class EventsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        paginator = CustomEventPagination()

        events_section = request.query_params.get('events_section')  # Default to 1 if not provided
        creator_type = request.query_params.get('creator_type')  # Get creator_type from query parameters
        created_by_id = request.query_params.get('created_by_id')  # Get created_by_id from query parameters

        try:
            events_section = int(events_section)
        except ValueError:
            return Response({
                'status': 0,
                'message': _('Invalid events_section value. It must be an integer.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if events_section == 1:
            # Show all events
            events = Event.objects.filter(event_status=1).order_by('-event_date')

        elif events_section == 2:
            # Show events created by the specified creator_type and created_by_id
            events = Event.objects.filter(
                creator_type=creator_type,
                created_by_id=created_by_id
            ).order_by('-event_date')


            if not events.exists():
                # If no created events, look up joined events in EventBooking
                joined_events = EventBooking.objects.filter(
                    creator_type=creator_type,
                    created_by_id=created_by_id
                )

                if joined_events.exists():
                    # Get event IDs from joined bookings
                    joined_event_ids = joined_events.values_list('event_id', flat=True)
                    events = Event.objects.filter(id__in=joined_event_ids).order_by('-event_date')

        else:
            return Response({
                'status': 0,
                'message': _('Invalid events_section value. Allowed values are 1 or 2.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Paginate the queryset
        paginated_events = paginator.paginate_queryset(events, request, view=self)
        serializer = EventSerializer(paginated_events, many=True, context={'request': request, 'creator_type': creator_type, 'created_by_id': created_by_id})
        notification_count = Notifictions.objects.filter(targeted_id=created_by_id, targeted_type=creator_type,read=False).count()


        return Response({
            'status': 1,
            'message': _('Events fetched successfully.'),
            'data': serializer.data,
            'notification_count': notification_count,
            'total_records': paginator.page.paginator.count,
            'total_pages': paginator.total_pages,
            'current_page': paginator.page.number
        })

###################### Event Details API ######################
class EventDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated
    parser_classes = (JSONParser, MultiPartParser, FormParser)  # Handle various parsers (for file uploads, if needed)

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get the event_id from query parameters
        event_id = request.query_params.get('event_id', None)

        if not event_id:
            return Response({
                "status": 0,
                "message": _("event_id is required."),
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # If event_id is provided, fetch a specific event
            event = Event.objects.get(id=event_id)  # Ensure the event exists
            serializer = EventSerializer(event)
            return Response({
                "status": 1,
                "message": _("Event details fetched successfully."),
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Event.DoesNotExist:
            return Response({
                "status": 0,
                "message": _("Event not found."),
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                "status": 0,
                "message": _("Error occurred while fetching event details."),
                "error": str(e)  # Include the exception message for debugging
            }, status=status.HTTP_400_BAD_REQUEST)

###################### Event Create API  ######################
class EventCreateAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EventSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        # Set language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Retrieve event types
        event_types = EventType.objects.all().order_by('name_en')
        serializer = EventTypeSerializer(event_types, many=True, context={'request': request})

        return Response({
            'status': 1,
            'message': _('Events retrieved successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        # Set language
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        data = request.data.copy()
        data['event_organizer'] = request.user.id  # Set logged-in user as organizer

        # Validate creator_type and created_by_id
        creator_type = data.get('creator_type')
        created_by_id = data.get('created_by_id')

        if not creator_type:
            return Response({
                'status': 0,
                'message': _('creator_type must be provided.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            creator_type = int(creator_type)
        except ValueError:
            return Response({
                'status': 0,
                'message': _('creator_type must be a valid integer.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate creator type and created_by_id
        if creator_type == Event.TEAM_TYPE:
            if not created_by_id:
                return Response({
                    'status': 0,
                    'message': _('created_by_id must be provided for TEAM_TYPE.')
                }, status=status.HTTP_400_BAD_REQUEST)

            if not Team.objects.filter(id=created_by_id).exists():
                return Response({
                    'status': 0,
                    'message': _('Invalid team ID.')
                }, status=status.HTTP_400_BAD_REQUEST)

            data['created_by_id'] = int(created_by_id)

        else:
            return Response({
                'status': 0,
                'message': _('Invalid creator type.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create Event
        serializer = self.serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            event = serializer.save()

            # Handle event image upload
            if 'event_image' in request.FILES:
                event_image = request.FILES['event_image']
                unique_suffix = get_random_string(8)
                file_name = f"event_images/{event.id}_{event.creator_type}_{event.created_by_id}_{unique_suffix}.{event_image.name.split('.')[-1]}"
                image_path = default_storage.save(file_name, event_image)
                event.event_image = image_path
                event.save()

            return Response({
                'status': 1,
                'message': _('Event created successfully.'),
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

###################### Event Detail Update ######################
class UpdateEventAPIView(APIView):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)


    def get_object(self, event_id):
        language = self.request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        try:
            return Event.objects.get(id=event_id, event_organizer=self.request.user)
        except Event.DoesNotExist:
            return None

    def patch(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        event_id = request.data.get('event_id')
        if not event_id:
            return Response({
                'status': 0,
                'message': _('Event ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        event = self.get_object(event_id)
        if not event:
            return Response({
                'status': 0,
                'message': _('Event not found or you are not authorized to update this event.')
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(event, data=request.data, partial=True)

        if serializer.is_valid():
            # Handle event image replacement
            if 'event_image' in request.FILES:
                # Delete old image if it exists
                if event.event_image and default_storage.exists(event.event_image.name):
                    default_storage.delete(event.event_image.name)

                # Save new image with a unique filename
                event_image = request.FILES['event_image']
                file_extension = event_image.name.split('.')[-1]
                unique_suffix = get_random_string(8)  # Ensure unique filename
                file_name = f"event_images/{event.id}_{event.creator_type}_{event.created_by_id}_{unique_suffix}.{file_extension}"
                image_path = default_storage.save(file_name, event_image)
                event.event_image = image_path

            serializer.save()  # Save other changes
            return Response({
                'status': 1,
                'message': _('Event updated successfully.'),
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 0,
            'message': _('Failed to update the event.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


###################### Event Bookin API ######################
class EventBookingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Fetch event_id from query parameters
        event_id = request.query_params.get("event_id")
        
        if not event_id:
            return Response({
                'status': 0,
                "error": "event id  is required"
                }, status=status.HTTP_400_BAD_REQUEST)

        # Get the logged-in user's ID
        user_id = request.user.id
        creator_type = EventBooking.USER_TYPE  # Or determine dynamically if there are multiple creator types

        # Get all bookings for the specified event by the logged-in user
        bookings = EventBooking.objects.filter(event_id=event_id, created_by_id=user_id, creator_type=creator_type)

        if not bookings.exists():
            return Response({"detail": "No bookings found for this event by the logged-in user."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the booking data with nested event details
        serializer = EventBookingSerializer(bookings, many=True, context={'request': request})
        
        return Response({
            'status': 1,
            'message': _('Event Booking Detail Fetched successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    
###################### Event Bokking Craete API ######################
class EventBookingCreateAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    serializer_class = EventBookingSerializer

    def post(self, request, *args, **kwargs):
        # Activate language based on the request header
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Ensure event_id is provided
        event_id = request.data.get('event_id')
        if not event_id:
            return Response({
                'status': 0,
                'message': _('Event ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the Event instance using the provided event_id
        event_instance = get_object_or_404(Event, id=event_id)

        # Retrieve convenience_fee from request or SystemSettings
        convenience_fee = request.data.get('convenience_fee')
        if convenience_fee is None:
            try:
                system_settings = SystemSettings.objects.latest('id')
                convenience_fee = system_settings.event_convenience_fee or 0
            except SystemSettings.DoesNotExist:
                convenience_fee = 0

        # Validate creator_type and created_by_id
        creator_type = request.data.get('creator_type')
        created_by_id = request.data.get('created_by_id')

        if creator_type is None:
            return Response({
                'status': 0,
                'message': _('creator_type must be provided.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Match created_by_id with a Team and fetch the team founder
        try:
            event_created_by_id = event_instance.created_by_id
            team = Team.objects.get(id=event_created_by_id)
            team_founder = team.team_founder
        except Team.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('No matching team found for this event.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Prepare booking data
        booking_data = {
            'event': event_instance.id,
            'tickets': request.data.get('tickets'),
            'convenience_fee': convenience_fee,
            'ticket_amount': request.data.get('ticket_amount', 0.0),
            'total_amount': request.data.get('total_amount', 0.0),
            'creator_type': creator_type,
            'created_by_id': created_by_id,
        }

        # Handle booking creation using the serializer
        serializer = self.get_serializer(data=booking_data)
        if serializer.is_valid():
            booking_instance = serializer.save()

            # Send notification to the team founder
            if team_founder:
                # Activate founder's preferred language for notification
                notification_language = team_founder.current_language
                if notification_language in ['ar', 'en']:
                    activate(notification_language)

                # Prepare notification title and body
                title = _('{} wants to attend your event!').format(request.user.username)
                body = _('{} has requested to book a ticket for your event "{}".').format(
                            request.user.username,
                            event_instance.event_name,
                        )



                # Create notification record with targeted_id and targeted_type
                notification = Notifictions.objects.create(
                    created_by_id=request.user.id,  # Requestor ID
                    creator_type=creator_type,      # Creator type
                    targeted_id=team_founder.id,    # Team founder ID
                    targeted_type=1,                # Assuming target is always a user
                    title=title,
                    content=body
                )
                notification.save()

                # Prepare push_data for additional details
                push_data = {
                    'notifier_id': event_instance.id,
                    "type": "my_events",
                }

                # Send push notification
                send_push_notification(
                    device_token=team_founder.device_token,
                    title=title,
                    body=body,
                    device_type=team_founder.device_type,
                    data=push_data
                )

            return Response({
                'status': 1,
                'message': _('Your event booking request has been submitted successfully. The admin will connect with you for further steps.'),
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        else:
            return Response({
                'status': 0,
                'message': _('Booking creation failed.'),
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

############################################################### FAQ API #####################################################################################################
class FAQListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = FAQ.objects.all().order_by('question_en')
    serializer_class = FAQSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Get all genders
        faq = self.get_queryset()
        serializer = self.get_serializer(faq, many=True)

        # Prepare the response with genders directly under 'data'
        return Response({
            'status': 1,
            'message': _('FAQ retrieved successfully.'),
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
    
############################################################ General Settings API ####################################################################################
class GeneralSettingsList(APIView):
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        # Retrieve the first general settings object
        general_settings = SystemSettings.objects.first()

        if not general_settings:
            return Response({
                'status': 0,
                'message': _('No general settings found.'),
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Serialize the general settings data
        serializer = SystemSettingsSerializer(general_settings)

        return Response({
            'status': 1,
            'message': _('General Settings retrieved successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

############################################################### User Profile API #####################################################################################################
class AgeGroupListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        try:
            age_groups = AgeGroup.objects.all().order_by('name_en')
            # Pass the request in the context to make it accessible in the serializer
            serializer = AgeGroupSerializer(age_groups, many=True, context={'request': request})

            return Response({
                'status': 1,
                'message': _('Age Groups fetched successfully.'),
                'data': serializer.data,
            })

        except Exception as e:
            return Response({
                'status': 0,
                'message': _('Error occurred while fetching Age Groups list.'),
                'error': str(e),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)


############################################################### Injury API #####################################################################################################
class InjuryListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        
        injury = InjuryType.objects.all().order_by('name_en')
        serializer = InjurySerializer(injury, many=True,context={'request': request})
        return Response({
           'status': 1,
           'message': _('Injury fetched successfully.'),
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


############################################################### User Role State API #####################################################################################################
class UserRoleStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id', request.user.id)
        years_param = request.query_params.get('years', '0')  # Default to '0' (all-time data)

        # Validate years
        try:
            # Parse years if provided as a comma-separated list
            years = [int(year.strip()) for year in years_param.split(',') if year.strip().isdigit()]
            if years and any(year < 0 for year in years):
                raise ValueError("Year cannot be negative.")
        except ValueError:
            return Response({
                "status": 0,
                "message": _("Invalid value for 'years'. Please provide a comma-separated list of valid years."),
                "data": []
            }, status=400)

        # If years is empty or contains '0', set it to all-time data
        if not years or 0 in years:
            time_filter = {}
        else:
            # Filter for the provided years
            time_filter = {'created_at__year__in': years}

        try:
            # Validate user_id and fetch user
            user = User.objects.get(id=user_id, is_deleted=False)

            # Check user role and fetch stats accordingly
            if user.role.id == 2:  # Player
                return self.get_player_stats(user, time_filter)
            elif user.role.id == 3:  # Coach
                return self.get_coach_stats(user, time_filter)
            elif user.role.id == 4:  # Referee
                return self.get_referee_stats(user, time_filter)
            else:
                return Response({
                    "status": 1,
                    "message": _("You don't have Any Statstics"),
                    "data":{},
                }, status=200)

        except User.DoesNotExist:
            return Response({
                "status": 0,
                "message":_("User not found or has been deleted."),
            }, status=404)
        except Exception as e:
            return Response({
                "status": 0,
                "message": _("An error occurred."),
                "error": str(e),
            }, status=500)

    def get_player_stats(self, user, time_filter):
        try:
            # Tournament games
            tournament_lineups = Lineup.objects.filter(player_id=user.id, **time_filter)
            tournament_team_ids = list(tournament_lineups.values_list('team_id', flat=True))
            tournament_game_ids = list(tournament_lineups.values_list('game_id', flat=True))
            tournament_games = TournamentGames.objects.filter(id__in=tournament_game_ids)

            tournament_total_games_played = tournament_games.count()
            tournament_games_won = tournament_games.filter(
                Q(team_a__in=tournament_team_ids, winner_id=F('team_a')) |
                Q(team_b__in=tournament_team_ids, winner_id=F('team_b'))
            ).count()
            tournament_games_lost = tournament_games.filter(
                Q(team_a__in=tournament_team_ids, loser_id=F('team_a')) |
                Q(team_b__in=tournament_team_ids, loser_id=F('team_b'))
            ).count()
            tournament_games_drawn = tournament_games.filter(is_draw=True).count()

            tournament_stats = PlayerGameStats.objects.filter(player_id=user.id, **time_filter)
            tournament_total_goals = tournament_stats.aggregate(Sum('goals'))['goals__sum'] or 0
            tournament_total_assists = tournament_stats.aggregate(Sum('assists'))['assists__sum'] or 0
            tournament_total_yellow_cards = tournament_stats.aggregate(Sum('yellow_cards'))['yellow_cards__sum'] or 0
            tournament_total_red_cards = tournament_stats.aggregate(Sum('red_cards'))['red_cards__sum'] or 0

            # Friendly games
            friendly_lineups = FriendlyGameLineup.objects.filter(player_id=user.id, **time_filter)
            friendly_team_ids = list(friendly_lineups.values_list('team_id', flat=True))
            friendly_game_ids = list(friendly_lineups.values_list('game_id', flat=True))
            friendly_games = FriendlyGame.objects.filter(id__in=friendly_game_ids)

            friendly_total_games_played = friendly_games.count()
            friendly_games_won = friendly_games.filter(
                Q(team_a__in=friendly_team_ids, winner_id=F('team_a')) |
                Q(team_b__in=friendly_team_ids, winner_id=F('team_b'))
            ).count()
            friendly_games_lost = friendly_games.filter(
                Q(team_a__in=friendly_team_ids, loser_id=F('team_a')) |
                Q(team_b__in=friendly_team_ids, loser_id=F('team_b'))
            ).count()
            friendly_games_drawn = friendly_games.filter(is_draw=True).count()

            friendly_stats = FriendlyGamesPlayerGameStats.objects.filter(player_id=user.id, **time_filter)
            friendly_total_goals = friendly_stats.aggregate(Sum('goals'))['goals__sum'] or 0
            friendly_total_assists = friendly_stats.aggregate(Sum('assists'))['assists__sum'] or 0
            friendly_total_yellow_cards = friendly_stats.aggregate(Sum('yellow_cards'))['yellow_cards__sum'] or 0
            friendly_total_red_cards = friendly_stats.aggregate(Sum('red_cards'))['red_cards__sum'] or 0

            # Combine totals
            total_games_played = tournament_total_games_played + friendly_total_games_played
            total_games_won = tournament_games_won + friendly_games_won
            total_games_lost = tournament_games_lost + friendly_games_lost
            total_games_drawn = tournament_games_drawn + friendly_games_drawn

            total_goals = tournament_total_goals + friendly_total_goals
            total_assists = tournament_total_assists + friendly_total_assists
            total_yellow_cards = tournament_total_yellow_cards + friendly_total_yellow_cards
            total_red_cards = tournament_total_red_cards + friendly_total_red_cards

            return Response({
                "status": 1,
                "message": _("Player stats fetched successfully."),
                "data": {
                    "user_id": user.id,
                    "total_goals": total_goals,
                    "total_assists": total_assists,
                    "total_yellow_cards": total_yellow_cards,
                    "total_red_cards": total_red_cards,
                    "total_games_played": total_games_played,
                    "games_won": total_games_won,
                    "games_lost": total_games_lost,
                    "games_drawn": total_games_drawn,
                    "type": "Player",
                    "skills": {
                        "passing": user.passing,
                        "shooting": user.shooting,
                        "interception": user.interception,
                        "dribbling": user.dribbling,
                        "tackling": user.tackling,
                        "aerial_duals": user.aerial_duals,
                    },
                    # Skills & Physical stats
                    "physical":{
                        "stamina": user.stamina,
                        "speed": user.speed,
                        "strength": user.strength,
                        "jump": user.jump,
                        "balance": user.balance,
                        "agility": user.agility,
                    },
                },
            }, status=200)
        except Exception as e:
            return Response({
                "status": 0,
                "message": _("Failed to fetch player stats."),
                "error": str(e),
            }, status=500)


    def get_coach_stats(self, user, time_filter):
        try:
            # Get branches where the user is a coach
            coach_branches = JoinBranch.objects.filter(
                user_id=user.id,
                joinning_type=JoinBranch.COACH_STAFF_TYPE
            ).values_list('branch_id', flat=True)

            # Tournament games
            tournament_games = TournamentGames.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                **time_filter
            )
            tournament_total_games = tournament_games.count()
            tournament_games_won = tournament_games.filter(
                Q(team_a__in=coach_branches, winner_id=F('team_a')) |
                Q(team_b__in=coach_branches, winner_id=F('team_b'))
            ).count()
            tournament_games_lost = tournament_games.filter(
                Q(team_a__in=coach_branches, loser_id=F('team_a')) |
                Q(team_b__in=coach_branches, loser_id=F('team_b'))
            ).count()
            tournament_games_drawn = tournament_games.filter(is_draw=True).count()

            # Friendly games
            friendly_games = FriendlyGame.objects.filter(
                Q(team_a__in=coach_branches) | Q(team_b__in=coach_branches),
                **time_filter
            )
            friendly_total_games = friendly_games.count()
            friendly_games_won = friendly_games.filter(
                Q(team_a__in=coach_branches, winner_id=F('team_a')) |
                Q(team_b__in=coach_branches, winner_id=F('team_b'))
            ).count()
            friendly_games_lost = friendly_games.filter(
                Q(team_a__in=coach_branches, loser_id=F('team_a')) |
                Q(team_b__in=coach_branches, loser_id=F('team_b'))
            ).count()
            friendly_games_drawn = friendly_games.filter(is_draw=True).count()

            # Combine stats
            total_games_played = tournament_total_games + friendly_total_games
            games_won = tournament_games_won + friendly_games_won
            games_lost = tournament_games_lost + friendly_games_lost
            games_drawn = tournament_games_drawn + friendly_games_drawn

            # Goals conceded
            goals_conceded = (
                tournament_games.aggregate(
                    total_goals=Sum(
                        Case(
                            When(team_a__in=coach_branches, then='team_b_goal'),
                            When(team_b__in=coach_branches, then='team_a_goal'),
                            default=0,
                            output_field=models.IntegerField()
                        )
                    )
                )['total_goals'] or 0
            ) + (
                friendly_games.aggregate(
                    total_goals=Sum(
                        Case(
                            When(team_a__in=coach_branches, then='team_b_goal'),
                            When(team_b__in=coach_branches, then='team_a_goal'),
                            default=0,
                            output_field=models.IntegerField()
                        )
                    )
                )['total_goals'] or 0
            )

            # Cards stats
            player_stats = PlayerGameStats.objects.filter(
                team_id__in=coach_branches,
                **time_filter
            )
            total_red_cards = player_stats.aggregate(Sum('red_cards'))['red_cards__sum'] or 0
            total_yellow_cards = player_stats.aggregate(Sum('yellow_cards'))['yellow_cards__sum'] or 0

            return Response({
                "status": 1,
                "message": _("Coach stats fetched successfully."),
                "data": {
                    "user_id": user.id,
                    "total_games_played": total_games_played,
                    "games_won": games_won,
                    "games_lost": games_lost,
                    "games_drawn": games_drawn,
                    "total_red_cards": total_red_cards,
                    "total_yellow_cards": total_yellow_cards,
                    "total_goals_conceded": goals_conceded,
                    "type": "Coach",
                },
            }, status=200)
        except Exception as e:
            return Response({
                "status": 0,
                "message": _("Failed to fetch coach stats."),
                "error": str(e),
            }, status=500)



    def get_referee_stats(self, user, time_filter):
        try:
            # Tournament games officiated
            tournament_games_officiated = GameOfficials.objects.filter(
                official_id=user.id,
                officials_type_id__in=[2, 3, 4, 5],
                **time_filter
            ).values_list('game_id', flat=True)

            # Friendly games officiated
            friendly_games_officiated = FriendlyGameGameOfficials.objects.filter(
                official_id=user.id,
                officials_type_id__in=[2, 3, 4, 5],
                **time_filter
            ).values_list('game_id', flat=True)

            total_games_officiated = len(tournament_games_officiated) + len(friendly_games_officiated)

            # Cards stats
            cards_stats = PlayerGameStats.objects.filter(
                game_id__in=list(tournament_games_officiated) + list(friendly_games_officiated),
                **time_filter
            ).aggregate(
                total_yellow_cards=Sum('yellow_cards'),
                total_red_cards=Sum('red_cards')
            )
            total_yellow_cards = cards_stats['total_yellow_cards'] or 0
            total_red_cards = cards_stats['total_red_cards'] or 0

            return Response({
                "status": 1,
                "message": _("Referee stats fetched successfully."),
                "data": {
                    "user_id": user.id,
                    "total_games_played": total_games_officiated,
                    "total_yellow_cards": total_yellow_cards,
                    "total_red_cards": total_red_cards,
                    "type": "Referee",
                },
            }, status=200)
        except Exception as e:
            return Response({
                "status": 0,
                "message": _("Failed to fetch referee stats."),
                "error": str(e),
            }, status=500)



class CustomSearchPagination(PageNumberPagination):
    page_size = 10  # Number of records per page
    page_query_param = 'page'  # Custom page number param
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        # Get the page parameter
        page_param = request.query_params.get(self.page_query_param, None)
        try:
            page_number = int(page_param) if page_param is not None else None
            if page_number == 0:  # Treat page=0 as if the page is not specified
                page_number = None
                # Remove the page parameter to mimic blank behavior
                request.query_params._mutable = True
                del request.query_params[self.page_query_param]
                request.query_params._mutable = False
        except (ValueError, TypeError):
            page_number = None  # Default to None for invalid input
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        # Calculate total pages
        total_pages = self.page.paginator.num_pages
        current_page = self.page.number
        total_records = self.page.paginator.count

        return Response({
            "status": 1,
            "message": _("Data fetched successfully."),
            "total_records": total_records,
            "total_pages": total_pages,
            "current_page": current_page,
            "results": {
                "data": data
            }
        })

class SearchAPIView(APIView):
    pagination_class = CustomSearchPagination

   

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        search_type = request.query_params.get('type')
        creator_type = request.query_params.get('creator_type')
        created_by_id = request.query_params.get('created_by_id')
        paginator = self.pagination_class()

        if not search_type:
            return Response({"status": 0, "message": _("Type is required."), "data": {}}, status=status.HTTP_400_BAD_REQUEST)

        if search_type.lower() == 'users':
            users = User.objects.all().order_by('username')
            if search_query:
                users = users.filter(username__icontains=search_query)
            # if creator_type and created_by_id:
            #     users = users.filter(creator_type=creator_type, created_by_id=created_by_id)
            paginated_users = paginator.paginate_queryset(users, request)
            user_data = [get_user_data(user, request) for user in paginated_users]
            return paginator.get_paginated_response(user_data)

        if search_type.lower() == 'posts':
            posts = Post.objects.all().order_by('title')
            if search_query:
                posts = posts.filter(title__icontains=search_query)
            # if creator_type and created_by_id:
            #     posts = posts.filter(creator_type=creator_type, created_by_id=created_by_id)
            paginated_posts = paginator.paginate_queryset(posts, request)
            serializer = PostSerializer(paginated_posts, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        if search_type.lower() == 'teams':
            teams = Team.objects.all().order_by('team_username')
            if search_query:
                teams = teams.filter(
                Q(team_name__icontains=search_query) | Q(team_username__icontains=search_query)
            )
            # if creator_type and created_by_id:
            #     teams = teams.filter(creator_type=creator_type, team_founder=created_by_id)
            team_data = [get_team_data(team.team_founder, request) for team in teams if get_team_data(team.team_founder, request)]
            
            return Response({
                "status": 1,
                "message": _("Data fetched successfully."),
                "results": {
                    "data": team_data
                }
            })

        if search_type.lower() == 'fields':
            fields = Field.objects.all().order_by('field_name')
            if search_query:
                fields = fields.filter(field_name__icontains=search_query)
            serializer = FieldSerializer(fields, many=True, context={'request': request})
            return Response({
                "status": 1,
                "message": _("Data fetched successfully."),
                "results": {
                    "data": serializer.data
                }
            })


        if search_type.lower() == 'events':
            events = Event.objects.all().order_by('event_name')
            if search_query:
                events = events.filter(event_name__icontains=search_query)
            # if creator_type and created_by_id:
            #     events = events.filter(creator_type=creator_type, created_by_id=created_by_id)
            paginated_events = paginator.paginate_queryset(events, request)
            serializer = EventSerializer(paginated_events, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        return Response({"status": 0, "message": _("Invalid search type."), "data": {}}, status=status.HTTP_400_BAD_REQUEST)

####### Change Language ##############
class UpdateCurrentLanguageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user  # Get the authenticated user
        current_language = request.data.get('current_language')

        # Validate the input
        if current_language not in ["en", "ar"]:
            return Response({
                'status': 0,
                'message': _('Invalid or missing current_language. It must be either "en" or "ar".')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Activate the selected language
        activate(current_language)

        # Update the user's current language
        user.current_language = current_language
        user.save()

        return Response({
            'status': 1,
            'message': _('Current language updated successfully.'),
            'data': {
                'current_language': user.current_language
            }
        }, status=status.HTTP_200_OK)
    

########################## timing notification #####################

############### Training #####################
class CheckTrainingTimeAndSendNotificationsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        # Get the current time and date
        current_time = timezone.now()
        current_date = current_time.date()
        one_hour_later = current_time + timedelta(hours=1)

        # Query all training sessions for today
        trainings = Training.objects.filter(training_date=current_date)
        notifications_sent = 0  # Counter for sent notifications

        for training in trainings:
            training_start_time = timezone.make_aware(
                datetime.combine(training.training_date, training.start_time)
            )

            # Check if the training is within the next hour
            if current_time <= training_start_time <= one_hour_later:
                attendance_message = _("Don't forget to mark your attendance")
                comments_message = _("Don't forget to add your comments on your players' performance.")
                push_data = {
                    "training_id": training.id,
                    "type":"training"
                }

                # Check the creator type
                if training.creator_type == 1:  # Created by a User
                    user = User.objects.get(id=training.created_by_id)
                    user_branches = JoinBranch.objects.filter(
                        user_id=user.id, joinning_type=4  # 4 = Player/Team Creator
                    ).values_list('branch_id', flat=True)

                    if user_branches.exists():
                        # Notify all managers and coaches of the branches
                        coaches_or_managers = JoinBranch.objects.filter(
                            branch_id__in=user_branches,
                            joinning_type__in=[1, 3]  # 1 = Coach, 3 = Manager
                        ).select_related('user_id')

                        for branch in coaches_or_managers:
                            coach_or_manager = branch.user_id
                            self.send_notification(
                                coach_or_manager, attendance_message, comments_message, push_data
                            )
                            notifications_sent += 1
                    else:
                        # Notify the user who created the training
                        self.send_notification(user, attendance_message, comments_message, push_data)
                        notifications_sent += 1

                elif training.creator_type == 2:  # Created by a Team
                    team = Team.objects.get(id=training.created_by_id)
                    team_founder = team.team_founder
                    self.send_notification(team_founder, attendance_message, comments_message, push_data)
                    notifications_sent += 1

        return Response(
            {"message": "Notifications sent to {} users.".format(notifications_sent)},
            status=status.HTTP_200_OK
        )

    def send_notification(self, user, attendance_message, comments_message, push_data):
        """
        Helper method to send notifications to a user.
        """
        notification_language = user.current_language
        if notification_language in ['ar', 'en']:
            activate(notification_language)

        send_push_notification(
            user.device_token,
            _("Training Reminder"),
            attendance_message,
            device_type=user.device_type,
            data=push_data
        )
        send_push_notification(
            user.device_token,
            _("Training Reminder"),
            comments_message,
            device_type=user.device_type,
            data=push_data
        )

        Notifictions.objects.create(
            created_by_id=1,  # Assumed system admin ID
            creator_type=1,
            targeted_id=user.id,
            targeted_type=1,
            title=_("Training Reminder"),
            content=attendance_message + comments_message
        )

#################### Training End Time Notification API ######################
class CheckEndTimeAndSendNotificationsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        # Get the current datetime
        current_time = timezone.now()
        one_hour_later = current_time + timedelta(hours=1)
        current_date = current_time.date()

        # Query all training sessions for today
        trainings = Training.objects.filter(training_date=current_date)

        notifications_sent = 0  # Counter for sent notifications

        for training in trainings:
            training_end_time = timezone.make_aware(
                datetime.combine(training.training_date, training.end_time)
            )

            # Check if the training ends within the next hour
            if current_time <= training_end_time <= one_hour_later:
                message = _("Don't forget to rate your players after the training session.")
                comments_message = _("Don't forget to add your comments on your players' performance.")
                push_data = {
                    "training_id": training.id,
                    "type":"training"
                }

                if training.creator_type == 1:  # Created by a User
                    creator_branches = JoinBranch.objects.filter(
                        user_id=training.created_by_id,
                        joinning_type=4  # Assuming 4 means team member/player
                    ).values_list('branch_id', flat=True)

                    if creator_branches.exists():
                        # Notify the team's branch manager and coach
                        branch_managers_and_coaches = JoinBranch.objects.filter(
                            branch_id__in=creator_branches,
                            joinning_type__in=[1, 3]  # 1 = Coach, 3 = Manager
                        ).select_related('user')

                        for branch in branch_managers_and_coaches:
                            manager_or_coach = branch.user
                            self.send_notification(manager_or_coach, message, comments_message, push_data)
                            notifications_sent += 1
                    else:
                        # Notify the training creator directly
                        user = User.objects.get(id=training.created_by_id)
                        self.send_notification(user, message, comments_message, push_data)
                        notifications_sent += 1

                elif training.creator_type == 2:  # Created by Team Founder
                    team = Team.objects.get(id=training.created_by_id)
                    team_founder = team.team_founder
                    self.send_notification(team_founder, message, comments_message, push_data)
                    notifications_sent += 1

        return Response(
            {"message": "Notifications sent to {} users.".format(notifications_sent)},
            status=status.HTTP_200_OK
        )


    def send_notification(self, user, message, comments_message, push_data):
        """
        Helper method to send notifications to a user.
        """
        notification_language = user.current_language
        if notification_language in ['ar', 'en']:
            activate(notification_language)

        send_push_notification(
            user.device_token,
            _("Training Reminder"),
            message,
            device_type=user.device_type,
            data=push_data
        )
        send_push_notification(
            user.device_token,
            _("Training Reminder"),
            comments_message,
            device_type=user.device_type,
            data=push_data
        )

        Notifictions.objects.create(
            created_by_id=1,
            creator_type=1,
            targeted_id=user.id,
            targeted_type=1,
            title=_("Training Reminder"),
            content=message + comments_message
        )


#################### Tournament Game LineUp Notification API ######################
class LineupNotificationAPIView(APIView):

    def get(self, request, *args, **kwargs):
        # Get current time and today's date
            current_time = timezone.now()
            current_date = date.today()

            # Calculate the time one hour from now
            one_hour_later = current_time + timedelta(hours=1)
            # Get upcoming tournament games within the next 1 hour for today
            upcoming_tournament_games = TournamentGames.objects.filter(
                game_date=current_date,
                game_start_time__gte=current_time.time(),
                game_start_time__lte=one_hour_later.time(),
                finish=False
            )

            # Get upcoming friendly games within the next 1 hour for today
            upcoming_friendly_games = FriendlyGame.objects.filter(
                game_date=current_date,
                game_start_time__gte=current_time.time(),
                game_start_time__lte=one_hour_later.time(),
                finish=False
            )

            # Check if there are no upcoming games for today
            if not upcoming_tournament_games and not upcoming_friendly_games:
                return Response({
                    "status": "success",
                    "message": _("No upcoming games found for today."),
                    "details": []
                }, status=status.HTTP_200_OK)

            notifications_sent = []

            # Process tournament games
            for game in upcoming_tournament_games:
                self._check_and_notify_lineup(game, "tournament", notifications_sent)

            # Process friendly games
            for game in upcoming_friendly_games:
                self._check_and_notify_lineup(game, "friendly", notifications_sent)

            return Response({
                "status": "success",
                "message": _("Notifications sent for incomplete lineups"),
                "details": notifications_sent
            }, status=status.HTTP_200_OK)

    def _check_and_notify_lineup(self, game, game_type, notifications_sent):
            if game_type == "tournament":
                # For tournament games, use the Lineup model
                team_a_lineup = Lineup.objects.filter(
                    game_id=game.id,
                    team_id=game.team_a,
                    lineup_status=Lineup.ALREADY_IN_LINEUP
                )
                team_b_lineup = Lineup.objects.filter(
                    game_id=game.id,
                    team_id=game.team_b,
                    lineup_status=Lineup.ALREADY_IN_LINEUP
                )
            else:
                # For friendly games, use the FriendlyGameLineup model
                team_a_lineup = FriendlyGameLineup.objects.filter(
                    game_id=game.id,
                    team_id=game.team_a,
                    lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP
                )
                team_b_lineup = FriendlyGameLineup.objects.filter(
                    game_id=game.id,
                    team_id=game.team_b,
                    lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP
                )

            if team_a_lineup.count() < 11:
                self._notify_team_staff(
                    team=game.team_a,
                    game=game,
                    game_type=game_type,
                    opponent_team_name=game.team_b.team_name,
                    notifications_sent=notifications_sent,
                    team_name="Team A"
                )

            if team_b_lineup.count() < 11:
                self._notify_team_staff(
                    team=game.team_b,
                    game=game,
                    game_type=game_type,
                    opponent_team_name=game.team_a.team_name,
                    notifications_sent=notifications_sent,
                    team_name="Team B"
                )

    def _notify_team_staff(self, team, game, game_type, opponent_team_name, notifications_sent,team_name):
        # Get staff members for the team (managers and coaches)
        staff_members = JoinBranch.objects.filter(
            branch_id=team,
            joinning_type__in=[JoinBranch.COACH_STAFF_TYPE, JoinBranch.MANAGERIAL_STAFF_TYPE]
        )

        # Notify staff members
        for staff_member in staff_members:
            if staff_member.user_id.device_token:
                role = "Manager" if staff_member.joinning_type == JoinBranch.MANAGERIAL_STAFF_TYPE else "Coach"
                self._send_notification(
                    user=staff_member.user_id,
                    game=game,
                    game_type=game_type,
                    opponent_team_name=opponent_team_name,
                    role=role,
                    notifications_sent=notifications_sent,
                    team_name=team_name
                )
                notification = Notifictions.objects.create(
                    created_by_id=1,  # Requestor ID (could be dynamic)
                    creator_type=1,  # Creator type (could vary based on game type)
                    targeted_id=staff_member.user_id.id,  # Targeted user (staff member)
                    targeted_type=1,  # Assuming the target is a user
                    title=_("Please add your line-up for your match against {opponent_team}").format(opponent_team=opponent_team_name),
                    content=_("Lineup is missing for game {game_number} in the {game_type} match.").format(
                        game_number=game.game_number, game_type=game_type)
                )
                notification.save()


        # Notify team founder (if present)
        team_founder = team.team_id.team_founder
        if team_founder and team_founder.device_token:
            self._send_notification(
                user=team_founder,
                game=game,
                game_type=game_type,
                opponent_team_name=opponent_team_name,
                role="Team Founder",
                notifications_sent=notifications_sent,
                team_name=team_name

            )
            notification = Notifictions.objects.create(
                created_by_id=1,  # Requestor ID (could be dynamic)
                creator_type=1,  # Creator type (could vary based on game type)
                targeted_id=team_founder.id,  # Targeted user (team founder)
                targeted_type=1,  # Assuming the target is a user
                title=_("Please add your line-up for your match against {opponent_team}").format(opponent_team=opponent_team_name),
                content=_("Lineup is missing for game {game_number} in the {game_type} match.").format(
                        game_number=game.game_number, game_type=game_type)

            )
            notification.save()

    def _send_notification(self, user, game, game_type, opponent_team_name, role, notifications_sent,team_name):
        # Set the notification title and body based on language
        notification_language = user.current_language
        if notification_language in ['ar', 'en']:
            activate(notification_language)

        # Dynamic message content
        if game_type == "tournament":
            body = _(
                "Lineup is missing for game {game_number} in the {tournament_name} tournament."
            ).format(
                game_number=game.game_number,
                tournament_name=game.tournament_id.tournament_name
            )
        else:
            body = _(
              
                "Lineup is missing for game {game_number} in the friendly match."
            ).format(game_number=game.game_number)

        title = _(
            "Please add your line-up for your match against {opponent_team}."
        ).format(opponent_team=opponent_team_name)

        push_data = {'type': "assign_handler"}

        # Send the notification
        send_push_notification(
            user.device_token,
            title=title,
            body=body,
            device_type=user.device_type,
            data=push_data
        )

        # Append details to notifications_sent
        notifications_sent.append(
            "Notification sent to {} ({}) for {} game of {}".format(user.username, role, game_type, team_name)
        )


class UniformConfirmationNotificationView(APIView):
    def get(self, request, *args, **kwargs):

        current_time = timezone.now()
        current_date = date.today()
        one_hour_later = current_time + timedelta(hours=1)
        # Retrieve upcoming tournament games that are not confirmed
        upcoming_tournament_games = TournamentGames.objects.filter(
            game_date=current_date,
            game_start_time__gte=current_time.time(),
            game_start_time__lte=one_hour_later.time(),
            finish=False,
            is_confirm=False  # Only include games where confirmation is required
        )

        # Retrieve upcoming friendly games that are not confirmed
        upcoming_friendly_games = FriendlyGame.objects.filter(
            game_date=current_date,
            game_start_time__gte=current_time.time(),
            game_start_time__lte=one_hour_later.time(),
            finish=False,
            is_confirm=False  # Only include games where confirmation is required
        )

        if not upcoming_tournament_games and not upcoming_friendly_games:
            return Response({
                "status": "success",
                "message": _("No upcoming games scheduled for today."),
                "details": []  # No notifications to send
            }, status=status.HTTP_200_OK)

        notifications_sent = []

        # Helper function to send notifications
        def notify_game_officials_and_handler(game, game_type):
            game_type_label = "Tournament" if game_type == "tournament" else "Friendly"
            game_number = game.game_number

            if game_type == "tournament":
                officials = GameOfficials.objects.filter(game_id=game, officials_type_id=2)
            else:  # Friendly game
                officials = FriendlyGameGameOfficials.objects.filter(game_id=game, officials_type_id=2)

            # Notify officials
            for official in officials:
                official_user = official.official_id
                notification_language = official_user.current_language  # Get user's preferred language
                if notification_language in ['ar', 'en']:
                    activate(notification_language)
                title = _("Uniform Confirmation Required")
                body = _(
                    "Please confirm the uniform colors for the {} game (Game #{}) between {} and {}.".format(
                        game_type_label, game_number, game.team_a, game.team_b
                    )
                )

                data = {'type': "assign_handler"}
                
                send_push_notification(
                    device_token=official_user.device_token,
                    title=title,
                    body=body,
                    device_type=official_user.device_type,
                    data=data
                )
                notification = Notifictions.objects.create(
                    created_by_id=1,  # Requestor ID (could be dynamic)
                    creator_type=1,  # Creator type (could vary based on game type)
                    targeted_id=official_user.id,  # Targeted user (official)
                    targeted_type=1,  # Assuming the target is a user
                    title=title,
                    content=body
                )
                notification.save()

                notifications_sent.append({
                    "user": official_user.id,
                    "message": body
                })

            # Notify game statistics handler
            if game.game_statistics_handler:
                handler = game.game_statistics_handler
                notification_language = handler.current_language  # Get handler's preferred language
                if notification_language in ['ar', 'en']:
                    activate(notification_language)
                title = "Uniform Confirmation Required"
                body = (
                    "Please confirm the uniforms colors for the {} game (Game #{}) between {} and {}.".format(
                        game_type_label, game_number, game.team_a, game.team_b
                    )
                )

                data = {'type': "assign_handler"}
                send_push_notification(
                    device_token=handler.device_token,
                    title=title,
                    body=body,
                    device_type=handler.device_type,
                    data=data   
                )
                notification = Notifictions.objects.create(
                    created_by_id=1,  # Requestor ID (could be dynamic)
                    creator_type=1,  # Creator type (could vary based on game type)
                    targeted_id=handler.id,  # Targeted user (official)
                    targeted_type=1,  # Assuming the target is a user
                    title=title,
                    content=body
                )
                notification.save()

                notifications_sent.append({
                    "user": handler.id,
                    "message": body
                })

        # Process tournament games
        for game in upcoming_tournament_games:
            notify_game_officials_and_handler(game, "tournament")

        # Process friendly games
        for game in upcoming_friendly_games:
            notify_game_officials_and_handler(game, "friendly")

        return Response({
            "status": "success",
            "message": _("Notifications sent for uniform confirmation."),
            "details": notifications_sent
        }, status=status.HTTP_200_OK)





class UniformAddNotificationAPIView(APIView):

    def get(self, request, *args, **kwargs):
        # Get current time and today's date
        current_time = timezone.now()
        current_date = date.today()  # This will give you today's date

        # Calculate the time one hour from now
        one_hour_later = current_time + timedelta(hours=1)
        # Get upcoming tournament games within the next 1 hour for today
        upcoming_tournament_games = TournamentGames.objects.filter(
            game_date=current_date,  # Ensure it's today's date
            game_start_time__gte=current_time.time(),
            game_start_time__lte=one_hour_later.time(),
            finish=False  # Only consider games that have not finished
        )
       

        # Get upcoming friendly games within the next 1 hour for today
        upcoming_friendly_games = FriendlyGame.objects.filter(
            game_date=current_date,  # Ensure it's today's date
            game_start_time__gte=current_time.time(),
            game_start_time__lte=one_hour_later.time(),
            finish=False  # Only consider games that have not finished
        )
     
        # Check if there are no upcoming games for today
        if not upcoming_tournament_games and not upcoming_friendly_games:
            
            return Response({
                "status": "success",
                "message": _("No upcoming games scheduled for today."),
                "details": []  # Empty list as no games are found
            }, status=status.HTTP_200_OK)

        notifications_sent = []

        # Process tournament games
        for game in upcoming_tournament_games:
           
            self._check_and_notify_missing_uniforms(game, "tournament", notifications_sent)

        # Process friendly games
        for game in upcoming_friendly_games:
            
            self._check_and_notify_missing_uniforms(game, "friendly", notifications_sent)

       

        return Response({
            "status": "success",
            "message":_("Notifications sent for missing uniforms"),
            "details": notifications_sent
        }, status=status.HTTP_200_OK)
    
    def _check_and_notify_missing_uniforms(self, game, game_type, notifications_sent):
      
        # Check if any uniform color fields are missing for Team A or Team B
        missing_team_a_colors = any([
            not game.team_a_primary_color_player,
            not game.team_a_secondary_color_player,
            not game.team_a_primary_color_goalkeeper,
            not game.team_a_secondary_color_goalkeeper
        ])
        
        missing_team_b_colors = any([
            not game.team_b_primary_color_player,
            not game.team_b_secondary_color_player,
            not game.team_b_primary_color_goalkeeper,
            not game.team_b_secondary_color_goalkeeper
        ])

        
        if missing_team_a_colors or missing_team_b_colors:
            # Get the coaches and managers for both teams
            team_a_staff = JoinBranch.objects.filter(
                branch_id=game.team_a,
                joinning_type__in=[JoinBranch.COACH_STAFF_TYPE, JoinBranch.MANAGERIAL_STAFF_TYPE]
            )

            team_b_staff = JoinBranch.objects.filter(
                branch_id=game.team_b,
                joinning_type__in=[JoinBranch.COACH_STAFF_TYPE, JoinBranch.MANAGERIAL_STAFF_TYPE]
            )

            team_founder_a = game.team_a.team_id.team_founder
            team_founder_b = game.team_b.team_id.team_founder


            
            # Notify staff members for Team A if any color is missing
            if missing_team_a_colors:
                for staff_member in team_a_staff:
                    self._send_notification(staff_member.user_id, game, game_type, game.team_b.team_name, "Manager" if staff_member.joinning_type == JoinBranch.MANAGERIAL_STAFF_TYPE else "Coach", notifications_sent, game.team_a.team_name)
                  

            
                # Notify the team founder for Team A
                if team_founder_a and team_founder_a.device_token:
                    self._send_notification(team_founder_a, game, game_type, game.team_b.team_name, "Team Founder", notifications_sent, game.team_a.team_name)

            # Notify staff members for Team B if any color is missing
            if missing_team_b_colors:
                for staff_member in team_b_staff:
                    self._send_notification(staff_member.user_id, game, game_type, game.team_a.team_name, "Manager" if staff_member.joinning_type == JoinBranch.MANAGERIAL_STAFF_TYPE else "Coach", notifications_sent, game.team_b.team_name)

            # Notify the team founder for Team B
                if team_founder_b and team_founder_b.device_token:
                    self._send_notification(team_founder_b, game, game_type, game.team_a.team_name, "Team Founder", notifications_sent, game.team_b.team_name)



    def _send_notification(self, user, game, game_type, opponent_team_name, role, notifications_sent, team_name):
        # Set the notification title and body based on language
        notification_language = user.current_language
        if notification_language in ['ar', 'en']:
            activate(notification_language)

        # Set the dynamic message
        body = _(
            "Please add your uniform colors to your {} match against {}.".format(
                game_type.capitalize(), opponent_team_name
            )
        )

        title = _("Missing Uniform Colors!!")

        push_data = {'type': "assign_handler"}

        # Send the notification
        send_push_notification(
            device_token=user.device_token,
            title=title,
            body=body,
            device_type=user.device_type,
            data=push_data
        )
    
        notification = Notifictions.objects.create(
                created_by_id=1,  # Replace with appropriate user ID or dynamic value
                creator_type=1,
                targeted_id=user.id,
                targeted_type=1,  # Assuming 1 represents a user in your system
                title=title,
                content=body
        )
        notification.save()
    

        # Log notification sent
        notifications_sent.append(
            "Notification sent to {} ({}) for {} game against {}".format(
                user.username, role, game_type, opponent_team_name
            )
        )

class PlayerReadyNotificationAPIView(APIView):
 
    def send_notifications_to_team_staff(self, team_branch, message_title, message_body):
        roles = {
            JoinBranch.COACH_STAFF_TYPE: "Coach",
            JoinBranch.MANAGERIAL_STAFF_TYPE: "Manager",
            "founder": "Founder"
        }

        notifications = []

        # Get the coach and manager for the team
        staff_members = JoinBranch.objects.filter(branch_id=team_branch)

        for staff in staff_members:
            if staff.joinning_type in roles:
                send_push_notification(
                    device_token=staff.user_id.device_token,
                    title=message_title,
                    body=message_body,
                    device_type=staff.user_id.device_type
                )
                notification = Notifictions.objects.create(
                        created_by_id=1,  # Replace with appropriate user ID or dynamic value
                        creator_type=1,
                        targeted_id=staff.user_id.id,
                        targeted_type=1,  # Assuming 1 represents a user in your system
                        title=message_title,
                        content=message_body
                )
                notification.save()


                notifications.append({
                    "role": roles[staff.joinning_type],
                    "username": staff.user_id.username
                })

        # Get the team founder from the team branch
        team_founder_a = staff.branch_id.team_id.team_founder
        if team_founder_a:
            send_push_notification(
                device_token=team_founder_a.device_token,
                title=message_title,
                body=message_body,
                device_type=team_founder_a.device_type
            )
            notification = Notifictions.objects.create(
                        created_by_id=1,  # Replace with appropriate user ID or dynamic value
                        creator_type=1,
                        targeted_id=team_founder_a.id,
                        targeted_type=1,  # Assuming 1 represents a user in your system
                        title=message_title,
                        content=message_body
                )
            notification.save()
            notifications.append({
                "role": roles["founder"],
                "username": team_founder_a.username
            })

        return notifications

    def check_and_notify(self, game, team_a_lineup, team_b_lineup, team_a_id, team_b_id):
        notifications = []

        # Check if any player in Team A has lineup_status=3 and player_ready=False
        team_a_not_ready = team_a_lineup.filter(lineup_status=3, player_ready=False).exists()

        # Check if any player in Team B has lineup_status=3 and player_ready=False
        team_b_not_ready = team_b_lineup.filter(lineup_status=3, player_ready=False).exists()

        # If a player is not ready in Team A, send notification
        if team_a_not_ready:
            team_a_notifications = self.send_notifications_to_team_staff(
                team_branch=team_a_id,
                message_title=_("Player Not Ready"),
                message_body=_("One or more of your players are not ready for the match! Make sure that they are ready ASAP.")
            )
            notifications.extend([
                "Notification sent to {} ({}) for Team A".format(n['role'], n['username'])
                for n in team_a_notifications
            ])


        # If a player is not ready in Team B, send notification
        if team_b_not_ready:
            team_b_notifications = self.send_notifications_to_team_staff(
                team_branch=team_b_id,
                message_title=_("Player Not Ready"),
                message_body=_("One or more of your players are not ready for the match! Make sure that they are ready ASAP.")
            )
            notifications.extend([
                "Notification sent to {} ({}) for Team B".format(n['role'], n['username'])
                for n in team_b_notifications
            ])


        return notifications

    def get(self, request, *args, **kwargs):
        current_time = timezone.now()
        current_date = date.today()
        one_hour_later = current_time + timedelta(hours=1)

        # Get upcoming tournament games within the next 1 hour for today
        upcoming_tournament_games = TournamentGames.objects.filter(
            game_date=current_date,
            game_start_time__gte=current_time.time(),
            game_start_time__lte=one_hour_later.time(),
            finish=False
        )

        # Get upcoming friendly games within the next 1 hour for today
        upcoming_friendly_games = FriendlyGame.objects.filter(
            game_date=current_date,
            game_start_time__gte=current_time.time(),
            game_start_time__lte=one_hour_later.time(),
            finish=False
        )

        # If no games are found
        if not upcoming_tournament_games and not upcoming_friendly_games:
            return Response({
                "status": "success",
                "message": _("No upcoming games scheduled for today."),
                "details": []
            }, status=status.HTTP_200_OK)

        notifications_sent = []

        # Process Tournament Games
        for game in upcoming_tournament_games:
            team_a_lineup = Lineup.objects.filter(
                game_id=game.id,
                lineup_status=3,
                player_ready=False
            )
            team_b_lineup = Lineup.objects.filter(
                game_id=game.id,
                lineup_status=3,
                player_ready=False
            )
            notifications = self.check_and_notify(
                game=game,
                team_a_lineup=team_a_lineup,
                team_b_lineup=team_b_lineup,
                team_a_id=game.team_a_id,
                team_b_id=game.team_b_id
            )
            notifications_sent.extend([
                "Tournament Game {}: {}".format(game.id, n)
                for n in notifications
            ])


        # Process Friendly Games
        for game in upcoming_friendly_games:
            team_a_lineup = FriendlyGameLineup.objects.filter(
                game_id=game.id,
                lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP,
                player_ready=False
            )
            team_b_lineup = FriendlyGameLineup.objects.filter(
                game_id=game.id,
                lineup_status=FriendlyGameLineup.ALREADY_IN_LINEUP,
                player_ready=False
            )
            notifications = self.check_and_notify(
                game=game,
                team_a_lineup=team_a_lineup,
                team_b_lineup=team_b_lineup,
                team_a_id=game.team_a_id,
                team_b_id=game.team_b_id
            )
            notifications_sent.extend([
                "Friendly Game {}: {}".format(game.id, n)
                for n in notifications
            ])


        return Response({
            "status": "success",
            "message": _("Notifications processed"),
            "details": notifications_sent
        }, status=status.HTTP_200_OK)



class ClearNotificationView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request):
        try:
            # Set the language for the response based on request header
            language = request.headers.get('Language', 'en')
            if language in ['en', 'ar']:
                activate(language)

            # Extract the notification_id from query parameters
            notification_id = request.query_params.get('notification_id')

            if not notification_id:
                return Response({
                    'status': 0,
                    'message': _('Notification ID is required.')
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get the notification by ID
            notification = Notifictions.objects.filter(id=notification_id).first()

            if not notification:
                return Response({
                    'status': 0,
                    'message': _('Notification not found.')
                }, status=status.HTTP_404_NOT_FOUND)

            # Delete the notification
            notification.delete()

            return Response({
                'status': 1,
                'message': _('Notification Clear successfully.'),
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': 0,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

################ Mark All Notifications Read ###################
class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request):
        try:
            # Set the language for the response based on request header
            language = request.headers.get('Language', 'en')
            if language in ['en', 'ar']:
                activate(language)

            # Extract created_by_id and creator_type from query parameters
            created_by_id = request.query_params.get('created_by_id')
            creator_type = request.query_params.get('creator_type')

            if not created_by_id or not creator_type:
                return Response({
                    'status': 0,
                    'message': _('Both created_by_id and creator_type are required.')
                }, status=status.HTTP_400_BAD_REQUEST)

            # Convert created_by_id and creator_type to integers
            created_by_id = int(created_by_id)
            creator_type = int(creator_type)

            # Filter notifications where targeted_id matches created_by_id and targeted_type matches creator_type
            notifications = Notifictions.objects.filter(targeted_id=created_by_id, targeted_type=creator_type)

            if not notifications.exists():
                return Response({
                    'status': 1,
                    'message': _('All notifications Clear successfully.'),
                }, status=status.HTTP_200_OK)

            # Delete all notifications
            notifications.delete()

            return Response({
                'status': 1,
                'message': _('All notifications Clear successfully.'),
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': 0,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







class CustomNotificationsPagination(PageNumberPagination):
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

        if self.page > self.total_pages or self.page < 1:
            return Response({
                'status': 0,
                'message': _('Page not found.'),
                'data': []
            }, status=400)

        # Get the paginated results as a list (instead of the Page object)
        return list(paginator.page(self.page))

    def get_paginated_response(self, data, notification_count):
        return Response({
            "status": 1,
            "message": _("Notifications fetched successfully."),
            "total_records": self.total_records,
            "total_pages": self.total_pages,
            "current_page": self.page,
            "data": data,  # Directly include data array
            "notification_count": notification_count  # Include notification count here
        })


class NotificationsListView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = CustomNotificationsPagination

    def get(self, request):
        try:
            # Set the language for the response based on request header
            language = request.headers.get('Language', 'en')
            if language in ['en', 'ar']:
                activate(language)

            # Extract created_by_id and creator_type from query parameters
            created_by_id = request.query_params.get('created_by_id')
            creator_type = request.query_params.get('creator_type')

            if not created_by_id or not creator_type:
                return Response({
                    'status': 0,
                    'message': _('Both created_by_id and creator_type are required.')
                }, status=status.HTTP_400_BAD_REQUEST)

            # Convert created_by_id and creator_type to integers
            created_by_id = int(created_by_id)
            creator_type = int(creator_type)

            # Filter notifications
            notifications = Notifictions.objects.filter(
                targeted_id=created_by_id, targeted_type=creator_type
            ).order_by('-date_created')

            # Count unread notifications
            notification_count = Notifictions.objects.filter(
                targeted_id=created_by_id, targeted_type=creator_type, read=False
            ).count()

            # Mark notifications as read
            notifications.update(read=True)

            # Apply pagination
            paginator = self.pagination_class()
            paginated_notifications = paginator.paginate_queryset(notifications, request, self)

            # Build the response data
            response_data = []
            for notification in paginated_notifications:
                entity = None
                if notification.creator_type == 1:  # User
                    try:
                        user = User.objects.get(id=notification.created_by_id)
                        entity = {
                            "username": user.username,
                            "fullname": user.fullname,
                            "profilepicture": user.profile_picture.url if user.profile_picture else None,
                            "target_id": notification.created_by_id,
                            "target_type": notification.creator_type,
                        }
                    except User.DoesNotExist:
                        entity = {}
                elif notification.creator_type == 2:  # Team
                    try:
                        team = Team.objects.get(id=notification.created_by_id)
                        entity = {
                            "username": team.team_username,
                            "team_name": team.team_name,
                            "team_logo": team.team_logo.url if team.team_logo else None,
                            "target_id": notification.created_by_id,
                            "target_type": notification.creator_type,
                        }
                    except Team.DoesNotExist:
                        entity = {}
                elif notification.creator_type == 3:  # Group
                    try:
                        group = TrainingGroups.objects.get(id=notification.created_by_id)
                        entity = {
                            "username": group.group_username,
                            "group_name": group.group_name,
                            "group_logo": group.group_logo.url if group.group_logo else None,
                            "target_id": notification.created_by_id,
                            "target_type": notification.creator_type,
                        }
                    except TrainingGroups.DoesNotExist:
                        entity = {}

                response_data.append({
                    "id": notification.id,
                    "entity": entity,
                    "title": notification.title,
                    "content": notification.content,
                    "status": notification.read,
                    "date_created": notification.date_created.strftime('%d %B %Y %H:%M'),
                })

            # Return the response
            return paginator.get_paginated_response(response_data, notification_count)

        except ValueError:
            return Response({
                "status": 0,
                "message": _("Invalid created_by_id or creator_type."),
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": 0,
                "message": _("An error occurred: ") + str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
