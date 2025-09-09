"""
Performance monitoring middleware for tracking request performance
"""

import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings
import json

logger = logging.getLogger(__name__)


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor API performance and collect metrics
    """
    
    def process_request(self, request):
        """Start timing the request"""
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log request performance"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            self.log_performance(request, response, duration)
        
        return response
    
    def log_performance(self, request, response, duration):
        """Log performance metrics"""
        # Convert duration to milliseconds
        duration_ms = duration * 1000
        
        # Create performance record
        perf_data = {
            'path': request.path,
            'method': request.method,
            'status_code': response.status_code,
            'duration_ms': round(duration_ms, 2),
            'timestamp': time.time(),
            'user_id': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
            'user_type': request.user.user_type if hasattr(request, 'user') and hasattr(request.user, 'user_type') else None,
        }
        
        # Log slow requests (> 1 second)
        if duration_ms > 1000:
            logger.warning(f"Slow request: {request.method} {request.path} - {duration_ms:.2f}ms")
        
        # Store in cache for recent performance data
        cache_key = f"perf_data_{int(time.time())}"
        cache.set(cache_key, perf_data, 300)  # Store for 5 minutes
        
        # Update running averages
        self.update_performance_metrics(request.path, duration_ms, response.status_code)
    
    def update_performance_metrics(self, path, duration_ms, status_code):
        """Update running performance metrics"""
        # Get or create metrics for this endpoint
        metrics_key = f"perf_metrics_{path.replace('/', '_')}"
        metrics = cache.get(metrics_key, {
            'total_requests': 0,
            'total_duration': 0,
            'avg_duration': 0,
            'min_duration': float('inf'),
            'max_duration': 0,
            'error_count': 0,
            'success_count': 0,
        })
        
        # Update metrics
        metrics['total_requests'] += 1
        metrics['total_duration'] += duration_ms
        metrics['avg_duration'] = metrics['total_duration'] / metrics['total_requests']
        metrics['min_duration'] = min(metrics['min_duration'], duration_ms)
        metrics['max_duration'] = max(metrics['max_duration'], duration_ms)
        
        if status_code >= 400:
            metrics['error_count'] += 1
        else:
            metrics['success_count'] += 1
        
        # Store updated metrics (expire in 1 hour)
        cache.set(metrics_key, metrics, 3600)


class DatabaseQueryCountMiddleware(MiddlewareMixin):
    """
    Middleware to monitor database query counts per request
    """
    
    def process_request(self, request):
        """Reset query count"""
        from django.db import connection
        connection.queries_log.clear()
        return None
    
    def process_response(self, request, response):
        """Log query count"""
        from django.db import connection
        
        query_count = len(connection.queries)
        query_time = sum(float(query['time']) for query in connection.queries)
        
        # Log excessive queries (> 10 queries per request)
        if query_count > 10:
            logger.warning(
                f"High query count: {request.method} {request.path} - "
                f"{query_count} queries, {query_time:.3f}s total"
            )
        
        # Store query metrics
        if hasattr(request, 'start_time'):
            query_data = {
                'path': request.path,
                'method': request.method,
                'query_count': query_count,
                'query_time': round(query_time * 1000, 2),  # Convert to ms
                'timestamp': time.time(),
            }
            
            cache_key = f"query_data_{int(time.time())}"
            cache.set(cache_key, query_data, 300)  # Store for 5 minutes
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware
    """
    
    def process_request(self, request):
        """Check rate limits"""
        if not hasattr(settings, 'RATE_LIMIT_ENABLED') or not settings.RATE_LIMIT_ENABLED:
            return None
        
        # Skip rate limiting for admin users
        if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_admin:
            return None
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Check rate limit (100 requests per minute per IP)
        rate_limit_key = f"rate_limit_{client_ip}"
        current_requests = cache.get(rate_limit_key, 0)
        
        if current_requests >= 100:
            from django.http import JsonResponse
            return JsonResponse(
                {'error': 'Rate limit exceeded. Please try again later.'},
                status=429
            )
        
        # Increment counter
        cache.set(rate_limit_key, current_requests + 1, 60)  # 1 minute window
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip