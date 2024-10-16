from django.db import models
from FutureStar_App.models import *
from django.utils import timezone
import datetime

# Create your models here.

class Team(models.Model):
    user_id = models.ForeignKey(User,on_delete=models.CASCADE,default=True)
    team_name = models.CharField(max_length=255,blank=True,null=True)
    team_type = models.ForeignKey(Category,on_delete=models.CASCADE,default=True)
    bio = models.TextField(null=True,blank=True)
    team_establishment_date = models.DateField(blank=True,null=True)
    team_president = models.CharField(max_length=255,blank=True,null=True)
    location = models.CharField(max_length=500,blank=True,null=True)
    latitude = models.CharField(max_length=500,blank=True,null=True)
    longitude = models.CharField(max_length=500,blank=True,null=True)    
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.CASCADE)
    phone = models.CharField(max_length=255,blank=True,null=True)
    email = models.EmailField(max_length=255,blank=True,null=True)
    age_group = models.CharField(max_length=255,blank=True,null=True)
    entry_fees = models.CharField(max_length=255,blank=True,null=True)
    branches = models.CharField(max_length=500,blank=True,null=True)
    team_logo = models.ImageField(upload_to='team/team_logo/', blank=True, null=True)  # Add image field
    team_background_image = models.ImageField(upload_to='team/team_background_image/', blank=True, null=True)  # Add image field
    team_uniform = models.ImageField(upload_to='team/team_uniform/', blank=True, null=True)  # Add image field

    def __str__(self):
        return self.team_name

    class Meta:
        db_table = 'futurestar_app_team'
    
class TrainingGroups(models.Model):
    TYPE_CHOICES = [
        (1, 'Open'),
        (2, 'Close'),
    ]
    user_id = models.ForeignKey(User,on_delete=models.CASCADE,default=True)
    group_name = models.CharField(max_length=255,blank=True,null=True)
    group_username = models.CharField(max_length=255,blank=True,null=True)
    group_type = models.IntegerField(choices=TYPE_CHOICES, default=1)
    bio = models.TextField(null=True,blank=True)
    group_president = models.CharField(max_length=255,blank=True,null=True)
    location = models.CharField(max_length=500,blank=True,null=True)
    latitude = models.CharField(max_length=500,blank=True,null=True)
    longitude = models.CharField(max_length=500,blank=True,null=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.CASCADE)
    phone = models.CharField(max_length=255,blank=True,null=True)
    group_logo = models.ImageField(upload_to='group/group_logo/', blank=True, null=True)  # Add image field
    group_background_image = models.ImageField(upload_to='group/group_background_image/', blank=True, null=True)  # Add image field

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
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'futurestar_app_post'

class Post_comment(models.Model):
    user = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE,default=True)
    team_id = models.ForeignKey(Team ,null=True,blank=True, on_delete=models.CASCADE)
    gropu_id = models.ForeignKey(TrainingGroups, on_delete=models.CASCADE,null=True,blank=True)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE,default=True)
    parent = models.ForeignKey('self', related_name='replies', null=True, blank=True, on_delete=models.CASCADE)
    comment = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.post.title}'

    class Meta:
        db_table = 'futurestar_app_post_comment'



class Field(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE,default=True)
    field_name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='fields_images/', blank=True, null=True)  # Add image field
    field_capacity = models.ForeignKey(FieldCapacity, on_delete=models.CASCADE,default=True)
    ground_type = models.ForeignKey(GroundMaterial, on_delete=models.CASCADE,default=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.CASCADE)
    location = models.CharField(max_length=500,blank=True,null=True)
    latitude = models.CharField(max_length=500,blank=True,null=True)
    longitude = models.CharField(max_length=500,blank=True,null=True)    
    additional_information = models.TextField(max_length=255,blank=True, null=True)

    def __str__(self):
        return self.field_name

    class Meta:
        db_table = 'futurestar_app_field'


class Tournament(models.Model):
    user_id = models.ForeignKey(User,on_delete=models.CASCADE,default=True)
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

    def __str__(self):
        return self.tournament_name

    class Meta:
        db_table = 'futurestar_app_tournament'
        

class OTPSave(models.Model):
    id = models.AutoField(primary_key=True)
    phone = models.CharField(max_length=100,blank=True,null=True)
    OTP = models.CharField(max_length=100,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'futurestar_app_otpsave'
              

    def save(self, *args, **kwargs):
            self.expires_at = timezone.now() + datetime.timedelta(minutes=1)
            super().save(*args, **kwargs)

    def is_expired(self):
            return timezone.now() > self.expires_at
    

class FollowRequest(models.Model):
    STATUS_CHOICES = [
        (1, 'Pending'),
        (2, 'Accepted'),
        (3, 'Rejected'),
    ]
    
    from_user = models.ForeignKey(User, related_name='follow_requests_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='follow_requests_received', on_delete=models.CASCADE)
    status = models.IntegerField(choices=STATUS_CHOICES, default=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'futurestar_app_followrequest'

    def __str__(self):
        return f"{self.from_user} wants to follow {self.to_user}"
    
    @staticmethod
    def get_follower_count(user):
        """Returns the number of followers for a given user"""
        return FollowRequest.objects.filter(to_user=user, status=2).count()

    @staticmethod
    def get_following_count(user):
        """Returns the number of users a given user is following"""
        return FollowRequest.objects.filter(from_user=user, status=2).count()



# Helper function for dynamic file paths
def user_directory_path(instance, filename):
    # Determine the content type (1 for Images, 2 for Videos)
    content_type = 'images' if instance.content_type == 1 else 'videos'
    # Construct path using user ID and content type
    return f'media/{instance.user.id}/{content_type}/{filename}'

class Album(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, related_name='user_album', on_delete=models.CASCADE)

    team_id = models.ForeignKey(Team, null=True, blank=True, on_delete=models.CASCADE)
    name = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'futurestar_app_album'
    
    def __str__(self):
        return self.name

class Gallary(models.Model):  # Fixing typo from "Gallary(models.Models)"
    CONTENT_TYPE = [
        (1, 'Images'),
        (2, 'Videos'),
    ]
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, related_name='user_gallary', on_delete=models.CASCADE)
    team_id = models.ForeignKey(Team, null=True, blank=True, on_delete=models.CASCADE)
    album_id = models.ForeignKey(Album, related_name='gallary_set',null=True, on_delete=models.CASCADE)
    content_type = models.IntegerField(choices=CONTENT_TYPE, default=1)
    
    # Use the helper function for the upload_to argument
    media_file = models.FileField(upload_to=user_directory_path, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = 'futurestar_app_gallary'
