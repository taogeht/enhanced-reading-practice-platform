from django.db import models


class Story(models.Model):
    """
    Model for educational stories that students will read.
    """
    GRADE_LEVEL_CHOICES = [
        ('K', 'Kindergarten'),
        ('1', 'Grade 1'),
        ('2', 'Grade 2'),
        ('3', 'Grade 3'),
        ('4', 'Grade 4'),
        ('5', 'Grade 5'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="The text content of the story")
    grade_level = models.CharField(
        max_length=2,
        choices=GRADE_LEVEL_CHOICES,
        help_text="Target grade level"
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium'
    )
    word_count = models.PositiveIntegerField(default=0)
    estimated_reading_time = models.PositiveIntegerField(
        default=0,
        help_text="Estimated reading time in seconds"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['grade_level', 'title']
        verbose_name_plural = "Stories"
    
    def __str__(self):
        return f"{self.title} (Grade {self.grade_level})"


class AudioFile(models.Model):
    """
    Model for pre-generated TTS audio files for stories.
    """
    VOICE_CHOICES = [
        ('female_1', 'Female Voice 1'),
        ('female_2', 'Female Voice 2'),
        ('male_1', 'Male Voice 1'),
        ('male_2', 'Male Voice 2'),
    ]
    
    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name='audio_files'
    )
    voice_type = models.CharField(
        max_length=20,
        choices=VOICE_CHOICES,
        default='female_1'
    )
    file_path = models.CharField(
        max_length=500,
        help_text="Path to the audio file in storage"
    )
    file_size = models.PositiveIntegerField(
        default=0,
        help_text="File size in bytes"
    )
    duration = models.PositiveIntegerField(
        default=0,
        help_text="Audio duration in seconds"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['story', 'voice_type']
    
    def __str__(self):
        return f"{self.story.title} - {self.get_voice_type_display()}"
