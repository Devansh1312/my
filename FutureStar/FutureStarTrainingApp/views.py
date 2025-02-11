from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from FutureStar.firebase_config import send_push_notification
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.utils.translation import gettext as _
from django.utils.crypto import get_random_string
from django.utils.translation import activate 
from django.core.files.storage import default_storage
from datetime import date
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
import json
from django.core.exceptions import ObjectDoesNotExist

################# Create Training API #######################
# class CreateTrainingView(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = (JSONParser, MultiPartParser, FormParser)

#     def post(self, request, *args, **kwargs):
#         language = request.headers.get('Language', 'en')
#         if language in ['en', 'ar']:
#             activate(language)
#         try:
#             creator_type = int(request.data.get('creator_type'))
#             created_by_id = int(request.data.get('created_by_id'))
#         except (ValueError, TypeError):
#             return Response({
#                 'status': 0,
#                 'message': _('Invalid creator_type or created_by_id.')
#             }, status=status.HTTP_400_BAD_REQUEST)

#         country_id = request.data.get('country')
#         city_id = request.data.get('city')
#         gender_id = request.data.get('gender')
#         field_id = request.data.get('field')
#         description = request.data.get('description', '')
#         cost = request.data.get('cost', '')
#         training_type = int(request.data.get('training_type', 1))  # Default: Open training

#         try:
#             country_id = int(country_id) if country_id else None
#             city_id = int(city_id) if city_id else None
#             gender_id = int(gender_id) if gender_id else None
#             field_id = int(field_id) if field_id else None
#             training_type = int(training_type)
#         except (ValueError, TypeError):
#             return Response({
#                 'status': 0,
#                 'message': _('Invalid country, city, gender, or field ID provided.')
#             }, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             country = Country.objects.get(id=country_id) if country_id else None
#             city = City.objects.get(id=city_id) if city_id else None
#             gender = UserGender.objects.get(id=gender_id) if gender_id else None
#             field = Field.objects.get(id=field_id) if field_id else None
#         except ObjectDoesNotExist:
#             return Response({
#                 'status': 0,
#                 'message': _('Invalid country, city, gender, or field provided.')
#             }, status=status.HTTP_400_BAD_REQUEST)

#         training_name = request.data.get('training_name', '')
#         training_date = request.data.get('training_date')

#         end_date = request.data.get('end_date', None)
#         repeat_type = int(request.data.get('repeat_type', 2))  # Default: Single training

#         days_str = request.data.get('days', '[]')  # Expected format: '[1, 3, 5]'
#         start_times_str = request.data.get('start_time', '[]')  # Expected format: '["18:00", "19:00"]'
#         end_times_str = request.data.get('end_time', '[]')  # Expected format: '["19:00", "20:00"]'
#         no_of_participants = int(request.data.get('no_of_participants', 0))

#         if repeat_type == 1:  # Only parse days, start_times, end_times for multiple sessions
#             try:
#                 days = ast.literal_eval(days_str)
#                 start_times = ast.literal_eval(start_times_str)
#                 end_times = ast.literal_eval(end_times_str)
#             except (ValueError, SyntaxError) as e:
#                 return Response({
#                     'status': 0,
#                     'message': _('Invalid format for days, start_time, or end_time.')
#                 }, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             days, start_times, end_times = [], [], []  # For single training, these can be empty or not required

#         training_photo = None
#         if "training_photo" in request.FILES:
#             image = request.FILES["training_photo"]
#             file_extension = image.name.split('.')[-1]
#             unique_suffix = get_random_string(8)
#             file_name = f"training_photo/{request.user.id}_{unique_suffix}.{file_extension}"
#             training_photo = default_storage.save(file_name, image)

#         weekday_mapping = {
#             0: 2, 1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 1
#         }

#         training_instances = []
#         if repeat_type == 2:  # Single training session
#             try:
#                 start_time_str = request.data.get('start_time')  # Assume 'start_time' is in H:M format
#                 end_time_str = request.data.get('end_time')      # Assume 'end_time' is in H:M format
#                 start_time_obj = datetime.strptime(start_time_str, "%H:%M:%S").time()
#                 end_time_obj = datetime.strptime(end_time_str, "%H:%M:%S").time()
#                 duration = (datetime.combine(datetime.today(), end_time_obj) - 
#                             datetime.combine(datetime.today(), start_time_obj)).seconds // 60
#             except ValueError as e:
#                 return Response({'status': 0, 'message': _('Invalid time format.')}, status=status.HTTP_400_BAD_REQUEST)

#             training_instance = Training.objects.create(
#                 training_name=training_name,
#                 training_photo=training_photo,
#                 training_date=training_date,
#                 start_time=start_time_obj,
#                 end_time=end_time_obj,
#                 training_duration=duration,
#                 creator_type=creator_type,
#                 created_by_id=created_by_id,
#                 country=country,
#                 city=city,
#                 gender=gender,
#                 field=field,
#                 no_of_participants=no_of_participants,
#                 description=description,
#                 cost=cost,
#                 training_type=training_type,
#             )
#             training_instances.append(training_instance)

#         elif repeat_type == 1 and end_date and days:
#             try:
#                 start_time_objs = [datetime.strptime(st, "%H:%M:%S").time() for st in start_times]
#                 end_time_objs = [datetime.strptime(et, "%H:%M:%S").time() for et in end_times]
#                 durations = [
#                     (datetime.combine(datetime.today(), et) - datetime.combine(datetime.today(), st)).seconds // 60
#                     for st, et in zip(start_time_objs, end_time_objs)
#                 ]
#             except ValueError as e:
#                 return Response({
#                     'status': 0,
#                     'message': _('Invalid time format or time arrays mismatch.'),
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             try:
#                 training_date_obj = datetime.strptime(training_date, "%Y-%m-%d").date()
#                 end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
#             except ValueError as e:
#                 return Response({'status': 0, 'message': _('Invalid date format.')}, status=status.HTTP_400_BAD_REQUEST)

#             current_date = training_date_obj
#             while current_date <= end_date_obj:
#                 weekday = current_date.weekday()
#                 custom_weekday = weekday_mapping.get(weekday)
#                 if custom_weekday in days:
#                     day_index = days.index(custom_weekday)
#                     training_instance = Training.objects.create(
#                         training_name=training_name,
#                         training_photo=training_photo,
#                         training_date=current_date,
#                         start_time=start_time_objs[day_index],
#                         end_time=end_time_objs[day_index],
#                         training_duration=durations[day_index],
#                         creator_type=creator_type,
#                         created_by_id=created_by_id,
#                         country=country,
#                         city=city,
#                         gender=gender,
#                         field=field,
#                         no_of_participants=no_of_participants,
#                         description=description,
#                         cost=cost,
#                         training_type=training_type,
#                     )
#                     training_instances.append(training_instance)
#                 current_date += timedelta(days=1)

#         # Serialize the training instances
#         serialized_trainings = TrainingSerializer(training_instances, many=True, context={'request': request})

#         # Create the corresponding Training_Joined instances for each training
#         for training_instance in training_instances:
#             if creator_type == Training.USER_TYPE:
#                 Training_Joined.objects.create(
#                     training=training_instance,
#                     user=request.user,
#                     attendance_status=False
#                 )
#             elif creator_type == Training.TEAM_TYPE:  # Team creator type
#                 try:
#                     team = Team.objects.get(id=created_by_id)
#                     team_founder = team.team_founder
#                     if team_founder:
#                         Training_Joined.objects.create(
#                             training=training_instance,
#                             user=team_founder,
#                             attendance_status=False
#                         )
#                 except Team.DoesNotExist:
#                     return Response({
#                         'status': 0,
#                         'message': _('No team found with the provided ID.')
#                     }, status=status.HTTP_404_NOT_FOUND)

#         if len(training_instances) > 0:
#             return Response({
#                 'status': 1,
#                 'message': _('Training successfully created'),
#                 'data': serialized_trainings.data  # Return the serialized data
#             }, status=status.HTTP_200_OK)
#         else:
#             return Response({
#                 'status': 0,
#                 'message': _('No training instances were created.')
#             }, status=status.HTTP_400_BAD_REQUEST)

####################### Craete Training API VIEW WITH OBJECTS ########################################
# class CreateTrainingView(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = (JSONParser, MultiPartParser, FormParser)

#     def post(self, request, *args, **kwargs):
#         language = request.headers.get('Language', 'en')
#         if language in ['en', 'ar']:
#             activate(language)

#         try:
#             creator_type = int(request.data.get('creator_type'))
#             created_by_id = int(request.data.get('created_by_id'))
#         except (ValueError, TypeError):
#             return Response({
#                 'status': 0,
#                 'message': _('Invalid creator_type or created_by_id.')
#             }, status=status.HTTP_400_BAD_REQUEST)

#         # Validate and fetch related objects
#         try:
#             country = Country.objects.get(id=int(request.data.get('country', 0)))
#             city = City.objects.get(id=int(request.data.get('city', 0)))
#             gender = UserGender.objects.get(id=int(request.data.get('gender', 0)))
#             field = Field.objects.get(id=int(request.data.get('field', 0)))
#         except ObjectDoesNotExist:
#             return Response({
#                 'status': 0,
#                 'message': _('Invalid country, city, gender, or field provided.')
#             }, status=status.HTTP_400_BAD_REQUEST)

#         training_photo = None
#         if "training_photo" in request.FILES:
#             image = request.FILES["training_photo"]
#             unique_suffix = get_random_string(8)
#             file_name = f"training_photo/{request.user.id}_{unique_suffix}.{image.name.split('.')[-1]}"
#             training_photo = default_storage.save(file_name, image)

#         try:
#             training_date = datetime.strptime(request.data.get('training_date'), "%Y-%m-%d").date()
#             end_date = datetime.strptime(request.data.get('end_date', ""), "%Y-%m-%d").date() if request.data.get('end_date') else None
#         except ValueError:
#             return Response({'status': 0, 'message': _('Invalid training_date or end_date format.')}, status=status.HTTP_400_BAD_REQUEST)

#         repeat_type = int(request.data.get('repeat_type', 2))
#         no_of_participants = int(request.data.get('no_of_participants', 0))
#         training_name = request.data.get('training_name', '')
#         description = request.data.get('description', '')
#         cost = request.data.get('cost', '')
#         training_type = int(request.data.get('training_type', 1))  # Default: Open training

#         # Parse `days` schedule
#         day_schedules = request.data.get('days', [])
#         parsed_days = []
#         if not isinstance(day_schedules, list):
#             return Response({'status': 0, 'message': _('Days must be a list of schedules.')}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             for entry in day_schedules:
#                 day = int(entry.get('day'))
#                 start_time = datetime.strptime(entry.get('start_time'), "%H:%M:%S").time()
#                 end_time = datetime.strptime(entry.get('end_time'), "%H:%M:%S").time()
#                 duration = (datetime.combine(datetime.today(), end_time) -
#                             datetime.combine(datetime.today(), start_time)).seconds // 60
#                 parsed_days.append({"day": day, "start_time": start_time, "end_time": end_time, "duration": duration})
#         except (ValueError, KeyError, TypeError):
#             return Response({'status': 0, 'message': _('Invalid format for days schedule.')}, status=status.HTTP_400_BAD_REQUEST)

#         # Map weekday mapping (Monday = 0 to Sunday = 6)
#         weekday_mapping = {
#             0: 2, 1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 1
#         }

#         training_instances = []

#         if repeat_type == 2:  # Single training session
#             try:
#                 start_time = datetime.strptime(request.data.get('start_time'), "%H:%M:%S").time()
#                 end_time = datetime.strptime(request.data.get('end_time'), "%H:%M:%S").time()
#                 duration = (datetime.combine(datetime.today(), end_time) -
#                             datetime.combine(datetime.today(), start_time)).seconds // 60
#                 training_instance = Training.objects.create(
#                     training_name=training_name,
#                     training_photo=training_photo,
#                     training_date=training_date,
#                     start_time=start_time,
#                     end_time=end_time,
#                     training_duration=duration,
#                     creator_type=creator_type,
#                     created_by_id=created_by_id,
#                     country=country,
#                     city=city,
#                     gender=gender,
#                     field=field,
#                     no_of_participants=no_of_participants,
#                     description=description,
#                     cost=cost,
#                     training_type=training_type,
#                 )
#                 training_instances.append(training_instance)
#             except ValueError:
#                 return Response({'status': 0, 'message': _('Invalid time format.')}, status=status.HTTP_400_BAD_REQUEST)   

#         elif repeat_type == 1 and end_date:
#             current_date = training_date
#             while current_date <= end_date:
#                 weekday = current_date.weekday()
#                 mapped_weekday = weekday_mapping[weekday]  # Use the mapped weekday
#                 for entry in parsed_days:
#                     if mapped_weekday == entry["day"]:
#                         training_instance = Training.objects.create(
#                             training_name=training_name,
#                             training_photo=training_photo,
#                             training_date=current_date,
#                             start_time=entry["start_time"],
#                             end_time=entry["end_time"],
#                             training_duration=entry["duration"],
#                             creator_type=creator_type,
#                             created_by_id=created_by_id,
#                             country=country,
#                             city=city,
#                             gender=gender,
#                             field=field,
#                             no_of_participants=no_of_participants,
#                             description=description,
#                             cost=cost,
#                             training_type=training_type,
#                         )
#                         training_instances.append(training_instance)
#                 current_date += timedelta(days=1)

#         serialized_trainings = TrainingSerializer(training_instances, many=True, context={'request': request})
#         for training_instance in training_instances:
#             if creator_type == Training.USER_TYPE:
#                 Training_Joined.objects.create(
#                     training=training_instance,
#                     user=request.user,
#                     attendance_status=False
#                 )
#             elif creator_type == Training.TEAM_TYPE:  # Team creator type
#                 try:
#                     team = Team.objects.get(id=created_by_id)
#                     team_founder = team.team_founder
#                     if team_founder:
#                         Training_Joined.objects.create(
#                             training=training_instance,
#                             user=team_founder,
#                             attendance_status=False
#                         )
#                 except Team.DoesNotExist:
#                     return Response({
#                         'status': 0,
#                         'message': _('No team found with the provided ID.')
#                     }, status=status.HTTP_404_NOT_FOUND)
#         return Response({
#             'status': 1,
#             'message': _('Training successfully created'),
#             'data': serialized_trainings.data
#         }, status=status.HTTP_200_OK) if training_instances else Response({
#             'status': 0,
#             'message': _('No training instances were created.')
#         }, status=status.HTTP_400_BAD_REQUEST)


############################ Craete Training Main Working IN IOS With Object ############
class CreateTrainingView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        try:
            creator_type = int(request.data.get('creator_type'))
            created_by_id = int(request.data.get('created_by_id'))
        except (ValueError, TypeError):
            return Response({
                'status': 0,
                'message': _('Invalid creator_type or created_by_id.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate and fetch related objects
        try:
            country = Country.objects.get(id=int(request.data.get('country', 0)))
            city = City.objects.get(id=int(request.data.get('city', 0)))
            gender = UserGender.objects.get(id=int(request.data.get('gender', 0)))
            field = Field.objects.get(id=int(request.data.get('field', 0)))
        except ObjectDoesNotExist:
            return Response({
                'status': 0,
                'message': _('Invalid country, city, gender, or field provided.')
            }, status=status.HTTP_400_BAD_REQUEST)

        training_photo = None
        if "training_photo" in request.FILES:
            image = request.FILES["training_photo"]
            unique_suffix = get_random_string(8)
            file_name = f"training_photo/{request.user.id}_{unique_suffix}.{image.name.split('.')[-1]}"
            training_photo = default_storage.save(file_name, image)

        try:
            training_date = datetime.strptime(request.data.get('training_date'), "%Y-%m-%d").date()
            end_date = datetime.strptime(request.data.get('end_date', ""), "%Y-%m-%d").date() if request.data.get('end_date') else None
        except ValueError:
            return Response({'status': 0, 'message': _('Invalid training_date or end_date format.')}, status=status.HTTP_400_BAD_REQUEST)

        repeat_type = int(request.data.get('repeat_type', 2))
        no_of_participants = int(request.data.get('no_of_participants', 0))
        training_name = request.data.get('training_name', '')
        description = request.data.get('description', '')
        cost = request.data.get('cost', '')
        training_type = int(request.data.get('training_type', 1))  # Default: Open training

        # Parse `days` schedule from the string to JSON object (list of dicts)
        try:
            day_schedules = json.loads(request.data.get('days', '[]'))
        except json.JSONDecodeError:
            return Response({'status': 0, 'message': _('Invalid format for days schedule.')}, status=status.HTTP_400_BAD_REQUEST)

        parsed_days = []
        if not isinstance(day_schedules, list):
            return Response({'status': 0, 'message': _('Days must be a list of schedules.')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            for entry in day_schedules:
                day = int(entry.get('day'))
                start_time = datetime.strptime(entry.get('start_time'), "%H:%M:%S").time()
                end_time = datetime.strptime(entry.get('end_time'), "%H:%M:%S").time()
                duration = (datetime.combine(datetime.today(), end_time) - 
                            datetime.combine(datetime.today(), start_time)).seconds // 60
                parsed_days.append({"day": day, "start_time": start_time, "end_time": end_time, "duration": duration})
        except (ValueError, KeyError, TypeError):
            return Response({'status': 0, 'message': _('Invalid format for days schedule.')}, status=status.HTTP_400_BAD_REQUEST)

        # Map weekday mapping (Monday = 0 to Sunday = 6)
        weekday_mapping = {
            0: 2, 1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 1
        }

        training_instances = []

        if repeat_type == 2:  # Single training session
            try:
                start_time = datetime.strptime(request.data.get('start_time'), "%H:%M:%S").time()
                end_time = datetime.strptime(request.data.get('end_time'), "%H:%M:%S").time()
                duration = (datetime.combine(datetime.today(), end_time) - 
                            datetime.combine(datetime.today(), start_time)).seconds // 60
                training_instance = Training.objects.create(
                    training_name=training_name,
                    training_photo=training_photo,
                    training_date=training_date,
                    start_time=start_time,
                    end_time=end_time,
                    training_duration=duration,
                    creator_type=creator_type,
                    created_by_id=created_by_id,
                    country=country,
                    city=city,
                    gender=gender,
                    field=field,
                    no_of_participants=no_of_participants,
                    description=description,
                    cost=cost,
                    training_type=training_type,
                )
                training_instances.append(training_instance)
            except ValueError:
                return Response({'status': 0, 'message': _('Invalid time format.')}, status=status.HTTP_400_BAD_REQUEST)   

        elif repeat_type == 1 and end_date:
            current_date = training_date
            while current_date <= end_date:
                weekday = current_date.weekday()
                mapped_weekday = weekday_mapping[weekday]  # Use the mapped weekday
                for entry in parsed_days:
                    if mapped_weekday == entry["day"]:
                        training_instance = Training.objects.create(
                            training_name=training_name,
                            training_photo=training_photo,
                            training_date=current_date,
                            start_time=entry["start_time"],
                            end_time=entry["end_time"],
                            training_duration=entry["duration"],
                            creator_type=creator_type,
                            created_by_id=created_by_id,
                            country=country,
                            city=city,
                            gender=gender,
                            field=field,
                            no_of_participants=no_of_participants,
                            description=description,
                            cost=cost,
                            training_type=training_type,
                        )
                        training_instances.append(training_instance)
                current_date += timedelta(days=1)

        serialized_trainings = TrainingSerializer(training_instances, many=True, context={'request': request})
        self.handle_training_notifications(training_instances, training_name)

        for training_instance in training_instances:
            if creator_type == Training.USER_TYPE:
                Training_Joined.objects.create(
                    training=training_instance,
                    user=request.user,
                    attendance_status=False
                )
            elif creator_type == Training.TEAM_TYPE:  # Team creator type
                try:
                    team = Team.objects.get(id=created_by_id)
                    team_founder = team.team_founder
                    if team_founder:
                        Training_Joined.objects.create(
                            training=training_instance,
                            user=team_founder,
                            attendance_status=False
                        )
                except Team.DoesNotExist:
                    return Response({
                        'status': 0,
                        'message': _('No team found with the provided ID.')
                    }, status=status.HTTP_404_NOT_FOUND)       
        return Response({
            'status': 1,
            'message': _('Training successfully created'),
            'data': serialized_trainings.data
        }, status=status.HTTP_200_OK) if training_instances else Response({
            'status': 0,
            'message': _('No training instances were created.')
        }, status=status.HTTP_400_BAD_REQUEST)
    

      

    def handle_training_notifications(self, training_instances, training_name):
        for training_instance in training_instances:
            message = f"New training session: {training_name} on {training_instance.training_date}"
            push_data = {"training_id": training_instance.id, "type": "training"}
            self.notify_users(training_instance, message, push_data)


             
    def notify_users(self, training, message, push_data):
        # Define the relevant roles for sending notifications (Player, Coach, Manager)
        target_roles = [4, 1, 2]  # Player, Coach, Manager roles

        # Handle notifications when the creator_type is 1 (individual user)
        if training.creator_type == 1:
            user = User.objects.get(id=training.created_by_id)
            
            # Get all branches associated with the user
            user_branches = JoinBranch.objects.filter(
                user_id=user.id
            ).values_list('branch_id', flat=True)

            # Iterate over each branch and notify relevant users
            for branch_id in user_branches:
                # Query the users who belong to the branch and have relevant roles
                relevant_users = JoinBranch.objects.filter(
                    branch_id=branch_id,
                    joinning_type__in=target_roles
                ).select_related('user_id')
                print(relevant_users)

                for join_branch in relevant_users:
                    user = join_branch.user_id
                    print(user)
                    self.send_notification(user, message, push_data)

        # Handle notifications when the creator_type is 2 (team or branch)
        elif training.creator_type == 2:
            # Get the branch associated with the team or creator
            team_branch = JoinBranch.objects.filter(branch_id=training.created_by_id).first()
            
            if team_branch:
                # Query the users who belong to the branch and have relevant roles
                relevant_users = JoinBranch.objects.filter(
                    branch_id=team_branch.branch_id,
                    joinning_type__in=target_roles
                ).select_related('user')

                for join_branch in relevant_users:
                    user = join_branch.user
                    self.send_notification(user, message, push_data)

           
        


    def send_notification(self, user, message, push_data):
        notification_language = user.current_language
        if notification_language in ['ar', 'en']:
            activate(notification_language)

        send_push_notification(
            user.device_token,
            _("Training Notification"),
            message,
            device_type=user.device_type,
            data=push_data
        )
        Notifictions.objects.create(
            created_by_id=1,  # Assumed system admin ID
            creator_type=1,
            targeted_id=user.id,
            targeted_type=1,
            title=_("Training Notification"),
            content=message
        )
                
            
    





    ##################


# class CreateTrainingView(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = [MultiPartParser, FormParser]

#     def post(self, request, *args, **kwargs):
#         language = request.headers.get('Language', 'en')

#         if language in ['en', 'ar']:
#             activate(language)

#         creator_type = request.data.get('creator_type', None)
#         created_by_id = request.data.get('created_by_id', None)

#         creator_type = int(creator_type)
#         created_by_id = int(created_by_id)

#         context = {'request': request}
#         serializer = TrainingSerializer(data=request.data, context=context)


#         if serializer.is_valid():


#             # Handle image saving logic if training photo is uploaded
#             if "training_photo" in request.FILES:
#                 image = request.FILES["training_photo"]
#                 file_extension = image.name.split('.')[-1]
#                 unique_suffix = get_random_string(8)
#                 file_name = f"training_photo/{request.user.id}_{unique_suffix}.{file_extension}"
#                 image_path = default_storage.save(file_name, image)
#                 serializer.validated_data['training_photo'] = image_path
#             training_instance = serializer.save()

#             if creator_type == 1:  # User
#                 Training_Joined.objects.create(
#                     training=training_instance,
#                     user=request.user,
#                     attendance_status=False  # Default attendance status
#                 )
#             elif creator_type == 2:  # Team
#                 try:
#                     team = Team.objects.get(id=created_by_id)
#                     team_founder = team.team_founder
#                     if team_founder:
#                         Training_Joined.objects.create(
#                             training=training_instance,
#                             user=team_founder,
#                             attendance_status=False
#                         )
#                 except Team.DoesNotExist:
#                     return Response({
#                         'status': 0,
#                         'message': _('No team found with the provided ID.')
#                     }, status=status.HTTP_404_NOT_FOUND)

#             training_instance = Training.objects.get(id=training_instance.id)
#             serializer = TrainingSerializer(training_instance, context={'request': request})
#             return Response({
#                 'status': 1,
#                 'message': _('Training successfully created'),
#                 'data': serializer.data  # Use the re-serialized data with language context
#             }, status=status.HTTP_201_CREATED)
#         return Response({
#             'status': 0,
#             'errors': serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)




##################### Get trainings Details ##################################
class TrainingDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Fetch the training using the training_id from the query parameters
        training_id = request.query_params.get('training_id')

        if not training_id:
            return Response({
                'status': 0,
                'message': _('Training ID is required.'),
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the training object using the provided tournament_id
            training = Training.objects.get(id=training_id)
            
            # Serialize the training data
            serializer = TrainingSerializer(training, context={'request': request})

            # Format the response as required
            return Response({
                'status': 1,
                'message': _('Training details fetched successfully.'),
                'data':  serializer.data,
               
            }, status=status.HTTP_200_OK)

        except Training.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Training not found.'),
            }, status=status.HTTP_404_NOT_FOUND)

###################### Edit Training Detail ############################
    def get_object(self, training_id):
            try:
                # Retrieve the training instance by ID
                return Training.objects.get(id=training_id)
            except Training.DoesNotExist:
                return None
            
            
    def patch(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Retrieve the training ID from the request data (in request.data)
        training_id = request.data.get('training_id')
        created_by_id = int(request.data.get('created_by_id'))
        creator_type = int(request.data.get('creator_type', None))

        if not training_id:
            return Response({
                'status': 0,
                'message': _('Training ID is required for update'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the training instance to update
        training_instance = self.get_object(training_id)

        if not training_instance:
            return Response({
                'status': 0,
                'message': _('Training not found'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)
        
        if training_instance.created_by_id != created_by_id or training_instance.creator_type != creator_type:
            return Response({
                'status': 0,
                'message': _('Unauthorized to update this training'),
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        # Pass the full 'request' object in the context
        context = {'request': request}

        # Initialize the serializer with the current instance and the updated data
        serializer = TrainingSerializer(training_instance, data=request.data, partial=True, context=context)

        if serializer.is_valid():
            # Handle image saving logic if a new training photo is uploaded
            if "training_photo" in request.FILES:
                image = request.FILES["training_photo"]
                file_extension = image.name.split('.')[-1]
                unique_suffix = get_random_string(8)
                file_name = f"training_photo/{request.user.id}_{unique_suffix}.{file_extension}"

                # Save the image using the default storage
                image_path = default_storage.save(file_name, image)
                serializer.validated_data['training_photo'] = image_path

            # Save the updated training instance
            updated_training_instance = serializer.save()

            # Re-fetch the training instance with the correct context for language handling
            updated_training_instance = Training.objects.get(id=updated_training_instance.id)

            # Re-serialize the updated training instance
            serializer = TrainingSerializer(updated_training_instance, context={'request': request})

            # Return the successfully updated training data
            return Response({
                'status': 1,
                'message': _('Training successfully updated'),
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        # If validation fails, return the errors
        return Response({
            'status': 0,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

###################### Delete Training ############################
    def delete(self, request, *args, **kwargs):
        # Retrieve the training ID from the query parameters
        training_id = request.query_params.get('training_id')
        created_by_id = int(request.query_params.get('created_by_id'))
        creator_type = int(request.query_params.get('creator_type', None))

        if not training_id:
            return Response({
                'status': 0,
                'message': _('Training ID is required for deletion'),
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the training instance to delete
        training_instance = self.get_object(training_id)

        if not training_instance:
            return Response({
                'status': 0,
                'message': _('Training not found'),
            }, status=status.HTTP_404_NOT_FOUND)
        
        if training_instance.created_by_id != created_by_id or training_instance.creator_type != creator_type:
            return Response({
                'status': 0,
                'message': _('Unauthorized to Delete this training'),
            }, status=status.HTTP_404_NOT_FOUND)

        # Delete the training instance
        training_instance.delete()

        # Return a success response
        return Response({
            'status': 1,
            'message': _('Training successfully deleted'),
        }, status=status.HTTP_200_OK) 

###################### Training LIKE ##################################
class TrainingLikeAPIView(APIView):
    parser_classes=[MultiPartParser, FormParser,JSONParser]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        training_id = request.data.get('training_id')

        if not training_id:
            return Response({
                'status': 0,
                'message': _('Training ID is required.')
            }, status=400)

        try:
            training = Training.objects.get(id=training_id)
        except Training.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Training not found.')
            }, status=404)

        # Toggle like/unlike
        creator_type = request.data.get('creator_type')
        created_by_id = request.data.get('created_by_id', request.user.id)  # Default to logged-in user ID

        training_like, created = TrainingLike.objects.get_or_create(created_by_id=created_by_id, training=training, creator_type=creator_type)
        
        if not created:
            # If the user already liked the Training, unlike it (delete the like)
            training_like.delete()
            message = _('Training unliked successfully.')
        else:
            message = _('Training liked successfully.')

        # Serialize the Training data with comments set to empty
        serializer = TrainingSerializer(training, context={'request': request})
        
        # Return the full Training data with an empty comment list
        return Response({
            'status': 1,
            'message': message,
            'data': serializer.data
        }, status=200)
    

################################## Pagination ##############################
class CustomTrainingPagination(PageNumberPagination):
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    page_size = 10  # Number of records per page
    page_query_param = 'page'  # Custom page number param in the body
    page_size_query_param = 'page_size'
    max_page_size = 100  # Set max size if needed

    def paginate_queryset(self, queryset, request, view=None):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
        # Get the page number from the body (default: 1)
        try:
            # Try to fetch and validate the page number
            page_number = request.data.get(self.page_query_param, 1)
            self.page = int(page_number)
            if self.page < 1:
                raise ValidationError(_("Page number must be a positive integer."))
        except (ValueError, TypeError):
            # If the page number is invalid, return a custom error response
            return Response({
                'status': 0,
                'message': _('Page Not Found'),
                'data': []
            }, status=400)

        # Get total number of pages based on the queryset
        paginator = self.django_paginator_class(queryset, self.get_page_size(request))
        total_pages = paginator.num_pages

        # Check if the requested page number is out of range
        if self.page > total_pages:
            # Return custom response for an invalid page
            return Response({
                'status': 0,
                'message': _('Page Not Found'),
                'data': []
            }, status=400)

        # Perform standard pagination if the page is valid
        return super().paginate_queryset(queryset, request, view)
    
################################ Get comment API #############################
class TrainingCommentPagination(CustomTrainingPagination):
    def paginate_queryset(self, queryset, request, view=None):
        return super().paginate_queryset(queryset, request, view)

class TrainingCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Validate training_id from request data
        training_id = request.data.get('training_id')
        training_id = int(training_id)
        if not training_id:
            return Response({
                'status': 0,
                'message': _('Training ID is required.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            training = Training.objects.get(id=training_id)
        except Training.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Training not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Get only top-level comments (parent=None) for the post
        top_level_comments = Training_comment.objects.filter(training=training, parent=None).order_by('-date_created')

        # Paginate the comments
        paginator = TrainingCommentPagination()
        paginated_comments = paginator.paginate_queryset(top_level_comments, request)

        # If pagination fails or no comments are found
        if paginated_comments is None:
            return Response({
                'status': 1,
                'message': _('No comments found for this Training.'),
                'data': {
                    'total_records': 0,
                    'total_pages': 0,
                    'current_page': 1,
                    'results': []
                }
            }, status=status.HTTP_200_OK)

        # Serialize the paginated comments
        serializer = TrainingCommentSerializer(paginated_comments, many=True, context={'request': request})

        # Return paginated response
        return Response({
            'status': 1,
            'message': _('Comments fetched successfully.'),
            'data': serializer.data,
            'total_records': top_level_comments.count(),
            'total_pages': paginator.page.paginator.num_pages,
            'current_page': paginator.page.number,
        }, status=status.HTTP_200_OK)



######################## COMMNET CREATE API ###########################
class TrainingCommentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        data = request.data
        training_id = data.get('training_id')
        comment_text = data.get('comment')
        parent_id = data.get('parent_id')
        created_by_id = data.get('created_by_id')
        creator_type = data.get('creator_type')

        # Validate the required fields
        if not training_id or not comment_text or not created_by_id or not creator_type:
            return Response({
                'status': 0,
                'message': _('training_id, comment, created_by_id and creator_type are required.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate training_id from request data
        training_id = request.data.get('training_id')
        training_id = int(training_id)

        try:
            training_id = Training.objects.get(id=training_id)
        except Training.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Training not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate parent comment if provided
        parent_comment = None
        if parent_id:
            try:
                parent_comment = Training_comment.objects.get(id=parent_id)
            except Training_comment.DoesNotExist:
                return Response({
                    'status': 0,
                    'message': _('Parent comment not found.')
                }, status=status.HTTP_404_NOT_FOUND)

        # Create the comment using the new fields
        comment = Training_comment.objects.create(
            created_by_id=created_by_id,
            creator_type=creator_type,
            training=training_id,
            comment=comment_text,
            parent=parent_comment
        )

        return Response({
            'status': 1,
            'message': _('Comment created successfully.'),
            'data': TrainingCommentSerializer(comment).data
        }, status=status.HTTP_201_CREATED)



#### VIEW TO RETRIEVE ALL OPEN TRAININGS FOR THE USER  ####
class OpenTrainingListView(APIView):
    def get(self, request, *args, **kwargs):
        # Get today's date
        today = date.today()

        # Get the type of training (whether to show past or upcoming)
        date_type = request.query_params.get('date_type', 0)  # Default to upcoming (0)

        # Validate date_type value
        try:
            date_type = int(date_type)
        except ValueError:
            return Response({
                'status': 0,
                'message': _('Invalid date_type value. It must be an integer.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Filter open training sessions based on the date_type
        if date_type == 0:  # Upcoming or ongoing open training sessions
            open_trainings = Training.objects.filter(
                training_type=1,
                training_date__gte=today  # Only future or today
            ).order_by('training_date')
        elif date_type == 1:  # Past open training sessions
            open_trainings = Training.objects.filter(
                training_type=1,
                training_date__lt=today  # Only past trainings
            ).order_by('-training_date')
        else:
            return Response({
                'status': 0,
                'message': _('Invalid date_type value. Allowed values are 0 or 1.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get creator type and created_by_id from query parameters
        creator_type = request.query_params.get('creator_type')
        created_by_id = request.query_params.get('created_by_id')

        # Get notification count for the user
        notification_count = Notifictions.objects.filter(
            targeted_id=created_by_id, 
            targeted_type=creator_type,
            read=False
        ).count()

        # Initialize custom pagination
        paginator = CustomTrainingPagination()

        # Paginate the queryset
        paginated_trainings = paginator.paginate_queryset(open_trainings, request)
        if paginated_trainings is not None:
            # Serialize the paginated data
            serializer = TrainingListSerializer(paginated_trainings, many=True, context={'request': request})

        

            # Return paginated data in the response, with the serialized data directly under 'data'
            return Response({
                'status': 1,
                'message': "Open trainings retrieved successfully",
                'total_records': open_trainings.count(),
                'total_pages': paginator.page.paginator.num_pages,
                'current_page': paginator.page.number,
                'data': serializer.data,
                'notification_count': notification_count  # Include the notification count in the response
            }, status=status.HTTP_200_OK)

        # If pagination is not applied, just return the serialized data
        serializer = TrainingListSerializer(open_trainings, many=True, context={'request': request})
        return Response({
            'status': 1,
            'message': "Open trainings retrieved successfully",
            'total_records': open_trainings.count(),
            'total_pages': 1,
            'current_page': 1,
            'data':  serializer.data,
            'notification_count': notification_count  # Include the notification count in the response
        }, status=status.HTTP_200_OK)
    


###### My Created Training List API ######
class MyTrainingsView(APIView):
    def get(self, request, *args, **kwargs):
        # Retrieve the logged-in user ID
        user = request.user.id

        # Get today's date
        today = date.today()

        # Get the date_type from query parameters (0 for upcoming, 1 for past)
        date_type = request.query_params.get('date_type', 0)  # Default to upcoming (0)

        # Validate date_type value
        try:
            date_type = int(date_type)
        except ValueError:
            return Response({
                'status': 0,
                'message': _('Invalid date_type value. It must be an integer.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve all trainings initially
        trainings = Training.objects.all()

        # Filter trainings based on the date_type
        if date_type == 0:  # Upcoming or ongoing trainings
            # Get upcoming trainings from today onwards, order by training_date
            trainings = trainings.filter(training_date__gte=today).order_by('training_date')
        elif date_type == 1:  # Past trainings
            # Get past trainings, order by training_date in reverse (from recent to past)
            trainings = trainings.filter(training_date__lt=today).order_by('-training_date')
        else:
            return Response({
                'status': 0,
                'message': _('Invalid date_type value. Allowed values are 0 or 1.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Filter trainings based on access logic
        accessible_trainings = []
        for training in trainings:
            if self._has_access(training, user):
                accessible_trainings.append(training)

        # Sort the trainings by `training_date` as per the required order
        if date_type == 0:
            accessible_trainings = sorted(accessible_trainings, key=lambda t: t.training_date)
        else:
            accessible_trainings = sorted(accessible_trainings, key=lambda t: t.training_date, reverse=True)

        # Apply custom pagination
        paginator = CustomTrainingPagination()

        # Paginate the accessible trainings
        paginated_trainings = paginator.paginate_queryset(accessible_trainings, request)
        if paginated_trainings is not None:
            # Serialize the paginated data
            serializer = TrainingListSerializer(paginated_trainings, many=True, context={'request': request})

            # Return paginated response with metadata
            return Response({
                'status': 1,
                'message': 'Trainings retrieved successfully',
                'total_records': len(accessible_trainings),
                'total_pages': paginator.page.paginator.num_pages,
                'current_page': paginator.page.number,
                'data': serializer.data,
            }, status=status.HTTP_200_OK)

        # If pagination is not applied, return all serialized data
        serializer = TrainingListSerializer(accessible_trainings, many=True, context={'request': request})
        return Response({
            'status': 1,
            'message': 'Trainings retrieved successfully',
            'total_records': len(accessible_trainings),
            'total_pages': 1,
            'current_page': 1,
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
    
    def _has_access(self, training, user):

        # Case 1: Creator type is USER_TYPE
        if training.creator_type == 1:
            if training.created_by_id == user:  # Request user is the creator
                return True

            # Check if the request user is in the same branch as the creator
            creator_branches = JoinBranch.objects.filter(
                user_id=training.created_by_id,
                joinning_type=4
            ).values_list('branch_id', flat=True)

            user_branch = JoinBranch.objects.filter(
                user_id=user
            ).values_list('branch_id', flat=True)

            if not creator_branches:
                return False

            request_user_branches = JoinBranch.objects.filter(
                user_id=user,
                branch_id__in=creator_branches,
                joinning_type__in=[1, 3]
            )

            if not request_user_branches.exists():
                return False

            return True

        # Case 2: Creator type is TEAM_TYPE
        elif training.creator_type == 2:
            team = get_object_or_404(Team, id=training.created_by_id)
            if team.team_founder_id == user:  # Request user is the team's founder
                return True

        # Default: No access
        return False
    
############ My Joined Training List API #################
class MyJoinedTrainingsView(APIView):
    def get(self, request, *args, **kwargs):
        # Get the current authenticated user
        user = request.user

        # Get today's date
        today = date.today()

        # Get the date_type from query parameters (0 for upcoming, 1 for past)
        date_type = request.query_params.get('date_type', 0)  # Default to upcoming (0)

        # Validate date_type value
        try:
            date_type = int(date_type)
        except ValueError:
            return Response({
                'status': 0,
                'message': _('Invalid date_type value. It must be an integer.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch all the trainings the user has joined and order by training_date (newest first)
        joined_trainings = Training_Joined.objects.filter(user=user).select_related('training')

        # Filter the trainings based on the date_type
        if date_type == 0:  # Upcoming or ongoing trainings
            joined_trainings = joined_trainings.filter(training__training_date__gte=today)  # Only future or today
        elif date_type == 1:  # Past trainings
            joined_trainings = joined_trainings.filter(training__training_date__lt=today)  # Only past trainings
        else:
            return Response({
                'status': 0,
                'message': _('Invalid date_type value. Allowed values are 0 or 1.')
            }, status=status.HTTP_400_BAD_REQUEST)

        # If the user has not joined any training, return a message
        if not joined_trainings.exists():
            return Response({
                'status': 0,
                'message': 'No joined trainings found',
                'data': []
            }, status=status.HTTP_200_OK)

        # Get the training sessions by joining the Training model
        trainings = [entry.training for entry in joined_trainings]

        # Sort the trainings by `training_date` as per the required order
        if date_type == 0:  # Upcoming
            trainings = sorted(trainings, key=lambda x: x.training_date)  # Sort from earliest to latest
        else:  # Past
            trainings = sorted(trainings, key=lambda x: x.training_date, reverse=True)  # Sort from latest to earliest

        # Initialize custom pagination
        paginator = CustomTrainingPagination()

        # Paginate the queryset
        paginated_trainings = paginator.paginate_queryset(trainings, request)
        if paginated_trainings is not None:
            # Serialize the paginated data
            serializer = TrainingListSerializer(paginated_trainings, many=True, context={'request': request})

            # Return paginated data in the response
            return Response({
                'status': 1,
                'message': 'Joined trainings retrieved successfully',
                'total_records': len(trainings),
                'total_pages': paginator.page.paginator.num_pages,
                'current_page': paginator.page.number,
                'data': serializer.data  
            }, status=status.HTTP_200_OK)

        # If pagination is not applied, just return the serialized data
        serializer = TrainingListSerializer(trainings, many=True, context={'request': request})
        return Response({
            'status': 1,
            'message': 'Joined trainings retrieved successfully',
            'total_records': len(trainings),
            'total_pages': 1,
            'current_page': 1,
            'data': serializer.data  # Directly place the data in 'data'
        }, status=status.HTTP_200_OK)

############################## Join Training API ##############################

class JoinTrainingAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def _has_access(self, training, user):
      

        # Case 1: Creator type is USER_TYPE
        if training.creator_type == 1:
            if training.created_by_id == user:  # Request user is the creator'
                return True

            # Check if the request user is in the same branch as the creator
            creator_branches = JoinBranch.objects.filter(
                user_id=training.created_by_id,
                joinning_type=4
            ).values_list('branch_id', flat=True)

            user_branch = JoinBranch.objects.filter(
                user_id=user,
                # joinning_type=4
            ).values_list('branch_id', flat=True)

            if not creator_branches:
                return False

            request_user_branches = JoinBranch.objects.filter(
                user_id=user,
                branch_id__in=creator_branches,
                joinning_type__in=[1, 3]
            )

            if not request_user_branches.exists():
                return False

            return True


        # Case 2: Creator type is TEAM_TYPE
        elif training.creator_type == 2:
            team = get_object_or_404(Team, id=training.created_by_id)
            if team.team_founder_id == user:  # Request user is the team's founder
                return True

        # Default: No access
        return False
    
####################### Create a new training membership for the user ################################
    def post(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Validate training_id
        training_id = request.data.get('training_id')
        if not training_id:
            return Response({'status': 0, 'message': _('Training ID is required.')}, status=status.HTTP_400_BAD_REQUEST)

        # Validate user existence
        user = request.user
        if not user:
            return Response({'status': 0, 'message': _('User not found.')}, status=status.HTTP_404_NOT_FOUND)

        if not user.gender:
            return Response({'status': 0, 'message': _('Please add your gender first.')}, status=status.HTTP_400_BAD_REQUEST)

        # Validate training existence
        try:
            training = Training.objects.get(id=training_id)
        except Training.DoesNotExist:
            return Response({'status': 0, 'message': _('Training not found.')}, status=status.HTTP_404_NOT_FOUND)

        # Check closed training restriction
        if training.training_type == Training.CLOSED_TRAINING:
            if not hasattr(user, 'role') or user.role.id != 2:
                return Response({'status': 0, 'message': _('Only Players can join closed training.')}, status=status.HTTP_403_FORBIDDEN)

        # Ensure user is not already a member
        if Training_Joined.objects.filter(user=user, training=training).exists():
            return Response({'status': 0, 'message': _('User is already a member of the training.')}, status=status.HTTP_400_BAD_REQUEST)

        # Create training membership
        membership = Training_Joined.objects.create(user=user, training=training)

        # Notify relevant users
        notifications_sent = self.notify_relevant_users(training, user)

        serializer = TrainingMembershipSerializer(membership)
        return Response({
            'status': 1,
            'message': _('User joined the training successfully.'),
            'data': serializer.data,
            'notifications_sent': notifications_sent
        }, status=status.HTTP_201_CREATED)

    def notify_relevant_users(self, training, user):
        """
        Notify relevant users: creator, branch managers, coaches.
        """
        message = _("A new player has joined the training.")
        comments_message = _("Don't forget to engage with the new player.")
        push_data = {
            "training_id": training.id,
          
            "type":"training"
        }

        notifications_sent = 0

        if training.creator_type == Training.USER_TYPE:
            creator_branches = JoinBranch.objects.filter(
                user_id=training.created_by_id, joinning_type=4
            ).values_list('branch_id', flat=True)          

            if creator_branches.exists():
                branch_managers_and_coaches = JoinBranch.objects.filter(
                    branch_id__in=creator_branches, joinning_type__in=[1, 3]
                ).select_related('user_id')

                for branch in branch_managers_and_coaches:
                    manager_or_coach = branch.user
                    self.send_notification(manager_or_coach, message, comments_message, push_data)
                    notifications_sent += 1
            else:
                creator = User.objects.get(id=training.created_by_id)
                self.send_notification(creator, message, comments_message, push_data)
                notifications_sent += 1

        elif training.creator_type == Training.TEAM_TYPE:
            team = Team.objects.get(id=training.created_by_id)
            team_founder = team.team_founder
            self.send_notification(team_founder, message, comments_message, push_data)
            notifications_sent += 1

        elif training.creator_type == Training.GROUP_TYPE:
            training_group = TrainingGroups.objects.get(id=training.created_by_id)
            group_founder = training_group.group_founder
            self.send_notification(group_founder, message, comments_message, push_data)
            notifications_sent += 1

        return notifications_sent

    def send_notification(self, user, message, comments_message, push_data):
        """
        Helper method to send notifications to a user.
        """
        notification_language = user.current_language
        if notification_language in ['ar', 'en']:
            activate(notification_language)

        send_push_notification(user.device_token, message, comments_message, device_type=user.device_type, data=push_data)
        send_push_notification(user.device_token,  message, comments_message, device_type=user.device_type, data=push_data)

        Notifictions.objects.create(
            created_by_id=1, creator_type=1, targeted_id=user.id, targeted_type=1,
            title=_("Training Reminder"), content=message + "\n" + comments_message
        )

    def get(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
            # Get the training ID from the request
            training_id = request.query_params.get('training_id')
            if not training_id:
                return Response({
                'status': 0,
                'message': _('Training ID is required.')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the user from the request
            user_id = request.query_params.get('user_id')
            if not user_id:
                return Response({
                'status': 0,
                'message': _('User not found.')
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate the training ID
            try:
                training = Training.objects.get(id=training_id)
            except Training.DoesNotExist:
                return Response({
                'status': 0,
                'message': _('Training not found.')
                }, status=status.HTTP_404_NOT_FOUND)

            user = request.user.id
            try:
                membership = Training_Joined.objects.get(user=user_id, training=training)
                serializer = TrainingMembershipSerializer(membership, context={'request': request})
                
                # Modify the serialized data by adding injury_type inside feedbacks
                data = serializer.data
                # Assuming feedbacks are part of the serialized data, no need to remove anything else
                
                return Response({
                'status': 1,
                'message': _('User membership retrieved successfully.'),
                'data': data
                }, status=status.HTTP_200_OK)
            except Training_Joined.DoesNotExist:
                return Response({
                'status': 0,
                'message': _('User is not a member of the training.')
                }, status=status.HTTP_404_NOT_FOUND)

    
    def delete(self, request, *args, **kwargs):
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)
            # Get the training ID from the request
            training_id = request.query_params.get('training_id')
            if not training_id:
                return Response({
                 'status': 0,
                 'message': _('Training ID is required.')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the user from the request
            user_id = request.query_params.get('user_id')
            if not user_id:
                return Response({
                 'status': 0,
                 'message': _('User not found.')
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate the training ID
            try:
                training = Training.objects.get(id=training_id)
            except Training.DoesNotExist:
                return Response({
                'status': 0,
                'message': _('Training not found.')
                }, status=status.HTTP_404_NOT_FOUND)
            user = request.user.id
            if not self._has_access(training, user):  # Pass None for manager_id and coach_id if not needed
                return Response({
                    'status': 0,
                    'message': _('User does not have access to delete this training.')
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get the membership of the user in the training
            try:
                membership = Training_Joined.objects.get(user=user_id, training=training)
            except Training_Joined.DoesNotExist:
                return Response({
                'status': 0,
                'message': _('User is not a member of the training.')
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Delete the membership
            membership.delete()
            return Response({
            'status': 1,
            'message': _('User membership deleted successfully.')
            }, status=status.HTTP_200_OK)
        
            
################## Training Feedback API ############################
class TrainingFeedbackAPI(APIView):
    def _has_access(self, training, user):

        # Case 1: Creator type is USER_TYPE
        if training.creator_type == 1:
            if training.created_by_id == user:  # Request user is the creator'
                return True

            # Check if the request user is in the same branch as the creator
            creator_branches = JoinBranch.objects.filter(
                user_id=training.created_by_id,
                joinning_type=4
            ).values_list('branch_id', flat=True)

            user_branch = JoinBranch.objects.filter(
                user_id=user,
                # joinning_type=4
            ).values_list('branch_id', flat=True)

            if not creator_branches:
                return False

            request_user_branches = JoinBranch.objects.filter(
                user_id=user,
                branch_id__in=creator_branches,
                joinning_type__in=[1, 3]
            )

            if not request_user_branches.exists():
                return False

            return True


        # Case 2: Creator type is TEAM_TYPE
        elif training.creator_type == 2:
            team = get_object_or_404(Team, id=training.created_by_id)
            if team.team_founder_id == user:  # Request user is the team's founder
                return True

        # Default: No access
        return False



    
    def patch(self, request, *args, **kwargs):
        # Set language based on the request header
        language = request.headers.get('Language', 'en')
        if language in ['en', 'ar']:
            activate(language)

        # Extract required and optional fields from request data
        user_id = request.data.get('user_id')
        training_id = request.data.get('training_id')
        feedback_id = request.data.get('feedback_id')  # Optional feedback ID
        attendance_status = request.data.get('attendance_status')
        feedback_text = request.data.get('feedback')
        rating = request.data.get('rating')
        injury_ids = request.data.get('injury_ids')  # A comma-separated list of injury IDs (e.g., '1,2,3')

        # Check if both training_id and user_id are provided
        if not user_id or not training_id:
            return Response({
                "status": 0,
                "message": _("user_id and training_id are required")
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            training = Training.objects.get(id=training_id)
        except Training.DoesNotExist:
            return Response({
                'status': 0,
                'message': _('Training not found.')
            }, status=status.HTTP_404_NOT_FOUND)

        user = request.user.id
        if not self._has_access(training, user):
            return Response({
                "status": 0,
                "message": _("Access denied")
            }, status=status.HTTP_403_FORBIDDEN)

        # Fetch the Training_Joined object
        training_joined = get_object_or_404(Training_Joined, user=user_id, training=training_id)

        # Initialize a flag to track if any changes were made
        updated = False
        update_messages = []

        # Update attendance status if provided
        if attendance_status is not None:
            # Normalize attendance status to handle different input formats
            truthy_values = {"true", "1", "yes", "y",1}
            falsy_values = {"false", "0", "no", "n",0}

            if str(attendance_status).strip().lower() in truthy_values:
                training_joined.attendance_status = True
            elif str(attendance_status).strip().lower() in falsy_values:
                training_joined.attendance_status = False
            else:
                # Handle invalid input or if you want to set a default value
                return Response({
                    "status": 0,
                    "message": _("Invalid attendance status value.")
                }, status=status.HTTP_400_BAD_REQUEST)

            updated = True
            update_messages.append(_("Attendance updated"))

        # Update rating if provided
        if rating is not None:
            training_joined.rating = rating
            updated = True
            update_messages.append(_("Rating updated"))

        # Save the updated Training_Joined record if there are any updates
        if updated:
            training_joined.save()

        # Handle feedback update or creation
        if feedback_id:
            feedback = get_object_or_404(Training_Feedback, id=feedback_id, user_id=user_id, training_id=training_id)

            # Update feedback text if provided
            if feedback_text:
                feedback.feedback = feedback_text
                update_messages.append(_("Feedback updated"))

            # Update injuries related to the feedback if provided
            if injury_ids:
                injury_id_list = [int(id) for id in injury_ids.split(',')]
                injuries = InjuryType.objects.filter(id__in=injury_id_list)
                feedback.injuries.set(injuries)

                notification_message = _("Someone Injured!!! Don't forget to add their injury to keep track.")
                self.notify_users(training, notification_message, {"type": "injury", "notifier_id": training_id})
                update_messages.append(_("Injury details updated and notification sent"))

            feedback.save()

        elif feedback_text:
            feedback = Training_Feedback.objects.create(
                training_id=training_id,
                user_id=user_id,
                feedback=feedback_text
            )

            if injury_ids:
                injury_id_list = [int(id) for id in injury_ids.split(',')]
                injuries = InjuryType.objects.filter(id__in=injury_id_list)
                feedback.injuries.set(injuries)

                notification_message = _("Someone Injured!!! Don't forget to add their injury to keep track.")
                self.notify_users(training, notification_message, {"type": "injury", "notifier_id": training_id})
                update_messages.append(_("New feedback added and injury notification sent"))

        # Serialize data
        feedbacks = Training_Feedback.objects.filter(training_id=training_id, user_id=user_id).order_by("-created_at")
        feedback_data = [
            {
                "id": feedback.id,
                "training": feedback.training.id,
                "user": feedback.user.id,
                "feedback": feedback.feedback,
                "injury_type": list(feedback.injuries.values_list("id", flat=True)),
                "date_created": feedback.date_created,
                "created_at": feedback.created_at,
                "updated_at": feedback.updated_at
            }
            for feedback in feedbacks
        ]

        joined_data = {
            "id": training_joined.id,
            "training": training_joined.training.id,
            "user": {
                "id": training_joined.user.id,
                "username": training_joined.user.username,
                "phone": training_joined.user.phone,
                "profile_picture": training_joined.user.profile_picture.url if training_joined.user.profile_picture else None,
                "country_id": training_joined.user.country.id if training_joined.user.country else None,
                "country_name": training_joined.user.country.name if training_joined.user.country else None,
                "attendance_status": bool(training_joined.attendance_status),
            },
            "rating": training_joined.rating,
            "feedbacks": feedback_data
        }

        update_message = ", ".join(update_messages) if update_messages else _("No changes made")
        return Response({
            "status": 1,
            "message": update_message,
            "data": joined_data
        }, status=status.HTTP_200_OK)

    def notify_users(self, training, message, push_data):
        """
        Notify users based on the creator type of the training.
        """
        notifications_sent = 0

        if training.creator_type == 1:  # Created by a User
            user = User.objects.get(id=training.created_by_id)
            user_branches = JoinBranch.objects.filter(
                user_id=user.id, joinning_type=4  # 4 = Player/Team Creator
            ).values_list('branch_id', flat=True)

            if user_branches.exists():
                # Notify all managers and coaches of the branches
                coaches_or_managers = JoinBranch.objects.filter(
                    branch_id__in=user_branches,
                    joinning_type__in=[1, 3]  # 1 = Coach, 3 = Manager
                ).select_related('user_id')

                for branch in coaches_or_managers:
                    coach_or_manager = branch.user_id
                    self.send_notification(
                        coach_or_manager, message, push_data
                    )
                    notifications_sent += 1
            else:
                # Notify the user who created the training
                self.send_notification(user, message, push_data)
                notifications_sent += 1

        elif training.creator_type == 2:  # Created by a Team
            team = Team.objects.get(id=training.created_by_id)
            team_founder = team.team_founder
            self.send_notification(team_founder, message, push_data)
            notifications_sent += 1

    def send_notification(self, user, message, push_data):
        """
        Helper method to send notifications to a user.
        """
        notification_language = user.current_language
        if notification_language in ['ar', 'en']:
            activate(notification_language)

        send_push_notification(
            user.device_token,
            _("Training Notification"),
            message,
            device_type=user.device_type,
            data=push_data
        )

      

        Notifictions.objects.create(
            created_by_id=1,  # Replace with the actual creator ID
            creator_type=1,
            targeted_id=user.id,
            targeted_type=1,
            title=_("Training Notification"),
            content=message 
        )
