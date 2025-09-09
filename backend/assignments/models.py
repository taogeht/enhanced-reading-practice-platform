from django.db import models
from django.conf import settings
from stories.models import Story
import uuid


class Assignment(models.Model):
    """
    Model for teacher-created reading assignments.
    """
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    class_assigned = models.ForeignKey(
        'authentication.Class',
        on_delete=models.CASCADE,
        related_name='assignments',
        null=True,
        blank=True,
        help_text="Class this assignment is assigned to"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    assignment_code = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="Unique code students use to access assignment"
    )
    due_date = models.DateTimeField(null=True, blank=True)
    max_attempts = models.PositiveIntegerField(
        default=3,
        help_text="Maximum number of recording attempts per student"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.teacher.username}"


class StudentAssignment(models.Model):
    """
    Model to track which students are assigned to which assignments.
    """
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='student_assignments'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_assignments'
    )
    attempts_used = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['assignment', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"
    
    @property
    def is_completed(self):
        return self.completed_at is not None
    
    @property
    def can_attempt(self):
        return self.attempts_used < self.assignment.max_attempts
