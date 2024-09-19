from django.shortcuts import render, redirect, get_object_or_404
from django import views
# from .forms import *
from django.contrib import messages
from FutureStar_App.models import Inquire
from django.views import View


class HomePage(View):
    
    def get(self, request, *args, **kwargs):
        
        return render(request, "home.html")

class DiscoverPage(View):
    
    def get(self, request, *args, **kwargs):
        
        return render(request, "discover.html")

class SuccessStoriesPage(View):
    
    def get(self, request, *args, **kwargs):
        
        return render(request, "success-stories.html")

class NewsPage(View):
    
    def get(self, request, *args, **kwargs):
        
        return render(request, "news.html")


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

