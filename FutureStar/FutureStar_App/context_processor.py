from django.conf import settings
from .models import SystemSettings, User

def system_settings(request):
    try:
        system_settings = SystemSettings.objects.first()  # Fetch your SystemSettings object

        # Initialize URLs to None
        fav_icon_url = None
        footer_logo_url = None
        header_logo_url = None

        if system_settings:
            # Update with the correct fields from SystemSettings
            if system_settings.fav_icon:
                fav_icon_url = settings.MEDIA_URL + system_settings.fav_icon
            if system_settings.footer_logo:
                footer_logo_url = settings.MEDIA_URL + system_settings.footer_logo
            if system_settings.header_logo:
                header_logo_url = settings.MEDIA_URL + system_settings.header_logo

        # Get the total count of coach users and referee users combined
        pending_approval_count = User.objects.filter(role__id=5, is_coach=True).count() + User.objects.filter(role__id=5, is_referee=True).count()

    except SystemSettings.DoesNotExist:
        system_settings = None

    return {
        'system_settings': system_settings,
        'fav_icon': fav_icon_url,
        'footer_logo': footer_logo_url,
        'header_logo': header_logo_url,
        'pending_approval_count': pending_approval_count,
    }
