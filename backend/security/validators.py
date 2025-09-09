"""
Security validation utilities for the reading platform
"""

import re
from django.core.exceptions import ValidationError
from django.utils.html import escape
import bleach
import logging

logger = logging.getLogger(__name__)

# Allowed HTML tags for user content
ALLOWED_HTML_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
    'h3', 'h4', 'h5', 'h6'  # Basic formatting only
]

ALLOWED_HTML_ATTRIBUTES = {
    '*': ['class'],  # Only allow class attributes
}

class SecurityValidator:
    """
    Centralized security validation for user inputs
    """
    
    @staticmethod
    def validate_user_input(value, field_name='input', max_length=1000):
        """
        Validate general user input for security issues
        """
        if not isinstance(value, str):
            raise ValidationError(f"Invalid {field_name} type")
        
        # Check length
        if len(value) > max_length:
            raise ValidationError(f"{field_name} too long (max {max_length} characters)")
        
        # Check for potential SQL injection patterns
        sql_patterns = [
            r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)",
            r"(--|\/\*|\*\/)",
            r"(\bOR\b\s+\d+\s*=\s*\d+|\bAND\b\s+\d+\s*=\s*\d+)",
            r"(\bEXEC\b|\bEVAL\b|\bCHAR\b|\bCONCAT\b)"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential SQL injection attempt in {field_name}: {value[:100]}")
                raise ValidationError(f"Invalid characters in {field_name}")
        
        # Check for XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>"
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential XSS attempt in {field_name}: {value[:100]}")
                raise ValidationError(f"Invalid content in {field_name}")
        
        return True
    
    @staticmethod
    def sanitize_html_content(content):
        """
        Sanitize HTML content to prevent XSS
        """
        if not content:
            return content
            
        # Use bleach to clean HTML
        cleaned = bleach.clean(
            content,
            tags=ALLOWED_HTML_TAGS,
            attributes=ALLOWED_HTML_ATTRIBUTES,
            strip=True
        )
        
        return cleaned
    
    @staticmethod
    def validate_file_upload(file_obj, allowed_types=None, max_size_mb=10):
        """
        Validate file uploads for security
        """
        if not file_obj:
            return True
            
        # Check file size
        max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        if file_obj.size > max_size:
            raise ValidationError(f"File too large (max {max_size_mb}MB)")
        
        # Check file extension if types specified
        if allowed_types:
            file_extension = file_obj.name.split('.')[-1].lower()
            if file_extension not in allowed_types:
                raise ValidationError(f"File type not allowed. Allowed: {', '.join(allowed_types)}")
        
        # Check for suspicious file names
        dangerous_patterns = [
            r"\.exe$", r"\.bat$", r"\.cmd$", r"\.com$", r"\.scr$",
            r"\.php$", r"\.asp$", r"\.jsp$", r"\.py$", r"\.pl$"
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, file_obj.name, re.IGNORECASE):
                raise ValidationError("File type not allowed for security reasons")
        
        return True
    
    @staticmethod
    def validate_audio_file(file_obj):
        """
        Specific validation for audio files
        """
        allowed_audio_types = ['mp3', 'wav', 'ogg', 'm4a', 'flac']
        return SecurityValidator.validate_file_upload(
            file_obj, 
            allowed_types=allowed_audio_types,
            max_size_mb=50  # Larger limit for audio files
        )


class InputSanitizer:
    """
    Input sanitization utilities
    """
    
    @staticmethod
    def sanitize_username(username):
        """
        Sanitize username input
        """
        if not username:
            return username
            
        # Remove any HTML/script content
        sanitized = escape(username.strip())
        
        # Only allow alphanumeric, underscore, hyphen, and dot
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '', sanitized)
        
        # Limit length
        sanitized = sanitized[:30]
        
        return sanitized
    
    @staticmethod
    def sanitize_email(email):
        """
        Sanitize email input
        """
        if not email:
            return email
            
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError("Invalid email format")
        
        return escape(email.strip().lower())
    
    @staticmethod
    def sanitize_text_field(text, max_length=500):
        """
        Sanitize general text fields
        """
        if not text:
            return text
            
        # Remove HTML tags but keep the text content
        sanitized = bleach.clean(text, tags=[], strip=True)
        
        # Escape any remaining special characters
        sanitized = escape(sanitized.strip())
        
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def sanitize_rich_text(text):
        """
        Sanitize rich text content (allows some HTML)
        """
        if not text:
            return text
            
        return SecurityValidator.sanitize_html_content(text)


# Custom password validation
class CustomPasswordValidator:
    """
    Enhanced password validation
    """
    
    def validate(self, password, user=None):
        """
        Validate password strength
        """
        errors = []
        
        # Minimum length
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        # Must contain uppercase
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Must contain lowercase
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Must contain number
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        # Must contain special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common patterns
        common_patterns = [
            r'123456', r'password', r'qwerty', r'abc123',
            r'admin', r'user', r'guest', r'test'
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password, re.IGNORECASE):
                errors.append("Password contains common patterns")
                break
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        return (
            "Password must be at least 8 characters long and contain "
            "uppercase, lowercase, number, and special character."
        )


def validate_api_input(data, field_rules=None):
    """
    Validate API input data according to specified rules
    """
    if not field_rules:
        return data
    
    validated_data = {}
    
    for field, value in data.items():
        if field in field_rules:
            rules = field_rules[field]
            
            # Apply validation rules
            if 'required' in rules and rules['required'] and not value:
                raise ValidationError(f"{field} is required")
            
            if 'type' in rules:
                expected_type = rules['type']
                if expected_type == 'string' and not isinstance(value, str):
                    raise ValidationError(f"{field} must be a string")
                elif expected_type == 'int' and not isinstance(value, int):
                    raise ValidationError(f"{field} must be an integer")
                elif expected_type == 'bool' and not isinstance(value, bool):
                    raise ValidationError(f"{field} must be a boolean")
            
            if 'max_length' in rules and isinstance(value, str):
                max_len = rules['max_length']
                if len(value) > max_len:
                    raise ValidationError(f"{field} too long (max {max_len})")
            
            if 'min_value' in rules and isinstance(value, (int, float)):
                min_val = rules['min_value']
                if value < min_val:
                    raise ValidationError(f"{field} must be at least {min_val}")
            
            if 'max_value' in rules and isinstance(value, (int, float)):
                max_val = rules['max_value']
                if value > max_val:
                    raise ValidationError(f"{field} cannot exceed {max_val}")
            
            # Sanitize the value
            if isinstance(value, str):
                SecurityValidator.validate_user_input(value, field)
                if 'allow_html' in rules and rules['allow_html']:
                    validated_data[field] = InputSanitizer.sanitize_rich_text(value)
                else:
                    validated_data[field] = InputSanitizer.sanitize_text_field(value)
            else:
                validated_data[field] = value
        else:
            # Field not in rules, apply basic sanitization
            if isinstance(value, str):
                SecurityValidator.validate_user_input(value, field)
                validated_data[field] = InputSanitizer.sanitize_text_field(value)
            else:
                validated_data[field] = value
    
    return validated_data