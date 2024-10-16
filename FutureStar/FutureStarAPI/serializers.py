import mimetypes
from rest_framework import serializers
from FutureStar_App.models import User
from FutureStarAPI.models import *
from django.core.files.storage import default_storage



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


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture']  # Customize as needed

class PostCommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(queryset=Post_comment.objects.all(), allow_null=True)

    class Meta:
        model = Post_comment
        fields = ['id', 'user', 'post', 'parent', 'comment', 'date_created', 'replies', 'team_id','group_id']

    def get_replies(self, obj):
        # Get replies for this comment
        replies = Post_comment.objects.filter(parent=obj)
        return PostCommentSerializer(replies, many=True).data  # Serialize replies


class PostSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField()  # Change to use a method for comments
    user = UserSerializer(read_only=True)  # Nested user details
    team_id = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all(), allow_null=True, required=False)
    group_id = serializers.PrimaryKeyRelatedField(queryset=TrainingGroups.objects.all(), allow_null=True, required=False)


    class Meta:
        model = Post
        fields = ['id', 'user', 'team_id', 'group_id', 'title', 'description', 'image', 'date_created', 'comments']

    def get_comments(self, obj):
        # Get only top-level comments (where parent is None)
        top_level_comments = Post_comment.objects.filter(post=obj, parent=None)
        return PostCommentSerializer(top_level_comments, many=True).data  # Serialize top-level comments

    def create(self, validated_data):
        team_id = validated_data.pop('team_id', None)
        group_id = validated_data.pop('group_id', None)
        post = Post.objects.create(**validated_data, team_id=team_id,group_id=group_id)
        return post

    def update(self, instance, validated_data):
        team_id = validated_data.get('team_id', instance.team_id)
        group_id = validated_data.get('group_id', instance.group_id)
        instance.team_id = team_id
        instance.group_id = group_id
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.image = validated_data.get('image', instance.image)
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
    class Meta:
        model = Field
        fields = ['field_name', 'image', 'field_capacity', 'ground_type', 'country', 'city', 'location', 'additional_information']  # Exclude user_id

    def create(self, validated_data):
        # Automatically associate the field with the currently logged-in user
        user = self.context['request'].user
        return Field.objects.create(user_id=user, **validated_data)
    


class TournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = [
            'tournament_name',
            'tournament_starting_date',
            'tournament_final_date',
            'number_of_team',
            'age_group',
            'country',
            'city',
            'tournament_fields',
            'logo',
            'tournament_joining_cost',
        ]  # Exclude user_id

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
        fields = ['id', 'user','team_id','group_id','album_id','content_type','media_file', 'created_at', 'updated_at']
        read_only_fields = ['user','album_id']

    def to_representation(self, instance):
        """Customize the representation of the object."""
        representation = super().to_representation(instance)

        # Check if it's a GET request and remove the album_id
        request = self.context.get('request')
        if request and request.method == 'GET':
            representation.pop('album_id', None)

        return representation

    def validate(self, data):
        media_file = data.get('media_file')
        
        # Ensure the media file is provided
        if not media_file:
            raise serializers.ValidationError("A media file (image or video) must be provided.")

        # Check the file type using the mimetype
        mime_type, _ = mimetypes.guess_type(media_file.name)

        if mime_type:
            if mime_type.startswith('image/'):
                data['content_type'] = 1  # Image
            elif mime_type.startswith('video/'):
                data['content_type'] = 2  # Video
            else:
                raise serializers.ValidationError("The file must be an image or video.")
        else:
            raise serializers.ValidationError("The file type could not be determined.")

        return data

class DetailAlbumSerializer(serializers.ModelSerializer):
    # Define a custom field to retrieve the thumbnail
    gallary_items = GallarySerializer(many=True, source='gallary_set', read_only=True)
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Album
        fields = ['id', 'user', 'team_id','group_id', 'name', 'thumbnail', 'gallary_items', 'created_at', 'updated_at']
        read_only_fields = ['user']  # Make the 'user' field read-only

    # Method to get the most recent image or video from the related Gallary
    def get_thumbnail(self, obj):
        last_media = Gallary.objects.filter(album_id=obj).order_by('-created_at').first()

        if not last_media:
            return None

        if last_media.content_type == 1:  # Assuming 1 is for images
            return last_media.media_file.url
        elif last_media.content_type == 2:  # Assuming 2 is for videos
            return last_media.media_file.url

        return None

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
    
    