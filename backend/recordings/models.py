from django.db import models
from django.conf import settings
from stories.models import Story


class Recording(models.Model):
    """
    Model for student audio recordings of stories.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('flagged', 'Flagged for Attention'),
    ]
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recordings'
    )
    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name='recordings'
    )
    assignment = models.ForeignKey(
        'assignments.Assignment',
        on_delete=models.CASCADE,
        related_name='recordings',
        null=True,
        blank=True
    )
    file_path = models.CharField(
        max_length=500,
        help_text="Path to the recording file in storage"
    )
    file_size = models.PositiveIntegerField(
        default=0,
        help_text="File size in bytes"
    )
    duration = models.PositiveIntegerField(
        default=0,
        help_text="Recording duration in seconds"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    grade = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Grade assigned by teacher (excellent, good, needs_practice)"
    )
    fluency_score = models.IntegerField(
        blank=True,
        null=True,
        help_text="Fluency score from 1-5"
    )
    accuracy_score = models.IntegerField(
        blank=True,
        null=True,
        help_text="Accuracy score from 1-5"
    )
    teacher_feedback = models.TextField(
        blank=True,
        null=True,
        help_text="Written feedback from teacher"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_recordings'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    attempt_number = models.PositiveIntegerField(
        default=1,
        help_text="Which attempt this is for the student"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.story.title} ({self.created_at.date()})"
