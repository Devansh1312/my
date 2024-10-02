from django.db import models
from FutureStar_App.models import *


# Create your models here.
# post  Model
class Post(models.Model):
    user = models.ForeignKey(User, related_name='posts', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)  # Add image field
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'futurestar_app_post'

class Post_comment(models.Model):
    user = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', related_name='replies', null=True, blank=True, on_delete=models.CASCADE)
    comment = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.post.title}'

    class Meta:
        db_table = 'futurestar_app_post_comment'



class Field(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='fields_images/', blank=True, null=True)  # Add image field
    field_capacity = models.ForeignKey(FieldCapacity, on_delete=models.CASCADE)
    ground_type = models.ForeignKey(GroundMaterial, on_delete=models.CASCADE)
    country = models.CharField(max_length=255)    
    city = models.CharField(max_length=255)
    location = models.CharField(max_length=500)
    additional_information = models.TextField(max_length=255,blank=True, null=True)

    def __str__(self):
        return self.field_name

    class Meta:
        db_table = 'futurestar_app_field'


class Tournament(models.Model):
    user_id = models.ForeignKey(User,on_delete=models.CASCADE)
    tournament_name = models.CharField(max_length=255,blank=True,null=True)
    tournament_starting_date = models.DateField(blank=True,null=True)
    tournament_final_date = models.DateField(blank=True,null=True)
    number_of_team = models.CharField(max_length=255,blank=True,null=True)
    tournament_name = models.CharField(max_length=255,blank=True,null=True)
    age_group = models.CharField(max_length=255,blank=True,null=True)
    country = models.CharField(max_length=255,blank=True,null=True)
    city = models.CharField(max_length=255,blank=True,null=True)
    tournament_fields = models.ForeignKey(Field,blank=True,null=True,on_delete=models.CASCADE)
    logo = models.ImageField(upload_to='tournament_logo/', blank=True, null=True)  # Add image field
    tournament_joining_cost = models.CharField(max_length=255,blank=True,null=True)

    def __str__(self):
        return self.tournament_name

    class Meta:
        db_table = 'futurestar_app_tournament'
    

class Team(models.Model):
    user_id = models.ForeignKey(User,on_delete=models.CASCADE)
    team_name = models.CharField(max_length=255,blank=True,null=True)
    team_type = models.ForeignKey(Category,on_delete=models.CASCADE)
    bio = models.TextField(null=True,blank=True)
    team_establishment_date = models.DateField(blank=True,null=True)
    team_president = models.CharField(max_length=255,blank=True,null=True)
    location = models.CharField(max_length=500,blank=True,null=True)
    country = models.CharField(max_length=255,blank=True,null=True)
    city = models.CharField(max_length=255,blank=True,null=True)
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