from rest_framework import serializers
from .models import StudentFlag, StudentAnalytics, SystemAnalytics


class StudentFlagSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', read_only=True)
    flag_type_display = serializers.CharField(source='get_flag_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = StudentFlag
        fields = [
            'id', 'student', 'student_name', 'student_username',
            'flag_type', 'flag_type_display', 'severity', 'severity_display',
            'description', 'auto_generated', 'is_resolved', 
            'resolved_by', 'resolved_by_name', 'resolved_at', 
            'resolution_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['auto_generated', 'created_at', 'updated_at']


class StudentAnalyticsSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)
    completion_rate = serializers.ReadOnlyField()
    needs_attention = serializers.ReadOnlyField()
    
    class Meta:
        model = StudentAnalytics
        fields = [
            'id', 'student', 'student_name', 'student_username',
            'total_assignments', 'completed_assignments', 'submission_rate',
            'completion_rate', 'total_recordings', 'avg_recording_duration',
            'avg_fluency_score', 'avg_accuracy_score', 'overall_grade_distribution',
            'days_since_last_submission', 'avg_time_to_complete',
            'missed_deadline_count', 'improvement_trend', 'needs_attention',
            'last_updated'
        ]
        read_only_fields = ['last_updated']


class SystemAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemAnalytics
        fields = [
            'id', 'date', 'total_students', 'active_students',
            'total_teachers', 'active_teachers', 'total_assignments_created',
            'total_recordings_submitted', 'total_recordings_reviewed',
            'avg_response_time', 'storage_used_gb', 'audio_files_generated',
            'avg_student_satisfaction', 'system_uptime_percentage', 'created_at'
        ]
        read_only_fields = ['created_at']


class FlagResolutionSerializer(serializers.Serializer):
    """Serializer for resolving student flags"""
    resolution_notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)