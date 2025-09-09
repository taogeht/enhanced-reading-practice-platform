"""
Database and query optimizations for the reading platform
"""

from django.db import models
from django.core.cache import cache
from django.db.models import Prefetch, Count, Avg
from functools import wraps
import hashlib
import json


def cache_result(timeout=300, key_prefix=''):
    """
    Decorator to cache function results
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{key_prefix}_{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Compute and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    return decorator


class OptimizedQueryMixin:
    """
    Mixin to provide optimized queries for models
    """
    
    @classmethod
    def get_optimized_queryset(cls):
        """
        Get queryset with optimized select_related and prefetch_related
        """
        queryset = cls.objects.all()
        
        # Add common optimizations based on model
        if hasattr(cls, '_meta'):
            # Automatically add select_related for ForeignKey fields
            foreign_keys = [
                field.name for field in cls._meta.get_fields() 
                if isinstance(field, models.ForeignKey)
            ]
            if foreign_keys:
                queryset = queryset.select_related(*foreign_keys)
            
            # Automatically add prefetch_related for ManyToMany fields
            many_to_many = [
                field.name for field in cls._meta.get_fields() 
                if isinstance(field, models.ManyToManyField)
            ]
            if many_to_many:
                queryset = queryset.prefetch_related(*many_to_many)
        
        return queryset


class QueryOptimizer:
    """
    Utility class for query optimizations
    """
    
    @staticmethod
    def optimize_user_queries():
        """
        Optimize common user-related queries
        """
        from authentication.models import User, Class
        
        # Pre-cache active user counts
        active_students = User.objects.filter(user_type='student', is_active=True).count()
        active_teachers = User.objects.filter(user_type='teacher', is_active=True).count()
        
        cache.set('active_students_count', active_students, 600)  # 10 minutes
        cache.set('active_teachers_count', active_teachers, 600)
        
        # Pre-cache class statistics
        class_stats = Class.objects.filter(is_active=True).aggregate(
            total_classes=Count('id'),
            total_students_in_classes=Count('students', distinct=True)
        )
        cache.set('class_statistics', class_stats, 600)
    
    @staticmethod
    def optimize_recording_queries():
        """
        Optimize recording-related queries
        """
        from recordings.models import Recording
        
        # Pre-cache recording statistics
        recording_stats = Recording.objects.aggregate(
            total_recordings=Count('id'),
            reviewed_recordings=Count('id', filter=models.Q(status='reviewed')),
            pending_recordings=Count('id', filter=models.Q(status='pending')),
            avg_duration=Avg('duration'),
        )
        cache.set('recording_statistics', recording_stats, 600)
        
        # Pre-cache performance metrics
        performance_stats = Recording.objects.filter(status='reviewed').aggregate(
            avg_fluency=Avg('fluency_score'),
            avg_accuracy=Avg('accuracy_score'),
        )
        cache.set('performance_statistics', performance_stats, 600)
    
    @staticmethod
    def optimize_assignment_queries():
        """
        Optimize assignment-related queries
        """
        from assignments.models import Assignment
        
        # Pre-cache assignment statistics
        assignment_stats = Assignment.objects.aggregate(
            total_assignments=Count('id'),
            active_assignments=Count('id', filter=models.Q(is_active=True)),
        )
        cache.set('assignment_statistics', assignment_stats, 600)
    
    @staticmethod
    def run_all_optimizations():
        """
        Run all query optimizations
        """
        QueryOptimizer.optimize_user_queries()
        QueryOptimizer.optimize_recording_queries()
        QueryOptimizer.optimize_assignment_queries()


# Optimized model managers
class OptimizedUserManager(models.Manager):
    """
    Optimized manager for User model
    """
    
    def get_students_with_analytics(self):
        """
        Get students with prefetched analytics data
        """
        return self.filter(user_type='student').prefetch_related(
            'analytics',
            'flags',
            'recordings'
        )
    
    def get_teachers_with_classes(self):
        """
        Get teachers with prefetched class data
        """
        return self.filter(user_type='teacher').prefetch_related(
            'classes_teaching__students',
            'classes_teaching__assignments'
        )


class OptimizedRecordingManager(models.Manager):
    """
    Optimized manager for Recording model
    """
    
    def get_for_teacher_review(self, teacher):
        """
        Get recordings optimized for teacher review
        """
        return self.select_related(
            'student',
            'story',
            'assignment'
        ).filter(
            assignment__teacher=teacher,
            status='pending'
        ).order_by('-created_at')
    
    def get_student_progress_data(self, student):
        """
        Get optimized student progress data
        """
        return self.select_related(
            'story',
            'assignment'
        ).filter(
            student=student
        ).order_by('created_at')


# Database indexing recommendations
DATABASE_INDEXES = {
    'authentication_user': [
        ['user_type', 'is_active'],  # For filtering users by type and status
        ['email'],  # For login lookups
        ['username'],  # For username lookups
    ],
    'recordings_recording': [
        ['student_id', 'status'],  # For student recording queries
        ['assignment_id', 'status'],  # For assignment recording queries
        ['created_at'],  # For chronological queries
        ['status', 'created_at'],  # For status-filtered chronological queries
    ],
    'assignments_assignment': [
        ['teacher_id', 'is_active'],  # For teacher assignment queries
        ['class_assigned_id', 'is_active'],  # For class assignment queries
        ['due_date'],  # For deadline queries
    ],
    'analytics_studentflag': [
        ['student_id', 'is_resolved'],  # For student flag queries
        ['severity', 'is_resolved'],  # For priority flag queries
        ['created_at'],  # For recent flag queries
    ],
    'analytics_studentanalytics': [
        ['student_id'],  # For student analytics lookups
        ['improvement_trend'],  # For trend analysis
        ['submission_rate'],  # For performance queries
    ]
}


def get_database_optimization_script():
    """
    Generate SQL script for database optimizations
    """
    sql_commands = [
        "-- Database Optimization Script for Reading Platform",
        "-- Generated for improved performance",
        "",
        "-- Add database indexes for better query performance"
    ]
    
    for table, indexes in DATABASE_INDEXES.items():
        sql_commands.append(f"\n-- Indexes for {table}")
        for i, columns in enumerate(indexes):
            index_name = f"idx_{table}_{i+1}_{'_'.join(columns)}"
            column_list = ', '.join(columns)
            sql_commands.append(
                f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column_list});"
            )
    
    # Add query optimization settings
    sql_commands.extend([
        "",
        "-- PostgreSQL specific optimizations",
        "-- Update table statistics",
        "ANALYZE;",
        "",
        "-- Configure query planner",
        "SET random_page_cost = 1.1;  -- For SSD storage",
        "SET effective_cache_size = '1GB';  -- Adjust based on available RAM",
        "SET work_mem = '64MB';  -- For complex queries",
        "",
        "-- Enable query plan caching",
        "SET shared_preload_libraries = 'pg_stat_statements';",
    ])
    
    return '\n'.join(sql_commands)


# Performance testing utilities
class PerformanceTester:
    """
    Utility class for performance testing
    """
    
    @staticmethod
    def test_api_endpoints():
        """
        Test common API endpoints for performance
        """
        import requests
        import time
        
        base_url = "http://localhost:8000/api"
        
        endpoints_to_test = [
            "/stories/",
            "/assignments/student/",
            "/recordings/student/",
            "/auth/classes/",
            "/analytics/dashboard-summary/",
        ]
        
        results = []
        
        for endpoint in endpoints_to_test:
            start_time = time.time()
            try:
                # Note: This would need authentication in a real test
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                end_time = time.time()
                
                results.append({
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'response_time_ms': round((end_time - start_time) * 1000, 2),
                    'success': response.status_code < 400
                })
            except Exception as e:
                results.append({
                    'endpoint': endpoint,
                    'error': str(e),
                    'success': False
                })
        
        return results
    
    @staticmethod
    def test_database_queries():
        """
        Test common database queries for performance
        """
        import time
        from django.db import connection
        
        test_results = []
        
        # Test queries
        queries_to_test = [
            ("User count query", "SELECT COUNT(*) FROM authentication_user"),
            ("Recording stats", "SELECT COUNT(*), AVG(duration) FROM recordings_recording"),
            ("Class with students", """
                SELECT c.name, COUNT(cm.student_id) 
                FROM authentication_class c 
                LEFT JOIN authentication_classmembership cm ON c.id = cm.class_id 
                GROUP BY c.id, c.name
            """),
        ]
        
        for name, query in queries_to_test:
            start_time = time.time()
            
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                
            end_time = time.time()
            
            test_results.append({
                'query_name': name,
                'execution_time_ms': round((end_time - start_time) * 1000, 2),
                'result_count': len(result) if result else 0
            })
        
        return test_results