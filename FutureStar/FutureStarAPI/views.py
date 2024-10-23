from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.utils.translation import activate
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

logger = logging.getLogger(__name__)


def get_user_data(user, request):
    """Returns a dictionary with all user details."""
    
    # Get follower and following counts for the user
    followers_count = FollowRequest.count_followers(to_user=user)
    following_count = FollowRequest.count_following(from_user=user)
    
    post_count = Post.objects.filter(user=user, team__isnull=True).count()
    
    gender_name = None
    if user.gender:
        serializer = UserGenderSerializer(user.gender, context={'request': request})
        gender_name = serializer.data['name']

    return {
        'id': user.id,
        'followers_count': 100,  # Actual follower count
        'following_count': 100,  # Actual following count
        'post_count': post_count,
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
                        **get_user_data(user, request) 
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
                                **get_user_data(user, request) 

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
                                **get_user_data(user, request) 

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
            file_name = f"profile_pics/{user.username}.{file_extension}"
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
                **get_user_data(user, request)
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
                **get_user_data(user, request)
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
        null_fields = ['fullname', 'bio', 'nationality', 'weight', 'height', 'main_playing_position',
                       'secondary_playing_position', 'playing_foot', 'favourite_local_team', 'favourite_team',
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
            file_name = f"profile_pics/{user.username}.{file_extension}"
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
            file_name = f"card_header/{user.username}.{file_extension}"
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
                **get_user_data(user, request)
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
            page_number = request.data.get(self.page_query_param, 1)
            self.page = int(page_number)
            if self.page < 1:
                raise ValidationError("Page number must be a positive integer.")
        except (ValueError, TypeError):
            raise ValidationError("Invalid page number.")

        # Get total number of pages based on the queryset
        paginator = self.django_paginator_class(queryset, self.get_page_size(request))
        total_pages = paginator.num_pages

        # Check if the requested page number is within the valid range
        if self.page > total_pages:
            # If page is out of range, return an empty list
            return []

        # Perform standard pagination
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
        post_like, created = PostLike.objects.get_or_create(user=request.user, post=post)
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
    pagination_class = CustomPostPagination  # Use custom pagination

    def get_queryset(self):
        # Return all posts without any filters
        return Post.objects.all().order_by('-date_created')

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        queryset = self.get_queryset()

        # Paginate the queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            total_records = queryset.count()
            total_pages = self.paginator.page.paginator.num_pages

            # Custom response to include pagination data
            return Response({ 
                'status': 1,
                'message': _('All posts fetched successfully.'),
                'data': serializer.data,
                'total_records': total_records,
                'total_pages': total_pages,
                'current_page': self.paginator.page.number
            }, status=status.HTTP_200_OK)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response({
            'status': 1,
            'message': _('All posts fetched successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

##########  LIST OF POST BASED ON USER TEAM AND GROUP ################
class PostListAPIView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = CustomPostPagination  # Use custom pagination

    def get_queryset(self):
        team_id = self.request.data.get('team_id')
        group_id = self.request.data.get('group_id')
        user_id = self.request.data.get('user_id')

        if team_id:
            return Post.objects.filter(team_id=team_id).order_by('-date_created')
        elif group_id:
            return Post.objects.filter(group_id=group_id).order_by('-date_created')
        elif user_id:
            return Post.objects.filter(user=user_id, team_id__isnull=True, group_id__isnull=True).order_by('-date_created')
        else:
            return Post.objects.filter(user=self.request.user, team_id__isnull=True, group_id__isnull=True).order_by('-date_created')


    def post(self, request, *args, **kwargs):
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

        team_id = request.data.get('team_id')  # Optional team_id from request data
        group_id = request.data.get('group_id')  # Optional group_id from request data

        serializer = PostSerializer(data=request.data)

        if serializer.is_valid():
            try:
                # Check if team_id is provided
                if team_id:
                    team = Team.objects.get(id=team_id)
                    post = serializer.save(user=request.user, team_id=team.id)
                elif group_id:
                    group = TrainingGroups.objects.get(id=group_id)
                    post = serializer.save(user=request.user, group_id=group.id)
                else:
                    post = serializer.save(user=request.user)

                # Handle image upload
                if "image" in request.FILES:
                    image = request.FILES["image"]
                    file_extension = image.name.split('.')[-1]
                    file_name = f"post_images/{post.id}_{request.user.username}.{file_extension}"
                    image_path = default_storage.save(file_name, image)
                    post.image = image_path
                    post.save()

                return Response({
                    'status': 1,
                    'message': _('Post created successfully'),
                    'data': PostSerializer(post).data
                }, status=status.HTTP_201_CREATED)

            except Team.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Team not found.')
                }, status=status.HTTP_404_NOT_FOUND)
            except TrainingGroups.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Group not found.')
                }, status=status.HTTP_404_NOT_FOUND)

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
        # Optional Team-ID from headers
        team_id = self.request.data.get('team_id')
        group_id = self.request.data.get('group_id')  
        if team_id:
            return Post.objects.filter(team_id=team_id)
        elif group_id:
            return Post.objects.filter(group_id=group_id)
        else:
            return Post.objects.filter(user=self.request.user)

    def get_object(self, post_id):
        # Get the post by post_id from the filtered queryset
        return get_object_or_404(self.get_queryset(), id=post_id)

    def get(self, request, *args, **kwargs):
        # Activate the requested language, default is 'en'
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        post_id = request.data.get('post_id')  # Get post_id from request data
        if not post_id:
            return Response({
                'status': 0,
                'message': _('Post ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        post = self.get_object(post_id)  # Retrieve the post object based on post_id
        serializer = self.get_serializer(post)

        return Response({
            'status': 1,
            'message': _('Post fetched successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        # Activate the requested language, default is 'en'
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        post_id = request.data.get('post_id')  # Get post_id from request data
        if not post_id:
            return Response({
                'status': 0,
                'message': _('Post ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        post = self.get_object(post_id)  # Retrieve the post object based on post_id
        serializer = self.get_serializer(post, data=request.data, partial=True)  # Allow partial update

        if serializer.is_valid():
            serializer.save()  # Save changes
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
        PostView.objects.get_or_create(user=request.user, post=post)

        # Retrieve the view count for the post
        view_count = PostView.objects.filter(post=post).count()

        # Serialize the post details with the paginated comments
        serializer = PostSerializer(post, context={'request': request})

        # Return the combined response with both post details and view count
        return Response({
            'status': 1,
            'message': _('Post details fetched successfully.'),
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


######################## COMMNET CREATE API ###########################
class CommentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def post(self, request, *args, **kwargs):
        # Set the language based on headers
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract data from request
        data = request.data
        post_id = data.get('post_id')
        comment_text = data.get('comment')
        parent_id = data.get('parent_id')
        team_id = data.get('team_id')  # Optional team_id
        group_id = data.get('group_id')  # Optional group_id

        # Validate that post_id and comment are provided
        if not post_id or not comment_text:
            return Response({
                'status': 0,
                'message': _('post_id and comment are required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            post = Post.objects.get(id=post_id)
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

        # Create the comment based on the entity type (team, group, or user)
        if team_id:
            try:
                team = Team.objects.get(id=team_id)
                comment = Post_comment.objects.create(
                    user=request.user,
                    post=post,
                    comment=comment_text,
                    parent=parent_comment,
                    team_id=team_id  # Store team ID
                )
            except Team.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Team not found.')
                }, status=status.HTTP_404_NOT_FOUND)

        elif group_id:
            try:
                group = TrainingGroups.objects.get(id=group_id)
                comment = Post_comment.objects.create(
                    user=request.user,
                    post=post,
                    comment=comment_text,
                    parent=parent_comment,
                    group_id=group_id  # Store group ID
                )
            except TrainingGroups.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Group not found.')
                }, status=status.HTTP_404_NOT_FOUND)

        else:
            # Comment is from the user
            comment = Post_comment.objects.create(
                user=request.user,
                post=post,
                comment=comment_text,
                parent=parent_comment
            )

        # Return the response with comment details including the entity (team, group, or user)
        return Response({
            'status': 1,
            'message': _('Comment created successfully.'),
            'data': PostCommentSerializer(comment).data  # Return serialized comment data
        }, status=status.HTTP_201_CREATED)

############### POST DELETE API ##############################
class PostDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def delete(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        post_id = request.data.get('post_id')
        team_id = request.data.get('team_id')  # Optional team_id
        group_id = request.data.get('group_id')  # Optional team_id

        if not post_id:
            return Response({
                'status': 0,
                'message': _('post_id is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            if team_id:
                post = Post.objects.get(id=post_id, team_id=team_id)
            elif group_id:
                post = Post.objects.get(id=post_id, group_id=group_id)
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

###########detail album with id ################

class DetailAlbumListAPIView(generics.ListAPIView):
    serializer_class = DetailAlbumSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPostPagination  # Use custom pagination

    def get_queryset(self):
        album_id = self.request.data.get('album_id')  # Fetch album_id from the request body

        if album_id:
            try:
                # Ensure that the album belongs to the user or team
                return Album.objects.filter(id=album_id)
            except Album.DoesNotExist:
                return Album.objects.none()
        else:
             raise ValidationError(_("Album Id is required"))
           
      

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)  # Paginate the queryset

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            total_records = queryset.count()
            total_pages = self.paginator.page.paginator.num_pages

            # Custom response to include pagination data
            return Response({
                'status': 1,
                'message': _('Detailed Albums fetched successfully.'),
                'data': serializer.data,
                'total_records': total_records,
                'total_pages': total_pages,
                'current_page': self.paginator.page.number
                
            }, status=status.HTTP_200_OK)

        # If pagination is not applicable, return all albums
        albums = self.get_queryset()
        serializer = self.get_serializer(albums, many=True)

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

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            album_instance = serializer.save(user=request.user)

            media_files = request.FILES.getlist('media_file')  # Get a list of media files
            gallery_items = []

            if media_files:
                for media_file in media_files:
                    gallary_data = {
                        'user': request.user.id,
                        'media_file': media_file,
                        'album_id': album_instance.id,
                        'content_type': request.data.get('content_type'),
                        'team_id': request.data.get('team_id'),
                        'group_id': request.data.get('group_id')
                    }
                    gallary_serializer = GallarySerializer(data=gallary_data)
                    if gallary_serializer.is_valid():
                        gallery_item = gallary_serializer.save()
                        print(gallery_item)
                        gallery_items.append(gallery_item)
                    else:
                        album_instance.delete()  # Clean up the album if any media fails
                        return Response({
                            'status': 0,
                            'message': _('Gallery entry creation failed.'),
                            'errors': gallary_serializer.errors
                        }, status=status.HTTP_400_BAD_REQUEST)

            # Return response after processing all media files
            album_data = DetailAlbumSerializer(album_instance).data
            return Response({
                'status': 1,
                'message': _('Detailed Albums Add successfully.'),
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
    pagination_class = CustomPostPagination 

    def get_queryset(self):
        team_id = self.request.data.get('team_id')
        user_id = self.request.data.get('user_id')
        group_id = self.request.data.get('group_id')

        if team_id:
            return Album.objects.filter(team_id=team_id).order_by('-created_at')
        elif group_id:
            return Album.objects.filter(group_id=group_id).order_by('-created_at')
        elif user_id:
            return Album.objects.filter(user=user_id, team_id__isnull=True, group_id__isnull=True).order_by('-created_at')
        else:
            return Album.objects.filter(user=self.request.user, team_id__isnull=True, group_id__isnull=True).order_by('-created_at')


    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset) 
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            total_records = queryset.count()
            total_pages = self.paginator.page.paginator.num_pages

            # Custom response to include pagination data
            return Response({
                'status': 1,
                'message': _('Albums fetched successfully.'),
                'data': serializer.data,
                'total_records': total_records,
                'total_pages': total_pages,
                'current_page': self.paginator.page.number
                
            }, status=status.HTTP_200_OK)


        albums = self.get_queryset()  # Renamed 'gallary' to 'albums' for clarity
        serializer = self.get_serializer(albums, many=True)

        return Response({
            'status': 1,
            'message': _('Album entries fetched successfully.'),
          
            'data': serializer.data
        }, status=status.HTTP_200_OK)
 

###########detail gallary with id with diffrentiatee ################

class GallaryListAPIView(generics.ListAPIView):
    serializer_class = GetGallarySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = CustomPostPagination

    def get_queryset(self):
            team_id = self.request.data.get('team_id')
            user_id = self.request.data.get('user_id')
            group_id = self.request.data.get('group_id')
            content_type = self.request.data.get('content_type')

            if team_id:
                return Gallary.objects.filter(team_id=team_id, album_id__isnull=True).order_by('-created_at')
            elif group_id:
                return Gallary.objects.filter(group_id=group_id, album_id__isnull=True).order_by('-created_at')
            elif content_type:
                return Gallary.objects.filter(content_type=content_type, album_id__isnull=True).order_by('-created_at')
            elif user_id:
                return Gallary.objects.filter(user_id=user_id, team_id__isnull=True, group_id__isnull=True, album_id__isnull=True).order_by('-created_at')
            else:
                return Gallary.objects.filter(user=self.request.user, team_id__isnull=True, group_id__isnull=True, album_id__isnull=True).order_by('-created_at')

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        queryset = self.get_queryset()
        print(queryset)

        # Pagination handling
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            total_records = queryset.count()
            total_pages = self.paginator.page.paginator.num_pages

            # return Response({
            #     'status': 1,
            #     'message': _('Gallery Items fetched successfully.'),
            #     'data': serializer.data,
            #     'total_records': total_records,
            #     'total_pages': total_pages,
            #     'current_page': self.paginator.page.number
            # }, status=status.HTTP_200_OK)

        # Handle non-paginated response
        image_extensions = ('.jfif', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff','.webp')
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')

        # Create Q objects for filtering images and videos
        image_query = Q()
        for ext in image_extensions:
            image_query |= Q(media_file__iendswith=ext)

        video_query = Q()
        for ext in video_extensions:
            video_query |= Q(media_file__iendswith=ext)

        # Filter images and videos based on the Q objects
        images = queryset.filter(image_query)
        videos = queryset.filter(video_query)

        # Serialize images and videos separately
        image_serializer = self.get_serializer(images, many=True)
        video_serializer = self.get_serializer(videos, many=True)

        print('images', image_serializer.data)
        print('videos', video_serializer.data)

        return Response({
            'status': 1,
            'message': _('Gallery entries fetched successfully.'),
            'data': {
                'images': image_serializer.data,
                'videos': video_serializer.data
            },
            'total_records': queryset.count(),  # This should count all records
            'total_pages': self.paginator.page.paginator.num_pages if page is not None else 1,
            'current_page': self.paginator.page.number if page is not None else 1
        }, status=status.HTTP_200_OK)




class GallaryCreateAPIView(generics.CreateAPIView):
    serializer_class = GetGallarySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract album_id, team_id, and group_id from the request
        album_id = request.data.get('album_id', None)
        team_id = request.data.get('team_id', None)
        group_id = request.data.get('group_id', None)

        # Initialize the serializer
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            album_instance = None
            team_instance = None
            group_instance = None

            # Fetch the training_group instance if training_group_id is provided
            if group_id:
                try:
                    group_instance = TrainingGroups.objects.get(id=group_id)
                except TrainingGroups.DoesNotExist:
                    raise NotFound(_("Training group not found."))

            # Fetch the album instance if album_id is provided
            if album_id:
                try:
                    album_instance = Album.objects.get(id=album_id)
                except Album.DoesNotExist:
                    raise NotFound(_("Album not found."))

            # Fetch the team instance if team_id is provided
            if team_id:
                try:
                    team_instance = Team.objects.get(id=team_id)
                except Team.DoesNotExist:
                    raise NotFound(_("Team not found."))

            # New validation: Check if the album is related to a team
            if album_instance:
                if album_instance.team_id and not team_id:
                    raise ValidationError(_("This album is associated with a team. Please provide a team ID."))
                if not album_instance.team_id and team_id:
                    raise ValidationError(_("This album is not associated with a team. Please remove the team ID."))

            # New validation: Check if the album is related to a training group
            if album_instance and group_instance:
                if album_instance.group_id and not group_id:
                    raise ValidationError(_("This album is associated with a training group. Please provide a training group ID."))
                if not album_instance.group_id and group_id:
                    raise ValidationError(_("This album is not associated with a training group. Please remove the training group ID."))

            # Condition 0: Both Training_id and album_id are provided
            if group_instance and album_instance:
                serializer.save(album_id=album_instance, group_id=group_instance)
            # Condition 1: Both team_id and album_id are provided
            elif team_instance and album_instance:
                serializer.save(album_id=album_instance, team_id=team_instance)
            # Condition 2: Only album_id is provided (check if it belongs to the user)
            elif album_instance:
                if album_instance.user == request.user:  # Assuming Album has a user field
                    serializer.save(album_id=album_instance)
                else:
                    raise ValidationError(_("You do not have permission to add to this album."))
            # Condition 3: Neither team_id nor album_id is provided
            else:
                serializer.save(album_id=None)

            return Response({
                'status': 1,
                'message': _('Gallery entry created successfully.'),
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 0,
            'message': _('Failed to create Gallery entry.'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
###########gallary list latest 9 ################

class LatestGallaryListAPIView(generics.ListCreateAPIView):

    serializer_class = GetGallarySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = CustomPostPagination 

    def get_queryset(self):
            team_id = self.request.data.get('team_id')
            user_id = self.request.data.get('user_id')
            group_id = self.request.data.get('group_id')
            

            if team_id:
                return Gallary.objects.filter(team_id=team_id, album_id__isnull=True).order_by('-created_at')
            elif group_id:
                return Gallary.objects.filter(group_id=group_id, album_id__isnull=True).order_by('-created_at')
           
            elif user_id:
                return Gallary.objects.filter(user_id=user_id, team_id__isnull=True, group_id__isnull=True, album_id__isnull=True).order_by('-created_at')
            else:
                return Gallary.objects.filter(user=self.request.user, team_id__isnull=True, group_id__isnull=True, album_id__isnull=True).order_by('-created_at')

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        queryset = self.get_queryset()
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            image_extensions = ('.jfif', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
            video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')

            # Create Q objects for filtering images and videos
            image_query = Q()
            for ext in image_extensions:
                image_query |= Q(media_file__iendswith=ext)

            video_query = Q()
            for ext in video_extensions:
                video_query |= Q(media_file__iendswith=ext)

            # Filter images and videos based on the Q objects
            images = queryset.filter(image_query)
            videos = queryset.filter(video_query)

            # Serialize images and videos separately
            image_serializer = self.get_serializer(images, many=True)
            video_serializer = self.get_serializer(videos, many=True)

            return Response({
                'status': 1,
                'message': _('Gallery entries fetched successfully.'),
                'data': {
                    'images': image_serializer.data,
                    'videos': video_serializer.data
                },
                'total_records': queryset.count(),  # This should count all records
                'total_pages': self.paginator.page.paginator.num_pages if page is not None else 1,
                'current_page': self.paginator.page.number if page is not None else 1
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 0,
            'message': _('No gallery entries found.')
        }, status=status.HTTP_404_NOT_FOUND)

###########  gallary list delete ################


class GallaryDeleteAPIView(generics.DestroyAPIView):
    queryset = Gallary.objects.all()
    serializer_class = GallarySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_object(self):
        # Fetch the 'id' from the request body
        id = self.request.data.get('gallary_id')
        if not id:
            raise ValidationError({"gallary_id": _("This field is required.")})
        try:
            return Gallary.objects.get(id=id)
        except Gallary.DoesNotExist:
            raise ({"message": _("Gallery entry not found.")})

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
                'message': _('Gallery entry deleted successfully.')
            }, status=status.HTTP_204_NO_CONTENT)

        except Gallary.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Gallery entry not found.')
            }, status=status.HTTP_404_NOT_FOUND)
        
###########  album list delete ################

class AlbumDeleteAPIView(generics.DestroyAPIView):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Fetch the 'id' from the request body
        id = self.request.data.get('album_id')
        if not id:
            raise ValidationError({"album_id": _("This field is required.")})
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
            }, status=status.HTTP_204_NO_CONTENT)

        except Album.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Album not found.')
            }, status=status.HTTP_404_NOT_FOUND)


########################################################################  Sponsor API ################################################################
class SponsorAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    team_query_param = 'team_id'  # Custom page number param in the body
    group_query_param = 'group_id'  # Custom page number param in the body

    def get(self, request):
        team_id = request.query_params.get(self.team_query_param)
        group_id = request.query_params.get(self.group_query_param)
        
        if team_id:
            sponsors = Sponsor.objects.filter(team_id=team_id).order_by('-created_at')
        elif group_id:
            sponsors = Sponsor.objects.filter(group_id=group_id).order_by('-created_at')
        else:
            return Response({
                "status": 0,
                "message": _("Please provide team_id or group_id"),
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare response data
        sponsor_list = [
            {
                "id": sponsor.id,
                "name": sponsor.name,
                "logo": sponsor.logo.url if sponsor.logo else None,
                "phone": sponsor.phone,
                "email": sponsor.email,
                "url": sponsor.url,
                "team_id": sponsor.team_id.id if sponsor.team_id else None,
                "group_id": sponsor.group_id.id if sponsor.group_id else None,
                "created_at": sponsor.created_at,
                "updated_at": sponsor.updated_at
            } for sponsor in sponsors
        ]
        
        return Response({
            "status": 1,
            "message": _("Sponsers list found sucessfully"),
            "data": sponsor_list
        }, status=status.HTTP_200_OK)
        
    def post(self, request):
        data = request.data
        
        name = data.get('name')
        phone = data.get('phone')
        email = data.get('email')
        url = data.get('url')
        team_id = data.get('team_id')
        group_id = data.get('group_id')
        
        # Ensure team_id or group_id is provided
        if not team_id and not group_id:
            return Response({
                "status": 0,
                "message": _("Please provide team_id or group_id")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Handle the image upload
            logo = None
            if "logo" in request.FILES:
                image = request.FILES["logo"]
                file_extension = image.name.split('.')[-1]
                file_name = f"sponsors_images/{name}_{request.user.username}.{file_extension}"
                image_path = default_storage.save(file_name, image)
                logo = image_path  # Assign the saved image path to the logo variable

            # Create the new sponsor
            sponsor = Sponsor.objects.create(
                name=name,
                logo=logo,
                phone=phone,
                email=email,
                url=url,
                team_id=Team.objects.get(id=team_id) if team_id else None,
                group_id=TrainingGroups.objects.get(id=group_id) if group_id else None
            )

            return Response({
                "status": 1,
                "message": _("Sponsor created successfully"),
                "data": {
                    "id": sponsor.id,
                    "name": sponsor.name,
                    "logo": sponsor.logo.url if sponsor.logo else None,
                    "phone": sponsor.phone,
                    "email": sponsor.email,
                    "url": sponsor.url,
                    "team_id": sponsor.team_id.id if sponsor.team_id else None,
                    "group_id": sponsor.group_id.id if sponsor.group_id else None,
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
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can create reports
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def perform_create(self, serializer):
        # Automatically associate the report with the logged-in user
        serializer.save(user_id=self.request.user)

    def create(self, request, *args, **kwargs):
        # Overriding the create method to return a custom response
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post_report = self.perform_create(serializer)  # Saving the report

        return Response({
            'status': 1,
            'message': _('Post Report Submitted Successfully.'),
            'data': serializer.data  # Directly include the serialized data
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

class TeamViewAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
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
    

    def post(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        user = request.user

        # Fetch the team type (category) by its ID from the request
        try:
            team_type_id = request.data.get('team_type')
            team_type_instance = Category.objects.get(id=team_type_id)
        except Category.DoesNotExist:
            return Response({
                'status': 0, 
                'message': _('Invalid team type provided.')}, 
                status=status.HTTP_400_BAD_REQUEST
                )

        # Check if team_username already exists in either the Team or User model
        team_username = request.data.get('team_username')

        if Team.objects.filter(team_username=team_username).exists() or User.objects.filter(username=team_username).exists():
            return Response({
                'status': 0, 
                'message': _('The username is already in use either as a team username or a user username.')}, 
                status=status.HTTP_400_BAD_REQUEST)

        # Create a new team instance
        team_instance = Team(
            user_id=user,
            team_name=request.data.get('team_name'),
            team_username=request.data.get('team_username'),
            team_type=team_type_instance,
        )

        # Handle file uploads (same as your existing logic)
        if 'team_logo' in request.FILES:
            logo = request.FILES['team_logo']
            file_extension = logo.name.split('.')[-1]
            file_name = f"team/team_logo/{team_instance.team_name}_{team_instance.id}.{file_extension}"
            logo_path = default_storage.save(file_name, logo)
            team_instance.team_logo = logo_path

        # Save the team instance
        team_instance.save()

        # Fetch the newly created team instance from the database to return fresh data
        team_instance = Team.objects.get(id=team_instance.id)

        # Serialize the data
        serializer = TeamSerializer(team_instance)

        return Response({
            'status': 1,
            'message': _('Team created successfully.'),
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    
    def put(self, request):
        team_id = request.data.get('team_id')
        user = request.user
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

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

        # Update other fields from the request data
        team_instance.team_name = request.data.get('team_name', team_instance.team_name)
        team_instance.team_username = request.data.get('team_username', team_instance.team_username)
        team_instance.bio = request.data.get('bio', team_instance.bio)
        team_instance.team_establishment_date = request.data.get('team_establishment_date', team_instance.team_establishment_date)
        team_instance.team_president = request.data.get('team_president', team_instance.team_president)

        # Add the remaining fields from the model
        team_instance.latitude = request.data.get('latitude', team_instance.latitude)
        team_instance.longitude = request.data.get('longitude', team_instance.longitude)
        team_instance.address = request.data.get('address', team_instance.address)
        team_instance.house_no = request.data.get('house_no', team_instance.house_no)
        team_instance.premises = request.data.get('premises', team_instance.premises)
        team_instance.street = request.data.get('street', team_instance.street)
        team_instance.city = request.data.get('city', team_instance.city)
        team_instance.state = request.data.get('state', team_instance.state)
        team_instance.country_name = request.data.get('country_name', team_instance.country_name)
        team_instance.postalCode = request.data.get('postalCode', team_instance.postalCode)
        team_instance.country_code = request.data.get('country_code', team_instance.country_code)
        team_instance.country_id = request.data.get('country_id', team_instance.country_id)
        team_instance.city_id = request.data.get('city_id', team_instance.city_id)
        team_instance.phone = request.data.get('phone', team_instance.phone)
        team_instance.email = request.data.get('email', team_instance.email)
        team_instance.age_group = request.data.get('age_group', team_instance.age_group)

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

        # Handle multiple team uniform uploads (if necessary)
        if 'team_uniform' in request.FILES:
            uniforms = request.FILES.getlist('team_uniform')
            team_uniform_images = []

            for uniform in uniforms:
                directory_path = os.path.join(settings.MEDIA_ROOT, 'team', 'team_uniform')
                os.makedirs(directory_path, exist_ok=True)
                file_path = os.path.join(directory_path, uniform.name)
                with open(file_path, 'wb+') as destination:
                    for chunk in uniform.chunks():
                        destination.write(chunk)
                team_uniform_images.append(f"team/team_uniform/{uniform.name}")

            team_instance.team_uniform = ','.join(team_uniform_images)

        team_instance.save()

        # Fetch the updated team instance from the database to return fresh data
        team_instance = Team.objects.get(id=team_instance.id)

        # Serialize the data
        serializer = TeamSerializer(team_instance)

        return Response({
            'status': 1,
            'message': _('Team updated successfully.'),
            'data': serializer.data
        }, status=status.HTTP_200_OK)



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
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        from_user = request.user  # Always the user sending the request

        # Retrieve the source (from_*): the user/team/group initiating the follow request
        from_team_id = request.data.get('from_team')
        from_group_id = request.data.get('from_group')

        # Retrieve the target (to_*): the user/team/group being followed
        to_user_id = request.data.get('to_user')
        to_team_id = request.data.get('to_team')
        to_group_id = request.data.get('to_group')

        # Ensure only one "from" field is filled
        if from_team_id and from_group_id:
            return Response({
                "status": 0,
                "message": _("You can only follow from either a team or a group, not both.")
            }, status=status.HTTP_400_BAD_REQUEST)

        # Ensure only one "to" field is filled
        if [to_user_id, to_team_id, to_group_id].count(None) < 2:
            return Response({
                "status": 0,
                "message": _("You can only follow a user, a team, or a group, not multiple.")
            }, status=status.HTTP_400_BAD_REQUEST)

        # Prepare the follow request based on provided data
        follow_request = FollowRequest.objects.filter(
            from_user=from_user if not from_team_id and not from_group_id else None,
            from_team_id=from_team_id,
            from_group_id=from_group_id,
            to_user_id=to_user_id,
            to_team_id=to_team_id,
            to_group_id=to_group_id
        ).first()

        if follow_request:
            # Unfollow logic
            follow_request.delete()
            return Response({
                "status": 1,
                "message": _("Unfollowed successfully.")
            }, status=status.HTTP_200_OK)
        else:
            # Follow logic
            FollowRequest.objects.create(
                from_user=from_user if not from_team_id and not from_group_id else None,
                from_team_id=from_team_id,
                from_group_id=from_group_id,
                to_user_id=to_user_id,
                to_team_id=to_team_id,
                to_group_id=to_group_id
            )
            return Response({
                "status": 1,
                "message": _("Followed successfully.")
            }, status=status.HTTP_201_CREATED)

####################################### LIST OF FOLLOWERS #######################################
class ListFollowersAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        to_user_id = request.data.get('to_user')
        to_team_id = request.data.get('to_team')
        to_group_id = request.data.get('to_group')

        # Ensure only one entity type is requested
        if [to_user_id, to_team_id, to_group_id].count(None) < 2:
            return Response({
                "status": 0,
                "message": _("You can only fetch followers for one entity type (user, team, or group).")
            }, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve followers
        followers = FollowRequest.objects.filter(
            to_user_id=to_user_id if to_user_id else None,
            to_team_id=to_team_id if to_team_id else None,
            to_group_id=to_group_id if to_group_id else None
        ).select_related('from_user', 'from_team', 'from_group')

        # Format followers list
        followers_list = [
            {
                "id": follower.get_from_entity().id,
                "name": getattr(follower.get_from_entity(), 'username', None) or
                        getattr(follower.get_from_entity(), 'team_name', None) or
                        getattr(follower.get_from_entity(), 'group_name', None),
                "profile_picture": getattr(follower.get_from_entity(), 'profile_picture', None) or
                                   getattr(follower.get_from_entity(), 'team_logo', None) or
                                   getattr(follower.get_from_entity(), 'group_logo', None)
            }
            for follower in followers
        ]

        return Response({
            "status": 1,
            "message": _("Followers list fetched successfully."),
            "data": followers_list
        }, status=status.HTTP_200_OK)


##################################### LIST OF FOLLOWING #######################################
class ListFollowingAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        from_user = request.user

        # Retrieve the following
        following = FollowRequest.objects.filter(
            from_user=from_user
        ).select_related('to_user', 'to_team', 'to_group')

        # Format the following list
        following_list = [
            {
                "id": follow.get_to_entity().id,
                "name": getattr(follow.get_to_entity(), 'username', None) or
                        getattr(follow.get_to_entity(), 'team_name', None) or
                        getattr(follow.get_to_entity(), 'group_name', None),
                "profile_picture": getattr(follow.get_to_entity(), 'profile_picture', None) or
                                   getattr(follow.get_to_entity(), 'team_logo', None) or
                                   getattr(follow.get_to_entity(), 'group_logo', None)
            }
            for follow in following
        ]

        return Response({
            "status": 1,
            "message": _("Following list fetched successfully."),
            "data": following_list
        }, status=status.HTTP_200_OK)
