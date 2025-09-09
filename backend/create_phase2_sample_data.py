#!/usr/bin/env python
"""
Script to create Phase 2 sample data - classes and enhanced assignments
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reading_platform.settings')
django.setup()

from authentication.models import User, Class, ClassMembership
from stories.models import Story
from assignments.models import Assignment, StudentAssignment

def create_phase2_sample_data():
    print("Creating Phase 2 sample data...")
    
    # Get existing teacher and students
    teacher = User.objects.get(username='teacher1')
    student1 = User.objects.get(username='student1')
    
    # Create additional students
    students = []
    for i in range(2, 6):  # Create students 2-5
        student, created = User.objects.get_or_create(
            username=f'student{i}',
            defaults={
                'email': f'student{i}@example.com',
                'first_name': f'Student{i}',
                'last_name': 'Smith',
                'user_type': 'student',
                'grade_level': '1',
                'school': 'Elementary School'
            }
        )
        if created:
            student.set_password('password123')
            student.save()
            print(f"Created student: {student.username}")
        students.append(student)
    
    students.append(student1)  # Add original student to the list
    
    # Create a class
    class_obj, created = Class.objects.get_or_create(
        teacher=teacher,
        name="Grade 1A - Reading",
        defaults={
            'grade_level': '1',
            'school_year': '2024-2025'
        }
    )
    if created:
        print(f"Created class: {class_obj.name}")
    
    # Add students to the class
    for student in students:
        membership, created = ClassMembership.objects.get_or_create(
            class_instance=class_obj,
            student=student
        )
        if created:
            print(f"Added {student.username} to class {class_obj.name}")
    
    # Create a class assignment
    story = Story.objects.first()  # Use existing story
    if story:
        assignment, created = Assignment.objects.get_or_create(
            teacher=teacher,
            story=story,
            class_assigned=class_obj,
            title="Week 2 Reading Assessment",
            defaults={
                'description': 'Read the assigned story aloud with expression and fluency.',
                'max_attempts': 3
            }
        )
        if created:
            print(f"Created class assignment: {assignment.title}")
            
            # Create student assignments for all students in the class
            for student in students:
                student_assignment, sa_created = StudentAssignment.objects.get_or_create(
                    assignment=assignment,
                    student=student
                )
                if sa_created:
                    print(f"Assigned {assignment.title} to {student.username}")
    
    print("Phase 2 sample data creation complete!")

if __name__ == '__main__':
    create_phase2_sample_data()