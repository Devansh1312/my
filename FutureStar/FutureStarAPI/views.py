from django.shortcuts import render, redirect, get_object_or_404
from django import views
# from .forms import *
from django.contrib import messages
from FutureStar_App.models import *
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from rest_framework.permissions import AllowAny
from django.utils.translation import gettext as _
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.translation import gettext as _  # For language translation
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken
import random


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)  # Add these parsers to handle form-data

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'status': 1,
                'message': 'User registered successfully',
            }, status=status.HTTP_201_CREATED)
        return Response({
            'status': 0,
            'message': 'User registration failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Parse language from the headers
        language = request.headers.get('Language', 'en')  # Fallback to 'en' if not provided
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            username_or_phone = serializer.validated_data['username_or_phone']
            password = serializer.validated_data['password']

            # Try to authenticate with either phone or username
            user = User.objects.filter(username=username_or_phone).first() or \
                   User.objects.filter(phone=username_or_phone).first()

            if user and user.check_password(password):
                if user.is_active:
                    # Generate JWT token
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'status': 1,
                        'message': _('Login successful'),
                        'data': {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token),
                            'user': {
                                'id' : user.id,
                                'username': user.username,
                                'phone': user.phone,
                                'email': user.email
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
        return Response({
            'status': 0,
            'message': _('Invalid data'),
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can log out

    def post(self, request, *args, **kwargs):
        try:
            # Get the user's current access token
            token = request.auth
            
            # Blacklist the current token
            # AccessToken(token).blacklist()
            
            return Response({
                'status': 1,
                'message': 'Logout successful',
            }, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({
                'status': 0,
                'message': 'Logout failed',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        

class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            user = User.objects.filter(phone=phone).first()

            if user:
                # Generate new OTP
                otp = str(random.randint(100000, 999999))
                user.otp = otp  # Store the OTP in the user's record
                user.save()

                # Simulate sending OTP via SMS
                print(f"Sending OTP {otp} to {phone}")  # Replace with actual SMS sending code

                return Response({
                    'status': 1,
                    'message': 'OTP sent to your phone.',
                    'otp':otp,
                }, status=status.HTTP_200_OK)

            return Response({
                'status': 0,
                'message': 'User with this phone number does not exist.',
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 0,
            'message': 'Invalid data.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            otp = serializer.validated_data['otp']

            # Fetch user from the database
            user = User.objects.filter(phone=phone).first()

            if user and user.otp == otp:
                return Response({
                    'status': 1,
                    'message': 'OTP verified successfully.',
                }, status=status.HTTP_200_OK)

            return Response({
                'status': 0,
                'message': 'Invalid OTP.',
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 0,
            'message': 'Invalid data.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



class ChangePasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            new_password = serializer.validated_data['new_password']

            # Fetch user from the database
            user = User.objects.filter(phone=phone).first()

            if user:
                user.set_password(new_password)
                user.otp = None  # Clear the OTP after successful password change
                user.save()

                return Response({
                    'status': 1,
                    'message': 'Password changed successfully.',
                }, status=status.HTTP_200_OK)

            return Response({
                'status': 0,
                'message': 'User not found.',
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'status': 0,
            'message': 'Invalid data.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
