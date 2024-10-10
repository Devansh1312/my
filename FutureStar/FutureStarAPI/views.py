from django.shortcuts import render, redirect, get_object_or_404,HttpResponse
from django.utils.translation import gettext as _
from django.utils.translation import activate
from django import views
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from FutureStar_App.models import *
from FutureStarAPI.models import *
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
import random
from django.db import IntegrityError
from django.utils import timezone
import os
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import generics
import json 
from django.db.models import Q
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import  csrf_exempt 
from django.utils.decorators import method_decorator
from django.db import transaction
import string


# class RegisterAPIView(APIView):
#     permission_classes = [AllowAny]
#     parser_classes = (JSONParser, MultiPartParser, FormParser)

#     def post(self, request, *args, **kwargs):
#         language = request.headers.get('Language', 'en')
#         if language in ['en', 'ar']:
#             activate(language)

#         registration_type = request.data.get('type')
#         device_type = request.data.get('device_type')
#         device_token = request.data.get('device_token')

#         if registration_type == 1:
#             serializer = RegisterSerializer(data=request.data)
#             if serializer.is_valid():
#                 try:
#                     user = serializer.save()
#                     user.device_type = device_type
#                     user.device_token = device_token
#                     user.last_login = timezone.now()
#                     user.save()

#                     refresh = RefreshToken.for_user(user)

#                     return Response({
#                         'status': 1,
#                         'message': _('User registered and logged in successfully'),
#                         'data': {
#                             'refresh_token': str(refresh),
#                             'access_token': str(refresh.access_token),
#                             'id': user.id,
#                             'username': user.username,
#                             'phone': user.phone,
#                             'email': user.email,
#                             'fullname': user.fullname,
#                             'bio': user.bio,
#                             'date_of_birth': user.date_of_birth,
#                             'age': user.age,
#                             'gender': user.gender.id if user.gender else None,
#                             'country': user.country.id if user.country else None,
#                             'city': user.city.id if user.country else None,
#                             'nationality': user.nationality,
#                             'weight': user.weight,
#                             'height': user.height,
#                             'main_playing_position': user.main_playing_position,
#                             'secondary_playing_position': user.secondary_playing_position,
#                             'playing_foot': user.playing_foot,
#                             'favourite_local_team': user.favourite_local_team,
#                             'favourite_team': user.favourite_team,
#                             'favourite_local_player': user.favourite_local_player,
#                             'favourite_player': user.favourite_player,
#                             'profile_picture': user.profile_picture.url if user.profile_picture else None,
#                             'cover_photo': user.card_header.url if user.card_header else None,
#                             'device_type': user.device_type,
#                             'device_token': user.device_token,
#                         }
#                     }, status=status.HTTP_201_CREATED)

#                 except IntegrityError as e:
#                     return Response({
#                         'status': 0,
#                         'message': _('User registration failed due to duplicate data'),
#                         'errors': str(e)
#                     }, status=status.HTTP_400_BAD_REQUEST)

#             # Custom handling for validation errors to ensure the message is returned as desired
#             error_message = serializer.errors.get('non_field_errors')
#             if error_message:
#                 return Response({
#                     'status': 0,
#                     'message': _(error_message[0])  # Ensures translation is applied
#                 }, status=status.HTTP_400_BAD_REQUEST)
#             else:
#                 return Response({
#                     'status': 0,
#                     'message': serializer.errors
#                 }, status=status.HTTP_400_BAD_REQUEST)

#         elif registration_type in [2, 3]:
#             # Email registration (no password provided)
#             email = request.data.get('username')
#             if not email:
#                 return Response({
#                     'status': 0,
#                     'message': _('Email is required for registration')
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             user = User.objects.filter(email=email).first()

#             if user:
#                 # If the user exists, log them in
#                 if user.is_active:
#                     user.device_type = device_type
#                     user.device_token = device_token
#                     user.last_login = timezone.now()
#                     user.save()

#                     refresh = RefreshToken.for_user(user)
#                     return Response({
#                         'status': 1,
#                         'message': _('User logged in successfully'),
#                         'data': {
#                             'refresh_token': str(refresh),
#                             'access_token': str(refresh.access_token),
#                             'id': user.id,
#                             'username': user.username,
#                             'phone': user.phone,
#                             'email': user.email,
#                             'fullname': user.fullname,
#                             'bio': user.bio,
#                             'date_of_birth': user.date_of_birth,
#                             'age': user.age,
#                             'gender': user.gender.id if user.gender else None,
#                             'country': user.country.id if user.country else None,
#                             'city': user.city.id if user.country else None,
#                             'nationality': user.nationality,
#                             'weight': user.weight,
#                             'height': user.height,
#                             'main_playing_position': user.main_playing_position,
#                             'secondary_playing_position': user.secondary_playing_position,
#                             'playing_foot': user.playing_foot,
#                             'favourite_local_team': user.favourite_local_team,
#                             'favourite_team': user.favourite_team,
#                             'favourite_local_player': user.favourite_local_player,
#                             'favourite_player': user.favourite_player,
#                             'profile_picture': user.profile_picture.url if user.profile_picture else None,
#                             'cover_photo': user.card_header.url if user.card_header else None,
#                             'device_type': user.device_type,
#                             'device_token': user.device_token, 
#                         }
#                     }, status=status.HTTP_200_OK)
#                 else:
#                     return Response({
#                         'status': 0,
#                         'message': _('Account is inactive')
#                     }, status=status.HTTP_400_BAD_REQUEST)

#             else:
#                 # Generate a random password manually
#                 user = User.objects.create_user(
#                     username=email.split('@')[0],
#                     email=email,
#                     password=email.split('@')[0],
#                     is_active=True  # Adjust this if you need email verification
#                 )
#                 user.device_type = device_type
#                 user.device_token = device_token
#                 user.last_login = timezone.now()
#                 user.save()

#                 refresh = RefreshToken.for_user(user)

#                 return Response({
#                     'status': 1,
#                     'message': _('User created and logged in successfully'),
#                     'data': {
#                         'refresh_token': str(refresh),
#                         'access_token': str(refresh.access_token),
#                         'data': {
#                             'id': user.id,
#                             'username': user.username,
#                             'phone': user.phone,
#                             'email': user.email,
#                             'fullname': user.fullname,
#                             'bio': user.bio,
#                             'date_of_birth': user.date_of_birth,
#                             'age': user.age,
#                             'gender': user.gender.id if user.gender else None,
#                             'country': user.country.id if user.country else None,
#                             'city': user.city.id if user.country else None,
#                             'nationality': user.nationality,
#                             'weight': user.weight,
#                             'height': user.height,
#                             'main_playing_position': user.main_playing_position,
#                             'secondary_playing_position': user.secondary_playing_position,
#                             'playing_foot': user.playing_foot,
#                             'favourite_local_team': user.favourite_local_team,
#                             'favourite_team': user.favourite_team,
#                             'favourite_local_player': user.favourite_local_player,
#                             'favourite_player': user.favourite_player,
#                             'profile_picture': user.profile_picture.url if user.profile_picture else None,
#                             'cover_photo': user.card_header.url if user.card_header else None,
#                             'device_type': user.device_type,
#                             'device_token': user.device_token,
#                         }
#                     }
#                 }, status=status.HTTP_201_CREATED)

#         return Response({
#             'status': 0,
#             'message': _('Invalid registration type')
#         }, status=status.HTTP_400_BAD_REQUEST)


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
                username_or_phone = serializer.validated_data['username']
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
                                    'fullname': user.fullname,
                                    'bio': user.bio,
                                    'date_of_birth': user.date_of_birth,
                                    'age': user.age,
                                    'gender': user.gender.id if user.gender else None,
                                    'country': user.country.id if user.country else None,
                                    'city': user.city.id if user.country else None,
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
                                    'cover_photo': user.card_header.url if user.card_header else None,
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
                email = serializer.validated_data['username']

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
                                    'fullname': user.fullname,
                                    'bio': user.bio,
                                    'date_of_birth': user.date_of_birth,
                                    'age': user.age,
                                    'gender': user.gender.id if user.gender else None,
                                    'country': user.country.id if user.country else None,
                                    'city': user.city.id if user.country else None,
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
                                    'cover_photo': user.card_header.url if user.card_header else None,
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
                            'data': {
                                'id': user.id,
                                'username': user.username,
                                'phone': user.phone,
                                'email': user.email,
                                'fullname': user.fullname,
                                'bio': user.bio,
                                'date_of_birth': user.date_of_birth,
                                'age': user.age,
                                'gender': user.gender.id if user.gender else None,
                                'country': user.country.id if user.country else None,
                                'city': user.city.id if user.country else None,
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
                                'cover_photo': user.card_header.url if user.card_header else None,
                                'device_type': user.device_type,
                                'device_token': user.device_token,
                            }
                        }
                    }, status=status.HTTP_201_CREATED)

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
            'data': {
                        'id': user.id,
                        'username': user.username,
                        'phone': user.phone,
                        'email': user.email,
                        'fullname': user.fullname,
                        'bio': user.bio,
                        'date_of_birth': user.date_of_birth,
                        'age': user.age,
                        'gender': user.gender.id if user.gender else None,
                        'country': user.country.id if user.country else None,
                        'city': user.city.id if user.country else None,
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
        
        # Assign gender by fetching the corresponding UserGender instance
        gender_id = request.data.get('gender')
        if gender_id:
            try:
                user.gender = UserGender.objects.get(id=gender_id)  # Fetch UserGender instance
            except UserGender.DoesNotExist:
                return Response({
                    'status': 2,
                    'message': _('Invalid gender specified.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Handle country
        country_id = request.data.get('country')
        # if country_id:
        #     try:
        #         user.country = Country.objects.get(id=country_id)  # Fetch Country instance
        #     except Country.DoesNotExist:
        #         return Response({
        #             'status': 2,
        #             'message': _('Invalid country specified.')
        #         }, status=status.HTTP_400_BAD_REQUEST)

        # Handle city
        city_id = request.data.get('city')
        if city_id:
            try:
                user.city = City.objects.get(id=city_id)  # Fetch City instance
            except City.DoesNotExist:
                return Response({
                    'status': 2,
                    'message': _('Invalid city specified.')
                }, status=status.HTTP_400_BAD_REQUEST)
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
                'gender': user.gender.id if user.gender else None,  # Return the ID of the gender
                'country': user.country.id if user.country else None,
                'city': user.city.id if user.country else None,
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



####################### POST API ###############################################################################
class PostListAPIView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        team_id = self.request.headers.get('Team-ID')  # Optional Team-ID from headers

        if team_id:
            return Post.objects.filter(team_id=team_id).order_by('-date_created')  # Filter posts by team
        else:
            return Post.objects.filter(user=self.request.user).order_by('-date_created')  # Filter posts by user

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        activate(language)

        posts = self.get_queryset()
        serializer = self.get_serializer(posts, many=True)

        return Response({
            'status': 1,
            'message': _('Posts fetched successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

class PostCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # To handle file uploads

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        activate(language)

        team_id = request.data.get('team_id')  # Optional team_id from request data
        serializer = PostSerializer(data=request.data)

        if serializer.is_valid():
            if team_id:
                try:
                    team = Team.objects.get(id=team_id)
                except Team.DoesNotExist:
                    return Response({
                        'status': 0,
                        'message': _('Team not found.')
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Save the post with a team
                post = serializer.save(user=request.user, team_id=team)
            else:
                # Save the post for the user without a team
                post = serializer.save(user=request.user)

            # Handle image upload
            if "image" in request.FILES:
                image = request.FILES["image"]

                # Save new image with a structured filename
                file_extension = image.name.split('.')[-1]
                file_name = f"post_images/{post.id}_{request.user.username}.{file_extension}"

                # Save the image and update the post instance
                image_path = default_storage.save(file_name, image)
                post.image = image_path
                post.save()

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

class PostDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        activate(language)

        post_id = request.data.get('post_id')
        team_id = request.data.get('team_id')  # Optional team_id

        if not post_id:
            return Response({
                'status': 0,
                'message': _('post_id is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            if team_id:
                post = Post.objects.get(id=post_id, team_id=team_id)
            else:
                post = Post.objects.get(id=post_id, user=request.user)
        except Post.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Post not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = PostSerializer(post)

        return Response({
            'status': 1,
            'message': _('Post details fetched successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

class CommentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        activate(language)

        data = request.data
        post_id = data.get('post_id')
        team_id = data.get('team_id')  # Optional team_id
        comment_text = data.get('comment')
        parent_id = data.get('parent_id')

        if not post_id or not comment_text:
            return Response({
                'status': 0,
                'message': _('post_id and comment are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            if team_id:
                post = Post.objects.get(id=post_id, team_id=team_id)
            else:
                post = Post.objects.get(id=post_id, user=request.user)
        except Post.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Post not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Handle parent comment (if it's a reply)
        parent_comment = None
        if parent_id:
            try:
                parent_comment = Post_comment.objects.get(id=parent_id)
            except Post_comment.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Parent comment not found.')
                }, status=status.HTTP_404_NOT_FOUND)

        # Create the comment
        comment = Post_comment.objects.create(
            user=request.user,
            post=post,
            comment=comment_text,
            parent=parent_comment,
            team_id=team_id  # Set the team_id if provided
        )

        return Response({
            'status': 1,
            'message': _('Comment created successfully.'),
            'data': PostCommentSerializer(comment).data
        }, status=status.HTTP_201_CREATED)

class PostDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        activate(language)

        post_id = request.data.get('post_id')
        team_id = request.data.get('team_id')  # Optional team_id

        if not post_id:
            return Response({
                'status': 0,
                'message': _('post_id is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            if team_id:
                post = Post.objects.get(id=post_id, team_id=team_id)
            else:
                post = Post.objects.get(id=post_id, user=request.user)
        except Post.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Post not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        post.delete()

        return Response({
            'status': 1,
            'message': _('Post deleted successfully.')
        }, status=status.HTTP_200_OK)

################################################ Field API View #################################
class FieldAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # To handle file uploads

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
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
    parser_classes = [MultiPartParser, FormParser]  # To handle file uploads

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
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

class TeamViewAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # To handle file uploads

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        activate(language)

        # Fetch all categories
        categories = Category.objects.all()

        # Construct the response data with language-specific names
        type_data = []
        for category in categories:
            if language == 'ar':
                type_name = category.name_ar
            else:
                type_name = category.name_en
            type_data.append({
                'id': category.id,
                'type_name': type_name
            })

        return Response({
            'status': 1,
            'message': _('Types retrieved successfully.'),
            'data': type_data
        }, status=status.HTTP_200_OK)
    

    def post(self, request, *args, **kwargs):
        user = request.user

        # Fetch the team type (category) by its ID from the request
        try:
            team_type_id = request.data.get('team_type')
            team_type_instance = Category.objects.get(id=team_type_id)
        except Category.DoesNotExist:
            return Response({'status': 0, 'message': _('Invalid team type provided.')}, status=status.HTTP_400_BAD_REQUEST)

        # Create a new team instance
        team_instance = Team(
            user_id=user,
            team_name=request.data.get('team_name'),
            team_type=team_type_instance,  # Assign the Category instance
            bio=request.data.get('bio'),
            team_establishment_date=request.data.get('team_establishment_date'),
            team_president=request.data.get('team_president'),
            location=request.data.get('location'),
            country=request.data.get('country'),
            city=request.data.get('city'),
            phone=request.data.get('phone'),
            email=request.data.get('email'),
            age_group=request.data.get('age_group'),
            entry_fees=request.data.get('entry_fees'),
            branches=request.data.get('branches'),
        )

        # Handle file uploads (same as your existing logic)
        if 'team_logo' in request.FILES:
            logo = request.FILES['team_logo']
            file_extension = logo.name.split('.')[-1]
            file_name = f"team/team_logo/{team_instance.team_name}_{team_instance.id}.{file_extension}"
            logo_path = default_storage.save(file_name, logo)
            team_instance.team_logo = logo_path

        if 'team_background_image' in request.FILES:
            background_image = request.FILES['team_background_image']
            file_extension = background_image.name.split('.')[-1]
            file_name = f"team/team_background_image/{team_instance.team_name}_{team_instance.id}.{file_extension}"
            background_image_path = default_storage.save(file_name, background_image)
            team_instance.team_background_image = background_image_path

        if 'team_uniform' in request.FILES:
            uniform_image = request.FILES['team_uniform']
            file_extension = uniform_image.name.split('.')[-1]
            file_name = f"team/team_uniform/{team_instance.team_name}_{team_instance.id}.{file_extension}"
            uniform_image_path = default_storage.save(file_name, uniform_image)
            team_instance.team_uniform = uniform_image_path

        # Save the team instance
        team_instance.save()

        # Construct response data
        response_data = {
            'id': team_instance.id,
            'user_id': user.id,
            'username': user.username,
            'team_name': team_instance.team_name,
            'team_type': team_instance.team_type.id,  # Return the category ID
            'bio': team_instance.bio,
            'team_establishment_date': team_instance.team_establishment_date,
            'team_president': team_instance.team_president,
            'location': team_instance.location,
            'country': team_instance.country,
            'city': team_instance.city,
            'phone': team_instance.phone,
            'email': team_instance.email,
            'age_group': team_instance.age_group,
            'entry_fees': team_instance.entry_fees,
            'branches': team_instance.branches,
            'team_logo': team_instance.team_logo.url if team_instance.team_logo else None,
            'team_background_image': team_instance.team_background_image.url if team_instance.team_background_image else None,
            'team_uniform': team_instance.team_uniform.url if team_instance.team_uniform else None
        }

        return Response({
            'status': 1,
            'message': _('Team created successfully.'),
            'data': response_data
        }, status=status.HTTP_201_CREATED)
    
    def put(self, request, *args, **kwargs):
        team_id = request.data.get('team_id')
        user = request.user

        if not team_id:
            return Response({'status': 0, 'message': _('Team ID is required.')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            team_instance = Team.objects.get(id=team_id, user_id=request.user)
        except Team.DoesNotExist:
            return Response({'status': 0, 'message': _('Team not found.')}, status=status.HTTP_404_NOT_FOUND)

        # Fetch the team type (category) by its ID, if provided
        team_type_id = request.data.get('team_type')
        if team_type_id:
            try:
                team_type_instance = Category.objects.get(id=team_type_id)
                team_instance.team_type = team_type_instance  # Assign the Category instance
            except Category.DoesNotExist:
                return Response({'status': 0, 'message': _('Invalid team type provided.')}, status=status.HTTP_400_BAD_REQUEST)

        # Update other fields from the request data (same as your logic)
        team_instance.team_name = request.data.get('team_name', team_instance.team_name)
        team_instance.bio = request.data.get('bio', team_instance.bio)
        team_instance.team_establishment_date = request.data.get('team_establishment_date', team_instance.team_establishment_date)
        team_instance.team_president = request.data.get('team_president', team_instance.team_president)
        team_instance.location = request.data.get('location', team_instance.location)
        team_instance.country = request.data.get('country', team_instance.country)
        team_instance.city = request.data.get('city', team_instance.city)
        team_instance.phone = request.data.get('phone', team_instance.phone)
        team_instance.email = request.data.get('email', team_instance.email)
        team_instance.age_group = request.data.get('age_group', team_instance.age_group)
        team_instance.entry_fees = request.data.get('entry_fees', team_instance.entry_fees)
        team_instance.branches = request.data.get('branches', team_instance.branches)

        # Handle file uploads (same as before)
        if 'team_logo' in request.FILES:
            logo = request.FILES['team_logo']
            file_extension = logo.name.split('.')[-1]
            file_name = f"team/team_logo/{team_instance.team_name}_{team_instance.id}.{file_extension}"
            logo_path = default_storage.save(file_name, logo)
            team_instance.team_logo = logo_path

        if 'team_background_image' in request.FILES:
            background_image = request.FILES['team_background_image']
            file_extension = background_image.name.split('.')[-1]
            file_name = f"team/team_background_image/{team_instance.team_name}_{team_instance.id}.{file_extension}"
            background_image_path = default_storage.save(file_name, background_image)
            team_instance.team_background_image = background_image_path

        if 'team_uniform' in request.FILES:
            uniform_image = request.FILES['team_uniform']
            file_extension = uniform_image.name.split('.')[-1]
            file_name = f"team/team_uniform/{team_instance.team_name}_{team_instance.id}.{file_extension}"
            uniform_image_path = default_storage.save(file_name, uniform_image)
            team_instance.team_uniform = uniform_image_path

        # Save the updated team instance
        team_instance.save()

        # Construct response data (same as before)
        response_data = {
            'id': team_instance.id,
            'user_id': user.id,
            'username': user.username,
            'team_name': team_instance.team_name,
            'team_type': team_instance.team_type.id,
            'bio': team_instance.bio,
            'team_establishment_date': team_instance.team_establishment_date,
            'team_president': team_instance.team_president,
            'location': team_instance.location,
            'country': team_instance.country,
            'city': team_instance.city,
            'phone': team_instance.phone,
            'email': team_instance.email,
            'age_group': team_instance.age_group,
            'entry_fees': team_instance.entry_fees,
            'branches': team_instance.branches,
            'team_logo': team_instance.team_logo.url if team_instance.team_logo else None,
            'team_background_image': team_instance.team_background_image.url if team_instance.team_background_image else None,
            'team_uniform': team_instance.team_uniform.url if team_instance.team_uniform else None
        }

        return Response({
            'status': 1,
            'message': _('Team updated successfully.'),
            'data': response_data
        }, status=status.HTTP_200_OK)


class UserGenderListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = UserGender.objects.all()
    serializer_class = UserGenderSerializer

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


# class LocationAPIView(APIView):

#     def get(self, request):
#         country_id = request.query_params.get('country_id')

#         # If country_id is not provided, return all active countries
#         if not country_id:
#             countries = Country.objects.filter(status=True)
#             country_data = [{'id': country.id, 'name': country.name} for country in countries]

#             return Response({
#                 'status': 1,
#                 'message': 'Countries fetched successfully',
#                 'data': country_data
#             }, status=status.HTTP_200_OK)

#         # If country_id is provided, return cities for that country
#         try:
#             country = Country.objects.get(id=country_id, status=True)
#         except Country.DoesNotExist:
#             return Response({
#                 'status': 0,
#                 'message': 'Country not found or inactive'
#             }, status=status.HTTP_404_NOT_FOUND)

#         cities = City.objects.filter(country=country, status=True)
#         city_data = [{'id': city.id, 'name': city.name} for city in cities]

#         return Response({
#             'status': 1,
#             'message': 'Cities fetched successfully',
#             'data': city_data
#         }, status=status.HTTP_200_OK)

                

                       
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
        registration_type = request.data.get('type')
        

        # Handle Registration Type 1 (Normal registration)
        if registration_type == '1':
            username = request.data.get('username')
            phone = request.data.get('phone')
            email = request.data.get('email')
            password = request.data.get('password')
            # Check if username or phone already exists in User table
            if User.objects.filter(Q(username=username) | Q(phone=phone)).exists():
                return Response({
                    'status': 0,
                    'message': _('Username or phone number already exists.')
                }, status=status.HTTP_400_BAD_REQUEST)

            # If user does not exist, generate OTP and store it in OTPSave table
            otp = generate_otp()
            # Save or update the OTP in OTPSave
            otp_record, created = OTPSave.objects.update_or_create(
                phone=phone,  # or username based on uniqueness
                defaults={'username': username, 'phone': phone, 'password': password, 'OTP': otp}
            )

            return Response({
                'status': 1,
                'message': _('OTP sent successfully.'),
                'otp': otp  # For development, this is sent in the response.
            }, status=status.HTTP_200_OK)

        # Handle Registration Type 2/3 (Social registration via email)
        elif registration_type in ['2', '3']:
            username = request.data.get('username')
            phone = request.data.get('phone')
            email = request.data.get('email')
            # Check if email exists in User table
            if User.objects.filter(email=email).exists():
                return Response({
                    'status': 0,
                    'message': _('Email already exists.')
                }, status=status.HTTP_400_BAD_REQUEST)

            # If email does not exist, check username and phone if provided
            if username and phone:
                # Validate if username or phone already exists in User table
                if User.objects.filter(Q(username=username) | Q(phone=phone)).exists():
                    return Response({
                        'status': 0,
                        'message': _('Username or phone number already exists.')
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Generate OTP and save in OTPSave for type 2/3 with phone, email, and password
                otp = generate_otp()
                random_password = self.generate_random_password()
                password = random_password  # Set the generated password
                otp_record, created = OTPSave.objects.update_or_create(
                    phone=phone,  # Assuming phone is required
                    password=email.split('@')[0],
                    defaults={'username': username, 'phone': phone, 'email': email, 'password': password, 'OTP': otp}
                )

                return Response({
                    'status': 1,
                    'message': _('OTP sent successfully.'),
                    'otp': otp  # Send OTP in response for development.
                }, status=status.HTTP_200_OK)

            else:
                # If username and phone are not provided, return success for email registration
                return Response({
                    'status': 1,
                    'message': _('User can proceed with registration.'),
                }, status=status.HTTP_200_OK)

        return Response({
            'status': 0,
            'message': _('Invalid registration type.')
        }, status=status.HTTP_400_BAD_REQUEST)


class verify_and_register(APIView):
    parser_classes = (JSONParser, MultiPartParser, FormParser)


    def post(self, request, *args, **kwargs):
        phone = request.data.get("phone")
        otp_input = request.data.get("otp")
        device_type = request.data.get("device_type")
        device_token = request.data.get("device_token")

        if not phone or not otp_input:
            return Response({
                'status': 0,
                'message': _('Phone and OTP are required fields.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if the OTP and phone exist in the OTPSave table
            otp_record = OTPSave.objects.get(phone=phone, OTP=otp_input)
        except OTPSave.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Invalid OTP or phone number.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create the user within a transaction to ensure atomicity
            with transaction.atomic():
                # Create the user in the User table with details from the OTPSave record
                user = User.objects.create(
                    username=otp_record.username,
                    phone=otp_record.phone,
                    email=otp_record.email,
                    role_id=5,  # Assuming role_id 5 is for regular users
                    device_type=device_type,
                    device_token=device_token
                )
                user.set_password(otp_record.password)
                user.save()

                # Delete OTP record after successful registration
                otp_record.delete()


                # Prepare user data to be sent in the response
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'phone': user.phone,
                    'email': user.email,
                    'fullname': user.fullname,
                    'bio': user.bio,
                    'date_of_birth': user.date_of_birth,
                    'age': user.age,
                    'gender': user.gender.id if user.gender else None,
                    'country': user.country.id if user.country else None,
                    'city': user.city.id if user.country else None,
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
                    'cover_photo': user.card_header.url if user.card_header else None,
                    'device_type': user.device_type,
                    'device_token': user.device_token,
                }

                # Return response with refresh and access tokens
                return Response({
                    'status': 1,
                    'message': _('User registered successfully'),
                    'data': user_data  # This should now work correctly
                }, status=status.HTTP_201_CREATED)


        except Exception as e:
            return Response({
                'status': 0,
                'message': _('An error occurred while registering the user.'),
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            
            
            
            
            
            
            
            
            
            
            
             
        
        
        
        
                
        
        
    
                
        
