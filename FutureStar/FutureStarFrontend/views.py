from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from FutureStar_App.models import *
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
            cmsdata = cms_pages.objects.get(id=4)
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
        context = {
            "current_language":current_language,
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
            "google_client_id": settings.GOOGLE_CLIENT_ID,
            "apple_client_id": settings.APPLE_CLIENT_ID,
            "apple_redirect_uri": settings.APPLE_REDIRECT_URI,
            "social_auth_state_string": settings.SOCIAL_AUTH_STATE_STRING,
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



########################################## Register Page #############################
class RegisterPage(View):

    def get(self, request, *args, **kwargs):
        current_language = request.session.get('language', 'en')
        try:
            cmsdata = cms_pages.objects.get(id=13)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
        context = {
            "current_language": current_language,
            "cmsdata":cmsdata,
        }
        return render(request, "register.html", context)

    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language

        # Fetch data from the form
        username = request.POST.get("username", "").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "").strip()

        # If only language is changed (no registration form fields are filled)
        if not username and not phone and not password:
            messages.success(request, "Language changed successfully!")
            return redirect('register')

        # Validation for registration process
        if not username or not phone or not password:
            messages.error(request, "All fields are required for registration.")
            context = {
                "current_language": selected_language,
            }
            return render(request, "register.html", context)

        # Check if username or phone already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            context = {
                "current_language": selected_language,
            }
            return render(request, "register.html", context)

        if User.objects.filter(phone=phone).exists():
            messages.error(request, "Phone number already exists.")
            context = {
                "current_language": selected_language,
            }
            return render(request, "register.html", context)

        # Create the user
        try:
            user = User(
                username=username,
                phone=phone,
                role_id=2,  # Adjust as per your logic
                register_type="Website",  # Adjust as necessary
                device_type="web"
            )
            user.set_password(password)  # Hash the password before saving
            user.save()
            messages.success(request, "Registration successful!")
            return redirect('login')  # Redirect to the login page after registration
        except ValidationError as e:
            messages.error(request, str(e))
            context = {
                "current_language": selected_language,
            }
            return render(request, "register.html", context)