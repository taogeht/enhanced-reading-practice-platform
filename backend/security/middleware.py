"""
Security middleware for the reading platform
"""

import json
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings
from django.middleware.csrf import get_token
import re
import time

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses
    """
    
    def process_response(self, request, response):
        """Add security headers"""
        
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Force HTTPS (in production)
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy
        csp_policy = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Allow React
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: blob:",
            "media-src 'self' blob:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response['Content-Security-Policy'] = '; '.join(csp_policy)
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Feature Policy / Permissions Policy
        permissions_policy = [
            "camera=()",
            "microphone=(self)",  # Allow microphone for recordings
            "geolocation=()",
            "payment=()",
            "usb=()"
        ]
        response['Permissions-Policy'] = ', '.join(permissions_policy)
        
        return response


class RequestValidationMiddleware(MiddlewareMixin):
    """
    Validate incoming requests for security threats
    """
    
    def process_request(self, request):
        """Validate request for security issues"""
        
        # Check for suspicious user agents
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        suspicious_agents = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'nessus',
            'burpsuite', 'owasp', 'zap', 'w3af', 'skipfish'
        ]
        
        for agent in suspicious_agents:
            if agent.lower() in user_agent.lower():
                logger.warning(f"Suspicious user agent detected: {user_agent}")
                return JsonResponse({'error': 'Request blocked'}, status=403)
        
        # Check for suspicious headers
        suspicious_headers = [
            'HTTP_X_FORWARDED_HOST',
            'HTTP_X_ORIGINAL_URL', 
            'HTTP_X_REWRITE_URL'
        ]
        
        for header in suspicious_headers:
            if header in request.META:
                value = request.META[header]
                if self._contains_suspicious_content(value):
                    logger.warning(f"Suspicious header {header}: {value}")
                    return JsonResponse({'error': 'Request blocked'}, status=403)
        
        # Validate request path
        if self._validate_request_path(request.path) is False:
            return JsonResponse({'error': 'Invalid request path'}, status=400)
        
        # Check request size
        if hasattr(request, 'body') and len(request.body) > 10 * 1024 * 1024:  # 10MB limit
            logger.warning(f"Large request body detected: {len(request.body)} bytes")
            return JsonResponse({'error': 'Request too large'}, status=413)
        
        return None
    
    def _contains_suspicious_content(self, content):
        """Check if content contains suspicious patterns"""
        suspicious_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'vbscript:',
            r'data:text/html',
            r'(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b)',
            r'(\.\.\/){2,}',  # Path traversal
            r'%2e%2e%2f',     # URL encoded path traversal
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def _validate_request_path(self, path):
        """Validate request path for security issues"""
        # Check for path traversal
        if '../' in path or '..\\' in path:
            logger.warning(f"Path traversal attempt: {path}")
            return False
        
        # Check for suspicious file extensions
        suspicious_extensions = ['.php', '.asp', '.jsp', '.cgi', '.pl', '.py', '.rb']
        for ext in suspicious_extensions:
            if path.endswith(ext):
                logger.warning(f"Suspicious file extension in path: {path}")
                return False
        
        return True


class APISecurityMiddleware(MiddlewareMixin):
    """
    API-specific security middleware
    """
    
    def process_request(self, request):
        """Process API security for requests"""
        
        # Only apply to API endpoints
        if not request.path.startswith('/api/'):
            return None
        
        # Rate limiting per endpoint
        if self._is_rate_limited(request):
            return JsonResponse({
                'error': 'Rate limit exceeded for this endpoint'
            }, status=429)
        
        # Validate Content-Type for POST/PUT requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.META.get('CONTENT_TYPE', '')
            if not content_type.startswith(('application/json', 'multipart/form-data')):
                return JsonResponse({
                    'error': 'Invalid Content-Type'
                }, status=400)
        
        # Check for API key if required (for external APIs)
        if self._requires_api_key(request.path):
            api_key = request.META.get('HTTP_X_API_KEY')
            if not api_key or not self._validate_api_key(api_key):
                return JsonResponse({
                    'error': 'Invalid or missing API key'
                }, status=401)
        
        return None
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Validate request data before view processing"""
        
        if not request.path.startswith('/api/'):
            return None
        
        # Validate JSON data
        if request.method in ['POST', 'PUT', 'PATCH'] and request.content_type == 'application/json':
            try:
                if hasattr(request, 'body') and request.body:
                    data = json.loads(request.body)
                    if not self._validate_json_data(data):
                        return JsonResponse({
                            'error': 'Invalid request data'
                        }, status=400)
            except json.JSONDecodeError:
                return JsonResponse({
                    'error': 'Invalid JSON format'
                }, status=400)
        
        return None
    
    def _is_rate_limited(self, request):
        """Check if request is rate limited"""
        # Get user identifier
        user_id = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
        else:
            user_id = self._get_client_ip(request)
        
        # Different limits for different endpoints
        endpoint_limits = {
            '/api/auth/login/': (5, 300),      # 5 attempts per 5 minutes
            '/api/auth/register/': (3, 600),   # 3 attempts per 10 minutes
            '/api/recordings/': (50, 3600),    # 50 recordings per hour
            'default': (100, 3600)             # 100 requests per hour default
        }
        
        # Find matching limit
        limit_info = endpoint_limits.get('default')
        for endpoint, limits in endpoint_limits.items():
            if endpoint != 'default' and request.path.startswith(endpoint):
                limit_info = limits
                break
        
        max_requests, window = limit_info
        
        # Create cache key
        cache_key = f"rate_limit_{user_id}_{request.path.replace('/', '_')}"
        
        # Get current count
        current_count = cache.get(cache_key, 0)
        
        if current_count >= max_requests:
            return True
        
        # Increment counter
        cache.set(cache_key, current_count + 1, window)
        return False
    
    def _requires_api_key(self, path):
        """Check if path requires API key"""
        api_key_paths = [
            '/api/external/',
            '/api/webhook/',
        ]
        
        return any(path.startswith(api_path) for api_path in api_key_paths)
    
    def _validate_api_key(self, api_key):
        """Validate API key"""
        # In production, this would validate against a database
        # For now, just check if it matches a configured key
        valid_keys = getattr(settings, 'API_KEYS', [])
        return api_key in valid_keys
    
    def _validate_json_data(self, data, max_depth=5, current_depth=0):
        """Validate JSON data structure"""
        if current_depth > max_depth:
            return False
        
        if isinstance(data, dict):
            # Check for suspicious keys
            suspicious_keys = ['__proto__', 'constructor', 'prototype']
            for key in data.keys():
                if key in suspicious_keys:
                    return False
                if not isinstance(key, str) or len(key) > 100:
                    return False
            
            # Recursively validate values
            for value in data.values():
                if not self._validate_json_data(value, max_depth, current_depth + 1):
                    return False
        
        elif isinstance(data, list):
            # Check list length
            if len(data) > 1000:
                return False
            
            # Recursively validate items
            for item in data:
                if not self._validate_json_data(item, max_depth, current_depth + 1):
                    return False
        
        elif isinstance(data, str):
            # Check string length and content
            if len(data) > 10000:
                return False
            
            # Check for suspicious patterns
            suspicious_patterns = [
                r'<script[^>]*>',
                r'javascript:',
                r'(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b)',
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    return False
        
        return True
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CSRFExemptionMiddleware(MiddlewareMixin):
    """
    Handle CSRF exemptions for specific API endpoints while maintaining security
    """
    
    def process_request(self, request):
        """Handle CSRF for API requests"""
        
        # API endpoints that should be exempt from CSRF
        csrf_exempt_paths = [
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/webhook/',
        ]
        
        # Check if path should be CSRF exempt
        is_exempt = any(request.path.startswith(path) for path in csrf_exempt_paths)
        
        if is_exempt:
            # Mark request as CSRF exempt
            setattr(request, '_dont_enforce_csrf_checks', True)
        
        return None
    
    def process_response(self, request, response):
        """Add CSRF token to response headers for SPA"""
        
        if request.path.startswith('/api/') and hasattr(request, 'user'):
            # Add CSRF token to response headers for authenticated users
            if request.user.is_authenticated:
                csrf_token = get_token(request)
                response['X-CSRFToken'] = csrf_token
        
        return response


class LoginAttemptMiddleware(MiddlewareMixin):
    """
    Track and limit login attempts to prevent brute force attacks
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Monitor login attempts"""
        
        if request.path != '/api/auth/login/' or request.method != 'POST':
            return None
        
        client_ip = self._get_client_ip(request)
        
        # Check if IP is temporarily blocked
        block_key = f"login_blocked_{client_ip}"
        if cache.get(block_key):
            return JsonResponse({
                'error': 'Too many failed login attempts. Try again later.'
            }, status=429)
        
        return None
    
    def process_response(self, request, response):
        """Track failed login attempts"""
        
        if request.path != '/api/auth/login/' or request.method != 'POST':
            return response
        
        client_ip = self._get_client_ip(request)
        attempts_key = f"login_attempts_{client_ip}"
        
        # If login failed (status 400 or 401)
        if response.status_code in [400, 401]:
            attempts = cache.get(attempts_key, 0) + 1
            cache.set(attempts_key, attempts, 900)  # 15 minutes
            
            # Block after 5 failed attempts
            if attempts >= 5:
                cache.set(f"login_blocked_{client_ip}", True, 1800)  # 30 minutes
                logger.warning(f"IP {client_ip} blocked due to excessive login attempts")
        
        # If login successful, clear attempts
        elif response.status_code == 200:
            cache.delete(attempts_key)
        
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip