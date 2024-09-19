from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

from django.contrib.auth.hashers import make_password, check_password

# Inquire Blog Management    
class Inquire(models.Model):
    fullname = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    message = models.TextField()  

    
# Role Model
class Role(models.Model):
    name_en = models.CharField(max_length=100,null=True,blank=True)
    name_ar = models.CharField(max_length=100,null=True,blank=True)

    def __str__(self):
        return self.name_en


# User Category Model
class Category(models.Model):
    name_en = models.CharField(max_length=100,null=True,blank=True)
    name_ar = models.CharField(max_length=100,null=True,blank=True)

    def __str__(self):
        return self.name_en


# Custom User Manager
class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username field must be set")
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(username, email, password, **extra_fields)


# Custom User Model
class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    username = models.CharField(max_length=150, unique=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", null=True, blank=True
    )
    card_header = models.ImageField(upload_to="card_header/", null=True, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    password = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    remember_token = models.CharField(max_length=255,null=True, blank=True)
    token_created_at = models.DateTimeField(null=True, blank=True)  # Add this field
    email_verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username


# System Settings Model
class SystemSettings(models.Model):
    fav_icon = models.CharField(max_length=255, null=True, blank=True)
    footer_logo = models.CharField(max_length=255, null=True, blank=True)
    header_logo = models.CharField(max_length=255, null=True, blank=True)
    website_name_english = models.CharField(max_length=255)
    website_name_arabic = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField()
    instagram = models.TextField(null=True, blank=True)
    facebook = models.TextField(null=True, blank=True)
    snapchat = models.TextField(null=True, blank=True)
    linkedin = models.TextField(null=True, blank=True)
    youtube = models.TextField(null=True, blank=True)
    happy_user = models.CharField(max_length=30,null=True, blank=True)
    line_of_code = models.CharField(max_length=30,null=True, blank=True)
    downloads = models.CharField(max_length=30,null=True, blank=True)
    app_rate = models.CharField(max_length=30,null=True, blank=True)
    years_of_experience = models.CharField(max_length=30,null=True, blank=True)
    project_completed = models.CharField(max_length=30,null=True, blank=True)
    proffesioan_team_members = models.CharField(max_length=30,null=True, blank=True)
    awards_winning = models.CharField(max_length=30,null=True, blank=True)

    def __str__(self):
        return self.website_name_english


# gender Model
class UserGender(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# # Game Type  Model
# class GameType(models.Model):
#     name = models.CharField(max_length=100)

#     def __str__(self):
#         return self.name


# Field Capacity  Model
class FieldCapacity(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# Ground Materials Model
class GroundMaterial(models.Model):
    name_en = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100,null=True,blank=True)


    def __str__(self):
        return self.name_en


# Tournamebt Style Model
class TournamentStyle(models.Model):
    name_en = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100,null=True,blank=True)


    def __str__(self):
        return self.name_en


# Event Types Model
class EventType(models.Model):
    name_en = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100,null=True,blank=True)


    def __str__(self):
        return self.name_en


#User Profile
class Player_Profile(models.Model):
    
    user_id = models.ForeignKey(User, on_delete=models.CASCADE ,blank=True, null=True)
    
    fullname = models.CharField(max_length=255, blank=True, null=True)
    
    username = models.CharField(max_length=150, unique=True,default='')
        
    password = models.CharField(max_length=128,default='')  
    
    date_joined = models.DateTimeField(auto_now_add=True)
    
    is_active = models.BooleanField(default=True)
    
    username = models.CharField(max_length=255,null = False)
    
    Phone_Number = models.PositiveIntegerField(null=False,default='')
    
    bio = models.TextField(blank=True, null=True)

    date_of_birth = models.DateField(blank=True, null=True)

    age = models.PositiveIntegerField(blank=True, null=True)

    gender = models.CharField(max_length=10, blank=True, null=True)

    country = models.CharField(max_length=100, blank=True, null=True)

    city = models.CharField(max_length=100, blank=True, null=True)

    nationality = models.CharField(max_length=100, blank=True, null=True)

    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    height = models.PositiveIntegerField(blank=True, null=True)

    main_playing_position = models.CharField(max_length=50, blank=True, null=True)

    secondary_playing_position = models.CharField(max_length=50, blank=True, null=True)

    playing_foot = models.CharField(max_length=10, blank=True, null=True)

    favourite_local_team = models.CharField(max_length=100, blank=True, null=True)

    favourite_team = models.CharField(max_length=100, blank=True, null=True)

    favourite_local_player = models.CharField(max_length=100, blank=True, null=True)

    favourite_player = models.CharField(max_length=100, blank=True, null=True)
    #data
    def set_password(self, raw_password):
         self.password = make_password(raw_password)
         self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def __str__(self):
        return self.fullname if self.fullname else 'Player Profile'

#News Blog Management        
class News(models.Model):
    title_en = models.CharField(max_length=255)
    title_ar = models.CharField(max_length=255,blank=True, null=True)
    description_en = models.TextField()
    description_ar = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='news/', blank=True, null=True)
    news_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title_en

# Partners Blog Management
class Partners(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='partners/', blank=True, null=True)

    def __str__(self):
        return self.title        

# Global Clients Blog Management
class Global_Clients(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='global_clients/', blank=True, null=True)

    def __str__(self):
        return self.title        

# Tryout Club Blog Management    
class Tryout_Club(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='tryout_club/')

    def __str__(self):
        return self.title

# Tryout Club Blog Management    
class Testimonial(models.Model):
    name_en = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True, null=True)
    designation_en = models.CharField(max_length=255)
    designation_ar = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='testimonial/')
    content_en = models.TextField()
    content_ar = models.TextField(blank=True, null=True)
    rattings = models.CharField(max_length=5)

    def __str__(self):
        return self.name_en
    
#Team Members    
class Team_Members(models.Model):
    name_en = models.CharField(max_length=255)
    designations_en = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True, null=True)
    designations_ar = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='team_members/', blank=True, null=True)

    def __str__(self):
        return self.name_en

#App_Feature Members    
class App_Feature(models.Model):
    title_en = models.CharField(max_length=255)
    sub_title_en = models.CharField(max_length=255)
    title_ar = models.CharField(max_length=255, blank=True, null=True)
    sub_title_ar = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='app_feature/')
    
    def __str__(self):
        return self.title

# Slider Content Model
class Slider_Content(models.Model):
    content_en = models.CharField(max_length=100,null=True,blank=True)
    content_ar = models.CharField(max_length=100,null=True,blank=True)
    def __str__(self):
        return self.content_en

#contact model

class ContactPage(models.Model):
    
    Title = models.CharField(max_length=255,blank=True)
    Title_content = models.CharField(max_length = 1000,blank =True)
    Title_background = models.TextField(max_length=255,blank=True)
    contact_us = models.CharField(max_length = 255,blank = True)
    contact_us_title = models.CharField(max_length=255,blank=True)
    contact_country = models.CharField(max_length=255,blank=True)
    contact_mail_icon = models.TextField(max_length=255,blank = True)
    contact_phone_icon = models.TextField(max_length=255,blank=True)
    quote = models.CharField(max_length=255,blank=True)
    quote_title = models.CharField(max_length=255,blank=True)
    
    def __str__(self):
            return self.Title
        


 