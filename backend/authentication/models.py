from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser.
    Supports both teachers and students.
    """
    USER_TYPE_CHOICES = [
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('admin', 'Administrator'),
    ]
    
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='student'
    )
    grade_level = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Student's current grade level"
    )
    school = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="School name"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    @property
    def is_teacher(self):
        return self.user_type == 'teacher'
    
    @property
    def is_student(self):
        return self.user_type == 'student'
    
    @property
    def is_admin(self):
        return self.user_type == 'admin'


class Class(models.Model):
    """
    Model for teacher's classes to organize students.
    """
    name = models.CharField(max_length=100, help_text="Class name (e.g., 'Grade 1A', 'Mrs. Smith's Reading Class')")
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='classes_teaching',
        limit_choices_to={'user_type': 'teacher'}
    )
    grade_level = models.CharField(
        max_length=20,
        help_text="Primary grade level for this class"
    )
    school_year = models.CharField(
        max_length=20,
        default="2024-2025",
        help_text="Academic year"
    )
    students = models.ManyToManyField(
        User,
        through='ClassMembership',
        related_name='classes_attending',
        limit_choices_to={'user_type': 'student'}
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Classes"
        unique_together = ['teacher', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.teacher.get_full_name()}"


class ClassMembership(models.Model):
    """
    Through model for Class-Student relationship with additional data.
    """
    class_instance = models.ForeignKey(Class, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'student'})
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['class_instance', 'student']
    
    def __str__(self):
        return f"{self.student.get_full_name()} in {self.class_instance.name}"