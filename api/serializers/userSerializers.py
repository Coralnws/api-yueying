from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import serializers, status
from rest_framework.validators import ValidationError
from ..utils import get_tokens
from ..models.users import CustomUser

"""
Serializer class for registering new user
"""
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(style={'input_type': 'password'}, write_only = True)
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only = True)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'password', 'password2']
        extra_kwargs = { 'password': {'write_only': True}, }
    
    def validate(self, attrs):
        email = attrs.get('email', '')
        username = attrs.get('username', '')
        password = attrs.get('password', '')
        password2 = attrs.get('password2', '')

        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Email is taken.")

        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError("Username is taken.")

        if password != password2:
            raise ValidationError("Password must match.")
        
        # uses validators listed in settings.
        if validate_password(password) is None:
            return super().validate(attrs)
    
    def save(self):
        instance = self.Meta.model(
            email=self.validated_data['email'],
            username=self.validated_data['username']
        )
        password = self.validated_data['password']
        instance.set_password(password)
        instance.save()
        return instance


"""
Serializer class for activate account through email verification
"""
class UserActivateSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()

    def get_token(self, obj):
        return self.context.get('token')

    class Meta:
        model = CustomUser
        fields = ['token']


"""
Serializer class for Request New Password
"""
class RequestPasswordSerializer(serializers.Serializer):
    
    class Meta:
        model = CustomUser
        fields = ['email', 'username']


"""
Serializer class for Reset Password
"""
class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def validate(self, attrs):
        password = attrs.get('password', '')
        password2 = attrs.get('password2', '')
        
        if password != password2:
            raise ValidationError("Password must match.")
        
        # uses validators listed in settings.
        if validate_password(password) is None:
            return super().validate(attrs)
    
    def updatePassword(self):
        password = self.validated_data['password']
        user = self.user
        user.set_password(password)
        user.save(updatedAt=timezone.now())

"""
Serializer class for login
"""
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255, min_length=1)
    password = serializers.CharField(max_length=68, min_length=1, write_only=True)
    tokens = serializers.SerializerMethodField()

    def get_tokens(self, obj):
        user = CustomUser.objects.get(username=obj['username'])
        return get_tokens(user)

    class Meta:
        fields = ['username', 'password', 'tokens']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, attrs):

        username = attrs.get('username', '')
        password = attrs.get('password', '')
        user = authenticate(username=username, password=password)
        
        if not user:
            raise serializers.ValidationError('Invalid credentials, try again')
        elif not user.is_active:
            raise serializers.ValidationError('Account disabled, contact admin')
        elif user.isDeleted:
            raise serializers.ValidationError('Account deleted, contact admin')
        else:
            return {
                'username': user.username,
                'tokens': user.tokens
            }
        return None

"""
Serializer class for logout
"""
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.refresh = attrs['refresh']
        return attrs
    
    def save(self):
        try:
            RefreshToken(self.refresh).blacklist()
        except TokenError:
            raise AuthenticationFailed("Token Error. Might already be blacklisted.")

"""
Serializer for User Detail
"""
class UserDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        # might need to have multiple models later on
        fields = ['id', 'email', 'username', 'firstName', 'lastName', 'about', 'gender', 'profile', 'dob']


"""
Serializer for Create User
"""
class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ['email', 'username']

    def validate(self, attrs):
        email = attrs.get('email', '')
        username = attrs.get('username', '')

        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Email is taken.")

        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError("Username is taken.")

    def save(self):
        instance = self.Meta.model(
            email=self.validated_data['email'],
            username=self.validated_data['username']
        )
        instance.save()
        return instance

"""
Serializer for List All Users
"""
class ListUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'profile']