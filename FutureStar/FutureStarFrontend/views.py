from django.shortcuts import render, redirect, get_object_or_404
from django import views
# from .forms import *
from django.contrib import messages
from FutureStar_App.models import *
from django.views import View


class HomePage(View):
    def get(self, request, *args, **kwargs):
        marquee = Slider_Content.objects.all()
        app_features = App_Feature.objects.all()
        testimonials = Testimonial.objects.all().order_by('-id')[:3]
        news = News.objects.all().order_by('-id')[:4]
        partner = Partners.objects.all()

        context = {
            "marquee": marquee,
            "app_features": app_features,
            "testimonials": testimonials,
            "news": news,
            "partner": partner,
        }
        return render(request, "home.html", context)

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
        
        return render(request, "news.html")

class AdvertisePage(View):
    
    def get(self, request, *args, **kwargs):
        
        return render(request, "advertise.html")

class AboutPage(View):
    
    def get(self, request, *args, **kwargs):
        marquee = Slider_Content.objects.all()
        testimonials = Testimonial.objects.all().order_by('-id')[:3]
        global_clients = Global_Clients.objects.all()

        context = {
            "marquee": marquee,
            "testimonials": testimonials,
            "global_clients": global_clients,

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
        
        return render(request, "contact.html")
    
    def post(self, request):
        fullname = request.POST.get("fullname")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        message = request.POST.get("message")

        Inquire.objects.create(
            fullname=fullname,
            phone=phone,
            email=email,
            message=message,
        )
        messages.success(request, "Inquire Submited successfully.")
        return redirect("contact")

