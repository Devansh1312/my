from django.db import models
from FutureStar_App.models import *
from FutureStarAPI.models import *

from django.utils import timezone
import datetime
from django.core.exceptions import ValidationError
from datetime import datetime 
from django.utils import timezone
from datetime import timedelta


class Training(models.Model):
    USER_TYPE = 1
    TEAM_TYPE = 2
    GROUP_TYPE = 3
    OPEN_TRAINING = 1
    CLOSED_TRAINING = 2
    
    CREATOR_TYPE_CHOICES = (
        (USER_TYPE, 'User'),
        (TEAM_TYPE, 'Team'),
        (GROUP_TYPE, 'Group'),
    )

    TRAINING_TYPE_CHOICES =(
        (OPEN_TRAINING, 'Open Training'),
        (CLOSED_TRAINING, 'Closed Training'),
    )

    training_name = models.CharField(max_length=255, null=True, blank=True)
    training_photo = models.ImageField(upload_to='training_photo/', null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True)
    field = models.ForeignKey(Field, on_delete=models.CASCADE, null=True, blank=True)
    gender = models.ForeignKey(UserGender, on_delete=models.CASCADE, null=True, blank=True)
    training_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    training_duration = models.IntegerField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    no_of_participants = models.IntegerField(null=True, blank=True)
    training_type = models.IntegerField(choices=TRAINING_TYPE_CHOICES, default=OPEN_TRAINING)  # Corrected default assignment
    cost = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    creator_type = models.IntegerField(choices=CREATOR_TYPE_CHOICES, null=True, blank=True)
    created_by_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.training_name
    
    class Meta:
        db_table = 'futurestar_app_training'


class TrainingLike(models.Model):
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
    training = models.ForeignKey(Training, related_name='likes', on_delete=models.CASCADE)
    date_liked = models.DateTimeField(default=datetime.now)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    class Meta:
        db_table = 'futurestar_app_training_like'
        unique_together = ('created_by_id', 'training')  # Ensure one like per user/team/group per post


class Training_comment(models.Model):
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
    training = models.ForeignKey(Training, related_name='comments', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', related_name='replies', null=True, blank=True, on_delete=models.CASCADE)
    comment = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    def __str__(self):
        return f'Comment by ID {self.created_by_id} on {self.post.title}'

    class Meta:
        db_table = 'futurestar_app_training_comment'


class Training_Joined(models.Model):
  training = models.ForeignKey(Training, related_name='joined', on_delete=models.CASCADE)
  user = models.ForeignKey(User, related_name='joined_training', on_delete=models.CASCADE)
  attendance_status = models.BooleanField(default=False)
  rating = models.IntegerField(default=0,null=True, blank=True)
  injury_type = models.ManyToManyField(InjuryType, blank=True)  # Change to ManyToManyField
  created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
  updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

  def __str__(self):
      return f'{self.user} joined {self.training}'
  
  class Meta:
      db_table = 'futurestar_app_training_joined'
      unique_together = ('user', 'training')


class Training_Feedback(models.Model):
    training = models.ForeignKey(Training, related_name='feedback', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='feedback', on_delete=models.CASCADE)
    feedback = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def __str__(self):
        return f'Feedback by {self.user} on {self.training}'
    
    class Meta:
        db_table = 'futurestar_app_training_feedback'