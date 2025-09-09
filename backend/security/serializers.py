"""
Secure serializers with enhanced validation
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .validators import SecurityValidator, InputSanitizer


class SecureLoginSerializer(serializers.Serializer):
    """
    Enhanced login serializer with security validations
    """
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    
    def validate_username(self, value):
        """Validate and sanitize username"""
        SecurityValidator.validate_user_input(value, 'username', max_length=150)
        return InputSanitizer.sanitize_username(value)
    
    def validate_password(self, value):
        """Validate password"""
        SecurityValidator.validate_user_input(value, 'password', max_length=128)
        return value
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            
            if not user.is_active:
                raise serializers.ValidationError('Account is disabled')
            
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return attrs


class SecureRegistrationSerializer(serializers.Serializer):
    """
    Enhanced registration serializer with security validations
    """
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    user_type = serializers.ChoiceField(choices=['student', 'teacher'])
    school = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_username(self, value):
        """Validate and sanitize username"""
        SecurityValidator.validate_user_input(value, 'username', max_length=150)
        sanitized = InputSanitizer.sanitize_username(value)
        
        # Check if username already exists
        from authentication.models import User
        if User.objects.filter(username=sanitized).exists():
            raise serializers.ValidationError('Username already exists')
        
        return sanitized
    
    def validate_email(self, value):
        """Validate and sanitize email"""
        sanitized = InputSanitizer.sanitize_email(value)
        
        # Check if email already exists
        from authentication.models import User
        if User.objects.filter(email=sanitized).exists():
            raise serializers.ValidationError('Email already registered')
        
        return sanitized
    
    def validate_password(self, value):
        """Validate password strength"""
        SecurityValidator.validate_user_input(value, 'password', max_length=128)
        
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        
        return value
    
    def validate_first_name(self, value):
        """Validate and sanitize first name"""
        SecurityValidator.validate_user_input(value, 'first_name', max_length=30)
        return InputSanitizer.sanitize_text_field(value, max_length=30)
    
    def validate_last_name(self, value):
        """Validate and sanitize last name"""
        SecurityValidator.validate_user_input(value, 'last_name', max_length=30)
        return InputSanitizer.sanitize_text_field(value, max_length=30)
    
    def validate_school(self, value):
        """Validate and sanitize school name"""
        if value:
            SecurityValidator.validate_user_input(value, 'school', max_length=100)
            return InputSanitizer.sanitize_text_field(value, max_length=100)
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password != password_confirm:
            raise serializers.ValidationError('Passwords do not match')
        
        # Remove password_confirm from validated data
        attrs.pop('password_confirm', None)
        
        return attrs


class SecurePasswordChangeSerializer(serializers.Serializer):
    """
    Secure password change serializer
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def validate_old_password(self, value):
        """Validate old password"""
        SecurityValidator.validate_user_input(value, 'old_password', max_length=128)
        
        if not self.user or not self.user.check_password(value):
            raise serializers.ValidationError('Invalid current password')
        
        return value
    
    def validate_new_password(self, value):
        """Validate new password"""
        SecurityValidator.validate_user_input(value, 'new_password', max_length=128)
        
        try:
            validate_password(value, user=self.user)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        old_password = attrs.get('old_password')
        
        if new_password != new_password_confirm:
            raise serializers.ValidationError('New passwords do not match')
        
        if old_password == new_password:
            raise serializers.ValidationError('New password must be different from current password')
        
        # Remove confirm field from validated data
        attrs.pop('new_password_confirm', None)
        
        return attrs


class SecureFileUploadSerializer(serializers.Serializer):
    """
    Secure file upload serializer
    """
    file = serializers.FileField()
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_file(self, value):
        """Validate uploaded file"""
        SecurityValidator.validate_file_upload(value)
        return value
    
    def validate_description(self, value):
        """Validate and sanitize description"""
        if value:
            SecurityValidator.validate_user_input(value, 'description', max_length=500)
            return InputSanitizer.sanitize_text_field(value, max_length=500)
        return value


class SecureAudioFileSerializer(serializers.Serializer):
    """
    Secure audio file upload serializer
    """
    audio_file = serializers.FileField()
    title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    
    def validate_audio_file(self, value):
        """Validate audio file"""
        SecurityValidator.validate_audio_file(value)
        return value
    
    def validate_title(self, value):
        """Validate and sanitize title"""
        if value:
            SecurityValidator.validate_user_input(value, 'title', max_length=200)
            return InputSanitizer.sanitize_text_field(value, max_length=200)
        return value


class SecureTextContentSerializer(serializers.Serializer):
    """
    Secure serializer for rich text content
    """
    content = serializers.CharField()
    allow_html = serializers.BooleanField(default=False)
    
    def validate_content(self, value):
        """Validate and sanitize content"""
        SecurityValidator.validate_user_input(value, 'content', max_length=10000)
        
        # Check if HTML is allowed
        allow_html = self.initial_data.get('allow_html', False)
        
        if allow_html:
            return InputSanitizer.sanitize_rich_text(value)
        else:
            return InputSanitizer.sanitize_text_field(value, max_length=10000)
    
    def validate(self, attrs):
        """Process content based on HTML allowance"""
        content = attrs.get('content', '')
        allow_html = attrs.get('allow_html', False)
        
        if allow_html:
            # Additional validation for HTML content
            if len(content) > 50000:  # Larger limit for rich text
                raise serializers.ValidationError('Content too long for HTML format')
        
        return attrs


class SecureSearchSerializer(serializers.Serializer):
    """
    Secure search query serializer
    """
    query = serializers.CharField(max_length=200)
    filters = serializers.DictField(required=False, default=dict)
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)
    
    def validate_query(self, value):
        """Validate search query"""
        SecurityValidator.validate_user_input(value, 'search_query', max_length=200)
        return InputSanitizer.sanitize_text_field(value, max_length=200)
    
    def validate_filters(self, value):
        """Validate search filters"""
        if not isinstance(value, dict):
            raise serializers.ValidationError('Filters must be a dictionary')
        
        # Limit number of filters
        if len(value) > 10:
            raise serializers.ValidationError('Too many filters (maximum 10)')
        
        # Validate each filter
        validated_filters = {}
        for key, filter_value in value.items():
            # Validate filter key
            if not isinstance(key, str) or len(key) > 50:
                raise serializers.ValidationError(f'Invalid filter key: {key}')
            
            SecurityValidator.validate_user_input(key, 'filter_key', max_length=50)
            clean_key = InputSanitizer.sanitize_text_field(key, max_length=50)
            
            # Validate filter value
            if isinstance(filter_value, str):
                SecurityValidator.validate_user_input(filter_value, f'filter_{key}', max_length=100)
                validated_filters[clean_key] = InputSanitizer.sanitize_text_field(filter_value, max_length=100)
            elif isinstance(filter_value, (int, float, bool)):
                validated_filters[clean_key] = filter_value
            elif isinstance(filter_value, list):
                if len(filter_value) > 10:
                    raise serializers.ValidationError(f'Too many values in filter {key} (maximum 10)')
                validated_list = []
                for item in filter_value:
                    if isinstance(item, str):
                        SecurityValidator.validate_user_input(item, f'filter_{key}_item', max_length=100)
                        validated_list.append(InputSanitizer.sanitize_text_field(item, max_length=100))
                    elif isinstance(item, (int, float, bool)):
                        validated_list.append(item)
                    else:
                        raise serializers.ValidationError(f'Invalid filter value type in {key}')
                validated_filters[clean_key] = validated_list
            else:
                raise serializers.ValidationError(f'Invalid filter value type for {key}')
        
        return validated_filters