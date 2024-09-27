from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext as _
from django.utils.translation import activate
from django import views
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from FutureStar_App.models import *
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
import random
from django.db import IntegrityError
from django.utils import timezone
import os
from django.conf import settings
from django.core.files.storage import default_storage

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Get the registration type (1 for normal, 2 or 3 for email-based)
        registration_type = request.data.get('type')
        device_type = request.data.get('device_type')
        device_token = request.data.get('device_token')

        if registration_type == 1:
            # Normal registration with username, phone, and password
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                try:
                    user = serializer.save()
                    user.device_type = device_type
                    user.device_token = device_token
                    user.last_login = timezone.now()
                    user.save()

                    # Automatically log in the user by generating a token
                    refresh = RefreshToken.for_user(user)

                    return Response({
                        'status': 1,
                        'message': _('User registered and logged in successfully'),
                        'data': {
                            'refresh_token': str(refresh),
                            'access_token': str(refresh.access_token),
                            'user': {
                                'id': user.id,
                                'username': user.username,
                                'phone': user.phone,
                                'email': user.email,
                                'device_type': user.device_type,
                                'device_token': user.device_token,
                            }
                        }
                    }, status=status.HTTP_201_CREATED)

                except IntegrityError as e:
                    return Response({
                        'status': 0,
                        'message': _('User registration failed due to duplicate data'),
                        'errors': str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'status': 0,
                'message': _('User registration failed'),
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        elif registration_type in [2, 3]:
            # Email registration (no password provided)
            email = request.data.get('email')
            if not email:
                return Response({
                    'status': 0,
                    'message': _('Email is required for registration')
                }, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(email=email).first()

            if user:
                # If the user exists, log them in
                if user.is_active:
                    user.device_type = device_type
                    user.device_token = device_token
                    user.last_login = timezone.now()
                    user.save()

                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'status': 1,
                        'message': _('User logged in successfully'),
                        'data': {
                            'refresh_token': str(refresh),
                            'access_token': str(refresh.access_token),
                            'user': {
                                'id': user.id,
                                'username': user.username,
                                'phone': user.phone,
                                'email': user.email,
                                'device_type': user.device_type,
                                'device_token': user.device_token,
                            }
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': 0,
                        'message': _('Account is inactive')
                    }, status=status.HTTP_400_BAD_REQUEST)

            else:
                # Generate a random password manually
                user = User.objects.create_user(
                    username=email.split('@')[0],
                    email=email,
                    password=email.split('@')[0],
                    is_active=True  # Adjust this if you need email verification
                )
                user.device_type = device_type
                user.device_token = device_token
                user.last_login = timezone.now()
                user.save()

                refresh = RefreshToken.for_user(user)

                return Response({
                    'status': 1,
                    'message': _('User created and logged in successfully'),
                    'data': {
                        'refresh_token': str(refresh),
                        'access_token': str(refresh.access_token),
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'phone': user.phone,
                            'email': user.email,
                            'device_type': user.device_type,
                            'device_token': user.device_token,
                        }
                    }
                }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 0,
            'message': _('Invalid registration type')
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

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
                username_or_phone = serializer.validated_data['username_or_phone']
                password = serializer.validated_data['password']

                user = User.objects.filter(username=username_or_phone).first() or \
                       User.objects.filter(phone=username_or_phone).first()

                if user and user.check_password(password):
                    if user.is_active:
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
                                'user': {
                                    'id': user.id,
                                    'username': user.username,
                                    'phone': user.phone,
                                    'email': user.email,
                                    'device_type': user.device_type,
                                    'device_token': user.device_token,
                                }
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
                email = serializer.validated_data['email']

                user = User.objects.filter(email=email).first()

                if user:
                    # If the user already exists, log them in
                    if user.is_active:
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
                                'user': {
                                    'id': user.id,
                                    'username': user.username,
                                    'phone': user.phone,
                                    'email': user.email,
                                    'device_type': user.device_type,
                                    'device_token': user.device_token,
                                }
                            }
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response({
                            'status': 0,
                            'message': _('Account is inactive'),
                        }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Create new user with random password if email doesn't exist
                    user = User.objects.create_user(
                        username=email.split('@')[0],
                        email=email,
                        password=email.split('@')[0],
                        is_active=True  # You can adjust if you need email verification
                    )
                    user.device_type = device_type
                    user.device_token = device_token
                    user.last_login = timezone.now()
                    user.save()

                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'status': 1,
                        'message': _('User created and login successful'),
                        'data': {
                            'refresh_token': str(refresh),
                            'access_token': str(refresh.access_token),
                            'user': {
                                'id': user.id,
                                'username': user.username,
                                'phone': user.phone,
                                'email': user.email,
                                'device_type': user.device_type,
                                'device_token': user.device_token,
                            }
                        }
                    }, status=status.HTTP_201_CREATED)
        return Response({
            'status': 0,
            'message': _('Invalid data'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

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
            }, status=status.HTTP_205_RESET_CONTENT)

        except Exception as e:
            return Response({
                'status': 0,
                'message': _('Logout failed'),
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            user = User.objects.filter(phone=phone).first()

            if user:
                otp = str(random.randint(1000, 9999))
                user.otp = otp
                user.save()

                print(f"Sending OTP {otp} to {phone}")

                return Response({
                    'status': 1,
                    'message': _('OTP sent to your phone.'),
                    'otp': otp,
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
class EditProfileAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        user = request.user
    
        return Response({
            'status': 1,
            'message': _('Player Details.'),
            'user': {
                        'id': user.id,
                        'username': user.username,
                        'phone': user.phone,
                        'email': user.email,
                        'fullname': user.fullname,
                        'bio': user.bio,
                        'date_of_birth': user.date_of_birth,
                        'age': user.age,
                        'gender': user.gender,
                        'country': user.country,
                        'city': user.city,
                        'nationality': user.nationality,
                        'weight': user.weight,
                        'height': user.height,
                        'main_playing_position': user.main_playing_position,
                        'secondary_playing_position': user.secondary_playing_position,
                        'playing_foot': user.playing_foot,
                        'favourite_local_team': user.favourite_local_team,
                        'favourite_team': user.favourite_team,
                        'favourite_local_player': user.favourite_local_player,
                        'favourite_player': user.favourite_player,
                        'profile_picture': user.profile_picture.url if user.profile_picture else None,
                        'cover_photo': user.card_header.url if user.card_header else None
                    }
        }, status=status.HTTP_200_OK)


    ######## Post of Create API ######
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        user = request.user

        # Get old profile picture and card header (before any changes)
        old_profile_picture = user.profile_picture
        old_card_header = user.card_header

        # Update all fields from request data
        user.fullname = request.data.get('fullname', user.fullname)
        user.bio = request.data.get('bio', user.bio)
        user.date_of_birth = request.data.get('date_of_birth', user.date_of_birth)
        user.age = request.data.get('age', user.age)
        user.gender = request.data.get('gender', user.gender)
        user.country = request.data.get('country', user.country)
        user.city = request.data.get('city', user.city)
        user.nationality = request.data.get('nationality', user.nationality)
        user.weight = request.data.get('weight', user.weight)
        user.height = request.data.get('height', user.height)
        user.main_playing_position = request.data.get('main_playing_position', user.main_playing_position)
        user.secondary_playing_position = request.data.get('secondary_playing_position', user.secondary_playing_position)
        user.playing_foot = request.data.get('playing_foot', user.playing_foot)
        user.favourite_local_team = request.data.get('favourite_local_team', user.favourite_local_team)
        user.favourite_team = request.data.get('favourite_team', user.favourite_team)
        user.favourite_local_player = request.data.get('favourite_local_player', user.favourite_local_player)
        user.favourite_player = request.data.get('favourite_player', user.favourite_player)

        # Handle profile picture update
        if "profile_picture" in request.FILES:
            profile_picture = request.FILES["profile_picture"]

            # Delete the old profile picture if it exists
            if old_profile_picture and os.path.isfile(os.path.join(settings.MEDIA_ROOT, str(old_profile_picture))):
                os.remove(os.path.join(settings.MEDIA_ROOT, str(old_profile_picture)))

            # Save the new profile picture
            file_extension = profile_picture.name.split('.')[-1]
            file_name = f"profile_pics/{user.username}.{file_extension}"

            path = default_storage.save(file_name, profile_picture)
            user.profile_picture = path

        # Handle card header update
        if "cover_photo" in request.FILES:
            card_header = request.FILES["cover_photo"]

            # Delete the old card header if it exists
            if old_card_header and os.path.isfile(os.path.join(settings.MEDIA_ROOT, str(old_card_header))):
                os.remove(os.path.join(settings.MEDIA_ROOT, str(old_card_header)))

            # Save the new card header
            file_extension = card_header.name.split('.')[-1]
            file_name = f"card_header/{user.username}.{file_extension}"

            path = default_storage.save(file_name, card_header)
            user.card_header = path

        # Save user details
        user.save()

        return Response({
            'status': 1,
            'message': _('Profile updated successfully.'),
            'data': {
                'id': user.id,
                'username': user.username,
                'phone': user.phone,
                'email': user.email,
                'fullname': user.fullname,
                'bio': user.bio,
                'date_of_birth': user.date_of_birth,
                'age': user.age,
                'gender': user.gender,
                'country': user.country,
                'city': user.city,
                'nationality': user.nationality,
                'weight': user.weight,
                'height': user.height,
                'main_playing_position': user.main_playing_position,
                'secondary_playing_position': user.secondary_playing_position,
                'playing_foot': user.playing_foot,
                'favourite_local_team': user.favourite_local_team,
                'favourite_team': user.favourite_team,
                'favourite_local_player': user.favourite_local_player,
                'favourite_player': user.favourite_player,
                'profile_picture': user.profile_picture.url if user.profile_picture else None,
                'cover_photo': user.card_header.url if user.card_header else None
            }
        }, status=status.HTTP_200_OK)