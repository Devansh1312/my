from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from FutureStar_App.models import User
import jwt

class MiddlewareToken(MiddlewareMixin):

    def process_request(self, request, *args, **kwargs):
        # Bypass authentication for specific endpoints like register, login, and admin
        if request.path.startswith("/api/register/") or request.path.startswith("/api/playerlogin/") or request.path.startswith("/api/forgot-password/") or request.path.startswith("/api/verify-otp/") or request.path.startswith("/api/change-password-otp/") or request.path.startswith("/api/media/") or request.path.startswith("/admin/"):
            return None

        # Retrieve the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({
                'status': 2,
                'message': 'Authorization header is missing or invalid'
            }, status=200)

        # Extract the token
        token = auth_header.split(' ')[1]

        try:
            # Decode the JWT token using the SECRET_KEY
            payload = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=['HS256'])

            # Get the user associated with the token
            user = User.objects.get(id=payload['user_id'])

            # Attach the user to the request object for use in the views
            request.user = user

        except jwt.ExpiredSignatureError:
            return JsonResponse({
                'status': 2,
                'message': 'Token has expired'
            }, status=200)
        except jwt.InvalidTokenError:
            return JsonResponse({
                'status': 2,
                'message': 'Invalid token'
            }, status=200)
        except User.DoesNotExist:
            return JsonResponse({
                'status': 2,
                'message': 'User does not exist'
            }, status=200)
        except Exception as e:
            # Catch any other unexpected errors
            print(f"Unknown Error: {e}")
            return JsonResponse({
                'status': 2,
                'message': 'Server error'
            }, status=200)

        return None  # Continue processing the request if the token is valid