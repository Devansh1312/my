from django.shortcuts import render, redirect, get_object_or_404
from django import views
# from .forms import *
from django.contrib import messages
from FutureStar_App.models import *
from django.views import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


##############################################   HomePage   ########################################################

class HomePage(View):
    def get(self, request, *args, **kwargs):
        marquee = Slider_Content.objects.all()
        app_features = App_Feature.objects.all()
        testimonials = Testimonial.objects.all().order_by('-id')[:3]
        news = News.objects.all().order_by('-id')[:4]
        partner = Partners.objects.all()
        team_members = Team_Members.objects.all().order_by('id')

        current_language = request.session.get('language', 'en')

        context = {
            "marquee": marquee,
            "app_features": app_features,
            "testimonials": testimonials,
            "news": news,
            "partner": partner,
            "team_members": team_members,
            "current_language":current_language,
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
        current_language = request.session.get('language', 'en')
        context = {
            "current_language":current_language,
        }
        return render(request, "login.html",context)

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
    

##############################################   DiscoverPage   ########################################################

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
