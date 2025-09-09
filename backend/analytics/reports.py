"""
Bulk report generation utilities for Phase 3
"""

import csv
import json
from io import StringIO
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone

from authentication.models import User, Class
from recordings.models import Recording
from assignments.models import Assignment
from .models import StudentAnalytics, StudentFlag


def generate_class_performance_report(class_id, format='csv'):
    """Generate a performance report for a specific class"""
    try:
        class_obj = Class.objects.get(id=class_id)
    except Class.DoesNotExist:
        return None
    
    # Get all students in the class
    students = class_obj.students.all()
    
    # Collect data for each student
    report_data = []
    for student in students:
        # Get student analytics
        analytics = StudentAnalytics.objects.filter(student=student).first()
        
        # Get recent recordings
        recent_recordings = Recording.objects.filter(
            student=student,
            status='reviewed'
        ).order_by('-created_at')[:5]
        
        # Calculate recent performance
        recent_fluency = recent_recordings.aggregate(
            avg=Avg('fluency_score')
        )['avg'] or 0
        
        recent_accuracy = recent_recordings.aggregate(
            avg=Avg('accuracy_score')
        )['avg'] or 0
        
        student_data = {
            'student_name': student.get_full_name(),
            'username': student.username,
            'total_assignments': analytics.total_assignments if analytics else 0,
            'completed_assignments': analytics.completed_assignments if analytics else 0,
            'completion_rate': analytics.submission_rate if analytics else 0,
            'avg_fluency_score': analytics.avg_fluency_score if analytics else 0,
            'avg_accuracy_score': analytics.avg_accuracy_score if analytics else 0,
            'recent_fluency_score': round(recent_fluency, 2),
            'recent_accuracy_score': round(recent_accuracy, 2),
            'improvement_trend': analytics.improvement_trend if analytics else 'insufficient_data',
            'days_since_last_submission': analytics.days_since_last_submission if analytics else 999,
            'total_recordings': analytics.total_recordings if analytics else 0,
            'needs_attention': analytics.needs_attention if analytics else True,
        }
        report_data.append(student_data)
    
    if format == 'csv':
        return generate_csv_report(report_data, f"class_{class_obj.name}_performance_report")
    elif format == 'json':
        return generate_json_report(report_data, f"class_{class_obj.name}_performance_report")
    else:
        return report_data


def generate_student_progress_report(student_id, format='csv'):
    """Generate a detailed progress report for a specific student"""
    try:
        student = User.objects.get(id=student_id, user_type='student')
    except User.DoesNotExist:
        return None
    
    # Get all recordings for the student
    recordings = Recording.objects.filter(student=student).order_by('created_at')
    
    report_data = []
    for recording in recordings:
        recording_data = {
            'date': recording.created_at.strftime('%Y-%m-%d'),
            'story_title': recording.story.title if recording.story else 'Unknown',
            'assignment_title': recording.assignment.title if recording.assignment else 'Practice',
            'duration_seconds': recording.duration,
            'status': recording.status,
            'fluency_score': recording.fluency_score or 'Not scored',
            'accuracy_score': recording.accuracy_score or 'Not scored',
            'grade': recording.grade or 'Not graded',
            'teacher_feedback': recording.teacher_feedback or 'No feedback',
            'attempt_number': recording.attempt_number or 1,
        }
        report_data.append(recording_data)
    
    if format == 'csv':
        return generate_csv_report(report_data, f"student_{student.username}_progress_report")
    elif format == 'json':
        return generate_json_report(report_data, f"student_{student.username}_progress_report")
    else:
        return report_data


def generate_teacher_summary_report(teacher_id, format='csv'):
    """Generate a summary report for a teacher's classes and students"""
    try:
        teacher = User.objects.get(id=teacher_id, user_type='teacher')
    except User.DoesNotExist:
        return None
    
    # Get all classes taught by this teacher
    classes = Class.objects.filter(teacher=teacher, is_active=True)
    
    report_data = []
    for class_obj in classes:
        students = class_obj.students.all()
        
        # Calculate class metrics
        total_students = students.count()
        
        # Get analytics for students in this class
        class_analytics = StudentAnalytics.objects.filter(student__in=students)
        
        if class_analytics.exists():
            avg_completion_rate = class_analytics.aggregate(
                avg=Avg('submission_rate')
            )['avg'] or 0
            
            avg_fluency = class_analytics.aggregate(
                avg=Avg('avg_fluency_score')
            )['avg'] or 0
            
            avg_accuracy = class_analytics.aggregate(
                avg=Avg('avg_accuracy_score')
            )['avg'] or 0
            
            students_needing_attention = class_analytics.filter(
                Q(submission_rate__lt=70) |
                Q(days_since_last_submission__gt=7) |
                Q(avg_fluency_score__lt=2.0)
            ).count()
            
        else:
            avg_completion_rate = 0
            avg_fluency = 0
            avg_accuracy = 0
            students_needing_attention = 0
        
        # Get active flags for this class
        active_flags = StudentFlag.objects.filter(
            student__in=students,
            is_resolved=False
        ).count()
        
        class_data = {
            'class_name': class_obj.name,
            'grade_level': class_obj.grade_level,
            'school_year': class_obj.school_year,
            'total_students': total_students,
            'avg_completion_rate': round(avg_completion_rate, 1),
            'avg_fluency_score': round(avg_fluency, 2),
            'avg_accuracy_score': round(avg_accuracy, 2),
            'students_needing_attention': students_needing_attention,
            'active_flags': active_flags,
            'created_date': class_obj.created_at.strftime('%Y-%m-%d'),
        }
        report_data.append(class_data)
    
    if format == 'csv':
        return generate_csv_report(report_data, f"teacher_{teacher.username}_summary_report")
    elif format == 'json':
        return generate_json_report(report_data, f"teacher_{teacher.username}_summary_report")
    else:
        return report_data


def generate_school_wide_report(format='csv'):
    """Generate a school-wide analytics report (admin only)"""
    
    # Overall statistics
    total_students = User.objects.filter(user_type='student').count()
    total_teachers = User.objects.filter(user_type='teacher').count()
    total_classes = Class.objects.filter(is_active=True).count()
    
    # Assignment and recording statistics
    total_assignments = Assignment.objects.count()
    total_recordings = Recording.objects.count()
    reviewed_recordings = Recording.objects.filter(status='reviewed').count()
    
    # Performance statistics
    overall_completion_rate = StudentAnalytics.objects.aggregate(
        avg=Avg('submission_rate')
    )['avg'] or 0
    
    overall_fluency = StudentAnalytics.objects.aggregate(
        avg=Avg('avg_fluency_score')
    )['avg'] or 0
    
    overall_accuracy = StudentAnalytics.objects.aggregate(
        avg=Avg('avg_accuracy_score')
    )['avg'] or 0
    
    # Flag statistics
    active_flags = StudentFlag.objects.filter(is_resolved=False).count()
    urgent_flags = StudentFlag.objects.filter(
        is_resolved=False, 
        severity='urgent'
    ).count()
    
    # Students needing attention
    students_needing_attention = StudentAnalytics.objects.filter(
        Q(submission_rate__lt=70) |
        Q(days_since_last_submission__gt=7) |
        Q(avg_fluency_score__lt=2.0)
    ).count()
    
    report_data = [{
        'report_date': datetime.now().strftime('%Y-%m-%d'),
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'total_assignments': total_assignments,
        'total_recordings': total_recordings,
        'reviewed_recordings': reviewed_recordings,
        'review_completion_rate': round((reviewed_recordings / total_recordings * 100) if total_recordings > 0 else 0, 1),
        'overall_completion_rate': round(overall_completion_rate, 1),
        'overall_fluency_score': round(overall_fluency, 2),
        'overall_accuracy_score': round(overall_accuracy, 2),
        'active_flags': active_flags,
        'urgent_flags': urgent_flags,
        'students_needing_attention': students_needing_attention,
        'attention_percentage': round((students_needing_attention / total_students * 100) if total_students > 0 else 0, 1),
    }]
    
    if format == 'csv':
        return generate_csv_report(report_data, "school_wide_analytics_report")
    elif format == 'json':
        return generate_json_report(report_data, "school_wide_analytics_report")
    else:
        return report_data


def generate_gradebook_export(class_id, format='csv'):
    """Generate gradebook export for LMS integration"""
    try:
        class_obj = Class.objects.get(id=class_id)
    except Class.DoesNotExist:
        return None
    
    students = class_obj.students.all()
    
    # Get all assignments for this class
    assignments = Assignment.objects.filter(class_assigned=class_obj)
    
    # Create gradebook data
    gradebook_data = []
    for student in students:
        student_row = {
            'student_id': student.id,
            'student_name': student.get_full_name(),
            'username': student.username,
            'email': student.email,
        }
        
        # Add grades for each assignment
        for assignment in assignments:
            recording = Recording.objects.filter(
                student=student,
                assignment=assignment,
                status='reviewed'
            ).first()
            
            if recording:
                # Convert grade to numeric score
                grade_mapping = {
                    'excellent': 95,
                    'good': 85,
                    'needs_practice': 70
                }
                numeric_grade = grade_mapping.get(recording.grade, 0)
                
                student_row[f"{assignment.title}_grade"] = numeric_grade
                student_row[f"{assignment.title}_fluency"] = recording.fluency_score or 0
                student_row[f"{assignment.title}_accuracy"] = recording.accuracy_score or 0
                student_row[f"{assignment.title}_submitted"] = recording.created_at.strftime('%Y-%m-%d')
            else:
                student_row[f"{assignment.title}_grade"] = 0
                student_row[f"{assignment.title}_fluency"] = 0
                student_row[f"{assignment.title}_accuracy"] = 0
                student_row[f"{assignment.title}_submitted"] = 'Not submitted'
        
        # Add overall statistics
        analytics = StudentAnalytics.objects.filter(student=student).first()
        if analytics:
            student_row['overall_completion_rate'] = round(analytics.submission_rate, 1)
            student_row['overall_fluency_avg'] = round(analytics.avg_fluency_score, 2)
            student_row['overall_accuracy_avg'] = round(analytics.avg_accuracy_score, 2)
        
        gradebook_data.append(student_row)
    
    if format == 'csv':
        return generate_csv_report(gradebook_data, f"gradebook_{class_obj.name}_export")
    elif format == 'json':
        return generate_json_report(gradebook_data, f"gradebook_{class_obj.name}_export")
    else:
        return gradebook_data


def generate_csv_report(data, filename):
    """Convert data to CSV format"""
    if not data:
        return None
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.DictWriter(response, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    
    return response


def generate_json_report(data, filename):
    """Convert data to JSON format"""
    if not data:
        return None
    
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{filename}_{datetime.now().strftime("%Y%m%d")}.json"'
    
    json.dump({
        'report_generated': datetime.now().isoformat(),
        'data': data
    }, response, indent=2, default=str)
    
    return response