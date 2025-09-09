#!/usr/bin/env python
"""
Script to create sample data for testing the reading platform
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reading_platform.settings')
django.setup()

from authentication.models import User
from stories.models import Story, AudioFile
from assignments.models import Assignment, StudentAssignment

def create_sample_data():
    print("Creating sample data...")
    
    # Create users
    teacher, created = User.objects.get_or_create(
        username='teacher1',
        defaults={
            'email': 'teacher@example.com',
            'first_name': 'Ms.',
            'last_name': 'Davis',
            'user_type': 'teacher',
            'school': 'Elementary School'
        }
    )
    if created:
        teacher.set_password('password123')
        teacher.save()
        print("Created teacher user")
    
    student, created = User.objects.get_or_create(
        username='student1',
        defaults={
            'email': 'student@example.com',
            'first_name': 'Johnny',
            'last_name': 'Smith',
            'user_type': 'student',
            'grade_level': '1',
            'school': 'Elementary School'
        }
    )
    if created:
        student.set_password('password123')
        student.save()
        print("Created student user")
    
    # Create stories
    story1, created = Story.objects.get_or_create(
        title='The Cat and the Hat',
        defaults={
            'content': 'Once upon a time, there was a cat who wore a red hat. The cat loved to play in the garden.',
            'grade_level': '1',
            'difficulty': 'easy',
            'word_count': 20,
            'estimated_reading_time': 30
        }
    )
    if created:
        print("Created story: The Cat and the Hat")
    
    story2, created = Story.objects.get_or_create(
        title='The Magic Tree',
        defaults={
            'content': 'In the forest stood a magical tree that granted wishes to kind children who visited it.',
            'grade_level': '2',
            'difficulty': 'medium',
            'word_count': 15,
            'estimated_reading_time': 25
        }
    )
    if created:
        print("Created story: The Magic Tree")
    
    # Create sample audio files (metadata only - no actual files)
    for story in [story1, story2]:
        for voice in ['female_1', 'male_1']:
            audio, created = AudioFile.objects.get_or_create(
                story=story,
                voice_type=voice,
                defaults={
                    'file_path': f'audio/{story.id}_{voice}.mp3',
                    'file_size': 1024000,  # 1MB sample
                    'duration': story.estimated_reading_time
                }
            )
            if created:
                print(f"Created audio file: {story.title} - {voice}")
    
    # Create a sample assignment
    assignment, created = Assignment.objects.get_or_create(
        teacher=teacher,
        story=story1,
        defaults={
            'title': 'Reading Practice - Week 1',
            'description': 'Practice reading aloud with expression',
            'max_attempts': 3
        }
    )
    if created:
        print("Created assignment")
        
        # Assign to student
        StudentAssignment.objects.get_or_create(
            assignment=assignment,
            student=student
        )
        print("Assigned story to student")
    
    print("Sample data creation complete!")

if __name__ == '__main__':
    create_sample_data()