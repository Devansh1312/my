from django.db import models
from FutureStar_App.models import *
from django.utils import timezone
import datetime
from django.core.exceptions import ValidationError
from datetime import datetime 

# Create your models here.

class Team(models.Model):
    user_id = models.ForeignKey(User,on_delete=models.CASCADE,default=True)
    team_name = models.CharField(max_length=255,blank=True,null=True)
    team_username = models.CharField(max_length=255,blank=True,null=True)
    team_type = models.ForeignKey(Category,on_delete=models.CASCADE,default=True)
    bio = models.TextField(null=True,blank=True)
    team_establishment_date = models.DateField(blank=True,null=True)
    team_president = models.CharField(max_length=255,blank=True,null=True)
    
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
    phone = models.CharField(max_length=255,blank=True,null=True)
    email = models.EmailField(max_length=255,blank=True,null=True)
    age_group = models.CharField(max_length=255,blank=True,null=True)
    entry_fees = models.CharField(max_length=255,blank=True,null=True)
    branches = models.CharField(max_length=500,blank=True,null=True)
    team_logo = models.ImageField(upload_to='team/team_logo/', blank=True, null=True)  # Add image field
    team_background_image = models.ImageField(upload_to='team/team_background_image/', blank=True, null=True)  # Add image field
    team_uniform = models.TextField( blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(default=datetime.now) 
    
    def __str__(self):
        return self.team_name

    class Meta:
        db_table = 'futurestar_app_team'
    
class TrainingGroups(models.Model):
    group_name = models.CharField(max_length=255,blank=True,null=True)
    group_username = models.CharField(max_length=255,blank=True,null=True)
    bio = models.TextField(null=True,blank=True)
    group_founder = models.ForeignKey(User,on_delete=models.CASCADE,default=True)

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
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return self.group_name

    class Meta:
        db_table = 'futurestar_app_traininggroups'

# post  Model
class Post(models.Model):
    user = models.ForeignKey(User, related_name='posts', on_delete=models.CASCADE,default=True)
    title = models.CharField(max_length=255)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)  # Add this if it's optional
    group = models.ForeignKey(TrainingGroups, on_delete=models.CASCADE,null=True,blank=True)
    description = models.TextField()
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)  # Add image field
    media_type = models.IntegerField(default=1)
    date_created = models.DateTimeField(default=datetime.now)

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

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'futurestar_app_post'

class Post_comment(models.Model):
    user = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE,default=True)
    team_id = models.ForeignKey(Team, null=True, blank=True, on_delete=models.CASCADE)
    group_id = models.ForeignKey(TrainingGroups, on_delete=models.CASCADE, null=True, blank=True)  # Corrected typo
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE, default=True)
    parent = models.ForeignKey('self', related_name='replies', null=True, blank=True, on_delete=models.CASCADE)
    comment = models.TextField()
    date_created = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.post.title}'


    class Meta:
        db_table = 'futurestar_app_post_comment'

# PostView model to track views on a post
class PostView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='views', on_delete=models.CASCADE)
    date_viewed = models.DateTimeField(default=datetime.now)
    
    class Meta:
        db_table = 'futurestar_app_post_view'
        unique_together = ('user', 'post')  # Each user can only view the post once (optional)

# PostLike model to track likes on a post
class PostLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='likes', on_delete=models.CASCADE)
    date_liked = models.DateTimeField(default=datetime.now)

    class Meta:
        db_table = 'futurestar_app_post_like'
        unique_together = ('user', 'post')  # Each user can only like the post once

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
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.field_name

    class Meta:
        db_table = 'futurestar_app_field'


class Tournament(models.Model):
    user_id = models.ForeignKey(User,on_delete=models.CASCADE,default=True)
    team_id = models.ForeignKey(Team,null=True, blank=True, on_delete=models.CASCADE)
    tournament_name = models.CharField(max_length=255,blank=True,null=True)
    tournament_starting_date = models.DateField(blank=True,null=True)
    tournament_final_date = models.DateField(blank=True,null=True)
    number_of_team = models.CharField(max_length=255,blank=True,null=True)
    tournament_name = models.CharField(max_length=255,blank=True,null=True)
    age_group = models.CharField(max_length=255,blank=True,null=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.CASCADE)
    tournament_fields = models.ForeignKey(Field,blank=True,null=True,on_delete=models.CASCADE)
    logo = models.ImageField(upload_to='tournament_logo/', blank=True, null=True)  # Add image field
    tournament_joining_cost = models.CharField(max_length=255,blank=True,null=True)
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tournament_name

    class Meta:
        db_table = 'futurestar_app_tournament'
        

class OTPSave(models.Model):
    id = models.AutoField(primary_key=True)
    phone = models.CharField(max_length=100,blank=True,null=True)
    OTP = models.CharField(max_length=100,blank=True,null=True)
    created_at = models.DateTimeField(default=datetime.now)

    class Meta:
        db_table = 'futurestar_app_otpsave'
              

    def save(self, *args, **kwargs):
            self.expires_at = timezone.now() + datetime.timedelta(minutes=1)
            super().save(*args, **kwargs)

    def is_expired(self):
            return timezone.now() > self.expires_at
    

class FollowRequest(models.Model):
    from_user = models.ForeignKey(User, null=True, blank=True, related_name='follow_requests_sent', on_delete=models.CASCADE)
    from_team = models.ForeignKey(Team, null=True, blank=True, related_name='team_follow_requests_sent', on_delete=models.CASCADE)
    from_group = models.ForeignKey(TrainingGroups, null=True, blank=True, related_name='group_follow_requests_sent', on_delete=models.CASCADE)
    
    to_user = models.ForeignKey(User, null=True, blank=True, related_name='follow_requests_received', on_delete=models.CASCADE)
    to_team = models.ForeignKey(Team, null=True, blank=True, related_name='team_follow_requests_received', on_delete=models.CASCADE)
    to_group = models.ForeignKey(TrainingGroups, null=True, blank=True, related_name='group_follow_requests_received', on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'futurestar_app_followrequest'
        unique_together = (
            ('from_user', 'to_user'),
            ('from_team', 'to_team'),
            ('from_group', 'to_group')
        )

    # Count followers for any entity (user, team, or group)
    @classmethod
    def count_followers(cls, to_user=None, to_team=None, to_group=None):
        return cls.objects.filter(
            to_user=to_user if to_user else None,
            to_team=to_team if to_team else None,
            to_group=to_group if to_group else None
        ).count()

    # Count followings for any entity (user, team, or group)
    @classmethod
    def count_following(cls, from_user=None, from_team=None, from_group=None):
        return cls.objects.filter(
            from_user=from_user if from_user else None,
            from_team=from_team if from_team else None,
            from_group=from_group if from_group else None
        ).count()

    # Helper method to return the source entity (user/team/group) from which the request was sent
    def get_from_entity(self):
        if self.from_user:
            return self.from_user
        elif self.from_team:
            return self.from_team
        elif self.from_group:
            return self.from_group

    # Helper method to return the target entity (user/team/group) to which the request was sent
    def get_to_entity(self):
        if self.to_user:
            return self.to_user
        elif self.to_team:
            return self.to_team
        elif self.to_group:
            return self.to_group



# Helper function for dynamic file paths
def user_directory_path(instance, filename):
    # Determine the content type (1 for Images, 2 for Videos)
    content_type = 'images' if instance.content_type == 1 else 'videos'
    # Construct path using user ID and content type
    return f'media/{content_type}/{filename}'

class Album(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, related_name='user_album', on_delete=models.CASCADE)
    team_id = models.ForeignKey('Team', null=True, blank=True, on_delete=models.CASCADE)
    group_id = models.ForeignKey('TrainingGroups', related_name='training_group_album', null=True, blank=True, on_delete=models.CASCADE)
    name = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'futurestar_app_album'

    def __str__(self):
        return self.name


class Gallary(models.Model):
    CONTENT_TYPE = [
        (1, 'Images'),
        (2, 'Videos'),
    ]
    
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, related_name='user_gallary', on_delete=models.CASCADE)
    team_id = models.ForeignKey('Team', null=True, blank=True, on_delete=models.CASCADE)
    album_id = models.ForeignKey('Album', related_name='gallary_set', null=True, on_delete=models.CASCADE)
    group_id = models.ForeignKey('TrainingGroups', related_name='training_group_gallary', null=True, blank=True, on_delete=models.CASCADE)
    content_type = models.IntegerField(choices=CONTENT_TYPE, default=1)
    media_file = models.FileField(upload_to=user_directory_path, blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Gallery Item {self.id} by User {self.user.id}"

    class Meta:
        db_table = 'futurestar_app_gallary'




class Report(models.Model):
    id=models.AutoField(primary_key=True)
    title_en=models.CharField(max_length=255, blank=True, null=True)
    title_ar=models.CharField(max_length=255, blank=True, null=True)
    content_en=models.TextField(blank=True, null=True)
    content_ar=models.TextField(blank=True, null=True)
    created_at=models.DateTimeField(default=datetime.now)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title_en
    
    class Meta:
        db_table = 'futurestar_app_reports'

    
class PostReport(models.Model):
    id=models.AutoField(primary_key=True)
    report_id=models.ForeignKey(Report, on_delete=models.CASCADE)
    post_id=models.ForeignKey(Post, on_delete=models.CASCADE)
    user_id=models.ForeignKey(User, on_delete=models.CASCADE)
    created_at=models.DateTimeField(default=datetime.now)
    updated_at=models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Post Report {self.id} for Report {self.report_id.id}"
    
    class Meta:
        db_table = 'futurestar_app_postreport'

class Sponsor(models.Model):
    name = models.CharField(max_length=20,blank=True, null=True)
    logo = models.ImageField(upload_to='sponsors_images/', blank=True, null=True)  
    url = models.CharField(max_length=255, blank=True, null=True)
    team_id = models.ForeignKey('Team', blank=True, null=True,  on_delete=models.CASCADE)
    group_id = models.ForeignKey('TrainingGroups', blank=True, null=True,  on_delete=models.CASCADE)
    created_at= models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'futurestar_app_sponsor'

class MobileDashboardBanner(models.Model):
    
    id = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to='dashboardbanner_images/', blank= True, null= True)
    created_at= models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.id

    class Meta:
        db_table = 'futurestar_app_dashboardbanner'


class Event(models.Model):
    id = models.AutoField(primary_key=True)
    team=models.ForeignKey('Team', on_delete=models.CASCADE)

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
    created_at=models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.event_name
    
    class Meta:
        db_table = 'futurestar_app_event'

class EventBooking(models.Model):
    id = models.AutoField(primary_key=True)
    event=models.ForeignKey(Event, on_delete=models.CASCADE)
    tickets=models.IntegerField()
    convenience_fee=models.FloatField(default=0.0)
    ticket_amount=models.FloatField(default=0.0)
    total_amount=models.FloatField(default=0.0)
    created_at=models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.event.event_name
    
    class Meta:
        db_table = 'futurestar_app_eventbooking'

class Event_comment(models.Model):
    user = models.ForeignKey(User, related_name='event_comments', on_delete=models.CASCADE,default=True)
    event = models.ForeignKey(Event, related_name='event_comments', on_delete=models.CASCADE, default=True)
    parent = models.ForeignKey('self', related_name='event_replies', null=True, blank=True, on_delete=models.CASCADE)
    comment = models.TextField()
    date_created = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return self.id


    class Meta:
        db_table = 'futurestar_app_event_comment'


# PostLike model to track likes on a post
class EventLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, related_name='event_likes', on_delete=models.CASCADE, default=True)
    date_liked = models.DateTimeField(default=datetime.now)
    date_created = models.DateTimeField(default=datetime.now)  

    class Meta:
        db_table = 'futurestar_app_event_like'
        unique_together = ('user', 'event')  # Each user can only like the post once



class FAQ(models.Model):
    question_en = models.TextField(blank=True,null=True)
    question_ar = models.TextField(blank=True,null=True)
    answer_en = models.TextField(blank=True,null=True)
    answer_ar = models.TextField(blank=True,null=True)
    date_created = models.DateTimeField(default=datetime.now)  

    def __str__(self):
        return self.question_en

    class Meta:
        db_table = 'futurestar_app_faq'
