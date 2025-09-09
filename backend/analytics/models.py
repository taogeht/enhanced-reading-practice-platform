from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class StudentFlag(models.Model):
    """
    Model for tracking students who may need attention based on automated analysis.
    """
    FLAG_TYPES = [
        ('low_submission', 'Low Submission Rate'),
        ('short_recordings', 'Consistently Short Recordings'),
        ('low_performance', 'Low Performance Scores'),
        ('missed_deadlines', 'Frequently Misses Deadlines'),
        ('no_improvement', 'No Progress Improvement'),
        ('technical_issues', 'Repeated Technical Issues'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('urgent', 'Urgent Attention Required'),
    ]
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='flags'
    )
    flag_type = models.CharField(max_length=20, choices=FLAG_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    description = models.TextField(help_text="Detailed description of the issue")
    auto_generated = models.BooleanField(default=True)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_flags'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['student', 'flag_type', 'is_resolved']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.get_flag_type_display()} ({self.severity})"
    
    def resolve(self, resolved_by, notes=""):
        """Mark flag as resolved"""
        self.is_resolved = True
        self.resolved_by = resolved_by
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save()


class StudentAnalytics(models.Model):
    """
    Model for storing computed analytics about student performance.
    """
    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    
    # Assignment metrics
    total_assignments = models.IntegerField(default=0)
    completed_assignments = models.IntegerField(default=0)
    submission_rate = models.FloatField(default=0.0)  # Percentage
    
    # Recording metrics
    total_recordings = models.IntegerField(default=0)
    avg_recording_duration = models.FloatField(default=0.0)  # Seconds
    avg_fluency_score = models.FloatField(default=0.0)
    avg_accuracy_score = models.FloatField(default=0.0)
    overall_grade_distribution = models.JSONField(default=dict)  # {'excellent': 5, 'good': 10, 'needs_practice': 2}
    
    # Engagement metrics
    days_since_last_submission = models.IntegerField(default=0)
    avg_time_to_complete = models.FloatField(default=0.0)  # Hours
    missed_deadline_count = models.IntegerField(default=0)
    
    # Progress tracking
    improvement_trend = models.CharField(
        max_length=20,
        choices=[
            ('improving', 'Improving'),
            ('stable', 'Stable'),
            ('declining', 'Declining'),
            ('insufficient_data', 'Insufficient Data')
        ],
        default='insufficient_data'
    )
    
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics for {self.student.get_full_name()}"
    
    @property
    def completion_rate(self):
        """Calculate assignment completion rate as percentage"""
        if self.total_assignments == 0:
            return 0
        return (self.completed_assignments / self.total_assignments) * 100
    
    @property
    def needs_attention(self):
        """Check if student needs attention based on metrics"""
        return (
            self.submission_rate < 70 or  # Less than 70% submission rate
            self.days_since_last_submission > 7 or  # No submission in a week
            self.avg_fluency_score < 2.0 or  # Low fluency scores
            self.missed_deadline_count > 2  # More than 2 missed deadlines
        )


class SystemAnalytics(models.Model):
    """
    Model for tracking system-wide analytics and metrics.
    """
    date = models.DateField(unique=True)
    
    # User metrics
    total_students = models.IntegerField(default=0)
    active_students = models.IntegerField(default=0)  # Students who submitted in last 7 days
    total_teachers = models.IntegerField(default=0)
    active_teachers = models.IntegerField(default=0)
    
    # Content metrics
    total_assignments_created = models.IntegerField(default=0)
    total_recordings_submitted = models.IntegerField(default=0)
    total_recordings_reviewed = models.IntegerField(default=0)
    
    # Performance metrics
    avg_response_time = models.FloatField(default=0.0)  # Average API response time in ms
    storage_used_gb = models.FloatField(default=0.0)
    audio_files_generated = models.IntegerField(default=0)
    
    # Quality metrics
    avg_student_satisfaction = models.FloatField(default=0.0)
    system_uptime_percentage = models.FloatField(default=100.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"System Analytics for {self.date}"