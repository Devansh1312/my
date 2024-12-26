from django.conf import settings
from FutureStar_App.models import *  
from FutureStarAPI.models import *  

def system_settings(request):
    try:
        system_settings = SystemSettings.objects.first()

        fav_icon_url = None
        footer_logo_url = None
        header_logo_url = None

        if system_settings:
            if system_settings.fav_icon:
                fav_icon_url = settings.MEDIA_URL + system_settings.fav_icon
            if system_settings.footer_logo:
                footer_logo_url = settings.MEDIA_URL + system_settings.footer_logo
            if system_settings.header_logo:
                header_logo_url = settings.MEDIA_URL + system_settings.header_logo

    except SystemSettings.DoesNotExist:
        system_settings = None

    return {
        'system_settings': system_settings,
        'fav_icon': fav_icon_url,
        'footer_logo': footer_logo_url,
        'header_logo': header_logo_url,
    }

def user_is_team_founder(request):
    is_founder = False

    if request.user.is_authenticated:
        # Check if the user is the founder of any team
        is_founder = Team.objects.filter(team_founder=request.user).exists()

    return {
        'is_founder': is_founder  # Ensure this matches with the template variable name
    }
