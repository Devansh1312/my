"""
URL configuration for FutureStar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.shortcuts import render

# Custom error handlers
def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)

# Set the custom handlers
handler404 = 'FutureStar.urls.custom_404'
handler500 = 'FutureStar.urls.custom_500'


# Set the custom handler for 404 errors
handler404 = 'FutureStar.urls.custom_404'
handler500 = 'FutureStar.urls.custom_500'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("FutureStar_App.urls")),
    path('', include("FutureStarFrontend.urls")),
    path('', include('FutureStarAPI.urls')),  # Point to the app's API urls
    path('', include('FutureStarTeamApp.urls')),  # Point to the app's API urls
    path('', include('FutureStarTrainingGroupApp.urls')),  # Point to the app's API urls
    path('', include('FutureStarTournamentApp.urls')),  # Point to the app's API urls
    path('', include('FutureStarTrainingApp.urls')),  # Point to the app's API urls
    path('', include('FutureStarGameSystem.urls')), 
    path('', include('FutureStarFriendlyGame.urls')), 


      # JWT Token routes
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] 

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)