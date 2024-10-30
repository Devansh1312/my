import mimetypes
from rest_framework import serializers
from FutureStar_App.models import User
from urllib.parse import urlparse
from FutureStarAPI.models import *
from django.core.files.images import get_image_dimensions



class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'phone', 'password']

    def validate(self, data):
        username_exists = User.objects.filter(username=data['username']).exists()
        phone_exists = User.objects.filter(phone=data['phone']).exists()

        if username_exists and phone_exists:
            raise serializers.ValidationError("Username and phone number already exist.")
        elif username_exists:
            raise serializers.ValidationError("Username already exists.")
        elif phone_exists:
            raise serializers.ValidationError("Phone number already exists.")
        
        return data

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            phone=validated_data['phone'],
            role_id=2,
            register_type="App"
        )
        user.set_password(validated_data['password'])
        user.save()
        return user



class LoginSerializer(serializers.Serializer):
    type = serializers.IntegerField(required=True)  # Add type field to distinguish login types
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False, allow_blank=True, write_only=True)
    device_type = serializers.CharField(required=True)
    device_token = serializers.CharField(required=True)

    def validate(self, data):
        login_type = data.get('type')

        # Initialize an empty list for collecting error messages
        errors = []

        # For type 1, username_or_phone and password are required
        if login_type == 1:
            if not data.get('username'):
                errors.append("Username or phone is required for normal login.")
            if not data.get('password'):
                errors.append("Password is required for normal login.")
            
            # Check if there are any errors to report
            if errors:
                # Combine errors into a single message
                raise serializers.ValidationError(" ".join(errors))
            
            # Check if the user exists with the provided username or phone
            user = User.objects.filter(username=data['username']).first() or User.objects.filter(phone=data['username']).first()
            if user is None:
                raise serializers.ValidationError("User with this username or phone does not exist.")
            
            # Check if the password is correct
            if not user.check_password(data['password']):
                raise serializers.ValidationError("Invalid password.")

        # For type 2 or 3, only username (email) is required
        elif login_type in [2, 3]:
            if not data.get('username'):
                errors.append("Email is required for type 2 and type 3 login.")
                raise serializers.ValidationError(" ".join(errors))

        return data


class ForgotPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)  # Adjust max_length based on your phone number format

class OTPVerificationSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)  # Same as above
    otp = serializers.CharField(max_length=6)      # Assuming OTP is a 6-digit code

class ChangePasswordOtpSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)  # Same as above
    new_password = serializers.CharField(min_length=8)  # Ensure a minimum length for security


from rest_framework import serializers


class TrainingGroupSerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField()
    group_logo_url = serializers.SerializerMethodField()
    group_background_image_url = serializers.SerializerMethodField()
    group_founder = serializers.SerializerMethodField()

    class Meta:
        model = TrainingGroups
        fields = [
            'id','group_name', 'group_username', 'bio', 'group_founder',
            'latitude', 'longitude', 'address', 'house_no', 'premises', 'street',
            'city', 'state', 'country_name', 'postalCode', 'country_code',
            'phone', 'group_logo', 'group_background_image', 'post_count', 
            'group_logo_url', 'group_background_image_url'
        ]
    
    def get_group_founder(self, obj):
        user = obj.group_founder
        return {
            'username': user.username,
            'fullname': user.fullname,
            'phone': user.phone,
            'email': user.email,
            'profile_pic': user.profile_picture.url if user.profile_picture else None,  # Use the correct field name
        }
    
    def get_post_count(self, obj):
        """Get the count of posts related to this group."""
        return Post.objects.filter(group=obj).count()

    def get_group_logo_url(self, obj):
        """Get the URL of the group logo."""
        return obj.group_logo.url if obj.group_logo else None

    def get_group_background_image_url(self, obj):
        """Get the URL of the group background image."""
        return obj.group_background_image.url if obj.group_background_image else None
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture']

    def get_profile_picture(self, obj):
        return obj.profile_picture.url if obj.profile_picture else None  

class PostCommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    entity = serializers.SerializerMethodField()

    class Meta:
        model = Post_comment
        fields = ['id', 'created_by_id', 'creator_type', 'post', 'parent', 'comment', 'date_created', 'replies', 'entity']

    def get_replies(self, obj):
        # Only fetch replies (children) where parent is the current comment (obj)
        replies = Post_comment.objects.filter(parent=obj).order_by('-date_created')
        return PostCommentSerializer(replies, many=True, context=self.context).data

    def get_entity(self, obj):
        # Get entity details based on creator_type
        if obj.creator_type == Post_comment.TEAM_TYPE:
            team = Team.objects.get(id=obj.created_by_id)
            return {
                'id': team.id,
                'name': team.team_name,
                'profile_image': team.team_logo.url if team.team_logo else None,
                'type': 'team'
            }
        elif obj.creator_type == Post_comment.GROUP_TYPE:
            group = TrainingGroups.objects.get(id=obj.created_by_id)
            return {
                'id': group.id,
                'name': group.group_name,
                'profile_image': group.group_logo.url if group.group_logo else None,
                'type': 'group'
            }
        else:  # USER_TYPE
            user = User.objects.get(id=obj.created_by_id)
            return {
                'id': user.id,
                'username': user.username,
                'profile_image': user.profile_picture.url if user.profile_picture else None,
                'type': 'user'
            }
        return None




class PostSerializer(serializers.ModelSerializer):
    entity = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    view_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_like = serializers.SerializerMethodField()
    is_reported = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'entity', 'title', 'description', 'image', 'media_type',
            'date_created', 'comments', 'view_count', 'like_count', 'is_like', 'is_reported',
            'latitude', 'longitude', 'address', 'house_no',
            'premises', 'street', 'city', 'state', 'country_name',
            'postalCode', 'country_code'
        ]

    def get_entity(self, obj):
        if obj.creator_type == Post.USER_TYPE:
            user = User.objects.get(id=obj.created_by_id)
            return {
                'id': user.id,
                'username': user.username,
                'profile_image': user.profile_picture.url if user.profile_picture else None,
                'type': 'user'
            }
        elif obj.creator_type == Post.TEAM_TYPE:
            team = Team.objects.get(id=obj.created_by_id)
            return {
                'id': team.id,
                'username': team.team_name,
                'profile_image': team.team_logo.url if team.team_logo else None,
                'type': 'team'
            }
        elif obj.creator_type == Post.GROUP_TYPE:
            group = TrainingGroups.objects.get(id=obj.created_by_id)
            return {
                'id': group.id,
                'username': group.group_name,
                'profile_image': group.group_logo.url if group.group_logo else None,
                'type': 'group'
            }
        return None

    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        return obj.image.url if obj.image else None

    def get_view_count(self, obj):
        return PostView.objects.filter(post=obj).count()

    def get_like_count(self, obj):
        return PostLike.objects.filter(post=obj).count()
    
    def get_is_like(self, obj):
        request = self.context.get('request')
        if request:
            # Retrieve creator_type and created_by_id from request data or query parameters
            creator_type = request.data.get('creator_type') or request.query_params.get('creator_type')
            created_by_id = request.data.get('created_by_id') or request.query_params.get('created_by_id')

            # Use default values if neither request data nor query parameters provide valid values
            creator_type = int(creator_type) if creator_type not in [None, '', '0'] else PostLike.USER_TYPE
            created_by_id = int(created_by_id) if created_by_id not in [None, '', '0'] else request.user.id

            # Check if a like exists for the given post, creator_type, and created_by_id
            if PostLike.objects.filter(
                post=obj,
                created_by_id=created_by_id,
                creator_type=creator_type
            ).exists():
                return True

        return False


    
    def get_is_reported(self, obj):
        request = self.context.get('request')
        if request:
            # Retrieve creator_type and created_by_id from request data or query parameters
            creator_type = request.data.get('creator_type') or request.query_params.get('creator_type')
            created_by_id = request.data.get('created_by_id') or request.query_params.get('created_by_id')

            # Use default values if neither request data nor query parameters provide valid values
            creator_type = int(creator_type) if creator_type not in [None, '', '0'] else PostReport.USER_TYPE
            created_by_id = int(created_by_id) if created_by_id not in [None, '', '0'] else request.user.id

            # Check if a report exists for the given post, creator_type, and created_by_id
            if PostReport.objects.filter(
                post_id=obj,
                creator_type=creator_type,
                created_by_id=created_by_id
            ).exists():
                return True

        return False



    
    def get_comments(self, obj):
        # Always return the count of top-level comments
        return Post_comment.objects.filter(post=obj, parent=None).count()



    def create(self, validated_data):
        # Remove 'created_by_id' and 'creator_type' from validated_data if they exist
        created_by_id = validated_data.pop('created_by_id', None)
        creator_type = validated_data.pop('creator_type', None)
        
        # Now create the post with validated data and additional fields
        post = Post.objects.create(**validated_data, created_by_id=created_by_id, creator_type=creator_type)
        return post



    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.image = validated_data.get('image', instance.image)
        instance.media_type = validated_data.get('media_type', instance.media_type)
        instance.latitude = validated_data.get('latitude', instance.latitude)
        instance.longitude = validated_data.get('longitude', instance.longitude)
        instance.address = validated_data.get('address', instance.address)
        instance.house_no = validated_data.get('house_no', instance.house_no)
        instance.premises = validated_data.get('premises', instance.premises)
        instance.street = validated_data.get('street', instance.street)
        instance.city = validated_data.get('city', instance.city)
        instance.state = validated_data.get('state', instance.state)
        instance.country_name = validated_data.get('country_name', instance.country_name)
        instance.postalCode = validated_data.get('postalCode', instance.postalCode)
        instance.country_code = validated_data.get('country_code', instance.country_code)
        instance.save()
        return instance



class FieldCapacitySerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldCapacity
        fields = '__all__'

class GroundMaterialSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = GroundMaterial
        fields = ['id', 'name']  # Only return id and the translated name

    def get_name(self, obj):
        # Get the language from the request context
        request = self.context.get('request')
        language = request.headers.get('Language', 'en') if request else 'en'
        
        # Return the appropriate name based on the language
        if language == 'ar':
            return obj.name_ar
        return obj.name_en
    

class FieldSerializer(serializers.ModelSerializer):
    city_id_name= serializers.SerializerMethodField()
    country_id_name = serializers.SerializerMethodField()
    class Meta:
        model = Field
        fields = ['field_name', 'image', 'field_capacity', 'ground_type', 'country_id','country_id_name', 'city_id','city_id_name', 'latitude', 'longitude', 'address', 'house_no', 
            'premises', 'street', 'city', 'state', 'country_name', 
            'postalCode', 'country_code', 'additional_information']  # Exclude user_id
    def get_country_id_name(self, obj):
        return obj.country_id.name if obj.country_id else None  # Return None if no country

    # Method to retrieve city name for city_id_name field
    def get_city_id_name(self, obj):
        return obj.city_id.name if obj.city_id else None # Return None if no city
    
    def create(self, validated_data):
        # Automatically associate the field with the currently logged-in user
        user = self.context['request'].user
        return Field.objects.create(user_id=user, **validated_data)
    


class TournamentSerializer(serializers.ModelSerializer):
    city_name = serializers.SerializerMethodField()  # Change to city_name
    country_name = serializers.SerializerMethodField()  # Change to country_name
    tournament_fields_name=serializers.SerializerMethodField()  # Change to tournament_fields_name

    class Meta:
        model = Tournament
        fields = [
            'tournament_name',
            'tournament_starting_date',
            'tournament_final_date',
            'number_of_team',
            'age_group',
            'country',
            'country_name',
            'city',
            'city_name',
            'tournament_fields',
            'tournament_fields_name',
            'logo',
            'tournament_joining_cost',
        ]  # Exclude user_id

    def get_country_name(self, obj):
        return obj.country.name if obj.country else None  # Assuming 'country' is the field in Tournament

    # Method to retrieve city name for city_name field
    def get_city_name(self, obj):
        return obj.city.name if obj.city else None  # # Return None if no city
    
    # Method to retrieve tournament fields name for tournament_fields_name field
    def get_tournament_fields_name(self, obj):
        return obj.tournament_fields.field_name if obj.tournament_fields else None

    def create(self, validated_data):
        # Automatically associate the tournament with the currently logged-in user
        user = self.context['request'].user
        return Tournament.objects.create(user_id=user, **validated_data)
    


class UserGenderSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = UserGender
        fields = ['id', 'name']  # Only return id and the translated name

    def get_name(self, obj):
        # Get the language from the request context
        request = self.context.get('request')
        language = request.headers.get('Language', 'en') if request else 'en'
        
        # Return the appropriate name based on the language
        if language == 'ar':
            return obj.name_ar
        return obj.name_en

class PlayingPositionSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = PlayingPosition
        fields = ['id', 'name']  # Only return id and the combined name

    def get_name(self, obj):
        # Get the language from the request context
        request = self.context.get('request')
        language = request.headers.get('Language', 'en') if request else 'en'
        
        # Get the name based on the language
        if language == 'ar':
            name = obj.name_ar
        else:
            name = obj.name_en
        
        # Combine the name and shortname
        return f"{name} - {obj.shortname}"

    
class UserRoleSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ['id', 'name']  # Only return id and the translated name

    def get_name(self, obj):
        # Get the language from the request context
        request = self.context.get('request')
        language = request.headers.get('Language', 'en') if request else 'en'
        
        # Return the appropriate name based on the language
        if language == 'ar':
            return obj.name_ar
        return obj.name_en
    



class GallarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Gallary
        fields = ['id', 'creator_type', 'created_by_id', 'album', 'content_type', 'media_file', 'created_at', 'updated_at']

    def validate(self, data):
        media_file = data.get('media_file')
        if not media_file:
            raise serializers.ValidationError("A media file (image or video) must be provided.")
        
        mime_type, _ = mimetypes.guess_type(media_file.name)
        if mime_type:
            if mime_type.startswith('image/'):
                data['content_type'] = 1
            elif mime_type.startswith('video/'):
                data['content_type'] = 2
            else:
                raise serializers.ValidationError("The file must be an image or video.")
        else:
            raise serializers.ValidationError("The file type could not be determined.")
        
        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        
        if 'media_file' in representation:
            full_url = representation['media_file']
            parsed_url = urlparse(full_url)
            relative_url = parsed_url.path
            representation['media_file'] = relative_url
        
        return representation
class GetGallarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Gallary
        fields = ['id', 'album', 'content_type', 'media_file', 'created_at', 'updated_at', 'creator_type', 'created_by_id']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if 'media_file' in representation:
            full_url = representation['media_file']
            parsed_url = urlparse(full_url)
            relative_url = parsed_url.path
            representation['media_file'] = relative_url

        if request and request.method == 'GET':
            representation.pop('album', None)
        return representation

    def validate(self, data):
        media_file = data.get('media_file')
        if not media_file:
            raise serializers.ValidationError("A media file (image or video) must be provided.")
        
        mime_type, _ = mimetypes.guess_type(media_file.name)
        if mime_type:
            if mime_type.startswith('image/'):
                data['content_type'] = 1
            elif mime_type.startswith('video/'):
                data['content_type'] = 2
            else:
                raise serializers.ValidationError("The file must be an image or video.")
        else:
            raise serializers.ValidationError("The file type could not be determined.")
        return data
class DetailAlbumSerializer(serializers.ModelSerializer):
    gallary_items = GallarySerializer(many=True, source='gallery_set', read_only=True)
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Album
        fields = ['id', 'creator_type', 'created_by_id', 'name', 'thumbnail', 'gallary_items', 'created_at', 'updated_at']

    def get_thumbnail(self, obj):
        last_media = Gallary.objects.filter(album=obj).order_by('-created_at').first()
        return last_media.media_file.url if last_media else None
class AlbumSerializer(serializers.ModelSerializer):
    # Define a custom field to retrieve the thumbnail
   
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Album
        # fields = '__all__'
        fields = ['id', 'created_by_id', 'creator_type', 'name','thumbnail', 'created_at', 'updated_at' ]

    # Method to get the most recent image or video from the related Gallary
    def get_thumbnail(self, obj):
        # Get the last inserted Gallary entry for this album
        last_media = Gallary.objects.filter(album_id=obj).order_by('-created_at').first()
        
        # If no media exists, return None
        if not last_media:
            return None
        
        # Return the image or video URL depending on the content type
        if last_media.content_type == 1:
            return last_media.media_file.url  # Image URL
        elif last_media.content_type == 2:
            return last_media.media_file.url  # Video URL

        
        return None
    

class ReportSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = ['id', 'title', 'content','created_at', 'updated_at']

    def get_title(self, obj):
        # Get the language from the request context
        request = self.context.get('request')
        language = request.headers.get('Language', 'en') if request else 'en'
        
        # Return the appropriate title based on the language
        if language == 'ar':
            return obj.title_ar
        return obj.title_en

    def get_content(self, obj):
        # Get the language from the request context
        request = self.context.get('request')
        language = request.headers.get('Language', 'en') if request else 'en'
        
        # Return the appropriate content based on the language
        if language == 'ar':
            return obj.content_ar
        return obj.content_en
    
class PostReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostReport
        fields = ['id', 'report_id', 'post_id', 'creator_type', 'created_by_id', 'created_at', 'updated_at']
        read_only_fields = ['created_by_id']  # Make created_by_id read-only

        

class MobileDashboardBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileDashboardBanner
        fields = ['id', 'image', 'created_at', 'updated_at']

class EventTypeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    class Meta:
        model = EventType
        fields = ['id', 'name','created_at', 'updated_at']

    def get_name(self, obj):
        # Get the language from the request context
        request = self.context.get('request')
        language = request.headers.get('Language', 'en') if request else 'en'
        
        # Return the appropriate title based on the language
        if language == 'ar':
            return obj.name_ar
        return obj.name_en



class EventSerializer(serializers.ModelSerializer):
    event_type_name = serializers.SerializerMethodField()  # Keep it as event_type_name
    comments = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_like = serializers.SerializerMethodField()
    event_organizer = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'team', 'event_organizer', 'event_name', 'event_type', 'event_type_name', 'event_date',
            'event_start_time', 'event_end_time', 'event_image', 'latitude', 'longitude', 'address',
            'house_no', 'premises', 'street', 'city', 'state', 'country_name', 'country_code',
            'event_description', 'event_cost', 'comments', 'like_count', 'is_like', 'created_at', 'updated_at'
        ]
        read_only_fields = ['event_organizer']  # Make 'event_organizer' read-only since it will be auto-assigned

    def get_event_organizer(self, obj):
        user = obj.event_organizer
        return {
            'username': user.username,
            'fullname': user.fullname,
            'phone': user.phone,
            'email': user.email,
            'profile_pic': user.profile_picture.url if user.profile_picture else None,
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Convert the event_image URL to a relative URL
        if 'event_image' in representation and representation['event_image'] is not None:
            full_url = representation['event_image']
            request = self.context.get('request')
            if request:
                parsed_url = urlparse(full_url)
                relative_url = parsed_url.path  # Extracts only the path part, giving the relative URL
                representation['event_image'] = relative_url
        else:
            representation['event_image'] = None  # Set to None if no image is available

        return representation

    def get_event_type_name(self, obj):
        return obj.event_type.name_en if obj.event_type else None

    def create(self, validated_data):
        # Automatically set the user from the request context
        validated_data['event_organizer'] = self.context['request'].user
        return Event.objects.create(**validated_data)

    def get_like_count(self, obj):
        return EventLike.objects.filter(event=obj).count()

    def get_is_like(self, obj):
        request = self.context.get('request')  # Access the request object from the context
        if request:
            creator_type = request.data.get('creator_type') or request.query_params.get('creator_type')
            created_by_id = request.data.get('created_by_id') or request.query_params.get('created_by_id')
            creator_type = int(creator_type) if creator_type not in [None, '', '0'] else EventLike.USER_TYPE
            created_by_id = int(created_by_id) if created_by_id not in [None, '', '0'] else request.user.id
            if EventLike.objects.filter(event=obj, created_by_id=created_by_id, creator_type=creator_type).exists():
                return True
        return False

    def get_comments(self, obj):
        # Always return the count of top-level comments
        return Event_comment.objects.filter(event=obj, parent=None).count()


class EventBookingSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = EventBooking
        fields = ['id', 'event', 'tickets', 'convenience_fee', 'ticket_amount', 'total_amount']

  

class EventCommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    entity = serializers.SerializerMethodField()

    class Meta:
        model = Event_comment
        fields = ['id', 'created_by_id', 'creator_type', 'event', 'parent', 'comment', 'date_created', 'replies', 'entity']

    def get_replies(self, obj):
        replies = Event_comment.objects.filter(parent=obj).order_by('-date_created')
        return EventCommentSerializer(replies, many=True).data

    def get_entity(self, obj):
        if obj.creator_type == Event_comment.TEAM_TYPE:
            team = Team.objects.get(id=obj.created_by_id)
            return {
                'id': team.id,
                'name': team.team_name,
                'profile_image': team.team_logo.url if team.team_logo else None,
                'type': 'team'
            }
        elif obj.creator_type == Event_comment.GROUP_TYPE:
            group = TrainingGroups.objects.get(id=obj.created_by_id)
            return {
                'id': group.id,
                'name': group.group_name,
                'profile_image': group.group_logo.url if group.group_logo else None,
                'type': 'group'
            }
        else:  # USER_TYPE
            user = User.objects.get(id=obj.created_by_id)
            return {
                'id': user.id,
                'username': user.username,
                'profile_image': user.profile_picture.url if user.profile_picture else None,
                'type': 'user'
            }
        return None



    
class FAQSerializer(serializers.ModelSerializer):
    question = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()


    class Meta:
        model = FAQ
        fields = ['id','question','answer']  # Only return id and the translated name

    def get_question(self, obj):
        # Get the language from the request context
        request = self.context.get('request')
        language = request.headers.get('Language', 'en') if request else 'en'
        
        # Return the appropriate name based on the language
        if language == 'ar':
            return obj.question_ar
        return obj.question_en
    
    def get_answer(self, obj):
        # Get the language from the request context
        request = self.context.get('request')
        language = request.headers.get('Language', 'en') if request else 'en'
        
        # Return the appropriate name based on the language
        if language == 'ar':
            return obj.answer_ar
        return obj.answer_en
    


class UpdateCurrentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['current_type']
    
    def validate_current_type(self, value):
        if value not in [User.USER_TYPE, User.TEAM_TYPE, User.GROUP_TYPE]:
            raise serializers.ValidationError("Invalid type. Allowed values are 1, 2, or 3.")
        return value



class AgeGroupSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = AgeGroup
        fields = ['id', 'name', 'created_at', 'updated_at']

    def get_name(self, obj):
        # Get the language from the request context
        request = self.context.get('request')
        language = request.headers.get('Language', 'en') if request else 'en'
        
        # Get the name based on the language, with a fallback to "Unnamed" if null
        if language == 'ar':
            name = obj.name_ar 
        else:
            name = obj.name_en 
        return name