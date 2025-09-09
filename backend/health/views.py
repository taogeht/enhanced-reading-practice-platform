"""
Health check endpoints for monitoring and deployment
"""

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import time
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Basic health check endpoint for load balancers
    """
    health_status = {
        'status': 'healthy',
        'timestamp': int(time.time()),
        'version': '1.0.0',
        'checks': {}
    }
    
    try:
        # Database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                health_status['checks']['database'] = 'healthy'
            else:
                health_status['checks']['database'] = 'unhealthy'
                health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['database'] = 'unhealthy'
        health_status['status'] = 'unhealthy'
        logger.error(f"Database health check failed: {e}")
    
    # Cache check
    try:
        test_key = f'health_check_{int(time.time())}'
        cache.set(test_key, 'ok', 10)
        if cache.get(test_key) == 'ok':
            health_status['checks']['cache'] = 'healthy'
            cache.delete(test_key)
        else:
            health_status['checks']['cache'] = 'unhealthy'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['cache'] = 'unhealthy'
        health_status['status'] = 'unhealthy'
        logger.error(f"Cache health check failed: {e}")
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def detailed_health_check(request):
    """
    Detailed health check endpoint with comprehensive system status
    """
    health_status = {
        'status': 'healthy',
        'timestamp': int(time.time()),
        'version': '1.0.0',
        'environment': 'development',  # This should be set via environment variable
        'checks': {},
        'metrics': {}
    }
    
    # Database health and metrics
    try:
        with connection.cursor() as cursor:
            # Basic connectivity test
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result and result[0] == 1:
                health_status['checks']['database'] = 'healthy'
                
                # Get database metrics
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins + n_tup_upd + n_tup_del as total_operations
                    FROM pg_stat_user_tables 
                    ORDER BY total_operations DESC 
                    LIMIT 5
                """)
                
                table_stats = cursor.fetchall()
                health_status['metrics']['database'] = {
                    'connection_status': 'connected',
                    'top_active_tables': [
                        {'schema': row[0], 'table': row[1], 'operations': row[2]}
                        for row in table_stats
                    ]
                }
            else:
                health_status['checks']['database'] = 'unhealthy'
                health_status['status'] = 'unhealthy'
                
    except Exception as e:
        health_status['checks']['database'] = 'unhealthy'
        health_status['status'] = 'unhealthy'
        health_status['metrics']['database'] = {'error': str(e)}
        logger.error(f"Detailed database health check failed: {e}")
    
    # Cache health and metrics
    try:
        test_key = f'detailed_health_check_{int(time.time())}'
        test_value = {'test': 'data', 'timestamp': time.time()}
        
        cache.set(test_key, test_value, 10)
        retrieved_value = cache.get(test_key)
        
        if retrieved_value and retrieved_value.get('test') == 'data':
            health_status['checks']['cache'] = 'healthy'
            cache.delete(test_key)
            
            # Cache metrics would typically come from Redis INFO command
            health_status['metrics']['cache'] = {
                'status': 'operational',
                'test_key_roundtrip': 'success'
            }
        else:
            health_status['checks']['cache'] = 'unhealthy'
            health_status['status'] = 'unhealthy'
            
    except Exception as e:
        health_status['checks']['cache'] = 'unhealthy'
        health_status['status'] = 'unhealthy'
        health_status['metrics']['cache'] = {'error': str(e)}
        logger.error(f"Cache health check failed: {e}")
    
    # Application-specific health checks
    try:
        from authentication.models import User
        from stories.models import Story
        from recordings.models import Recording
        
        # Check if core models are accessible
        user_count = User.objects.count()
        story_count = Story.objects.count()
        recording_count = Recording.objects.count()
        
        health_status['checks']['models'] = 'healthy'
        health_status['metrics']['application'] = {
            'total_users': user_count,
            'total_stories': story_count,
            'total_recordings': recording_count,
            'models_accessible': True
        }
        
    except Exception as e:
        health_status['checks']['models'] = 'unhealthy'
        health_status['status'] = 'unhealthy'
        health_status['metrics']['application'] = {'error': str(e)}
        logger.error(f"Model health check failed: {e}")
    
    # Disk space check (simple)
    try:
        import os
        import shutil
        
        total, used, free = shutil.disk_usage("/")
        disk_usage_percent = (used / total) * 100
        
        if disk_usage_percent < 90:
            health_status['checks']['disk_space'] = 'healthy'
        else:
            health_status['checks']['disk_space'] = 'warning'
            if disk_usage_percent > 95:
                health_status['status'] = 'unhealthy'
        
        health_status['metrics']['disk'] = {
            'total_gb': round(total / (1024**3), 2),
            'used_gb': round(used / (1024**3), 2),
            'free_gb': round(free / (1024**3), 2),
            'usage_percent': round(disk_usage_percent, 2)
        }
        
    except Exception as e:
        health_status['checks']['disk_space'] = 'unknown'
        health_status['metrics']['disk'] = {'error': str(e)}
        logger.error(f"Disk space check failed: {e}")
    
    # Memory usage check (basic)
    try:
        import psutil
        memory = psutil.virtual_memory()
        
        if memory.percent < 90:
            health_status['checks']['memory'] = 'healthy'
        else:
            health_status['checks']['memory'] = 'warning'
            if memory.percent > 95:
                health_status['status'] = 'unhealthy'
        
        health_status['metrics']['memory'] = {
            'total_gb': round(memory.total / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2),
            'usage_percent': memory.percent
        }
        
    except ImportError:
        # psutil not available, skip memory check
        health_status['checks']['memory'] = 'not_available'
    except Exception as e:
        health_status['checks']['memory'] = 'error'
        health_status['metrics']['memory'] = {'error': str(e)}
        logger.error(f"Memory check failed: {e}")
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return Response(health_status, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Kubernetes-style readiness probe
    Checks if the application is ready to serve traffic
    """
    ready_status = {
        'ready': True,
        'timestamp': int(time.time()),
        'checks': {}
    }
    
    # Database readiness
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            ready_status['checks']['database'] = True
    except Exception as e:
        ready_status['checks']['database'] = False
        ready_status['ready'] = False
        logger.error(f"Database readiness check failed: {e}")
    
    # Cache readiness
    try:
        cache.set('readiness_check', 'ready', 5)
        if cache.get('readiness_check') == 'ready':
            ready_status['checks']['cache'] = True
        else:
            ready_status['checks']['cache'] = False
            ready_status['ready'] = False
    except Exception as e:
        ready_status['checks']['cache'] = False
        ready_status['ready'] = False
        logger.error(f"Cache readiness check failed: {e}")
    
    status_code = 200 if ready_status['ready'] else 503
    return Response(ready_status, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """
    Kubernetes-style liveness probe
    Checks if the application is alive and should not be restarted
    """
    alive_status = {
        'alive': True,
        'timestamp': int(time.time())
    }
    
    # Very basic check - if we can respond, we're alive
    # Could add more sophisticated checks like deadlock detection
    
    return Response(alive_status, status=200)