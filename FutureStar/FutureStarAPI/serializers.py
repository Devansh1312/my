import mimetypes
from rest_framework import serializers
from FutureStar_App.models import User
from FutureStarAPI.models import *
from django.core.files.storage import default_storage
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser



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

class TeamSerializer(serializers.ModelSerializer):
    # Custom fields
    team_type_name = serializers.SerializerMethodField()
    country_id_name = serializers.CharField(source='country_id.name', allow_null=True)  # Assuming 'country_id' is a ForeignKey
    city_id_name = serializers.CharField(source='city_id.name', allow_null=True)  # Assuming 'city_id' is a ForeignKey
    post_count = serializers.SerializerMethodField()  # Adding the post count field


    class Meta:
        model = Team
        fields = [
            'id', 'user_id', 'team_name', 'team_username', 'team_type', 'team_type_name','bio', 'team_establishment_date', 'team_president',
            'latitude', 'longitude', 'address', 'house_no', 'premises', 'street', 'city', 'state', 'country_name','postalCode', 'country_code', 
            'country_id', 'country_id_name', 'city_id',  'city_id_name',  'phone', 'email','age_group', 'entry_fees', 'branches', 'team_logo', 
            'team_background_image', 'team_uniform','post_count'
        ]

    def get_post_count(self, obj):
        # Assuming Post model has a ForeignKey to Team
        return Post.objects.filter(team=obj).count()

    def get_team_type_name(self, obj):
        request = self.context.get('request')
        language = request.headers.get('Language', 'en') if request else 'en'
        return obj.team_type.name_ar if language == 'ar' else obj.team_type.name_en

    def get_team_logo(self, obj):
        return obj.team_logo.url if obj.team_logo else None,

    def get_team_background_image(self, obj):
        # Return the relative path for the team background image
        return obj.team_background_image.url if obj.team_background_image else None



class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingGroups
        fields = ['id', 'group_name', 'group_logo']

    def get_group_logo(self, obj):
        return obj.group_logo.url if obj.group_logo else None 

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture']

    def get_profile_picture(self, obj):
        return obj.profile_picture.url if obj.profile_picture else None  

class PostCommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(queryset=Post_comment.objects.all(), allow_null=True)
    entity = serializers.SerializerMethodField()  # Add entity field

    class Meta:
        model = Post_comment
        fields = ['id', 'user', 'post', 'parent', 'comment', 'date_created', 'replies', 'entity']

    def get_replies(self, obj):
        # Get replies for this comment
        replies = Post_comment.objects.filter(parent=obj)
        return PostCommentSerializer(replies, many=True).data  # Serialize replies

    def get_entity(self, obj):
        # Return unified structure for Team, Group, or User
        if obj.team_id:  # Corrected field name
            return {
                'id': obj.team_id.id,
                'username': obj.team_id.team_name,
                'profile_image': obj.team_id.team_logo.url if obj.team_id.team_logo else None,
                'type': 'team'  # Optional: entity type for frontend differentiation
            }
        elif obj.group_id:  # Corrected typo and field name
            return {
                'id': obj.group_id.id,
                'username': obj.group_id.group_name,
                'profile_image': obj.group_id.group_logo.url if obj.group_id.group_logo else None,
                'type': 'group'  # Optional: entity type for frontend differentiation
            }
        elif obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'profile_image': obj.user.profile_picture.url if obj.user.profile_picture else None,
                'type': 'user'  # Optional: entity type for frontend differentiation
            }
        return None


class PostSerializer(serializers.ModelSerializer):
    entity = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    view_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_like = serializers.SerializerMethodField()
    is_reported = serializers.SerializerMethodField()  # New field



    class Meta:
        model = Post
        fields = [
            'id', 'entity', 'title', 'description', 'image', 'media_type',
            'date_created', 'comments', 'view_count', 'like_count','is_like','is_reported',
            'latitude', 'longitude', 'address', 'house_no', 
            'premises', 'street', 'city', 'state', 'country_name', 
            'postalCode', 'country_code'
        ]

    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        return obj.image.url if obj.image else None
    
    def get_entity(self, obj):
        if obj.team:
            # Return unified structure for Team
            return {
                'id': obj.team.id,
                'username': obj.team.team_name,
                'profile_image': obj.team.team_logo.url if obj.team.team_logo else None,
                'type': 'team'  # Optional, to indicate type
            }
        elif obj.group:
            # Return unified structure for Group
            return {
                'id': obj.group.id,
                'username': obj.group.group_name,  # Using group_name as a username equivalent
                'profile_image': obj.group.group_logo.url if obj.group.group_logo else None,
                'type': 'group'  # Optional, to indicate type
            }
        elif obj.user:
            # Return unified structure for User
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'profile_image': obj.user.profile_picture.url if obj.user.profile_picture else None,
                'type': 'user'  # Optional, to indicate type
            }
        return None

    def get_view_count(self, obj):
        return PostView.objects.filter(post=obj).count()

    def get_like_count(self, obj):
        return PostLike.objects.filter(post=obj).count()
    
    def get_is_like(self, obj):
        request = self.context.get('request')  # Access the request object from the context
        if request and PostLike.objects.filter(post=obj, user=request.user).exists():
            return True
        return False
    
    def get_is_reported(self, obj):
        request = self.context.get('request')  # Access the request object from the context
        if request and PostReport.objects.filter(post_id=obj, user_id=request.user).exists():
            return True
        return False

    
    def get_comments(self, obj):
        # Always return the count of top-level comments
        return Post_comment.objects.filter(post=obj, parent=None).count()



    def create(self, validated_data):
        # Override create to handle team_id/group_id/user assignments
        user = validated_data.pop('user', None)
        team_id = validated_data.pop('team_id', None)
        group_id = validated_data.pop('group_id', None)
        
        post = Post.objects.create(**validated_data, user=user, team_id=team_id, group_id=group_id)
        return post

    def update(self, instance, validated_data):
        instance.user = validated_data.get('user', instance.user)
        instance.team = validated_data.get('team', instance.team)
        instance.group = validated_data.get('group', instance.group)
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
        fields = ['id', 'user', 'team_id', 'group_id', 'album_id', 'content_type', 'media_file', 'created_at', 'updated_at']
        # read_only_fields = ['album_id']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')

        if 'media_file' in representation:
            full_url = representation['media_file']
            # Get the relative path from the full URL
            relative_url = full_url.replace(f"{request.scheme}://{request.get_host()}", "")
            representation['media_file'] = relative_url
        if request and request.method == 'GET':
            representation.pop('album_id', None)
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

    def create(self, validated_data):
        return Gallary.objects.create(**validated_data)


class GetGallarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Gallary
        fields = ['id', 'user', 'team_id', 'group_id', 'album_id', 'content_type', 'media_file', 'created_at', 'updated_at']
        read_only_fields = ['album_id', 'user']  # Make 'user' read-only since it will be auto-assigned

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')

        if 'media_file' in representation:
            full_url = representation['media_file']
            # Get the relative path from the full URL
            relative_url = full_url.replace(f"{request.scheme}://{request.get_host()}", "")
            representation['media_file'] = relative_url

        if request and request.method == 'GET':
            representation.pop('album_id', None)
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

    def create(self, validated_data):
        # Automatically set the user from the request context
        validated_data['user'] = self.context['request'].user
        return Gallary.objects.create(**validated_data)

class DetailAlbumSerializer(serializers.ModelSerializer):
    gallary_items = GallarySerializer(many=True, source='gallary_set', read_only=True)
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Album
        fields = ['id', 'user', 'team_id', 'group_id', 'name', 'thumbnail', 'gallary_items', 'created_at', 'updated_at']
        read_only_fields = ['user']

    def get_thumbnail(self, obj):
        last_media = Gallary.objects.filter(album_id=obj).order_by('-created_at').first()
        if not last_media:
            return None
        return last_media.media_file.url

class AlbumSerializer(serializers.ModelSerializer):
    # Define a custom field to retrieve the thumbnail
   
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Album
        # fields = '__all__'
        fields = ['id', 'user','team_id','group_id', 'name','thumbnail', 'created_at', 'updated_at' ]

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
        fields = ['id', 'report_id', 'post_id', 'user_id', 'created_at', 'updated_at']
        read_only_fields = ['user_id']  # Make user_id read-only
        

class MobileDashboardBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileDashboardBanner
        fields = ['id', 'image', 'created_at', 'updated_at']

class EventTypeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    class Meta:
        model = EventType
        fields = ['id', 'name']

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

    class Meta:
        model = Event
        fields = ['team', 'event_organizer', 'event_name', 'event_type', 'event_type_name', 'event_date',
                  'event_start_time', 'event_end_time', 'event_image', 'latitude', 'longitude', 'address',
                  'house_no', 'premises', 'street', 'city', 'state', 'country_name', 'country_code',
                  'event_description', 'event_cost', 'created_at', 'updated_at']
        read_only_fields = ['event_organizer']  # Make 'user' read-only since it will be auto-assigned
        

    def get_event_type_name(self, obj):
        return obj.event_type.name_en if obj.event_type else None

    def create(self, validated_data):
        # Automatically set the user from the request context
        validated_data['event_organizer'] = self.context['request'].user
        return Event.objects.create(**validated_data)