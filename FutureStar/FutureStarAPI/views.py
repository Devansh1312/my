from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.utils.translation import activate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from FutureStarAPI.serializers import *
from FutureStarTeamApp.serializers import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from FutureStar_App.models import *
from FutureStarAPI.models import *
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
import random
from django.utils import timezone
import os
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils.translation import gettext as _
from django.db import transaction
import string
from rest_framework.exceptions import ValidationError
import re
import logging
from django.utils.crypto import get_random_string
from django.utils.timezone import now


logger = logging.getLogger(__name__)

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
    """Returns a dictionary with all user details."""
    
    # Calculate follower and following counts for the user
    followers_count = FollowRequest.objects.filter(target_id=user.id, target_type=FollowRequest.USER_TYPE).count()
    following_count = FollowRequest.objects.filter(created_by_id=user.id, creator_type=FollowRequest.USER_TYPE).count()
    
    post_count = Post.objects.filter(created_by_id=user.id, creator_type=FollowRequest.USER_TYPE).count()
    
    # Check if the current user is following this user
    is_follow = FollowRequest.objects.filter(
        created_by_id=request.user.id,
        creator_type=FollowRequest.USER_TYPE,
        target_id=user.id,
        target_type=FollowRequest.USER_TYPE
    ).exists()
    
    gender_name = None
    if user.gender:
        serializer = UserGenderSerializer(user.gender, context={'request': request})
        gender_name = serializer.data['name']
    
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
        'playing_foot': user.playing_foot,
        'favourite_local_team': user.favourite_local_team,
        'favourite_team': user.favourite_team,
        'favourite_local_player': user.favourite_local_player,
        'favourite_player': user.favourite_player,
        'profile_picture': user.profile_picture.url if user.profile_picture else None,
        'cover_photo': user.card_header.url if user.card_header else None,
        'device_type': user.device_type,
        'device_token': user.device_token,
    }


######################################################################################### Get Team Data ###################################################################
def get_team_data(user, request):
    """Returns a dictionary with the user's team details."""
    
    # Get the user's team (assuming only one team is allowed per user)
    try:
        team = Team.objects.get(user_id=user)
    except Team.DoesNotExist:
        return None  # If no team exists, return None or empty dictionary as needed
    
    # Get follower and following counts for the team
    followers_count = FollowRequest.objects.filter(target_id=team.id, target_type=FollowRequest.TEAM_TYPE).count()
    following_count = FollowRequest.objects.filter(created_by_id=team.id, creator_type=FollowRequest.TEAM_TYPE).count()
    
    # Check if the current user is following this team
    is_follow = FollowRequest.objects.filter(
        created_by_id=request.user.id,
        creator_type=FollowRequest.USER_TYPE,
        target_id=team.id,
        target_type=FollowRequest.TEAM_TYPE
    ).exists()
    
    # Get post count for the team
    team_post_count = Post.objects.filter(created_by_id=team.id, creator_type=FollowRequest.TEAM_TYPE).count()
    
    return {
        'team_id': team.id,
        'followers_count': followers_count,
        'following_count': following_count,
        'post_count': team_post_count,
        'is_follow': is_follow,
        'creator_type': 2,
        'team_name': team.team_name,
        'team_username': team.team_username,
        'team_type_id': team.team_type.id if team.team_type else None,
        'team_type_name': team.team_type.name_en if team.team_type else None,
        'bio': team.bio,
        'team_establishment_date': team.team_establishment_date,
        'team_president': team.team_president,
        'latitude': team.latitude,
        'longitude': team.longitude,
        'address': team.address,
        'house_no': team.house_no,
        'premises': team.premises,
        'street': team.street,
        'city': team.city,
        'state': team.state,
        'country_name': team.country_name,
        'postalCode': team.postalCode,
        'country_code': team.country_code,
        'country_id': team.country_id.id if team.country_id else None,
        'country_name': team.country_id.name if team.country_id else None,
        'city_id': team.city_id.id if team.city_id else None,
        'city_name': team.city_id.name if team.city_id else None,
        'phone': team.phone,
        'email': team.email,
        'age_group': team.age_group,
        'entry_fees': team.entry_fees,
        'branches': team.branches,
        'team_logo': team.team_logo.url if team.team_logo else None,
        'team_background_image': team.team_background_image.url if team.team_background_image else None,
        'team_uniform': team.team_uniform,
    }

############################################################################# Get Group Data ######################################################
def get_group_data(user, request):
    """Returns a dictionary with the user's group details."""
    
    # Get the user's group (assuming only one group is allowed per user)
    try:
        group = TrainingGroups.objects.get(group_founder=user)
    except TrainingGroups.DoesNotExist:
        return None  # If no group exists, return None or empty dictionary as needed
    
    # Get follower and following counts for the group
    followers_count = FollowRequest.objects.filter(target_id=group.id, target_type=FollowRequest.GROUP_TYPE).count()
    following_count = FollowRequest.objects.filter(created_by_id=group.id, creator_type=FollowRequest.GROUP_TYPE).count()
    
    # Check if the current user is following this group
    is_follow = FollowRequest.objects.filter(
        created_by_id=request.user.id,
        creator_type=FollowRequest.USER_TYPE,
        target_id=group.id,
        target_type=FollowRequest.GROUP_TYPE
    ).exists()
    
    # Get post count for the group
    group_post_count = Post.objects.filter(created_by_id=group.id, creator_type=FollowRequest.GROUP_TYPE).count()
    
    return {
        'group_id': group.id,
        'followers_count': followers_count,
        'following_count': following_count,
        'post_count': group_post_count,
        'is_follow': is_follow,
        'creator_type': 3,
        'group_name': group.group_name,
        'group_username': group.group_username,
        'bio': group.bio,
        'group_founder': group.group_founder.id,
        'latitude': group.latitude,
        'longitude': group.longitude,
        'address': group.address,
        'house_no': group.house_no,
        'premises': group.premises,
        'street': group.street,
        'city': group.city,
        'state': group.state,
        'country_name': group.country_name,
        'postalCode': group.postalCode,
        'country_code': group.country_code,
        'phone': group.phone,
        'group_logo': group.group_logo.url if group.group_logo else None,
        'group_background_image': group.group_background_image.url if group.group_background_image else None,
    }

###################################################### Send OTP API #############################################################################################################
              
# Generate a random 6-digit OTP
def generate_otp():
    return str(random.randint(100000, 999999))

class send_otp(APIView):
    permission_classes = [AllowAny]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def generate_random_password(self, length=8):
        """Generate a random password with letters and digits."""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for i in range(length))
    
    def post(self, request, *args, **kwargs):
        logger.debug("Starting send_otp post method")
        
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        registration_type = request.data.get('type')
        logger.debug(f"Registration Type: {registration_type}")

        try:
            # Handle Registration Type 1 (Normal registration)
            if registration_type == 1:
                username = request.data.get('username')
                phone = request.data.get('phone')
                password = request.data.get('password')

                # Check if username or phone already exists
                if User.objects.filter(username=username).exists():
                    return Response({
                        'status': 0,
                        'message': _('Username already exists.')
                    }, status=status.HTTP_400_BAD_REQUEST)

                if User.objects.filter(phone=phone).exists():
                    return Response({
                        'status': 0,
                        'message': _('Phone number already exists.')
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Generate OTP and save it
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
                        'message': _('Email is required.')
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
                        'message': _('Email already exists.')
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Validate if username or phone already exists if provided
                if username and phone:
                    if User.objects.filter(username=username).exists():
                        return Response({
                            'status': 0,
                            'message': _('Username already exists.')
                        }, status=status.HTTP_400_BAD_REQUEST)

                    if User.objects.filter(phone=phone).exists():
                        return Response({
                            'status': 0,
                            'message': _('Phone number already exists.')
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
            logger.error(f"Error in send_otp: {str(e)}")
            return Response({
                'status': 0,
                'message': _('An error occurred while sending OTP.'),
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



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
                'message': _('Phone is a required field.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if not otp_input:
            return Response({
                'status': 0,
                'message': _('OTP is a required field.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if not username:
            return Response({
                'status': 0,
                'message': _('Username is a required field.')
            }, status=status.HTTP_400_BAD_REQUEST)


        # Check if the OTP and phone exist in the OTPSave table
        try:
            otp_record = OTPSave.objects.get(phone=phone, OTP=otp_input)
        except OTPSave.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Invalid OTP or phone number.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the username already exists in the User table
        if User.objects.filter(username=username).exists():
            return Response({
                'status': 0,
                'message': _('Username already exists.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the phone already exists in the User table
        if User.objects.filter(phone=phone).exists():
            return Response({
                'status': 0,
                'message': _('Phone number already exists.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if email : 
        # Check if the email already exists in the User table
            if User.objects.filter(email=email).exists():
                return Response({
                    'status': 0,
                    'message': _('Email already exists.')
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

                user = User.objects.filter(username=username_or_phone).first() or \
                       User.objects.filter(phone=username_or_phone).first()

                if user and user.check_password(password):
                    if user.role == 1:
                        return Response({
                            'status': 0,
                            'message': _('You Can Not Login Here'),
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
                                'user':get_user_data(user, request),
                                'team':get_team_data(user, request),
                                'group':get_group_data(user, request),
                                'current_type':user.current_type,

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
                        'message': _('Invalid credentials'),
                    }, status=status.HTTP_400_BAD_REQUEST)

            elif login_type in [2, 3]:
                # Login with email, no password provided
                email = serializer.validated_data['username']

                user = User.objects.filter(email=email).first()

                if user:
                    # If the user already exists, log them in
                    if user.role == 1:
                        return Response({
                            'status': 0,
                            'message': _('You Can Not Login Here'),
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
                                'user':get_user_data(user, request),
                                'team':get_team_data(user, request),
                                'group':get_group_data(user, request),
                                'current_type':user.current_type,

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
                        'message': _("Email Does Not Exits Please Register First")
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

            # Blacklist the token or any other token management action if required
            # token = request.auth
            # if token:
            #     token.blacklist()  # If using token blacklisting
            
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

                print(f"Sending OTP {otp} to {phone}")

                return Response({
                    'status': 1,
                    'message': _('OTP sent to your phone.'),
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
            'message': _('Profile Image updated successfully.'),
            'data': {
                'user':get_user_data(user, request),
                'team':get_team_data(user, request),
                'group':get_group_data(user, request),
                'current_type':user.current_type,
            }
        }, status=status.HTTP_200_OK)


class EditProfileAPIView(APIView):
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        user = request.user
        
        return Response({
            'status': 1,
            'message': _('Player Details.'),
            'data': {
                'user':get_user_data(user, request),
                'team':get_team_data(user, request),
                'group':get_group_data(user, request),
                'current_type':user.current_type,
            }
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
                       'playing_foot', 'favourite_local_team', 'favourite_team',
                       'favourite_local_player', 'favourite_player']

        for field in null_fields:
            field_value = request.data.get(field)
            if field_value is None or field_value == '':
                setattr(user, field, None)  # Set the field to null if blank or None
            else:
                setattr(user, field, field_value)  # Otherwise, update with new value

        # Handle date_of_birth - retain old value if None or blank
        date_of_birth = request.data.get('date_of_birth')
        if date_of_birth not in [None, '', 'null']:
            try:
                user.date_of_birth = date_of_birth  # Assuming valid format
            except (ValueError, TypeError):
                return Response({
                    'status': 2,
                    'message': _('Invalid date format for date_of_birth.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Handle age - retain old value if None or blank
        age = request.data.get('age')
        if age not in [None, '', 'null']:
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
        if gender_id not in [None, '', 'null']:  # Ensure 'null' is also checked
            try:
                user.gender = UserGender.objects.get(id=gender_id)
            except UserGender.DoesNotExist:
                return Response({
                    'status': 2,
                    'message': _('Invalid gender specified.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Handle country - retain old value if None or blank
        country_id = request.data.get('country')
        if country_id not in [None, '', 'null']:
            try:
                user.country = Country.objects.get(id=country_id)
            except Country.DoesNotExist:
                return Response({
                    'status': 2,
                    'message': _('Invalid country specified.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Handle city - retain old value if None or blank
        city_id = request.data.get('city')
        if city_id not in [None, '', 'null']:
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
        # Get the page number from the body (default: 1)
        try:
            # Try to fetch and validate the page number
            page_number = request.data.get(self.page_query_param, 1)
            self.page = int(page_number)
            if self.page < 1:
                raise ValidationError("Page number must be a positive integer.")
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
        post_id = request.data.get('post_id')

        if not post_id:
            return Response({
                'status': 0,
                'message': _('Post ID is required.')
            }, status=400)

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Post not found.')
            }, status=404)

        # Toggle like/unlike
        creator_type = request.data.get('creator_type')
        created_by_id = request.data.get('created_by_id', request.user.id)  # Default to logged-in user ID

        post_like, created = PostLike.objects.get_or_create(created_by_id=created_by_id, post=post, creator_type=creator_type)
        
        if not created:
            # If the user already liked the post, unlike it (delete the like)
            post_like.delete()
            message = _('Post unliked successfully.')
        else:
            message = _('Post liked successfully.')

        # Serialize the post data with comments set to empty
        serializer = PostSerializer(post, context={'request': request})
        
        # Return the full post data with an empty comment list
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
        created_by_id = self.request.query_params.get('created_by_id')
        creator_type = self.request.query_params.get('creator_type')

        # Set default values if either parameter is missing
        if not created_by_id or not creator_type:
            created_by_id = self.request.user.id  # Default to the logged-in user’s ID
            creator_type = 1  # Default type

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

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            total_records = queryset.count()
            total_pages = self.paginator.page.paginator.num_pages

            return Response({
                'status': 1,
                'message': _('Posts fetched successfully.'),
                'data': serializer.data,
                'total_records': total_records,
                'total_pages': total_pages,
                'current_page': self.paginator.page.number
            }, status=status.HTTP_200_OK)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response({
            'status': 1,
            'message': _('Posts fetched successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


######################### POST CREATE API ###########################################
class PostCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get created_by_id and creator_type from request data
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

            if "image" in request.FILES:
                image = request.FILES["image"]
                file_extension = image.name.split('.')[-1]
                unique_suffix = get_random_string(8)
                file_name = f"post_images/{post.id}_{created_by_id}_{creator_type}_{unique_suffix}.{file_extension}"
                image_path = default_storage.save(file_name, image)
                post.image = image_path
                post.save()
            
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

        post_id = request.data.get('post_id')
        if not post_id:
            return Response({
                'status': 0,
                'message': _('Post ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        post = self.get_object(post_id)
        serializer = self.get_serializer(post, data=request.data, partial=True)

        if serializer.is_valid():
            if 'image' in request.FILES:
                if post.image and default_storage.exists(post.image.name):
                    default_storage.delete(post.image.name)

                image = request.FILES['image']
                file_extension = image.name.split('.')[-1]
                unique_suffix = get_random_string(8)
                file_name = f"post_images/{post.id}_{created_by_id}_{creator_type}_{unique_suffix}.{file_extension}"
                image_path = default_storage.save(file_name, image)
                post.image = image_path

            serializer.save()
            return Response({
                'status': 1,
                'message': _('Post updated successfully.'),
                'data': serializer.data
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
        created_by_id = request.data.get('created_by_id', request.user.id)  # Default to logged-in user ID

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
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        data = request.data
        post_id = data.get('post_id')
        comment_text = data.get('comment')
        parent_id = data.get('parent_id')
        created_by_id = data.get('created_by_id')
        creator_type = data.get('creator_type')

        # Validate the required fields
        if not post_id or not comment_text or not created_by_id or not creator_type:
            return Response({
                'status': 0,
                'message': _('post_id, comment, created_by_id and creator_type are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

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

        # Create the comment using the new fields
        comment = Post_comment.objects.create(
            created_by_id=created_by_id,
            creator_type=creator_type,
            post=post,
            comment=comment_text,
            parent=parent_comment
        )

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
        user_roles = Role.objects.filter(id__in=[3, 4, 6])  # Filter for roles with IDs 3, 4, or 6
        serializer = UserRoleSerializer(user_roles, many=True)

        # Prepare the response with roles directly under 'data'
        return Response({
            'status': 1,
            'message': _('User Profiles retrieved successfully.'),
            'data': serializer.data  # Directly include the serialized data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract the profile type from the request data
        profile_type = request.data.get('profile_type')
        certificates = request.FILES.getlist('certificates')  # Get the list of uploaded files

        # Assuming the user is already authenticated and you have access to the user object
        user = request.user

        # Check if the user is already a coach or referee
        if user.is_coach and profile_type == '3':
            return Response({
                'status': 0,
                'message': _('You are already registered as a coach and cannot create a new coach profile.')
            }, status=status.HTTP_400_BAD_REQUEST)

        if user.is_referee and profile_type == '4':
            return Response({
                'status': 0,
                'message': _('You are already registered as a referee and cannot create a new referee profile.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Set profile type flags and store certificates
        if profile_type == '3':  # Profile type for coach
            user.is_coach = True
            user.is_referee = False

            # Handle saving certificates for coach
            coach_certificates = []
            for cert in certificates:
                # Create the directory path
                directory_path = os.path.join('media', coach_directory_path(user, ''))
                os.makedirs(directory_path, exist_ok=True)  # Create the directory if it doesn't exist

                # Save the file to the desired path
                file_path = os.path.join(directory_path, cert.name)
                with open(file_path, 'wb+') as destination:
                    for chunk in cert.chunks():
                        destination.write(chunk)
                coach_certificates.append(cert.name)

            user.coach_certificate = ','.join(coach_certificates)

        elif profile_type == '4':  # Profile type for referee
            user.is_referee = True
            user.is_coach = False

            # Handle saving certificates for referee
            referee_certificates = []
            for cert in certificates:
                # Create the directory path
                directory_path = os.path.join('media', referee_directory_path(user, ''))
                os.makedirs(directory_path, exist_ok=True)  # Create the directory if it doesn't exist

                # Save the file to the desired path
                file_path = os.path.join(directory_path, cert.name)
                with open(file_path, 'wb+') as destination:
                    for chunk in cert.chunks():
                        destination.write(chunk)
                referee_certificates.append(cert.name)

            user.referee_certificate = ','.join(referee_certificates)

        # Save the user instance
        user.save()

        return Response({
            'status': 1,
            'message': _('Profile type and certificates uploaded successfully.'),
            'data': {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'is_coach': user.is_coach,
                'is_referee': user.is_referee,
                'coach_certificate': user.coach_certificate if user.is_coach else None,
                'referee_certificate': user.referee_certificate if user.is_referee else None,
            }
        }, status=status.HTTP_201_CREATED)


def coach_directory_path(instance, filename):
    return f'certificates/coach/{instance.id}/{filename}'

def referee_directory_path(instance, filename):
    return f'certificates/referee/{instance.id}/{filename}'





################################ album and gallary ######################################################################################################################
class CustomMediaPagination(PageNumberPagination):
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    page_size = 30  # Number of records per page
    page_query_param = 'page'  # Custom page number param in the body
    page_size_query_param = 'page_size'
    max_page_size = 100  # Set max size if needed

    def paginate_queryset(self, queryset, request, view=None):
        # Get the page number from the body (default: 1)
        try:
            # Try to fetch and validate the page number
            page_number = request.data.get(self.page_query_param, 1)
            self.page = int(page_number)
            if self.page < 1:
                raise ValidationError("Page number must be a positive integer.")
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

    def get_queryset(self):
        album_id = self.request.query_params.get('album_id')  # Fetch album_id from the request body

        if album_id:
            # Ensure that the album belongs to the user or team
            return Album.objects.filter(id=album_id)
        return Album.objects.none()  # Return an empty queryset if no album_id is provided

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        queryset = self.get_queryset()  # Get the queryset
        if not queryset.exists():  # Check if the queryset is empty
            return Response({
                'status': 0,
                'message': _("Album Id is required or Album not found."),
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(queryset, many=True)  # Serialize all albums

        return Response({
            'status': 1,
            'message': _('Albums fetched successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)




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
        created_by_id = request.data.get('creator_type_id')

        # Check if creator_type is provided
        if not creator_type:
            return Response({
                'status': 0,
                'message': 'creator_type is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convert creator_type to int and strip created_by_id if provided
        try:
            creator_type = int(creator_type.strip())
            created_by_id = int(created_by_id.strip()) if created_by_id else None
        except (ValueError, TypeError):
            return Response({
                'status': 0,
                'message': 'creator_type and creator_type_id must be valid integers.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate created_by_id based on creator_type
        if creator_type == Album.USER_TYPE:
            created_by_id = request.user.id  # Set created_by_id to logged-in user's ID
        elif creator_type == Album.TEAM_TYPE:
            if not Team.objects.filter(id=created_by_id).exists():
                return Response({
                    'status': 0,
                    'message': 'For TEAM_TYPE, created_by_id must correspond to an existing Team.'
                }, status=status.HTTP_400_BAD_REQUEST)
        elif creator_type == Album.GROUP_TYPE:
            if not TrainingGroups.objects.filter(id=created_by_id).exists():
                return Response({
                    'status': 0,
                    'message': 'For GROUP_TYPE, created_by_id must correspond to an existing Group.'
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
                            'message': 'Gallery entry creation failed.',
                            'errors': gallary_serializer.errors
                        }, status=status.HTTP_400_BAD_REQUEST)

            album_data = DetailAlbumSerializer(album_instance).data
            return Response({
                'status': 1,
                'message': 'Detailed Albums added successfully.',
                'data': [album_data]
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 0,
            'message': 'Album creation failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
########### only album list ################

class AlbumListAPIView(generics.ListAPIView):
    serializer_class = AlbumSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = CustomMediaPagination 

    def get_queryset(self):
        creator_type = self.request.query_params.get('creator_type', None)
        created_by_id = self.request.query_params.get('created_by_id', None)

        queryset = Album.objects.all()

        # Validate creator_type and created_by_id
        if creator_type is not None:
            try:
                creator_type = int(creator_type)
                if creator_type not in [Album.USER_TYPE, Album.TEAM_TYPE, Album.GROUP_TYPE]:
                    raise ValueError("Invalid creator_type.")
            except (ValueError, TypeError):
                raise Exception("creator_type must be a valid integer.")
            
            queryset = queryset.filter(creator_type=creator_type)

        if created_by_id is not None:
            try:
                created_by_id = int(created_by_id)
                if creator_type == Album.TEAM_TYPE:
                    if not Team.objects.filter(id=created_by_id).exists():
                        raise Exception("For TEAM_TYPE, created_by_id must correspond to an existing Team.")
                elif creator_type == Album.GROUP_TYPE:
                    if not TrainingGroups.objects.filter(id=created_by_id).exists():
                        raise Exception("For GROUP_TYPE, created_by_id must correspond to an existing Group.")
                # For USER_TYPE, you can check if created_by_id is the logged-in user
                elif creator_type == Album.USER_TYPE and created_by_id != self.request.user.id:
                    raise Exception("For USER_TYPE, created_by_id must match the logged-in user.")
            except (ValueError, TypeError):
                raise Exception("created_by_id must be a valid integer.")

            queryset = queryset.filter(created_by_id=created_by_id)

        return queryset

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
                    'user': request.user.id,
                    'team_id': album_data['created_by_id'] if album_data['creator_type'] == Album.TEAM_TYPE else None,
                    'group_id': album_data['created_by_id'] if album_data['creator_type'] == Album.GROUP_TYPE else None,
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

        if not creator_type:
            return Response({
                'status': 0,
                'message': _('creator_type is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = GetGallarySerializer(data=request.data)
        if serializer.is_valid():
            # Fetch album instance if album_id is provided
            album_instance = None
            if album_id:
                try:
                    album_instance = Album.objects.get(id=album_id)
                except Album.DoesNotExist:
                    return Response({
                        'status': 0,
                        'message': _("Album not found."),
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Validate the creator_type
            creator_type = int(creator_type)
            if creator_type not in [Gallary.USER_TYPE, Gallary.TEAM_TYPE, Gallary.GROUP_TYPE]:
                return Response({
                    'status': 0,
                    'message': _("Invalid creator type."),
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check permissions based on creator type
            if creator_type == Gallary.USER_TYPE and created_by_id != request.user.id:
                return Response({
                    'status': 0,
                    'message': _("You can only create a gallary for yourself."),
                }, status=status.HTTP_400_BAD_REQUEST)

            elif creator_type == Gallary.TEAM_TYPE:
                if not Team.objects.filter(id=created_by_id).exists():
                    print("vbn",Team.id)
                    print("dfgdf",created_by_id)
                    print(Team.objects.filter(id=created_by_id).exists())
                    return Response({
                        'status': 0,
                        'message': _("Invalid team ID."),
                    }, status=status.HTTP_400_BAD_REQUEST)

            elif creator_type == Gallary.GROUP_TYPE:
                if not TrainingGroups.objects.filter(id=created_by_id).exists():
                    return Response({
                        'status': 0,
                        'message': _("Invalid group ID."),
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Save the gallary entry
            gallary = serializer.save(created_by_id=created_by_id, creator_type=creator_type, album_id=album_instance)

            return Response({
                'status': 1,
                'message': _('gallary entry created successfully.'),
                'data': GetGallarySerializer(gallary).data,
                # 'team_id': created_by_id if creator_type == Gallary.TEAM_TYPE else None,
                # 'group_id': created_by_id if creator_type == Gallary.GROUP_TYPE else None
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 0,
            'message': _('Failed to create gallary entry.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)    
###########gallary list latest 9 ################

class LatestGallaryListAPIView(generics.ListCreateAPIView):
    serializer_class = GetGallarySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
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
                'created_at': album.get('created_at'),
                'updated_at': album.get('updated_at'),
                'creator_type': album.get('creator_type'),  # Use album object here
                'created_by_id': album.get('created_by_id')
            }
            for album in album_serializer.data
            if (creator_type == str(Album.TEAM_TYPE) and album['creator_type'] == Album.TEAM_TYPE) or
               (creator_type == str(Album.GROUP_TYPE) and album['creator_type'] == Album.GROUP_TYPE) or
               (creator_type == str(Album.USER_TYPE) and album['creator_type'] == Album.USER_TYPE)
        ]

        return Response({
            'status': 1,
            'message': _('gallary entries and latest albums fetched successfully.'),
            'data': {
                'images': formatted_images,
                'videos': formatted_videos,
                'albums': formatted_albums,
            },
        }, status=status.HTTP_200_OK)


###########  gallary list delete ################


class GallaryDeleteAPIView(generics.DestroyAPIView):
    queryset = Gallary.objects.all()
    serializer_class = GallarySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_object(self):
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
            raise ({"message": _("gallary entry not found.")})

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
                'message': _('gallary entry deleted successfully.')
            }, status=status.HTTP_200_OK)

        except Gallary.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('gallary entry not found.')
            }, status=status.HTTP_404_NOT_FOUND)
        
###########  album list delete ################

class AlbumDeleteAPIView(generics.DestroyAPIView):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    permission_classes = [IsAuthenticated]

    def get_object(self):
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
    queryset = Report.objects.all()
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
    queryset = PostReport.objects.all()
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
        ground_type = GroundMaterial.objects.all()

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
        
        if serializer.is_valid():
            field_instance = serializer.save()

            # Handle image upload
            if 'image' in request.FILES:
                image = request.FILES['image']
                # Save the new image with a structured filename
                file_extension = image.name.split('.')[-1]
                file_name = f"fields_images/{field_instance.field_name}_{field_instance.id}.{file_extension}"

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



class TournamentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Fetch all fields for the current user
        fields = Field.objects.filter(user_id=request.user)

        # Construct the response data manually
        fields_data = [{'id': field.id, 'field_name': field.field_name} for field in fields]

        return Response({
            'status': 1,
            'message': _('Fields retrieved successfully.'),
            'data': fields_data
        }, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Handle tournament creation with logo upload
        serializer = TournamentSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            tournament_instance = serializer.save()

            # Handle logo upload
            if 'logo' in request.FILES:
                logo = request.FILES['logo']
                # Save the new logo with a structured filename
                file_extension = logo.name.split('.')[-1]
                file_name = f"tournament_logo/{tournament_instance.tournament_name}_{tournament_instance.id}.{file_extension}"

                # Save the logo and update the instance
                logo_path = default_storage.save(file_name, logo)
                tournament_instance.logo = logo_path
                tournament_instance.save()

            return Response({
                'status': 1,
                'message': _('Tournament created successfully.'),
                'data': TournamentSerializer(tournament_instance).data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'status': 0,
                'message': _('Tournament creation failed.'),
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)



#################################################################### Trainnig Group API #########################################################################################
class TrainingGroupAPI(APIView):
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    # 1. Get Group Detail by ID
    def get(self, request):
        group_id = request.query_params.get('group_id')
        if not group_id:
            return Response({
                'status': 0, 
                'message': _('Group ID is required.')
                },status=status.HTTP_400_BAD_REQUEST)
        
        try:
            group = TrainingGroups.objects.get(id=group_id)
            serializer = TrainingGroupSerializer(group)
            return Response({
                'status': 1,
                'message': _('Group details retrieved successfully.'),
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except TrainingGroups.DoesNotExist:
            return Response({
                'status': 0, 
                'message': _('Group not found.')
                }, status=status.HTTP_404_NOT_FOUND)
    
    # 2. Create a Group
    def post(self, request):
        request.data['group_founder'] = request.user.id  # Set the logged-in user as the group founder
        serializer = TrainingGroupSerializer(data=request.data)
        
        if serializer.is_valid():
            group = serializer.save(created_at=now(), updated_at=now())

            # Handle group_logo upload
            if 'group_logo' in request.FILES:
                logo = request.FILES['group_logo']
                file_extension = logo.name.split('.')[-1]
                file_name = f"group/group_logo/{group.id}_{get_random_string(8)}.{file_extension}"
                logo_path = default_storage.save(file_name, logo)
                group.group_logo = logo_path

            # Handle group_background_image upload
            if 'group_background_image' in request.FILES:
                background_image = request.FILES['group_background_image']
                file_extension = background_image.name.split('.')[-1]
                file_name = f"group/group_background_image/{group.id}_{get_random_string(8)}.{file_extension}"
                background_image_path = default_storage.save(file_name, background_image)
                group.group_background_image = background_image_path

            group.save()  # Save logo and background image fields
            return Response({
                'status': 1,
                'message': _('Group created successfully.'),
                'data': TrainingGroupSerializer(group).data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'status': 0,
                'message': _('Failed to create group.'),
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    
    # 3. Update Group Logo and Background Image
    def patch(self, request):
        group_id = request.data.get('group_id')
        if not group_id:
            return Response({
                'status': 0, 
                'message': _('Group ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            group = TrainingGroups.objects.get(id=group_id, group_founder=request.user)
            
            # Update group fields based on request data, retaining old values if not provided
            fields_to_update = [
                'group_name', 'group_username', 'bio', 'latitude', 'longitude',
                'address', 'house_no', 'premises', 'street', 'city',
                'state', 'country_name', 'postalCode', 'country_code', 'phone'
            ]

            for field in fields_to_update:
                new_value = request.data.get(field)
                if new_value is not None:  # Only update if a new value is provided
                    setattr(group, field, new_value)

            # Handle group_logo update and delete old one if exists
            if 'group_logo' in request.FILES:
                if group.group_logo and default_storage.exists(group.group_logo.name):
                    default_storage.delete(group.group_logo.name)
                logo = request.FILES['group_logo']
                file_extension = logo.name.split('.')[-1]
                file_name = f"group/group_logo/{group_id}_{get_random_string(8)}.{file_extension}"
                logo_path = default_storage.save(file_name, logo)
                group.group_logo = logo_path

            # Handle group_background_image update
            if 'group_background_image' in request.FILES:
                if group.group_background_image and default_storage.exists(group.group_background_image.name):
                    default_storage.delete(group.group_background_image.name)
                background_image = request.FILES['group_background_image']
                file_extension = background_image.name.split('.')[-1]
                file_name = f"group/group_background_image/{group_id}_{get_random_string(8)}.{file_extension}"
                background_image_path = default_storage.save(file_name, background_image)
                group.group_background_image = background_image_path

            # No need to get user from request data; it's already part of the group
            user = group.group_founder  

            group.updated_at = timezone.now()  # Set updated_at to the current time
            group.save()  # Save the group instance

            return Response({
                'status': 1,
                'message': _('Group updated successfully.'),
                'data': {
                    'group_id': group.id,
                    'group_name': group.group_name,
                    'group_username': group.group_username,
                    'group_founder': {
                        'username': user.username,
                        'fullname': user.fullname,
                        'phone': user.phone,
                        'email': user.email,
                        'profile_pic': user.profile_picture.url if user.profile_picture else None,  # Use the correct field name
                    },
                    'bio': group.bio,
                    'latitude': group.latitude,
                    'longitude': group.longitude,
                    'address': group.address,
                    'house_no': group.house_no,
                    'premises': group.premises,
                    'street': group.street,
                    'city': group.city,
                    'state': group.state,
                    'country_name': group.country_name,
                    'postalCode': group.postalCode,
                    'country_code': group.country_code,
                    'phone': group.phone,
                    'group_logo': group.group_logo.url if group.group_logo else None,
                    'group_background_image': group.group_background_image.url if group.group_background_image else None,
                    'updated_at': group.updated_at,
                }
            }, status=status.HTTP_200_OK)

        except TrainingGroups.DoesNotExist:
            return Response({
                'status': 0, 
                'message': _('Group not found or you are not the founder.')
            }, status=status.HTTP_404_NOT_FOUND)


##################################################################### User Gender List API View ##############################################################################
class UserGenderListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserGender.objects.all()
    serializer_class = UserGenderSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        # Get all genders
        user_genders = self.get_queryset()
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
    queryset = PlayingPosition.objects.all()
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


#######################################################  USER ROLE API LIST VIEW #############################################################################################

class UserRoleListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Role.objects.all()
    serializer_class = UserRoleSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
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
    def post(self, request):
        creator_type = request.data.get('creator_type')
        created_by_id = request.data.get('created_by_id')
        target_id = request.data.get('target_id')
        target_type = request.data.get('target_type')

        try:
            follow_request = FollowRequest.objects.get(
                created_by_id=created_by_id,
                creator_type=creator_type,
                target_id=target_id,
                target_type=target_type
            )
            # If follow request exists, unfollow
            follow_request.delete()
            return Response({
                'status': 1,
                'message': 'Unfollowed successfully.',
                'data': {}
            }, status=status.HTTP_200_OK)
        except FollowRequest.DoesNotExist:
            # Follow request does not exist, create one
            FollowRequest.objects.create(
                created_by_id=created_by_id,
                creator_type=creator_type,
                target_id=target_id,
                target_type=target_type
            )
            return Response({
                'status': 1,
                'message': 'Followed successfully.',
            }, status=status.HTTP_201_CREATED)


####################################### LIST OF FOLLOWERS #######################################
class ListFollowersAPI(generics.ListAPIView):
    def get_queryset(self):
        target_id = self.request.query_params.get('target_id')
        target_type = self.request.query_params.get('target_type')
        return FollowRequest.objects.filter(target_id=target_id, target_type=target_type)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        followers = []

        for follow in queryset:
            if follow.creator_type == FollowRequest.USER_TYPE:
                user = User.objects.get(id=follow.created_by_id)
                followers.append({
                    'creator_type': 1,
                    'creator_id': user.id,
                    'username': user.username,
                    'profile': user.profile_picture.url if user.profile_picture else None
                })
            elif follow.creator_type == FollowRequest.TEAM_TYPE:
                team = Team.objects.get(id=follow.created_by_id)
                followers.append({
                    'creator_type': 2,
                    'creator_id': team.id,
                    'username': team.team_username,
                    'profile': team.team_logo.url if team.team_logo else None
                })
            elif follow.creator_type == FollowRequest.GROUP_TYPE:
                group = TrainingGroups.objects.get(id=follow.created_by_id)
                followers.append({
                    'creator_type': 3,
                    'creator_id': group.id,
                    'username': group.group_username,
                    'profile': group.group_logo.url if group.group_logo else None
                })

        return Response({
            'status': 1,
            'message': 'Followers fetched successfully.',
            'data': followers
        }, status=status.HTTP_200_OK)


##################################### LIST OF FOLLOWING #######################################
class ListFollowingAPI(generics.ListAPIView):
    def get_queryset(self):
        creator_type = self.request.query_params.get('creator_type')
        created_by_id = self.request.query_params.get('created_by_id')
        return FollowRequest.objects.filter(creator_type=creator_type, created_by_id=created_by_id)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        following = []

        for follow in queryset:
            if follow.target_type == FollowRequest.USER_TYPE:
                user = User.objects.get(id=follow.target_id)
                following.append({
                    'creator_type': 1,
                    'creator_id': user.id,
                    'username': user.username,
                    'profile': user.profile_picture.url if user.profile_picture else None
                })
            elif follow.target_type == FollowRequest.TEAM_TYPE:
                team = Team.objects.get(id=follow.target_id)
                following.append({
                    'creator_type': 2,
                    'creator_id': team.id,
                    'username': team.team_username,
                    'profile': team.team_logo.url if team.team_logo else None
                })
            elif follow.target_type == FollowRequest.GROUP_TYPE:
                group = TrainingGroups.objects.get(id=follow.target_id)
                following.append({
                    'creator_type': 3,
                    'creator_id': group.id,
                    'username': group.group_username,
                    'profile': group.group_logo.url if group.group_logo else None
                })

        return Response({
            'status': 1,
            'message': 'Following list fetched successfully.',
            'data': following
        }, status=status.HTTP_200_OK)


##################################### Mobile Dashboard Image #######################################

class DashboardImageAPI(APIView):
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated
    parser_classes = (JSONParser, MultiPartParser, FormParser)  # Handle various parsers (for file uploads, if needed)

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
            
        banners = MobileDashboardBanner.objects.all()
        serializer = MobileDashboardBannerSerializer(banners, many=True)
        
     
    
        return Response({
            "status": 1,
            "message": _("Dashboard banner list fetched successfully."),
            "data": serializer.data
        }, status=status.HTTP_200_OK)


####################################################################### Event Moodule #############################################################################################

###################### Event LIKE ##################################
class EventLikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        event_id = request.data.get('event_id')

        if not event_id:
            return Response({
                'status': 0,
                'message': _('Event id is required.')
            }, status=400)

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Event not found.')
            }, status=404)

        # Toggle like/unlike
        event_like, created = EventLike.objects.get_or_create(user=request.user, event=event)
        if not created:
            # If the user already liked the post, unlike it (delete the like)
            event_like.delete()
            message = _('Event unliked successfully.')
        else:
            message = _('Event liked successfully.')

        # Serialize the post data with comments set to empty
        serializer = EventSerializer(event, context={'request': request})
        
        # Return the full post data with an empty comment list
        return Response({
            'status': 1,
            'message': message,
            'data': serializer.data
        }, status=200)
    

################################ Get comment of EVENT API #############################
class EventCommentPagination(CustomPostPagination):
    def paginate_queryset(self, queryset, request, view=None):
        return super().paginate_queryset(queryset, request, view)

class EventCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Validate event_id from request data
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

        # Get the top-level comments for the event
        comments = Event_comment.objects.filter(event=event, parent=None).order_by('-date_created')

        # Paginate the comments
        paginator = EventCommentPagination()
        paginated_comments = paginator.paginate_queryset(comments, request)

        # If pagination fails or no comments are found
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

        # Use a serializer to serialize the paginated comments (not the pagination class)
        serializer = EventCommentSerializer(paginated_comments, many=True)

        # Return paginated response
        return Response({
            'status': 1,
            'message': _('Comments fetched successfully.'),
            'data': serializer.data,
            'total_records': comments.count(),
            'total_pages': paginator.page.paginator.num_pages,
            'current_page': paginator.page.number,
        }, status=status.HTTP_200_OK)



######################## COMMNET CREATE API ###########################
class EventCommentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def post(self, request, *args, **kwargs):
        # Set the language based on headers
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract data from request
        data = request.data
        event_id = data.get('event_id')
        comment_text = data.get('comment')
        parent_id = data.get('parent_id')
       
        # Validate that event_id and comment are provided
        if not event_id or not comment_text:
            return Response({
                'status': 0,
                'message': _('event_id and comment are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Post not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Handle parent comment (if it's a reply)
        parent_comment = None
        if parent_id:
            try:
                parent_comment = Event_comment.objects.get(id=parent_id)
            except Event_comment.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Parent comment not found.')
                }, status=status.HTTP_404_NOT_FOUND)


        # Comment is from the user
        comment = Event_comment.objects.create(
            user=request.user,
            event=event,
            comment=comment_text,
            parent=parent_comment
        )

        # Return the response with comment details including the entity (team, group, or user)
        return Response({
            'status': 1,
            'message': _('Comment created successfully.'),
            'data': EventCommentSerializer(comment).data  # Return serialized comment data
        }, status=status.HTTP_201_CREATED)





##################################### Event #######################################

class CustomEventPagination(PageNumberPagination):
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

class EventsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        paginator = CustomEventPagination()
        try:
            events = Event.objects.all()
            paginated_events = paginator.paginate_queryset(events, request, view=self)
            serializer = EventSerializer(paginated_events, many=True)

            # Return paginated response with pagination details
            return Response({
                'status': 1,
                'message': _('All Events fetched successfully.'),
                'data': serializer.data,
                'total_records': paginator.page.paginator.count,
                'total_pages': paginator.total_pages,
                'current_page': paginator.page.number
            })
        
         

        except Exception as e:
            return Response({
                'status': 0,
                'message': _('Error occurred while fetching event list.'),
                'error': str(e),
                'data':[]
            }, status=status.HTTP_400_BAD_REQUEST)

class TeamEventAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated
    parser_classes = (JSONParser, MultiPartParser, FormParser)  # Handle various parsers (for file uploads, if needed)

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get the team_id from query parameters
        team_id = request.query_params.get('team_id', None)

        # Return error if team_id is not provided
        if not team_id:
            return Response({
                "status": 0,
                "message": _("Team id is required."),
            }, status=status.HTTP_400_BAD_REQUEST)

        paginator = CustomEventPagination()  # Initialize the custom pagination

        try:
            # Filter events by team_id
            events = Event.objects.filter(team=team_id)

            # Paginate the queryset
            paginated_events = paginator.paginate_queryset(events, request, view=self)

            # If pagination returns None, it means the page was invalid
            if paginated_events is None:
                return Response({
                    'status': 0,
                    'message': _('Page not found.'),
                    'data': []
                }, status=status.HTTP_400_BAD_REQUEST)

            # Serialize the paginated events
            serializer = EventSerializer(paginated_events, many=True)

            # Return paginated response with pagination details
            return Response({
                'status': 1,
                'message': _("Event list fetched successfully."),
                'data': serializer.data,
                'total_records': paginator.page.paginator.count,
                'total_pages': paginator.total_pages,
                'current_page': paginator.page.number
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': 0,
                'message': _('Error occurred while fetching event list.'),
                'error': str(e),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
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

class EventCreateAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Fetch all event types
        event_types = EventType.objects.all()
        serializer = EventTypeSerializer(event_types, many=True, context={'request': request})

        return Response({
            'status': 1,
            'message': _('Events retrieved successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Ensure team_id is provided
        team_id = request.data.get('team')
        if not team_id:
            return Response({
                'status': 0,
                'message': _('Team ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the Team instance using the provided team_id
            team_instance = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Team not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Handle event creation
        serializer = EventSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # Set the team instance on the validated data before saving
            event_instance = serializer.save(team=team_instance)

            return Response({
                'status': 1,
                'message': _('Event created successfully.'),
                'data': EventSerializer(event_instance).data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'status': 0,
                'message': _('Event creation failed.'),
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class UpdateEventAPIView(APIView):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)


    def get_object(self, event_id):
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
                file_name = f"event_images/{event.id}_{request.user.username}_{unique_suffix}.{file_extension}"
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



class EventBookingDetailView(APIView):
  def get(self, request, *args, **kwargs):
        # Fetch event_id from query parameters
        event_id = request.query_params.get("event_id")
        
        if not event_id:
            return Response({"error": "event_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the event by ID
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"detail": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the event data
        serializer = EventSerializer(event)
        return Response({
                'status': 1,
                'message': _('Event Booking Detail Fetched successfully.'),
                'data': serializer.data
            }, status=status.HTTP_200_OK)

       

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
        try:
            event_instance = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Event not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Prepare data for booking creation
        booking_data = {
            'event': event_instance.id,
            'tickets': request.data.get('tickets'),
            'convenience_fee': request.data.get('convenience_fee', 0.0),
            'ticket_amount': request.data.get('ticket_amount', 0.0),
            'total_amount': request.data.get('total_amount', 0.0),
        }

        # Handle booking creation using the serializer
        serializer = self.get_serializer(data=booking_data)

        if serializer.is_valid():
            booking_instance = serializer.save()
            return Response({
                'status': 1,
                'message': _('Booking created successfully.'),
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'status': 0,
                'message': _('Booking creation failed.'),
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        





# class DeleteEventAPIView(APIView):

#     def get_object(self, event_id):
#         try:
#             return Event.objects.get(id=event_id, event_organizer=self.request.user)
#         except Event.DoesNotExist:
#             return None

#     def delete(self, request, *args, **kwargs):
#         language = request.headers.get('Language', 'en')
#         if language in ['en', 'ar']:
#             activate(language)

#         event_id = request.data.get('event_id')
#         if not event_id:
#             return Response({
#                 'status': 0,
#                 'message': _('Event ID is required.')
#             }, status=status.HTTP_400_BAD_REQUEST)

#         event = self.get_object(event_id)
#         if not event:
#             return Response({
#                 'status': 0,
#                 'message': _('Event not found or you are not authorized to delete this event.')
#             }, status=status.HTTP_404_NOT_FOUND)

#         # Optionally delete the associated event image
#         if event.event_image and default_storage.exists(event.event_image.name):
#             default_storage.delete(event.event_image.name)

#         event.delete()
#         return Response({
#             'status': 1,
#             'message': _('Event deleted successfully.')
#         }, status=status.HTTP_200_OK)






############################################################### FAQ API #####################################################################################################
class FAQListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
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
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        general_settings = SystemSettings.objects.first()

        if not general_settings:
            return Response({
                'status': 0,
                'message': _('No general settings found.'),
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'status': 1,
            'message': _('General Settings retrieved successfully.'),
            'data': {
                'website_name_english': general_settings.website_name_english,
                'website_name_arabic': general_settings.website_name_arabic,
                'phone': general_settings.phone,
                'email': general_settings.email,
                'address': general_settings.address,
                'currency_symbol': general_settings.currency_symbol,
                'event_convenience_fee': general_settings.event_convenience_fee,
                'instagram': general_settings.instagram,
                'facebook': general_settings.facebook,
                'twitter': general_settings.twitter,
                'linkedin': general_settings.linkedin,
                'pinterest': general_settings.pinterest,
                'happy_user': general_settings.happy_user,
                'line_of_code': general_settings.line_of_code,
                'downloads': general_settings.downloads,
                'app_rate': general_settings.app_rate,
                'years_of_experience': general_settings.years_of_experience,
                'project_completed': general_settings.project_completed,
                'proffesioan_team_members': general_settings.proffesioan_team_members,
                'awards_winning': general_settings.awards_winning,
            }
        }, status=status.HTTP_200_OK)
