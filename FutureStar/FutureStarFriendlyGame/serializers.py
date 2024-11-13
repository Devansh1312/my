from rest_framework import serializers
from FutureStar_App.models import User
from urllib.parse import urlparse
from FutureStarAPI.models import *
from django.core.files.images import get_image_dimensions
from django.core.files.storage import default_storage
from django.utils.translation import gettext as _
from django.utils.crypto import get_random_string


