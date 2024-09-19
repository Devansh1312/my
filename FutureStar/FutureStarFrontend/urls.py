from django.urls import path
from FutureStarFrontend.views import *
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import redirect

urlpatterns = [
    

    #Dashboard URL
    path('contact/', ContactPage.as_view(),name="contact"),
    path('', HomePage.as_view(),name="index"),
    path('discover/', DiscoverPage.as_view(),name="discover"),
    path('success-stories/', SuccessStoriesPage.as_view(),name="success-stories"),
    path('news/', NewsPage.as_view(),name="news"),
    path('advertise/', AdvertisePage.as_view(),name="advertise"),







    ]

