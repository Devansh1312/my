from django.db import models
from FutureStar_App.models import *
from django.utils import timezone
import datetime
from django.core.exceptions import ValidationError
from datetime import datetime 
from django.utils import timezone
from datetime import timedelta

# Create your models here.

class AgeGroup(models.Model):
    id=models.AutoField(primary_key=True)
    name_en=models.CharField(max_length=255, blank=True, null=True)
    name_ar=models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return self.name_en
    
    class Meta:
        db_table = 'futurestar_app_age_group'

class Team(models.Model):
    team_name = models.CharField(max_length=255, blank=True, null=True)
    team_username = models.CharField(max_length=255, blank=True, null=True)
    team_type = models.ForeignKey(Category, on_delete=models.CASCADE, default=True)
    bio = models.TextField(null=True, blank=True)
    team_establishment_date = models.DateField(blank=True, null=True)
    team_president = models.CharField(max_length=255, blank=True, null=True)
    team_founder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='founder_of_teams',blank=True, null=True)  # ForeignKey to User model

    
    # New fields
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    address = models.CharField(max_length=255, blank=True, null=True)
    house_no = models.CharField(max_length=50, blank=True, null=True)
    premises = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country_name = models.CharField(max_length=100, blank=True, null=True)
    postalCode = models.CharField(max_length=20, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)
        
    country_id = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    city_id = models.ForeignKey(City, null=True, blank=True, on_delete=models.CASCADE)
    phone = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    
   
    team_logo = models.ImageField(upload_to='team/team_logo/', blank=True, null=True)
    team_background_image = models.ImageField(upload_to='team/team_background_image/', blank=True, null=True)
    team_uniform = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return self.team_name

    class Meta:
        db_table = 'futurestar_app_team'

class TeamBranch(models.Model):
    id=models.AutoField(primary_key=True)
    team_id=models.ForeignKey(Team,on_delete=models.CASCADE)
    team_name=models.CharField(max_length=200)
    age_group_id=models.ForeignKey(AgeGroup,on_delete=models.CASCADE,blank=True, null=True)
    upload_image=models.ImageField(upload_to='team/team_branch/', blank=True, null=True)
    field_size=models.ForeignKey(FieldCapacity,on_delete=models.CASCADE)
    phone = models.CharField(max_length=100,blank=True,null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=255,null=True,blank=True)
   
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    address = models.CharField(max_length=255, blank=True, null=True)
    house_no = models.CharField(max_length=50, blank=True, null=True)
    premises = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country_name = models.CharField(max_length=100, blank=True, null=True)
    postalCode = models.CharField(max_length=20, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)

    entry_fees=models.CharField(max_length=200,blank=True, null=True)
    description=models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)


    def __str__(self):
        return self.team_name

    class Meta:
        db_table = 'futurestar_app_team_branch'

    
class TrainingGroups(models.Model):
    group_name = models.CharField(max_length=255,blank=True,null=True)
    group_username = models.CharField(max_length=255,blank=True,null=True)
    bio = models.TextField(null=True,blank=True)
    group_founder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_founder',blank=True, null=True)  # ForeignKey to User model

     # New fields
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    address = models.CharField(max_length=255, blank=True, null=True)
    house_no = models.CharField(max_length=50, blank=True, null=True)
    premises = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country_name = models.CharField(max_length=100, blank=True, null=True)
    postalCode = models.CharField(max_length=20, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)

    phone = models.CharField(max_length=255,blank=True,null=True)
    group_logo = models.ImageField(upload_to='group/group_logo/', blank=True, null=True)  # Add image field
    group_background_image = models.ImageField(upload_to='group/group_background_image/', blank=True, null=True)  # Add image field
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return self.group_name

    class Meta:
        db_table = 'futurestar_app_traininggroups'

# post  Model
class Post(models.Model):
    USER_TYPE = 1
    TEAM_TYPE = 2
    GROUP_TYPE = 3
    CREATOR_TYPE_CHOICES = (
        (USER_TYPE, 'User'),
        (TEAM_TYPE, 'Team'),
        (GROUP_TYPE, 'Group'),
    )

    created_by_id = models.IntegerField(default=0)  # Stores ID of User, Team, or Group
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES,default=1)  # Stores 1, 2, or 3 based on the type

    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    media_type = models.IntegerField(default=1)
    date_created = models.DateTimeField(default=datetime.now)

    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    address = models.CharField(max_length=255, blank=True, null=True)
    house_no = models.CharField(max_length=50, blank=True, null=True)
    premises = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country_name = models.CharField(max_length=100, blank=True, null=True)
    postalCode = models.CharField(max_length=20, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'futurestar_app_post'

class Post_comment(models.Model):
    USER_TYPE = 1
    TEAM_TYPE = 2
    GROUP_TYPE = 3
    
    CREATOR_TYPE_CHOICES = (
        (USER_TYPE, 'User'),
        (TEAM_TYPE, 'Team'),
        (GROUP_TYPE, 'Group'),
    )

    created_by_id = models.IntegerField(default=0)  # Stores ID of User, Team, or Group
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES,default=1)  # Stores 1, 2, or 3 based on the type
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', related_name='replies', null=True, blank=True, on_delete=models.CASCADE)
    comment = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return f'Comment by ID {self.created_by_id} on {self.post.title}'

    class Meta:
        db_table = 'futurestar_app_post_comment'


# models.py

class PostView(models.Model):
    USER_TYPE = 1
    TEAM_TYPE = 2
    GROUP_TYPE = 3
    
    CREATOR_TYPE_CHOICES = (
        (USER_TYPE, 'User'),
        (TEAM_TYPE, 'Team'),
        (GROUP_TYPE, 'Group'),
    )

    created_by_id = models.IntegerField(default=0)  # Stores ID of User, Team, or Group
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES,default=1)  # 1, 2, or 3 based on the type
    post = models.ForeignKey(Post, related_name='views', on_delete=models.CASCADE)
    date_viewed = models.DateTimeField(default=datetime.now)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    class Meta:
        db_table = 'futurestar_app_post_view'
        unique_together = ('created_by_id', 'post')  # Ensure one view per user/team/group per post

class PostLike(models.Model):
    USER_TYPE = 1
    TEAM_TYPE = 2
    GROUP_TYPE = 3
    
    CREATOR_TYPE_CHOICES = (
        (USER_TYPE, 'User'),
        (TEAM_TYPE, 'Team'),
        (GROUP_TYPE, 'Group'),
    )

    created_by_id = models.IntegerField(default=0)  # Stores ID of User, Team, or Group
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES,default=1)  # 1, 2, or 3 based on the type
    post = models.ForeignKey(Post, related_name='likes', on_delete=models.CASCADE)
    date_liked = models.DateTimeField(default=datetime.now)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    class Meta:
        db_table = 'futurestar_app_post_like'
        unique_together = ('created_by_id', 'post')  # Ensure one like per user/team/group per post


class Field(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE,default=True)
    field_name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='fields_images/', blank=True, null=True)  # Add image field
    field_capacity = models.ForeignKey(FieldCapacity, on_delete=models.CASCADE,default=True)
    ground_type = models.ForeignKey(GroundMaterial, on_delete=models.CASCADE,default=True)
    country_id = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    city_id = models.ForeignKey(City, null=True, blank=True, on_delete=models.CASCADE)

     # New fields
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    address = models.CharField(max_length=255, blank=True, null=True)
    house_no = models.CharField(max_length=50, blank=True, null=True)
    premises = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country_name = models.CharField(max_length=100, blank=True, null=True)
    postalCode = models.CharField(max_length=20, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True) 
    
    additional_information = models.TextField(max_length=255,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return self.field_name

    class Meta:
        db_table = 'futurestar_app_field'



class OTPSave(models.Model):
    id = models.AutoField(primary_key=True)
    phone = models.CharField(max_length=100,blank=True,null=True)
    OTP = models.CharField(max_length=100,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    class Meta:
        db_table = 'futurestar_app_otpsave'
              

    def save(self, *args, **kwargs):
        self.expires_at = timezone.now() + timedelta(minutes=1)  # Set expiration time
        super().save(*args, **kwargs)


    def is_expired(self):
            return timezone.now() > self.expires_at
    

class FollowRequest(models.Model):
    USER_TYPE = 1
    TEAM_TYPE = 2
    GROUP_TYPE = 3
    CREATOR_TYPE_CHOICES = (
        (USER_TYPE, 'User'),
        (TEAM_TYPE, 'Team'),
        (GROUP_TYPE, 'Group'),
    )

    created_by_id = models.IntegerField(null=True,blank=True)
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES,default=USER_TYPE)
    target_id = models.IntegerField(null=True,blank=True)
    target_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES,default=USER_TYPE)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    class Meta:
        db_table = 'futurestar_app_followrequest'
        unique_together = (
            ('created_by_id', 'creator_type', 'target_id', 'target_type'),
        )




def user_directory_path(instance, filename):
    # Determine the content type (1 for Images, 2 for Videos)
    content_type = 'images' if instance.content_type == 1 else 'videos'
    # Construct path using user ID and content type
    return f'media/{content_type}/{filename}'


class Album(models.Model):
    USER_TYPE = 1
    TEAM_TYPE = 2
    GROUP_TYPE = 3

    CREATOR_TYPE_CHOICES = (
        (USER_TYPE, 'User'),
        (TEAM_TYPE, 'Team'),
        (GROUP_TYPE, 'Group'),
    )

    id = models.AutoField(primary_key=True)
    name = models.TextField(null=True, blank=True)
    created_by_id = models.IntegerField(blank=True, null=True)  # Stores the ID of User, Team, or Group
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES,blank=True, null=True)  # Stores 1, 2, or 3 based on the type
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    class Meta:
        db_table = 'futurestar_app_album'

    def __str__(self):
        return self.name

class Gallary(models.Model):
    USER_TYPE = 1
    TEAM_TYPE = 2
    GROUP_TYPE = 3

    CREATOR_TYPE_CHOICES = (
        (USER_TYPE, 'User'),
        (TEAM_TYPE, 'Team'),
        (GROUP_TYPE, 'Group'),
    )
    CONTENT_TYPE_CHOICES = [
        (1, 'Images'),
        (2, 'Videos'),
    ]
    
    id = models.AutoField(primary_key=True)
    created_by_id = models.IntegerField(blank=True, null=True)  # Stores the ID of User, Team, or Group
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES, blank=True, null=True)
    album = models.ForeignKey('Album', related_name='gallery_set', null=True, on_delete=models.CASCADE)

    content_type = models.IntegerField(choices=CONTENT_TYPE_CHOICES, default=1)
    media_file = models.FileField(upload_to=user_directory_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return f"Gallery Item {self.id} by {self.get_creator_type_display()}"

    class Meta:
        db_table = 'futurestar_app_gallery'






class Report(models.Model):
    id=models.AutoField(primary_key=True)
    title_en=models.CharField(max_length=255, blank=True, null=True)
    title_ar=models.CharField(max_length=255, blank=True, null=True)
    content_en=models.TextField(blank=True, null=True)
    content_ar=models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return self.title_en
    
    class Meta:
        db_table = 'futurestar_app_reports'

    
class PostReport(models.Model):
    USER_TYPE = 1
    TEAM_TYPE = 2
    GROUP_TYPE = 3

    CREATOR_TYPE_CHOICES = (
        (USER_TYPE, 'User'),
        (TEAM_TYPE, 'Team'),
        (GROUP_TYPE, 'Group'),
    )

    id = models.AutoField(primary_key=True)
    report_id = models.ForeignKey(Report, on_delete=models.CASCADE)
    post_id = models.ForeignKey(Post, on_delete=models.CASCADE)
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES, blank=True, null=True)
    created_by_id = models.IntegerField(blank=True, null=True)  # Stores the ID of User, Team, or Group
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return f"Post Report {self.id} for Report {self.report_id.id}"

    class Meta:
        db_table = 'futurestar_app_postreport'

class Sponsor(models.Model):
     
    TEAM_TYPE = 2
    GROUP_TYPE = 3

    CREATOR_TYPE_CHOICES = (
        (TEAM_TYPE, 'Team'),
        (GROUP_TYPE, 'Group'),
    )
    name = models.CharField(max_length=20,blank=True, null=True)
    logo = models.ImageField(upload_to='sponsors_images/', blank=True, null=True)  
    url = models.CharField(max_length=255, blank=True, null=True)
    created_by_id = models.IntegerField(blank=True, null=True)  # Stores the ID of User, Team, or Group
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES, blank=True, null=True)
   
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 
    
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'futurestar_app_sponsor'





class MobileDashboardBanner(models.Model):
    
    id = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to='dashboardbanner_images/', blank= True, null= True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return self.id

    class Meta:
        db_table = 'futurestar_app_dashboardbanner'


class Event(models.Model):
  
    TEAM_TYPE = 2

    CREATOR_TYPE_CHOICES = (
   
        (TEAM_TYPE, 'Team'),
       
    )

    id = models.AutoField(primary_key=True)
    # team=models.ForeignKey('Team', on_delete=models.CASCADE)

    event_organizer=models.ForeignKey(User, on_delete=models.CASCADE)
    event_name=models.CharField(max_length=255, blank=True, null=True)
    event_type=models.ForeignKey(EventType, on_delete=models.CASCADE)
    event_date=models.DateTimeField(blank=True, null=True)
    event_start_time=models.TimeField(blank=True, null=True)
    event_end_time=models.TimeField(blank=True, null=True)
    event_image=models.ImageField(upload_to='event_images/', blank=True, null=True)

    #event_vanue
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    address = models.CharField(max_length=255, blank=True, null=True)
    house_no = models.CharField(max_length=50, blank=True, null=True)
    premises = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country_name = models.CharField(max_length=100, blank=True, null=True)
    postalCode = models.CharField(max_length=20, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True) 

    event_description=models.TextField(blank=True, null=True)
    event_cost=models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_by_id = models.IntegerField(blank=True, null=True)  # Stores the ID of User, Team, or Group
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES, blank=True, null=True,default=TEAM_TYPE)


    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 
    
    def __str__(self):
        return self.event_name
    
    class Meta:
        db_table = 'futurestar_app_event'

class EventBooking(models.Model):
    USER_TYPE = 1
  
    
    CREATOR_TYPE_CHOICES = (
        (USER_TYPE, 'User'),
      
    )

    id = models.AutoField(primary_key=True)
    created_by_id = models.IntegerField(default=0)  # Stores ID of User, Team, or Group
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES, default=USER_TYPE)    
    event=models.ForeignKey(Event, on_delete=models.CASCADE)
    tickets=models.IntegerField()
    convenience_fee=models.FloatField(default=0.0)
    ticket_amount=models.FloatField(default=0.0)
    total_amount=models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return self.event.event_name
    
    class Meta:
        db_table = 'futurestar_app_eventbooking'


# Event  model to track likes & Comments on a Event
class Event_comment(models.Model):
    USER_TYPE = 1
    TEAM_TYPE = 2
    GROUP_TYPE = 3
    
    CREATOR_TYPE_CHOICES = (
        (USER_TYPE, 'User'),
        (TEAM_TYPE, 'Team'),
        (GROUP_TYPE, 'Group'),
    )

    created_by_id = models.IntegerField(default=0)  # Stores ID of User, Team, or Group
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES, default=USER_TYPE)
    event = models.ForeignKey(Event, related_name='event_comments', on_delete=models.CASCADE, default=True)
    parent = models.ForeignKey('self', related_name='event_replies', null=True, blank=True, on_delete=models.CASCADE)
    comment = models.TextField()
    date_created = models.DateTimeField(default=datetime.now)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return f'Comment by ID {self.created_by_id} on Event {self.event.id}'

    class Meta:
        db_table = 'futurestar_app_event_comment'


class EventLike(models.Model):
    USER_TYPE = 1
    TEAM_TYPE = 2
    GROUP_TYPE = 3
    
    CREATOR_TYPE_CHOICES = (
        (USER_TYPE, 'User'),
        (TEAM_TYPE, 'Team'),
        (GROUP_TYPE, 'Group'),
    )

    created_by_id = models.IntegerField(default=0)  # Stores ID of User, Team, or Group
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES, default=USER_TYPE)
    event = models.ForeignKey(Event, related_name='event_likes', on_delete=models.CASCADE, default=True)
    date_liked = models.DateTimeField(default=datetime.now)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)   

    class Meta:
        db_table = 'futurestar_app_event_like'
        unique_together = ('creator_type','created_by_id', 'event')  # Ensure one like per user/team/group per event


class FAQ(models.Model):
    question_en = models.TextField(blank=True,null=True)
    question_ar = models.TextField(blank=True,null=True)
    answer_en = models.TextField(blank=True,null=True)
    answer_ar = models.TextField(blank=True,null=True)
    date_created = models.DateTimeField(default=datetime.now)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)  

    def __str__(self):
        return self.question_en

    class Meta:
        db_table = 'futurestar_app_faq'



