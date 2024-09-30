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

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

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
    username_or_phone = serializers.CharField(required=False)
    password = serializers.CharField(required=False, write_only=True)
    email = serializers.EmailField(required=False)  # Required for Type 2 or 3
    device_type = serializers.CharField(required=True)
    device_token = serializers.CharField(required=True)

    def validate(self, data):
        # For type 1, username_or_phone and password are required
        if data['type'] == 1:
            if not data.get('username_or_phone') or not data.get('password'):
                raise serializers.ValidationError("Username or phone and password are required for normal login.")
        # For type 2 or 3, email is required
        elif data['type'] in [2, 3]:
            if not data.get('email'):
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
