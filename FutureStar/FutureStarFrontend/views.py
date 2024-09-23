from django.shortcuts import render, redirect, get_object_or_404
from django import views
# from .forms import *
from django.contrib import messages
from FutureStar_App.models import *
from django.views import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class HomePage(View):
    def get(self, request, *args, **kwargs):
        marquee = Slider_Content.objects.all()
        app_features = App_Feature.objects.all()
        testimonials = Testimonial.objects.all().order_by('-id')[:3]
        news = News.objects.all().order_by('-id')[:4]
        partner = Partners.objects.all()
        current_language = request.session.get('language', 'en')

        context = {
            "marquee": marquee,
            "app_features": app_features,
            "testimonials": testimonials,
            "news": news,
            "partner": partner,
            "current_language":current_language,
        }
        return render(request, "home.html", context)
    def post(self, request, *args, **kwargs):
        # Update the language based on the user's selection and store it in the session
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language

        # Redirect to the same page after changing the language
        return redirect('index')  # Replace 'news-page' with the correct view name if different

class DiscoverPage(View):
    
    def get(self, request, *args, **kwargs):
        
        return render(request, "discover.html")

class SuccessStoriesPage(View):
    
    def get(self, request, *args, **kwargs):
        tryout_clubs = Tryout_Club.objects.all()
        context = {
            "tryout_clubs": tryout_clubs,
        }
        
        return render(request, "success-stories.html",context)

class NewsPage(View):
    
    def get(self, request, *args, **kwargs):
        # Get the selected language from the session, default to 'en'
        current_language = request.session.get('language', 'en')
        
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
        }
        return render(request, "news.html", context)

    def post(self, request, *args, **kwargs):
        # Update the language based on the user's selection and store it in the session
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language

        # Redirect to the same page after changing the language
        return redirect('news')  # Replace 'news-page' with the correct view name if different

class NewsDetailPage(View):
    def get(self, request, *args, **kwargs):
        # Get the selected language from the session, default to 'en'
        current_language = request.session.get('language', 'en')
        # Pass the current language and news to the template
        context = {
            "current_language": current_language,
        }
        return render(request, "news.html",context)

    def post(self, request):
        # Retrieve the news ID from the hidden input
        id = request.POST.get("id")
        selected_language = request.POST.get('language', 'en')
        request.session['language'] = selected_language

        # Find the news with the matching id or raise 404 if not found
        news = get_object_or_404(News, id=id)

        context = {
            "news": news,
            "current_language": selected_language,
        }
        return render(request, "news-details.html", context)

class AdvertisePage(View):
    
    def get(self, request, *args, **kwargs):
        
        return render(request, "advertise.html")

class AboutPage(View):
    
    def get(self, request, *args, **kwargs):
        marquee = Slider_Content.objects.all()
        testimonials = Testimonial.objects.all().order_by('-id')[:3]
        global_clients = Global_Clients.objects.all()
        current_language = request.session.get('language', 'en')


        context = {
            "marquee": marquee,
            "testimonials": testimonials,
            "global_clients": global_clients,
            "current_language":current_language,


        }
        return render(request, "about.html",context)

class LoginPage(View):
    
    def get(self, request, *args, **kwargs):
        
        return render(request, "login.html")

class RegisterPage(View):
    
    def get(self, request, *args, **kwargs):
        
        return render(request, "register.html")


class ContactPage(View):
    
    def get(self, request, *args, **kwargs):
        try:
            cmsdata = cms_pages.objects.get(name_en="Contacts")  # Use get() to fetch a single object
        except cms_pages.DoesNotExist:
            cmsdata = None  # Handle the case where the object does not exist

        current_language = request.session.get('language', 'en')
        print(cmsdata)  # This will print the single object to the console

        context = {
            "current_language": current_language,
            "cmsdata": cmsdata,
        } 
                
        return render(request, "contact.html", context)

            
    def post(self, request):
        cmsdata = cms_pages.objects.filter(name_en="Contacts")
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
        context = {
            "current_language": selected_language,
            "cmsdata":cmsdata,

        }
        messages.success(request, "Inquire Submited successfully.")
        return redirect("contact",context)

