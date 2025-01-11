from django.contrib import admin
from FutureStar_App.models import *
from FutureStarTeamApp.models import *
from FutureStarAPI.models import *
from FutureStarTournamentApp.models import *
from urllib.parse import urlparse
from FutureStarAPI.models import *
from django.core.files.images import get_image_dimensions
from FutureStarGameSystem.models import *
# Register your models here.
admin.site.register(User)
admin.site.register(Country)
admin.site.register(City)
