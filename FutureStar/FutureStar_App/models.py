from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

# Inquire Blog Management    
class Inquire(models.Model):
    fullname = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    message = models.TextField()  

    class Meta:
        db_table = 'futurestar_app_inquire'
    
# Role Model
class Role(models.Model):
    name_en = models.CharField(max_length=100,null=True,blank=True)
    name_ar = models.CharField(max_length=100,null=True,blank=True)

    def __str__(self):
        return self.name_en
    class Meta:
        db_table = 'futurestar_app_role'

# User Category Model
class Category(models.Model):
    name_en = models.CharField(max_length=100,null=True,blank=True)
    name_ar = models.CharField(max_length=100,null=True,blank=True)

    def __str__(self):
        return self.name_en

    class Meta:
        db_table = 'futurestar_app_category'

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

# gender Model
class UserGender(models.Model):
    name_en = models.CharField(max_length=100,null=True,blank=True)
    name_ar = models.CharField(max_length=100,null=True,blank=True)
    def __str__(self):
        return self.name_en
    
    class Meta:
        db_table = 'futurestar_app_gender'


class Country(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=2)
    name = models.CharField(max_length=100)
    zone_id = models.IntegerField(default=0)
    country_code = models.IntegerField(null=True, blank=True)
    status = models.BooleanField(default=True, help_text='0 = InActive | 1 = Active')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'futurestar_app_country'

    def __str__(self):
        return self.name


class City(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    country= models.ForeignKey(Country, on_delete=models.CASCADE )
    status = models.BooleanField(default=True, help_text='0 = InActive | 1 = Active')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'futurestar_app_city'

    def __str__(self):
        return self.name

# Custom User Model
class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    username = models.CharField(max_length=150, unique=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", null=True, blank=True
    )
    card_header = models.ImageField(upload_to="card_header/", null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20)
    fullname = models.CharField(max_length=150,null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.CharField(max_length=5,null=True, blank=True)
    gender = models.ForeignKey(UserGender, null=True, blank=True, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.CASCADE)
    nationality = models.CharField(max_length=150,null=True, blank=True)
    weight = models.CharField(max_length=150,null=True, blank=True)
    height = models.CharField(max_length=150,null=True, blank=True)
    main_playing_position = models.CharField(max_length=150,null=True, blank=True)
    secondary_playing_position = models.CharField(max_length=150,null=True, blank=True)
    playing_foot = models.CharField(max_length=150,null=True, blank=True)
    favourite_local_team = models.CharField(max_length=150,null=True, blank=True)
    favourite_team = models.CharField(max_length=150,null=True, blank=True)
    favourite_local_player = models.CharField(max_length=150,null=True, blank=True)
    favourite_player = models.CharField(max_length=150,null=True, blank=True)
    otp = models.CharField(max_length=6, null=True, blank=True)  # Add this field for OTP
    device_type = models.CharField(max_length=255,null=True,blank=True)
    device_token = models.CharField(max_length=255,null=True,blank=True)
    register_type = models.CharField(max_length=10,null=True,blank=True)
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
    
    class Meta:
        db_table = 'futurestar_app_user'


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
    twitter = models.TextField(null=True, blank=True)
    linkedin = models.TextField(null=True, blank=True)
    pinterest = models.TextField(null=True, blank=True)
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
    
    class Meta:
        db_table = 'futurestar_app_systemsettings'






# Field Capacity  Model
class FieldCapacity(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'futurestar_app_fieldcapacity'

# Ground Materials Model
class GroundMaterial(models.Model):
    name_en = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100,null=True,blank=True)


    def __str__(self):
        return self.name_en
    
    class Meta:
        db_table = 'futurestar_app_groundmaterial'


# Tournamebt Style Model
class TournamentStyle(models.Model):
    name_en = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100,null=True,blank=True)


    def __str__(self):
        return self.name_en

    class Meta:
        db_table = 'futurestar_app_tournamentstyle'

# Event Types Model
class EventType(models.Model):
    name_en = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100,null=True,blank=True)


    def __str__(self):
        return self.name_en
    
    class Meta:
        db_table = 'futurestar_app_eventtype'




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
    
    class Meta:
        db_table = 'futurestar_app_player_profile'

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
    
    class Meta:
        db_table = 'futurestar_app_news'

# Partners Blog Management
class Partners(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='partners/', blank=True, null=True)

    def __str__(self):
        return self.title 
    
    class Meta:
        db_table = 'futurestar_app_partners'       

# Global Clients Blog Management
class Global_Clients(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='global_clients/', blank=True, null=True)

    def __str__(self):
        return self.title
    
    class Meta:
        db_table = 'futurestar_app_global_clients'        

# Tryout Club Blog Management    
class Tryout_Club(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='tryout_club/')

    def __str__(self):
        return self.title
    
    class Meta:
        db_table = 'futurestar_app_tryout_club'


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
    
    class Meta:
        db_table = 'futurestar_app_testimonial'

    
#Team Members    
class Team_Members(models.Model):
    name_en = models.CharField(max_length=255)
    designations_en = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True, null=True)
    designations_ar = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='team_members/', blank=True, null=True)

    def __str__(self):
        return self.name_en
    
    class Meta:
        db_table = 'futurestar_app_team_members'


#App_Feature Members    
class App_Feature(models.Model):
    title_en = models.CharField(max_length=255)
    sub_title_en = models.CharField(max_length=255)
    title_ar = models.CharField(max_length=255, blank=True, null=True)
    sub_title_ar = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='app_feature/')
    
    def __str__(self):
        return self.title_en
    
    class Meta:
        db_table = 'futurestar_app_app_feature'

# Slider Content Model
class Slider_Content(models.Model):
    content_en = models.CharField(max_length=100,null=True,blank=True)
    content_ar = models.CharField(max_length=100,null=True,blank=True)
    def __str__(self):
        return self.content_en
    
    class Meta:
        db_table = 'futurestar_app_slider_content'


#cmspages
class cms_pages(models.Model):
    
    
    #name 
    name_en = models.CharField(max_length=100,null=True,blank=True)
    name_ar = models.CharField(max_length=100,null=True,blank=True)
    
    #heading-section-1   
    heading_en =  models.CharField(max_length=100,blank= True,null=True)
    heading_ar = models.CharField(max_length=100,blank = True,null=True)
    heading_title_en = models.CharField(max_length=100,blank = True,null=True)
    heading_title_ar = models.CharField(max_length=100,blank = True,null=True)

    heading_content_en = models.TextField(blank = True,null=True)
    heading_content_ar = models.TextField(blank = True,null=True)
    heading_video = models.FileField(upload_to='cmspages/',blank =True,null=True)
    heading_banner = models.ImageField(upload_to='cmspages/', blank=True, null=True)
    heading_image_1 = models.ImageField(upload_to='cmspages/',blank=True,null = True)
    heading_image_2 = models.ImageField(upload_to='cmspages/',blank=True,null = True)
    heading_image_3 = models.ImageField(upload_to='cmspages/',blank=True,null = True)
    heading_year_title_en = models.CharField(max_length=100,blank=True,null=True)
    heading_year_title_ar = models.CharField(max_length=100,blank=True,null=True)
    heading_year_title = models.CharField(max_length=100,blank=True,null=True)
    
    
    #heading-section-2
    sub_heading_name_en = models.CharField(max_length=100,blank=True,null=True)
    sub_heading_name_ar = models.CharField(max_length=100,blank=True,null=True)

    sub_heading_logo = models.ImageField(upload_to='cmspages/',blank =True,null = True)
    sub_heading_en = models.CharField(max_length=100,blank=True,null=True)
    sub_heading_ar = models.CharField(max_length=100,blank=True,null=True)
    sub_heading_title_en = models.CharField(max_length=100,blank=True,null=True)
    sub_heading_title_ar = models.CharField(max_length=100,blank=True,null=True)
    
    #heading-section-3
    sub_heading_icon_1 = models.ImageField(upload_to='cmspages/',blank =True,null = True)
    sub_heading_logo_title_1_en = models.CharField(max_length=100,blank =True,null=True)
    sub_heading_logo_title_1_ar = models.CharField(max_length=100,blank =True,null=True)
    sub_heading_logo_content_1_en = models.TextField(blank =True,null=True)
    sub_heading_logo_content_1_ar = models.TextField(blank =True,null=True)

    sub_heading_icon_2 = models.ImageField(upload_to='cmspages/',blank =True,null = True)
    sub_heading_logo_title_2_en = models.CharField(max_length=100,blank =True,null=True)
    sub_heading_logo_title_2_ar = models.CharField(max_length=100,blank =True,null=True)
    sub_heading_logo_content_2_en = models.TextField(blank =True,null=True)
    sub_heading_logo_content_2_ar = models.TextField(blank =True,null=True)

    #section-2
    section_2_heading_en = models.CharField(max_length=100,blank =True,null=True)
    section_2_heading_ar = models.CharField(max_length=100,blank =True,null=True)
    section_2_title_en = models.CharField(max_length=100,blank=True,null=True)
    section_2_title_ar = models.CharField(max_length=100,blank=True,null=True)
    section_2_content_en = models.TextField(max_length=100,blank=True,null=True)
    section_2_content_ar = models.TextField(max_length=100,blank=True,null=True)
    #section_2_logo = models.CharField(max_length=100,blank=True,null=True)
    section_2_background = models.ImageField(upload_to='cmspages/',blank=True,null=True)
    section_2_logo = models.ImageField(upload_to='cmspages/',blank=True,null=True)
    section_2_images = models.ImageField(upload_to='cmspages/',blank=True,null=True)
    
    section_2_country_name_en = models.CharField(max_length=100,blank=True,null=True)
    section_2_country_name_ar = models.CharField(max_length=100,blank=True,null=True)
    section_2_discover_title_en = models.TextField(blank=True,null=True)
    section_2_discover_title_ar = models.TextField(blank=True,null=True)

    sub_section_2_title_1_en = models.CharField(max_length=100,blank=True,null=True)
    sub_section_2_title_1_ar = models.CharField(max_length=100,blank=True,null=True)
    sub_section_2_content_1_en = models.TextField(blank =True,null=True)
    sub_section_2_content_1_ar = models.TextField(blank =True,null=True)
    
    sub_section_2_title_2_en = models.CharField(max_length=100,blank=True,null=True)
    sub_section_2_title_2_ar = models.CharField(max_length=100,blank=True,null=True)
    sub_section_2_content_2_en = models.TextField(blank =True,null=True)
    sub_section_2_content_2_ar = models.TextField(blank =True,null=True)

    sub_section_2_1_icon = models.ImageField(upload_to='cmspages/',blank=True,null=True)
    sub_section_2_2_icon = models.ImageField(upload_to='cmspages/',blank=True,null=True)
    
    #section-3
    section_3_heading_en = models.CharField(max_length=100,blank=True,null=True)
    section_3_heading_ar = models.CharField(max_length=100,blank=True,null=True)
    
    section_3_title_en = models.CharField(max_length=100,blank=True,null=True)
    section_3_title_ar = models.CharField(max_length=100,blank=True,null=True)
    
    section_3_content_en = models.TextField(blank=True,null=True)
    section_3_content_ar = models.TextField(blank=True,null=True)
    
    section_3_titlee_en = models.TextField(blank=True,null=True)
    section_3_titlee_ar = models.TextField(blank=True,null=True)
    
    section_3_feature_icons = models.ImageField(upload_to='cmspages/',blank=True,null=True)
    section_3_feature_title_en = models.CharField(max_length=100,blank=True,null=True)
    section_3_feature_title_ar = models.CharField(max_length=100,blank=True,null=True)

    section_3_feature_short_content_en = models.TextField(blank=True,null=True)
    section_3_feature_short_content_ar = models.TextField(blank=True,null=True)
    
    
    
    #for discovery page
    section_3_long_title_en = models.TextField(blank=True,null=True)
    section_3_long_title_ar = models.TextField(blank=True,null=True)
    
    section_3_sub_title_en = models.CharField(max_length=100,blank=True,null=True)
    section_3_sub_title_ar = models.CharField(max_length=100,blank=True,null=True)
    section_3_sub_content_en = models.TextField(blank=True,null=True)
    section_3_sub_content_ar = models.TextField(blank=True,null=True)
    section_3_image = models.ImageField(upload_to='cmspages/',blank=True,null=True)

    #section-4
    
    section_4_heading_en = models.CharField(max_length=100,blank=True,null=True)
    section_4_heading_ar = models.CharField(max_length=100,blank=True,null=True)
    
    section_4_title_en = models.TextField(blank=True,null=True)
    section_4_title_ar = models.TextField(blank=True,null=True) 
    
    section_4_content_en = models.TextField(blank=True,null=True)
    section_4_content_ar = models.TextField(blank=True,null=True)
    
    section_4_image = models.ImageField(upload_to='cmspages/',blank=True,null=True)
    section_4_background = models.ImageField(upload_to='cmspages/',blank=True,null=True)

    #for advertise
    section_4_info_1 = models.TextField(blank=-True,null=True)
    section_4_info_2 = models.TextField(blank=True,null=True)
    section_4_info_3 = models.TextField(blank=True,null=True)
    section_4_info_4 = models.TextField(blank=True,null=True)
    section_4_info_5 = models.TextField(blank=True,null=True)
    section_4_info_6 = models.TextField(blank=True,null=True)

    #section 5
    section_5_heading_en = models.CharField(max_length=100,blank=True,null=True)
    section_5_heading_ar = models.CharField(max_length=100,blank=True,null=True)
    
    section_5_title_en = models.CharField(max_length=100,blank=True,null=True)
    section_5_title_ar = models.CharField(max_length=100,blank=True,null=True)
    
    section_5_image = models.ImageField(upload_to='cmspages/',blank=True,null=True)
    
    section_5_info_title_1_en = models.CharField(max_length=100,blank=True,null=True)
    section_5_info_title_2_en = models.CharField(max_length=100,blank=True,null=True)
    section_5_info_title_3_en = models.CharField(max_length=100,blank=True,null=True)
    section_5_info_title_4_en = models.CharField(max_length=100,blank=True,null=True)
    
    section_5_info_title_1_ar = models.CharField(max_length=100,blank=True,null=True)
    section_5_info_title_2_ar = models.CharField(max_length=100,blank=True,null=True)
    section_5_info_title_3_ar = models.CharField(max_length=100,blank=True,null=True)
    section_5_info_title_4_ar = models.CharField(max_length=100,blank=True,null=True)
    
    section_5_info_short_content_1_en = models.TextField(blank=True,null=True)
    section_5_info_short_content_2_en = models.TextField(blank=True,null=True)
    section_5_info_short_Content_3_en = models.TextField(blank=True,null=True)
    section_5_info_short_content_4_en = models.TextField(blank=True,null=True)

    section_5_info_short_content_1_ar = models.TextField(blank=True,null=True)
    section_5_info_short_content_2_ar = models.TextField(blank=True,null=True)
    section_5_info_short_Content_3_ar = models.TextField(blank=True,null=True)
    section_5_info_short_content_4_ar = models.TextField(blank=True,null=True)
    
    #section 6
    section_6_heading_en = models.CharField(max_length=100,blank =True,null=True)
    section_6_heading_ar = models.CharField(max_length=100,blank =True,null=True)

    section_6_title_en = models.CharField(max_length=100,blank =True,null=True)
    section_6_title_ar = models.CharField(max_length=100,blank =True,null=True)
    
    section_6_content_en_1 = models.TextField(blank = True,null =True)
    section_6_content_ar_1 = models.TextField(blank = True,null =True)
    section_6_content_en_2 = models.TextField(blank = True,null =True)
    section_6_content_ar_2 = models.TextField(blank = True,null =True)
    section_6_content_en_3 = models.TextField(blank = True,null =True)
    section_6_content_ar_3 = models.TextField(blank = True,null =True)
    section_6_content_en_4 = models.TextField(blank = True,null =True)
    section_6_content_ar_4 = models.TextField(blank = True,null =True)
    section_6_content_en_5 = models.TextField(blank = True,null =True)
    section_6_content_ar_5 = models.TextField(blank = True,null =True)
    section_6_content_en_6 = models.TextField(blank = True,null =True)
    section_6_content_ar_6 = models.TextField(blank = True,null =True)
    
    section_6_logo = models.ImageField(upload_to='cmspages/',blank=True,null=True)
    section_6_image  = models.ImageField(upload_to='cmspages/',blank=True,null=True)
    
    #section 7
    section_7_logo = models.ImageField(upload_to='cmspages/',blank=True,null=True)
    section_7_image  = models.ImageField(upload_to='cmspages/',blank=True,null=True)
    
    #section 8
    section_8_heading_en = models.CharField(max_length=100,blank =True,null=True)
    section_8_heading_ar = models.CharField(max_length=100,blank =True,null=True)

    section_8_title_en = models.CharField(max_length=100,blank =True,null=True)
    section_8_title_ar = models.CharField(max_length=100,blank =True,null=True)
    
     #section 9
    
    section_9_heading_en = models.CharField(max_length=100,blank =True,null=True)
    section_9_heading_ar = models.CharField(max_length=100,blank =True,null=True)

    section_9_title_en = models.TextField(blank =True,null=True)
    section_9_title_ar = models.TextField(blank =True,null=True)
    section_9_image = models.ImageField(upload_to='cmspages/',blank=True,null=True)

    #section 10
    section_10_heading_en = models.CharField(max_length=100,blank =True,null=True)
    section_10_heading_ar = models.CharField(max_length=100,blank =True,null=True)

    section_10_title_en = models.CharField(max_length=100,blank =True,null=True)
    section_10_title_ar = models.CharField(max_length=100,blank =True,null=True)

    achivement_heading_en = models.CharField(max_length=255,blank=True,null=True)
    achivement_heading_ar = models.CharField(max_length=255,blank=True,null=True)
    
    achivement_title_en = models.CharField(max_length=255,blank=True,null=True)
    achivement_title_ar = models.CharField(max_length=255,blank=True,null=True)


    meta_title_en = models.CharField(max_length=100,blank = True,null =True)
    meta_title_ar = models.CharField(max_length=100,blank = True,null =True)
    
    meta_content_en = models.TextField(blank = True,null =True)
    meta_content_ar = models.TextField(blank = True,null =True)

    
    
    def __str__(self):
        return self.name_en
    
    class Meta:
        db_table = 'futurestar_app_cms_pages'

class cms_dicovery_dynamic_view(models.Model):
    
    id = models.AutoField(primary_key=True)
    title_en = models.CharField(max_length=255,blank=True,null=True)
    title_ar = models.CharField(max_length=255,blank=True,null=True)

    content_en = models.TextField(blank=True,null=True)
    content_ar = models.TextField(blank=True,null=True)
    field_id = models.CharField(max_length=255,blank=True,null=True)


    def __str__(self):
        return self.title
    
    class Meta:
        db_table = "futurestar_app_cms_dicovery_dynamic_view"

    
class cms_dicovery_dynamic_image(models.Model):
    
    id = models.AutoField(primary_key=True)
    field_id = models.CharField(max_length=255,blank=True,null=True)

    images = models.ImageField(upload_to='cmspages/',blank=True,null=True)

    class Meta:
        db_table = "futurestar_app_cms_dicovery_dynamic_image"
        
        

'''class cms_advertise_dynamic_field(models.Model):
    
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255,blank=True,null=True)
    content = models.TextField(blank=True,null=True)
    images = models.ImageField(upload_to='cmspages/',blank=True,null=True)

    class Meta():
        db_table = "futurestar_app_cms_advertise_dynamic_field"    '''
class cms_advertise_section_2_dynamic_field(models.Model):
    
    id = models.AutoField(primary_key=True)
    title_en = models.CharField(max_length=255,blank=True,null=True)
    title_ar = models.CharField(max_length=255,blank=True,null=True)

    content_en = models.TextField(blank=True,null=True)
    content_ar = models.TextField(blank=True,null=True)

    images = models.ImageField(upload_to='cmspages/',blank=True,null=True)
    field_id = models.CharField(max_length=255,blank=True,null=True)

    class Meta():
        db_table = "futurestar_app_cms_advertise_section_2_dynamic_field"

class cms_advertise_Partnership_dynamic_field(models.Model):
    
    id = models.AutoField(primary_key=True)
    title_en = models.CharField(max_length=255,blank=True,null=True)
    title_ar = models.CharField(max_length=255,blank=True,null=True)

    content_en = models.TextField(blank=True,null=True)
    content_ar = models.TextField(blank=True,null=True)

    images = models.ImageField(upload_to='cmspages/',blank=True,null=True)
    field_id = models.CharField(max_length=255,blank=True,null=True)

    class Meta():
        db_table = "futurestar_app_cms_advertise_Partnership_dynamic_field"      

class cms_advertise_ads_dynamic_field(models.Model):
    
    id = models.AutoField(primary_key=True)

    images = models.ImageField(upload_to='cmspages/',blank=True,null=True)
    field_id = models.CharField(max_length=255,blank=True,null=True)

    class Meta():
        db_table = "futurestar_app_cms_advertise_ads_dynamic_field" 

class cms_advertise_premium_dynamic_field(models.Model):
    
    id = models.AutoField(primary_key=True)
    title_en = models.CharField(max_length=255,blank=True,null=True)
    title_ar = models.CharField(max_length=255,blank=True,null=True)

    images = models.ImageField(upload_to='cmspages/',blank=True,null=True)
    field_id = models.CharField(max_length=255,blank=True,null=True)

    class Meta():
        db_table = "futurestar_app_cms_advertise_premium_dynamic_field"                
#changes   
class cms_home_dynamic_field(models.Model):
    
    id = models.AutoField(primary_key=True)
    field_id = models.CharField(max_length=255,blank=True,null=True)

    title_en = models.CharField(max_length=255,blank=True,null=True)
    title_ar = models.CharField(max_length=255,blank=True,null=True)

    content_en = models.TextField(blank=True,null=True)
    content_ar = models.TextField(blank=True,null=True)

    images = models.ImageField(upload_to='cmspages/',blank=True,null=True)

    class Meta():
        db_table = "futurestar_app_cms_home_dynamic_field"      

class cms_home_dynamic_achivements_field(models.Model):
    
    id = models.AutoField(primary_key=True)
    field_id = models.CharField(max_length=255,blank=True,null=True)

    heading_en = models.CharField(max_length=255,blank=True,null=True)
    heading_ar = models.CharField(max_length=255,blank=True,null=True)
    
    title_en = models.CharField(max_length=255,blank=True,null=True)
    title_ar = models.CharField(max_length=255,blank=True,null=True)

    def __str__(self):
        return self.heading_en

    class Meta():
        db_table = "futurestar_app_cms_home_achivements_dynamic_field"           
                                        