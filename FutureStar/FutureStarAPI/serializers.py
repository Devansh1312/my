from rest_framework import serializers
from FutureStar_App.models import User
from FutureStarAPI.models import *


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
    password = serializers.CharField(required=False, write_only=True)
    # username = serializers.EmailField(required=False)  # Required for Type 2 or 3
    device_type = serializers.CharField(required=True)
    device_token = serializers.CharField(required=True)

    def validate(self, data):
        # For type 1, username_or_phone and password are required
        if data['type'] == 1:
            if not data.get('username') or not data.get('password'):
                raise serializers.ValidationError("Username or phone and password are required for normal login.")
        # For type 2 or 3, email is required
        elif data['type'] in [2, 3]:
            if not data.get('username'):
                raise serializers.ValidationError("Email is required for type 2 and type 3 login.")
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
        fields = ['id', 'username', 'email']  # Customize as needed

class PostCommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)  # Nested user details
    parent = serializers.PrimaryKeyRelatedField(queryset=Post_comment.objects.all(), allow_null=True)

    class Meta:
        model = Post_comment
        fields = ['id', 'user', 'post', 'parent', 'comment', 'date_created', 'replies']
        # Changed 'post_id' to 'post' and 'parent_id' to 'parent' for better representation

    def get_replies(self, obj):
        # Fetch replies where the parent_id is the current comment's id
        if obj.replies.exists():
            return PostCommentSerializer(obj.replies.all(), many=True).data
        return []

class PostSerializer(serializers.ModelSerializer):
    comments = PostCommentSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)  # Nested user details

    class Meta:
        model = Post
        fields = ['id', 'user', 'title', 'description', 'image', 'date_created', 'comments']


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