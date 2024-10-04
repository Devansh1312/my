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


##############################################   HomePage   ########################################################

class HomePage(View):
    def get(self, request, *args, **kwargs):
        marquee = Slider_Content.objects.all()
        app_features = App_Feature.objects.all()
        testimonials = Testimonial.objects.all().order_by('-id')[:3]
        news = News.objects.all().order_by('-id')[:4]
        partner = Partners.objects.all()
        team_members = Team_Members.objects.all().order_by('id')
        cmsfeatures = cms_home_dynamic_field.objects.all()
        cms_home_dynamic_achivements = cms_home_dynamic_achivements_field.objects.all()
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
        current_language = request.session['language'] = selected_language
        marquee = Slider_Content.objects.all()
        app_features = App_Feature.objects.all()
        testimonials = Testimonial.objects.all().order_by('-id')[:3]
        news = News.objects.all().order_by('-id')[:4]
        partner = Partners.objects.all()
        team_members = Team_Members.objects.all().order_by('id')
        cmsfeatures = cms_home_dynamic_field.objects.all()
        # print("post" , current_language )
        cms_home_dynamic_achivements = cms_home_dynamic_achivements_field.objects.all()
        try:
            cmsdata = cms_pages.objects.get(id=1)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist
        
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



##############################################   DiscoverPage   ########################################################

class DiscoverPage(View):
    
    def get(self, request, *args, **kwargs):
        current_language = request.session.get('language', 'en')
        context = {
            "current_language":current_language,
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
    def get(self, request, *args, **kwargs):
        try:
            cmsdata = cms_pages.objects.get(id=5)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  
        current_language = request.session.get('language', 'en')
        context = {
            "current_language": current_language,
            "cmsdata" : cmsdata,
        }
        return render(request, "news.html",context)

    def post(self, request):
        id = request.POST.get("id")
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        try:
            cmsdata = cms_pages.objects.get(id=5)  
        except cms_pages.DoesNotExist:
            cmsdata = None  
        news = get_object_or_404(News, id=id)

        context = {
            "news": news,
            "current_language": selected_language,
            "cmsdata" : cmsdata,

        }
        return render(request, "news-details.html", context)



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
        # current_language = request.session.get('language', 'en')
        current_language = "en",

        context = {
            "current_language": current_language,
            "google_client_id": settings.GOOGLE_CLIENT_ID,
            "apple_client_id": settings.APPLE_CLIENT_ID,
            "apple_redirect_uri": settings.APPLE_REDIRECT_URI,
            "social_auth_state_string": settings.SOCIAL_AUTH_STATE_STRING,
        }
        return render(request, "login.html", context)

    def post(self, request, *args, **kwargs):
        login_type = int(request.POST.get('login_type', 1))

        if login_type == 1:
            username_or_phone = request.POST.get('username_or_phone')
            password = request.POST.get('password')

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


class RegisterPage(View):
    
    def get(self, request, *args, **kwargs):
        current_language = request.session.get('language', 'en')
        context = {
            "current_language":current_language,
        }
        return render(request, "register.html",context)





##############################################   ContactPage   ########################################################

class ContactPage(View):
    
    def get(self, request, *args, **kwargs):
        try:
            cmsdata = cms_pages.objects.get(id=8)  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist

        current_language = request.session.get('language', 'en')

        context = {
            "current_language": current_language,
            "cmsdata": cmsdata,
        } 
                
        return render(request, "contact.html", context)

            
    def post(self, request):
        # try:
        #     cmsdata = cms_pages.objects.get(id=8)  # Use get() to fetch a single object
        # except cms_pages.DoesNotExist:
        #     cmsdata = None  # Handle the case where the object does not exist
        fullname = request.POST.get("fullname")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        message = request.POST.get("message")
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language

        Inquire.objects.create(
            fullname=fullname,
            phone=phone,
            email=email,
            message=message,
        )
        # context = {
        #     "cmsdata":cmsdata,
        # }
        messages.success(request, "Inquiry submitted successfully.")
        return redirect("contact")  # No need to pass context here




##############################################   DiscoverPage   ########################################################

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

        context = {
            "current_language": current_language,
            # "cmsdata": cmsdata,
        } 

        return render(request, "PlayerDashboard.html",context)
    
    def post(self, request, *args, **kwargs):
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language
        return redirect('player-dashboard')  



