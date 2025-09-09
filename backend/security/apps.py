"""
Security app configuration
"""

from django.apps import AppConfig


class SecurityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'security'
    verbose_name = 'Security'
    
    def ready(self):
        """App initialization"""
        # Import signal handlers if needed
        pass