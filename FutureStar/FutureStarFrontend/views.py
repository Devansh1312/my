from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from FutureStar_App.models import *
from FutureStarAPI.models import *
from django.views import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import activate
from django.contrib.auth import authenticate, login
import json
import requests
from django.conf import settings
from jwt import decode, exceptions  # For Apple JWT decoding
from django.core.exceptions import ValidationError
import random
from django.db.models import Q
from django.http import JsonResponse



##############################################   HomePage   ########################################################

class HomePage(View):
    def get(self, request, *args, **kwargs):
        marquee = Slider_Content.objects.all()
        app_features = App_Feature.objects.all()
        testimonials = Testimonial.objects.all().order_by('-id')[:3]
        news = News.objects.all().order_by('-id')[:4]
        partner = Partners.objects.all()
        team_members = Team_Members.objects.all().order_by('id')
        cmsfeatures = cms_home_dynamic_field.objects.all() or None
        cms_home_dynamic_achivements = cms_home_dynamic_achivements_field.objects.all() or None

        try:
            cmsdata = cms_pages.objects.get(id=1)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist

        current_language = request.session.get('language', 'en')
        print("get" , current_language )

        context = {
            "marquee": marquee,
            "app_features": app_features,
            "testimonials": testimonials,
            "news": news,
            "partner": partner,
            "team_members": team_members,
            "cmsdata": cmsdata,
            "current_language":current_language,
            "cmsfeatures":cmsfeatures,
            "cms_home_dynamic_achivements":cms_home_dynamic_achivements,


        }
        return render(request, "home.html", context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('index')



##############################################   DiscoverPage   ########################################################

class DiscoverPage(View):
    
    def get(self, request, *args, **kwargs):
        current_language = request.session.get('language', 'en')
        dynamic = cms_dicovery_dynamic_image.objects.all()
        whyus = cms_dicovery_dynamic_view.objects.all()
        try:
            cmsdata = cms_pages.objects.get(id=2)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
        context = {
            "current_language":current_language,
            "cmsdata" : cmsdata,
            "dynamic":dynamic,
            "whyus":whyus
        }
        return render(request, "discover.html",context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('discover')  



##############################################   SuccessStoriesPage   ########################################################

class SuccessStoriesPage(View):
    
    def get(self, request, *args, **kwargs):
        tryout_clubs = Tryout_Club.objects.all()
        current_language = request.session.get('language', 'en')

        try:
            cmsdata = cms_pages.objects.get(id=3)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
        context = {
            "tryout_clubs": tryout_clubs,
            "cmsdata":cmsdata,                        
            "current_language": current_language,

        }
        return render(request, "success-stories.html",context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('success-stories')
    

##############################################   NewsPage   ########################################################

class NewsPage(View):
    
    def get(self, request, *args, **kwargs):
        # Get the selected language from the session, default to 'en'
        current_language = request.session.get('language', 'en')
        try:
            cmsdata = cms_pages.objects.get(id=4)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
        # Get the list of news
        news_list = News.objects.all().order_by('-id')

        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(news_list, 6)  # Display 6 items per page
        
        try:
            news = paginator.page(page)
        except PageNotAnInteger:
            news = paginator.page(1)
        except EmptyPage:
            news = paginator.page(paginator.num_pages)

        # Pass the current language and news to the template
        context = {
            "news": news,
            "current_language": current_language,
            "cmsdata" : cmsdata,
        }
        return render(request, "news.html", context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('news')
    

##############################################   NewsDetailPage   ########################################################

class NewsDetailPage(View):
    def get(self, request, pk):
        # Get the selected language from the session, default to 'en'
        current_language = request.session.get('language', 'en')

        # Get the news item based on the provided pk in the URL
        news = get_object_or_404(News, id=pk)

        # Fetch CMS data
        try:
            cmsdata = cms_pages.objects.get(id=5)
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist

        # Pass the current language and news to the template
        context = {
            "news": news,
            "current_language": current_language,
            "cmsdata": cmsdata,
        }
        return render(request, "news-details.html", context)
    
    def post(self, request, pk):
        # Handle language change
        selected_language = request.POST.get('language', 'en')

        # Store the selected language in the session
        request.session['language'] = selected_language

        # Redirect to the same news detail page with the correct pk
        return redirect('news-detail', pk=pk)



##############################################   AdvertisePage   ########################################################

class AdvertisePage(View):
    
    def get(self, request, *args, **kwargs):
        current_language = request.session.get('language', 'en')
        dynamic_field = cms_advertise_section_2_dynamic_field.objects.all()
        partnership_dynamic_field = cms_advertise_Partnership_dynamic_field.objects.all()
        ads_dynamic_field = cms_advertise_ads_dynamic_field.objects.all()
        premium_dynamic_field = cms_advertise_premium_dynamic_field.objects.all()

        try:
            cmsdata = cms_pages.objects.get(id=6)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
        context = {
            "current_language":current_language,
            "cmsdata" : cmsdata,
            "dynamic_field":dynamic_field,
            "partnership_dynamic_field":partnership_dynamic_field,
            "ads_dynamic_field":ads_dynamic_field,
            "premium_dynamic_field":premium_dynamic_field,
        }
       
        return render(request, "advertise.html",context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('advertise')

##############################################   AboutPage   ########################################################

class AboutPage(View):
    
    def get(self, request, *args, **kwargs):
        
        marquee = Slider_Content.objects.all()
        testimonials = Testimonial.objects.all().order_by('-id')[:3]
        global_clients = Global_Clients.objects.all()
        team_members = Team_Members.objects.all().order_by('id')
        current_language = request.session.get('language', 'en')
        try:
            cmsdata = cms_pages.objects.get(id=7)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist

        context = {
            "marquee": marquee,
            "testimonials": testimonials,
            "global_clients": global_clients,
            "current_language":current_language,
            "cmsdata" : cmsdata,
            "team_members" : team_members,

        }
        return render(request, "about.html",context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language

        return redirect('about')


##############################################   ContactPage   ########################################################

class ContactPage(View):
    
    def get(self, request, *args, **kwargs):
        try:
            cmsdata = cms_pages.objects.get(id=8)  # Fetch the CMS data
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle case where the CMS data doesn't exist

        current_language = request.session.get('language', 'en')

        context = {
            "current_language": current_language,
            "cmsdata": cmsdata,
        }
        return render(request, "contact.html", context)

    def post(self, request):
        # Fetch form data
        fullname = request.POST.get("fullname", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        message = request.POST.get("message", "").strip()
        selected_language = request.POST.get('language', 'en')
        current_language = request.session['language'] = selected_language

        try:
            cmsdata = cms_pages.objects.get(id=8)  # Fetch CMS data again for context
        except cms_pages.DoesNotExist:
            cmsdata = None

        # If no contact form fields are filled, assume the user is only changing the language
        if not fullname and not phone and not email and not message:
            messages.success(request, "Language changed successfully!")
            return redirect('contact')  # Redirect after language change

        # Validation: Ensure all fields are filled
        if not fullname or not phone or not email or not message:
            messages.error(request, "All fields are required for submitting an inquiry.")
            context = {
                "current_language": current_language,
                "cmsdata": cmsdata,
            }
            return render(request, "contact.html", context)

        # Save the inquiry
        Inquire.objects.create(
            fullname=fullname,
            phone=phone,
            email=email,
            message=message,
        )

        # Success message and redirect after submission
        messages.success(request, "Inquiry submitted successfully.")
        return redirect("contact")

##############################################   PrivacyPolicyPage   ########################################################

class PrivacyPolicyPage(View):
    
    def get(self, request, *args, **kwargs):
        try:
            cmsdata = cms_pages.objects.get(id=10)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist

        current_language = request.session.get('language', 'en')

        context = {
            "current_language": current_language,
            "cmsdata": cmsdata,
        } 
        return render(request, "privacy-policy.html",context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('privacy-policy')
    

##############################################   TermsofServicesPage   ########################################################

class TermsofServicesPage(View):
    
    def get(self, request, *args, **kwargs):
        
        try:
            cmsdata = cms_pages.objects.get(id=9)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
            
        current_language = request.session.get('language', 'en')

        context = {
            "current_language": current_language,
            "cmsdata": cmsdata,
        } 

        return render(request, "terms-of-services.html",context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('terms-of-services')  



##############################################   PlayerDashboardPage   ########################################################

class PlayerDashboardPage(LoginRequiredMixin,View):
    
    def get(self, request, *args, **kwargs):
    
        current_language = request.session.get('language', 'en')
        try:
            cmsdata = cms_pages.objects.get(id=14)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist

        context = {
            "current_language": current_language,
            "cmsdata":cmsdata
            # "cmsdata": cmsdata,
        } 

        return render(request, "PlayerDashboard.html",context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('player-dashboard')  






##############################################   LoginPage   ########################################################

class LoginPage(View):

    def get(self, request, *args, **kwargs):
        current_language = request.session.get('language', 'en')
        try:
            cmsdata = cms_pages.objects.get(id=12)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
        context = {
            "current_language": current_language,
            "cmsdata": cmsdata,
            # "google_client_id": settings.GOOGLE_CLIENT_ID,
            # "apple_client_id": settings.APPLE_CLIENT_ID,
            # "apple_redirect_uri": settings.APPLE_REDIRECT_URI,
            # "social_auth_state_string": settings.SOCIAL_AUTH_STATE_STRING,
        }
        return render(request, "login.html", context)

    def post(self, request, *args, **kwargs):
        # Handle language change
        selected_language = request.POST.get('language', 'en')
        current_language = request.session['language'] = selected_language
        
        # Fetch login type
        login_type = int(request.POST.get('login_type', 1))
        username_or_phone = request.POST.get('username_or_phone')
        password = request.POST.get('password')
       # If only language is changed (no registration form fields are filled)
        if not username_or_phone and not password and not password:
            messages.success(request, "Language changed successfully!")
            return redirect('login')

        # Proceed with normal login process
        if login_type == 1:
            username_or_phone = request.POST.get('username_or_phone')
            password = request.POST.get('password')

            # Authenticate user
            user = authenticate(request, username=username_or_phone, password=password)

            if user:
                if user.is_active:
                    login(request, user)
                    user.device_type = "Website"
                    user.last_login = timezone.now()
                    user.save()
                    messages.success(request, "Login successful!")
                    return redirect('Dashboard' if user.role_id == 1 else 'player-dashboard')
                messages.error(request, "Account is inactive.")
            else:
                messages.error(request, "Invalid credentials.")

        return redirect('login')

    #     elif login_type == 2:
    #         google_token = request.POST.get('google_token')
    #         if google_token:
    #             google_user_info = self.verify_google_token(google_token)
    #             if google_user_info:
    #                 return self.handle_social_login(request, google_user_info, login_type='google')

    #         messages.error(request, "Failed to authenticate with Google.")
    #         return redirect('login')

    #     elif login_type == 3:
    #         apple_token = request.POST.get('apple_token')
    #         if apple_token:
    #             apple_user_info = self.verify_apple_token(apple_token)
    #             if apple_user_info:
    #                 return self.handle_social_login(request, apple_user_info, login_type='apple')

    #         messages.error(request, "Failed to authenticate with Apple.")
    #         return redirect('login')

    #     messages.error(request, "Invalid login type.")
    #     return redirect('login')

    # def verify_google_token(self, token):
    #     try:
    #         response = requests.get(f'https://oauth2.googleapis.com/tokeninfo?id_token={token}')
    #         if response.status_code == 200:
    #             return response.json()
    #     except Exception as e:
    #         print(f"Error verifying Google token: {e}")
    #     return None

    # def verify_apple_token(self, token):
    #     try:
    #         apple_public_keys = requests.get('https://appleid.apple.com/auth/keys').json()
    #         key = apple_public_keys['keys'][0]
    #         decoded_token = decode(token, key, algorithms=['RS256'], audience=settings.APPLE_CLIENT_ID)
    #         return decoded_token
    #     except exceptions.InvalidTokenError as e:
    #         print(f"Error verifying Apple token: {e}")
    #     return None

    # def handle_social_login(self, request, user_info, login_type):
    #     email = user_info.get('email')
    #     if not email:
    #         messages.error(request, f"Unable to retrieve email for {login_type} login.")
    #         return redirect('login')

    #     user = User.objects.filter(email=email).first()

    #     if user:
    #         if user.is_active:
    #             login(request, user)
    #             user.device_type = "Website"
    #             user.last_login = timezone.now()
    #             user.save()
    #             messages.success(request, f"Login successful via {login_type.capitalize()}!")
    #             return redirect('Dashboard' if user.role_id == 1 else 'player-dashboard')
    #         else:
    #             messages.error(request, "Account is inactive.")
    #             return redirect('login')
    #     else:
    #         username = email.split('@')[0]
    #         user = User.objects.create_user(
    #             username=username,
    #             email=email,
    #             password=None,
    #             role_id=2,
    #             is_active=True,
    #         )
    #         login(request, user)
    #         user.device_type = "Website"
    #         user.last_login = timezone.now()
    #         user.save()
    #         messages.success(request, f"User created and login successful via {login_type.capitalize()}!")
    #         return redirect('player-dashboard')




# Generate a random 6-digit OTP
def generate_otp():
    return str(random.randint(100000, 999999))

#################################### Register Page ##########################################
class RegisterPage(View):
    def get(self, request, *args, **kwargs):
        current_language = request.session.get('language', 'en')
        # Fetching specific CMS data
        try:
            cmsdata = cms_pages.objects.get(id=13)
        except cms_pages.DoesNotExist:
            cmsdata = None

        context = {
            "current_language": current_language,
            "cmsdata": cmsdata,
        }
        return render(request, "register.html", context)

    def post(self, request, *args, **kwargs):
        register_type = request.POST.get("register_type")
        
        if register_type == "1":  # Normal registration
            return self.handle_normal_registration(request)
        
        else:  # Google or Apple sign-up
            email = request.POST.get("email")  # Get email from OAuth
            return self.handle_social_signup(email, register_type)

    def handle_normal_registration(self, request):
        username = request.POST.get("username")
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirmPassword")

        # Validate password match
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect("register")

        # Check if username or phone already exists in the User table
        if User.objects.filter(Q(username=username) | Q(phone=phone)).exists():
            messages.error(request, "Username or phone number already exists.")
            return redirect("register")

        # Generate OTP and save user details in OTPSave table
        otp = generate_otp()
        OTPSave.objects.create(username=username, phone=phone, password=password, OTP=otp)

        # Log the OTP for development purposes
        print(f"OTP: {otp}")

        # Store phone and username in the session to access in OTP verification
        request.session['phone'] = phone
        request.session['username'] = username
        messages.success(request, f"Your OTP is {otp}")
        return redirect("verify_otp")

    def handle_social_signup(self, email, register_type):
        # Redirect to the username and phone entry page
        return redirect('social_signup', email=email, register_type=register_type)

class SocialSignupView(View):
    def get(self, request, *args, **kwargs):
        email = request.GET.get('email')
        register_type = request.GET.get('register_type')

        context = {
            'email': email,
            'register_type': register_type,
        }
        return render(request, "social_signup.html", context)

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        register_type = request.POST.get("register_type")

        # Validate username and phone number
        if User.objects.filter(Q(username=username) | Q(phone=phone)).exists():
            messages.error(request, "Username or phone number already exists.")
            return redirect("social_signup", email=email, register_type=register_type)

        # Generate OTP and save user details in OTPSave table
        otp = generate_otp()
        OTPSave.objects.create(username=username, phone=phone, email=email, OTP=otp)

        # Log the OTP for development purposes
        print(f"OTP: {otp}")

        # Store necessary data in the session
        request.session['username'] = username
        request.session['phone'] = phone
        request.session['email'] = email

        return redirect("verify_otp")

#################################### OTP Verification #######################################
class OTPVerificationView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "otp_verification.html")

    def post(self, request, *args, **kwargs):
        otp_input = request.POST.get("otp")

        # Retrieve the saved username and phone from the session
        username = request.session.get('username')
        phone = request.session.get('phone')

        try:
            otp_record = OTPSave.objects.get(OTP=otp_input, phone=phone)
        except OTPSave.DoesNotExist:
            messages.error(request, "Invalid OTP. Please try again.")
            return redirect("verify_otp")

        # If OTP is valid, create a new user in the User table
        user = User.objects.create(username=otp_record.username, phone=otp_record.phone, email=otp_record.email,
                                    role_id=5, device_type="web")
        user.set_password(otp_record.password)
        user.save()

        # Delete the OTP record now that the user is registered
        otp_record.delete()

        # Clear session data
        request.session.pop('username', None)
        request.session.pop('phone', None)

        messages.success(request, "Registration successful! Please log in.")
        return redirect("login")
    

############################### google ###########################
# class GoogleLoginView(View):
#     def get(self, request):
#         # Step 1: Redirect user to Google OAuth 2.0 URL
#         google_auth_url = (
#             f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY}"
#             f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}&scope=email profile"
#         )
#         return redirect(google_auth_url)

# class GoogleCallbackView(View):
#     def get(self, request):
#         # Step 2: Handle callback from Google
#         code = request.GET.get('code')
#         token_url = 'https://oauth2.googleapis.com/token'

#         # Exchange authorization code for access token
#         token_data = {
#             'code': code,
#             'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
#             'client_secret': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
#             'redirect_uri': settings.GOOGLE_REDIRECT_URI,
#             'grant_type': 'authorization_code'
#         }
#         token_r = requests.post(token_url, data=token_data)
#         token_json = token_r.json()
#         access_token = token_json.get('access_token')

#         # Step 3: Retrieve user info from Google
#         userinfo_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
#         headers = {'Authorization': f'Bearer {access_token}'}
#         userinfo_r = requests.get(userinfo_url, headers=headers)
#         user_info = userinfo_r.json()

#         email = user_info.get('email')
#         print(email)
#         username = user_info.get('name')

#         # Check if user already exists
#         user= User.objects.get_or_create(
#             username=username,
#             defaults={'email': email, 'register_type': '2'}
#         )

#         return redirect('social_signup',user)  # Redirect to your desired page


########################## Apple ###########################
# class AppleLoginView(View):
#     def get(self, request):
#         # Step 1: Redirect to Apple Sign-In page
#         apple_auth_url = (
#             f"https://appleid.apple.com/auth/authorize?response_type=code&client_id={settings.SOCIAL_AUTH_APPLE_ID}"
#             f"&redirect_uri={settings.APPLE_REDIRECT_URI}&scope=email%20name"
#         )
#         return redirect(apple_auth_url)
    
# class AppleCallbackView(View):
#     def get(self, request):
#         # Step 2: Handle the callback from Apple
#         code = request.GET.get('code')
#         token_url = 'https://appleid.apple.com/auth/token'

#         # Exchange authorization code for access token
#         token_data = {
#             'code': code,
#             'client_id': settings.SOCIAL_AUTH_APPLE_ID,
#             'client_secret': settings.SOCIAL_AUTH_APPLE_SECRET,
#             'redirect_uri': settings.APPLE_REDIRECT_URI,
#             'grant_type': 'authorization_code'
#         }
#         token_r = requests.post(token_url, data=token_data)
#         token_json = token_r.json()
#         access_token = token_json.get('access_token')

#         # Step 3: Retrieve user info from Apple
#         userinfo_url = 'https://appleid.apple.com/auth/userinfo'
#         headers = {'Authorization': f'Bearer {access_token}'}
#         userinfo_r = requests.get(userinfo_url, headers=headers)
#         user_info = userinfo_r.json()

#         email = user_info.get('email')
#         username = user_info.get('name')

#         # Check if user already exists
#         user = User.objects.filter(email=email).first()  # Fetch user based on email

#         if user:
#             # If the user already exists, prompt to log in
#             messages.error(request, "This Apple ID is already registered. Please log in.")
#             return redirect("login")  # Redirect to your login view

#         # If not registered, proceed with OTP flow
#         otp = generate_otp()  # Generate OTP as per your existing logic

#         # Save user details in OTPSave table
#         OTPSave.objects.create(username=username, phone=None, email=email, OTP=otp)

#         # Log the OTP for development purposes
#         print(f"OTP: {otp}")

       ## # # Store necessary data in the session
       ## # request.session['username'] = username
       ## # request.session['email'] = email

       ## # messages.success(request, f"An OTP has been sent to your registered email: {email}")
       ## # return redirect("verify_otp")  # Redirect to the OTP verification page
       ## # Check if user already exists
#         user= User.objects.get_or_create(
#             username=username,
#             defaults={'email': email, 'register_type': '2'}
#         )

#         return redirect('social_signup',user)  # Redirect to your desired page