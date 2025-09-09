from django.contrib import admin
from .models import StudentFlag, StudentAnalytics, SystemAnalytics


@admin.register(StudentFlag)
class StudentFlagAdmin(admin.ModelAdmin):
    list_display = ['student', 'flag_type', 'severity', 'is_resolved', 'created_at']
    list_filter = ['flag_type', 'severity', 'is_resolved', 'auto_generated']
    search_fields = ['student__username', 'student__first_name', 'student__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('student', 'flag_type', 'severity', 'description', 'auto_generated')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_by', 'resolved_at', 'resolution_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudentAnalytics)
class StudentAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['student', 'submission_rate', 'avg_fluency_score', 'improvement_trend', 'last_updated']
    list_filter = ['improvement_trend']
    search_fields = ['student__username', 'student__first_name', 'student__last_name']
    readonly_fields = ['last_updated', 'completion_rate', 'needs_attention']
    
    fieldsets = (
        (None, {
            'fields': ('student',)
        }),
        ('Assignment Metrics', {
            'fields': ('total_assignments', 'completed_assignments', 'submission_rate', 'completion_rate')
        }),
        ('Recording Metrics', {
            'fields': ('total_recordings', 'avg_recording_duration', 'avg_fluency_score', 'avg_accuracy_score', 'overall_grade_distribution')
        }),
        ('Engagement Metrics', {
            'fields': ('days_since_last_submission', 'avg_time_to_complete', 'missed_deadline_count')
        }),
        ('Progress Tracking', {
            'fields': ('improvement_trend', 'needs_attention', 'last_updated')
        }),
    )


@admin.register(SystemAnalytics)
class SystemAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_students', 'active_students', 'total_teachers', 'system_uptime_percentage']
    list_filter = ['date']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (None, {
            'fields': ('date',)
        }),
        ('User Metrics', {
            'fields': ('total_students', 'active_students', 'total_teachers', 'active_teachers')
        }),
        ('Content Metrics', {
            'fields': ('total_assignments_created', 'total_recordings_submitted', 'total_recordings_reviewed')
        }),
        ('Performance Metrics', {
            'fields': ('avg_response_time', 'storage_used_gb', 'audio_files_generated')
        }),
        ('Quality Metrics', {
            'fields': ('avg_student_satisfaction', 'system_uptime_percentage')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )