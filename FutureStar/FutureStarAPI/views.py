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


def get_user_data(user, request):
    """Returns a dictionary with all user details."""
    followers_count = FollowRequest.get_follower_count(user)
    following_count = FollowRequest.get_following_count(user)
    post_count = Post.objects.filter(user=user, team__isnull=True).count()
    gender_name = None
    if user.gender:
        serializer = UserGenderSerializer(user.gender, context={'request': request})
        gender_name = serializer.data['name']

    return {
        'id': user.id,
        'followers_count' : followers_count,
        'following_count' : following_count,
        'post_count' : post_count,
        'user_role' : user.role_id,
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
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        registration_type = request.data.get('type')
        

        # Handle Registration Type 1 (Normal registration)
        if registration_type == 1 :
            username = request.data.get('username')
            phone = request.data.get('phone')
            email = request.data.get('email')
            password = request.data.get('password')
            # Check if username or phone already exists in User table
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

            # If user does not exist, generate OTP and store it in OTPSave table
            otp = generate_otp()
            # Save or update the OTP in OTPSave
            otp_record, created = OTPSave.objects.update_or_create(
                phone=phone,  # or username based on uniqueness
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


            # If email does not exist, check username and phone if provided
            if username and phone:
                # Validate if username or phone already exists in User table
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

                # Generate OTP and save in OTPSave for type 2/3 with phone, email, and password
                otp = generate_otp()
                random_password = self.generate_random_password()
                password = random_password  # Set the generated password
                otp_record, created = OTPSave.objects.update_or_create(
                    phone=phone,  # Assuming phone is required
                    defaults={'phone': phone,'OTP': otp}
                )

                return Response({
                    'status': 1,
                    'message': _('OTP sent successfully.'),
                    'data': otp  # Send OTP in response for development.
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

        # Get old profile picture and card header (before any changes)
        old_profile_picture = user.profile_picture
        old_card_header = user.card_header

        # Update all fields from request data
        user.fullname = request.data.get('fullname', user.fullname)
        user.bio = request.data.get('bio', user.bio)
        date_of_birth = request.data.get('date_of_birth')
        if date_of_birth is not None:
            try:
                user.date_of_birth = date_of_birth  # No specific format validator here, assuming the input is correct
            except (ValueError, TypeError):
                return Response({
                    'status': 2,
                    # 'message': _('Invalid date format for date_of_birth.')
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            user.date_of_birth = None
        user.age = request.data.get('age', user.age)

        # Assign gender by fetching the corresponding UserGender instance
        gender_id = request.data.get('gender')
       
        if gender_id is None:
            
            try:
                user.gender = UserGender.objects.get(id=gender_id)  # Fetch UserGender instance
            except UserGender.DoesNotExist:
                return Response({
                    'status': 2,
                    'message': _('Invalid gender specified.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Handle country
        country_id = request.data.get('country')
        if country_id is None:
            try:
                user.country = Country.objects.get(id=country_id)  # Fetch Country instance
            except Country.DoesNotExist:
                return Response({
                    'status': 2,
                    'message': _('Invalid country specified.')
                }, status=status.HTTP_400_BAD_REQUEST)

        # Handle city
        city_id = request.data.get('city')
        if city_id is None:
            if not user.country:  # Ensure country is set before updating city
                return Response({
                    'status': 2,
                    'message': _('City cannot be set without a valid country.')
                }, status=status.HTTP_400_BAD_REQUEST)

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

        # Perform standard pagination
        return super().paginate_queryset(queryset, request, view)



###################################################################################### POST MODULE ################################################################################


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
            serializer = self.get_serializer(page, many=True)
            total_records = queryset.count()
            total_pages = self.paginator.page.paginator.num_pages

            # Custom response to include pagination data
            return Response({
                'status': 1,
                'message': _('All posts fetched successfully.'),
                'data': serializer.data,
                'meta': {
                    'total_records': total_records,
                    'total_pages': total_pages,
                    'current_page': self.paginator.page.number
                }
            }, status=status.HTTP_200_OK)

        # In case pagination is not needed or there's no data
        serializer = self.get_serializer(queryset, many=True)
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
        else:
            return Post.objects.filter(user=user_id).order_by('-date_created')

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        queryset = self.get_queryset()

        # Paginate the queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            total_records = queryset.count()
            total_pages = self.paginator.page.paginator.num_pages

            # Custom response to include pagination data
            return Response({
                'status': 1,
                'message': _('Posts fetched successfully.'),
                'data': serializer.data,
                'meta': {
                    'total_records': total_records,
                    'total_pages': total_pages,
                    'current_page': self.paginator.page.number
                }
            }, status=status.HTTP_200_OK)

        # In case pagination is not needed or there's no data
        serializer = self.get_serializer(queryset, many=True)
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
        group_id = request.data.get('group_id')  # Optional team_id from request data

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
            elif group_id:
                try:
                    group = TrainingGroups.objects.get(id=group_id)
                except TrainingGroups.DoesNotExist:
                    return Response({
                        'status': 0,
                        'message': _('Group not found.')
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Save the post with a team
                post = serializer.save(user=request.user, group_id=group)
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
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        post_id = request.data.get('post_id')
        team_id = request.data.get('team_id')
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

        serializer = PostSerializer(post)

        return Response({
            'status': 1,
            'message': _('Post details fetched successfully.'),
            'data': serializer.data
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
        team_id = data.get('team_id')  # Optional team_id
        group_id = data.get('group_id')  # Optional team_id
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
            elif group_id:
                post = Post.objects.get(id=post_id, group_id=group_id)
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
            team_id=team_id,  # Set the team_id if provided
            group_id=group_id  # Set the team_id if provided
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
            # Create the album first
            album_instance = serializer.save(user=request.user)

            # Now handle the media file upload for the gallery
            media_file = request.FILES.get('media_file')  # Adjust field name accordingly
            content_type=self.request.data.get('content_type')
            if media_file:
                # Create a gallery entry using the media file
                gallary_serializer = GallarySerializer(data={
                    'user': request.user.id,
                    'media_file': media_file,
                    'content_type' : content_type,
                    'album_id': album_instance.id,
                    # You may want to include other fields like team_id, group_id if needed
                })
                
                if gallary_serializer.is_valid():
                    gallary_serializer.save()  # Save the gallery entry

                else:
                    # If gallery entry fails, you might want to rollback the album creation
                    album_instance.delete()  # Rollback album creation
                    return Response({
                        'status': 0,
                        'message': _('Gallery entry creation failed.'),
                        'errors': gallary_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'status': 1,
                'message': _('Album created successfully.'),
                'data': serializer.data
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
        user_id=self.request.data.get('user_id')
        group_id=self.request.data.get('group_id')

    

        queryset = Album.objects.all()
        if team_id:
            queryset = queryset.filter(team_id=team_id)
        elif group_id:
            queryset = queryset.filter(group_id=group_id)

      
        else:
           
            queryset = queryset.filter(user=user_id)
 
        return queryset.order_by('-created_at')

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
    serializer_class = GallarySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = CustomPostPagination 


    def get_queryset(self):
        team_id = self.request.data.get('team_id')
      
        user_id=self.request.data.get('user_id')
        group_id=self.request.data.get('group_id')
        content_type=self.request.data.get('content_type')



        queryset = Gallary.objects.filter(album_id__isnull=True)        
        if team_id:
            queryset = queryset.filter(team_id=team_id)
        if group_id:
            queryset = queryset.filter(group_id=group_id)
      
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        return queryset.order_by('-created_at')

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
                'message': _('Gallary Items fetched successfully.'),
                'data': serializer.data,
                'total_records': total_records,
                'total_pages': total_pages,
                'current_page': self.paginator.page.number
                
            }, status=status.HTTP_200_OK)


        gallary = self.get_queryset()
        image_extensions = ('jfif','PNG','.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')

        # Filter images and videos based on their file extensions
        images = [item for item in gallary if item.media_file.name.endswith(image_extensions)]
        videos = [item for item in gallary if item.media_file.name.endswith(video_extensions)]
        
        # Serialize images and videos separately
        image_serializer = self.get_serializer(images, many=True)
        video_serializer = self.get_serializer(videos, many=True)

        return Response({
            'status': 1,
            'message': _('Gallery entries fetched successfully.'),
            'data': {
                'images': image_serializer.data,
                'videos': video_serializer.data
            }
        }, status=status.HTTP_200_OK)



class GallaryCreateAPIView(generics.CreateAPIView):
    serializer_class = GallarySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract album_id, team_id, and training_group_id from the request
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
                except TrainingGroup.DoesNotExist:
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
                serializer.save(user=request.user, album_id=album_instance, group_id=group_instance)
             # Condition 1: Both team_id and album_id are provided
            if team_instance and album_instance:
                serializer.save(user=request.user, album_id=album_instance, team_id=team_instance)

            # Condition 2: Only album_id is provided (check if it belongs to the user)
            elif album_instance:
                if album_instance.user == request.user:  # Assuming Album has a user field
                    serializer.save(user=request.user, album_id=album_instance)
                else:
                    raise ValidationError(_("You do not have permission to add to this album."))

            # Condition 3: Neither team_id nor album_id is provided
            else:
                serializer.save(user=request.user, album_id=None)

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
    serializer_class = GallarySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = CustomPostPagination 


    def get_queryset(self):
        team_id = self.request.data.get('team_id')
      
        user_id=self.request.data.get('user_id')
        group_id=self.request.data.get('group_id')
       

        queryset = Gallary.objects.filter(album_id__isnull=True)        
        if team_id:
            queryset = queryset.filter(team_id=team_id)
      
        if user_id:
            queryset = queryset.filter(user_id=user_id)
      
        if group_id:
            queryset = queryset.filter(group_id=group_id)


        return queryset.order_by('-created_at')

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
                'message': _('Latest Gallary Items fetched successfully.'),
                'data': serializer.data,
                'total_records': total_records,
                'total_pages': total_pages,
                'current_page': self.paginator.page.number
                
            }, status=status.HTTP_200_OK)

        gallary = self.get_queryset()
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')

        # Filter images and videos based on their file extensions
        images = [item for item in gallary if item.media_file.name.endswith(image_extensions)]
        videos = [item for item in gallary if item.media_file.name.endswith(video_extensions)]
        
        latest_images = images[:9]  # Slice to get the first 9 images
        latest_videos = videos[:9] 
        
        # Serialize images and videos separately
        image_serializer = self.get_serializer(latest_images, many=True)
        video_serializer = self.get_serializer(latest_videos, many=True)

        return Response({
            'status': 1,
            'message': _('Gallery entries fetched successfully.'),
            'data': {
                'images': image_serializer.data,
                'videos': video_serializer.data
            }
        }, status=status.HTTP_200_OK)



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

    def get(self, request, *args, **kwargs):
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
    

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
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
        from_user = request.user
        to_user_id = request.data.get("to_user")
        
        to_user = get_object_or_404(User, id=to_user_id)
        
        follow_request = FollowRequest.objects.filter(from_user=from_user, to_user=to_user).first()
        
        if follow_request:
            # Unfollow
            follow_request.delete()
            return Response({
                "status": 1,
                "message": _("You have unfollowed %(username)s.") % {'username': to_user.username}
            }, status=status.HTTP_200_OK)
        else:
            # Follow
            FollowRequest.objects.create(from_user=from_user, to_user=to_user)
            return Response({
                "status": 1,
                "message": _("You are now following %(username)s.") % {'username': to_user.username}
            }, status=status.HTTP_201_CREATED)



####################################### LIST OF FOLLOWERS #######################################
class UserFollowersAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    def post(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        user_id = request.data.get('user_id')

        if not user_id:
            return Response({
                "status": 0,
                "message": _("User ID is required.")
            }, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, id=user_id)

        followers = FollowRequest.objects.filter(to_user=user).select_related('from_user')

        followers_list = [
            {
                "id": follower.from_user.id,
                "username": follower.from_user.username,
                "profile_picture": follower.from_user.profile_picture.url if follower.from_user.profile_picture else None
            }
            for follower in followers
        ]

        return Response({
            "status": 1,
            "message": _("Followers fetched successfully."),
            "data": followers_list
        }, status=status.HTTP_200_OK)


##################################### LIST OF FOLLOWING ###############################
class UserFollowingAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    def post(self, request):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        user_id = request.data.get('user_id')

        if not user_id:
            return Response({
                "status": 0,
                "message": _("User ID is required.")
            }, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, id=user_id)

        following = FollowRequest.objects.filter(from_user=user).select_related('to_user')

        following_list = [
            {
                "id": follow.to_user.id,
                "username": follow.to_user.username,
                "profile_picture": follow.to_user.profile_picture.url if follow.to_user.profile_picture else None
            }
            for follow in following
        ]

        return Response({
            "status": 1,
            "message": _("Following users fetched successfully."),
            "data": following_list
        }, status=status.HTTP_200_OK)