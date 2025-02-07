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


def get_language(request):
    """
    Retrieves the language from the URL or session and updates the session values.
    Ensures the language is either 'en' or 'ar', defaulting to 'en'.
    """
    allowed_languages = {'en', 'ar'}
    language = request.GET.get('Language', '').lower()

    if language in allowed_languages:
        request.session['language'] = language
    else:
        language = request.session.get('language', 'en')
        if language not in allowed_languages:
            language = 'en'
        request.session['language'] = language

    request.session['current_language'] = language  # Keep 'current_language' consistent
    return language

# Custom error handlers
def custom_404(request, exception):
    language_from_url = get_language(request)
    # Prepare context for rendering
    context = {
        "current_language": language_from_url,         
    }
    return render(request, '404.html', status=404,context=context)

def custom_500(request):
    language_from_url = get_language(request)
    # Prepare context for rendering
    context = {
        "current_language": language_from_url,         
    }
    return render(request, '500.html', status=500,context=context)

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
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    from django.views.static import serve
    from django.urls import re_path

    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)