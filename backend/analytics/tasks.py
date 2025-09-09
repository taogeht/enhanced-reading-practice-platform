"""
Analytics tasks for automated student analysis and flagging.
In a production environment, these would be run as Celery tasks.
"""

from django.utils import timezone
from django.db.models import Count, Avg, Q, Sum, F
from django.db import models
from datetime import timedelta, date
from authentication.models import User
from recordings.models import Recording
from assignments.models import Assignment
from .models import StudentFlag, StudentAnalytics, SystemAnalytics


def run_student_analysis():
    """
    Analyze all students and create/update analytics and flags.
    This should be run periodically (e.g., daily) via cron or task queue.
    """
    print("Starting student analysis...")
    
    students = User.objects.filter(user_type='student')
    
    for student in students:
        analyze_student(student)
    
    # Also update system-wide analytics
    update_system_analytics()
    
    print(f"Student analysis completed for {students.count()} students")


def analyze_student(student):
    """Analyze individual student and create/update their analytics and flags"""
    
    # Get or create student analytics record
    analytics, created = StudentAnalytics.objects.get_or_create(student=student)
    
    # Calculate assignment metrics
    assignments = Assignment.objects.filter(
        Q(assigned_student=student) | Q(class_assigned__students=student)
    ).distinct()
    
    completed_assignments = assignments.filter(
        recordings__student=student
    ).distinct()
    
    analytics.total_assignments = assignments.count()
    analytics.completed_assignments = completed_assignments.count()
    analytics.submission_rate = (
        (analytics.completed_assignments / analytics.total_assignments * 100) 
        if analytics.total_assignments > 0 else 0
    )
    
    # Calculate recording metrics
    recordings = Recording.objects.filter(student=student)
    analytics.total_recordings = recordings.count()
    
    if recordings.exists():
        analytics.avg_recording_duration = recordings.aggregate(
            avg=Avg('duration')
        )['avg'] or 0
        
        reviewed_recordings = recordings.filter(status='reviewed')
        if reviewed_recordings.exists():
            analytics.avg_fluency_score = reviewed_recordings.aggregate(
                avg=Avg('fluency_score')
            )['avg'] or 0
            
            analytics.avg_accuracy_score = reviewed_recordings.aggregate(
                avg=Avg('accuracy_score')
            )['avg'] or 0
            
            # Calculate grade distribution
            grade_dist = reviewed_recordings.values('grade').annotate(
                count=Count('id')
            )
            analytics.overall_grade_distribution = {
                item['grade']: item['count'] for item in grade_dist if item['grade']
            }
    
    # Calculate engagement metrics
    latest_recording = recordings.order_by('-created_at').first()
    if latest_recording:
        analytics.days_since_last_submission = (
            timezone.now().date() - latest_recording.created_at.date()
        ).days
    else:
        analytics.days_since_last_submission = 999  # No submissions
    
    # Calculate missed deadlines
    analytics.missed_deadline_count = assignments.filter(
        due_date__lt=timezone.now(),
        recordings__student=student,
        recordings__created_at__gt=timezone.F('due_date')
    ).distinct().count()
    
    # Determine improvement trend
    if analytics.total_recordings >= 3:
        recent_recordings = recordings.filter(status='reviewed').order_by('-created_at')[:3]
        older_recordings = recordings.filter(status='reviewed').order_by('-created_at')[3:6]
        
        if recent_recordings.count() >= 2 and older_recordings.count() >= 2:
            recent_avg = recent_recordings.aggregate(
                avg_fluency=Avg('fluency_score'),
                avg_accuracy=Avg('accuracy_score')
            )
            older_avg = older_recordings.aggregate(
                avg_fluency=Avg('fluency_score'),
                avg_accuracy=Avg('accuracy_score')
            )
            
            recent_score = (recent_avg['avg_fluency'] or 0) + (recent_avg['avg_accuracy'] or 0)
            older_score = (older_avg['avg_fluency'] or 0) + (older_avg['avg_accuracy'] or 0)
            
            if recent_score > older_score + 0.5:
                analytics.improvement_trend = 'improving'
            elif recent_score < older_score - 0.5:
                analytics.improvement_trend = 'declining'
            else:
                analytics.improvement_trend = 'stable'
        else:
            analytics.improvement_trend = 'insufficient_data'
    else:
        analytics.improvement_trend = 'insufficient_data'
    
    analytics.save()
    
    # Now check for flags
    check_and_create_flags(student, analytics)


def check_and_create_flags(student, analytics):
    """Check if student needs to be flagged and create appropriate flags"""
    
    flags_to_create = []
    
    # Check for low submission rate
    if analytics.submission_rate < 50:
        flags_to_create.append({
            'flag_type': 'low_submission',
            'severity': 'high' if analytics.submission_rate < 25 else 'medium',
            'description': f'Student has only completed {analytics.submission_rate:.1f}% of assignments ({analytics.completed_assignments}/{analytics.total_assignments})'
        })
    
    # Check for short recordings
    if analytics.avg_recording_duration > 0 and analytics.avg_recording_duration < 30:
        flags_to_create.append({
            'flag_type': 'short_recordings',
            'severity': 'medium',
            'description': f'Average recording duration is only {analytics.avg_recording_duration:.1f} seconds, which may indicate rushed submissions'
        })
    
    # Check for low performance
    if analytics.avg_fluency_score > 0 and analytics.avg_fluency_score < 2.0:
        flags_to_create.append({
            'flag_type': 'low_performance',
            'severity': 'high',
            'description': f'Average fluency score is {analytics.avg_fluency_score:.1f}/5, indicating reading difficulties'
        })
    
    # Check for missed deadlines
    if analytics.missed_deadline_count > 2:
        flags_to_create.append({
            'flag_type': 'missed_deadlines',
            'severity': 'medium' if analytics.missed_deadline_count < 5 else 'high',
            'description': f'Student has missed {analytics.missed_deadline_count} assignment deadlines'
        })
    
    # Check for no improvement
    if analytics.improvement_trend == 'declining' and analytics.total_recordings > 5:
        flags_to_create.append({
            'flag_type': 'no_improvement',
            'severity': 'medium',
            'description': 'Student shows declining performance trend over recent submissions'
        })
    
    # Check for long absence
    if analytics.days_since_last_submission > 7:
        severity = 'urgent' if analytics.days_since_last_submission > 14 else 'high'
        flags_to_create.append({
            'flag_type': 'low_submission',
            'severity': severity,
            'description': f'Student has not submitted any recordings in {analytics.days_since_last_submission} days'
        })
    
    # Create flags (avoid duplicates)
    for flag_data in flags_to_create:
        existing_flag = StudentFlag.objects.filter(
            student=student,
            flag_type=flag_data['flag_type'],
            is_resolved=False
        ).first()
        
        if not existing_flag:
            StudentFlag.objects.create(
                student=student,
                **flag_data
            )
            print(f"Created {flag_data['flag_type']} flag for {student.get_full_name()}")


def update_system_analytics():
    """Update system-wide analytics for today"""
    today = date.today()
    
    analytics, created = SystemAnalytics.objects.get_or_create(
        date=today,
        defaults={
            'total_students': 0,
            'active_students': 0,
            'total_teachers': 0,
            'active_teachers': 0,
        }
    )
    
    # Update user metrics
    analytics.total_students = User.objects.filter(user_type='student').count()
    analytics.total_teachers = User.objects.filter(user_type='teacher').count()
    
    # Active users (activity in last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    analytics.active_students = User.objects.filter(
        user_type='student',
        recordings__created_at__gte=week_ago
    ).distinct().count()
    
    analytics.active_teachers = User.objects.filter(
        user_type='teacher',
        last_login__gte=week_ago
    ).count()
    
    # Content metrics
    analytics.total_assignments_created = Assignment.objects.count()
    analytics.total_recordings_submitted = Recording.objects.count()
    analytics.total_recordings_reviewed = Recording.objects.filter(status='reviewed').count()
    
    # Calculate storage usage (simplified)
    total_recordings = Recording.objects.aggregate(
        total_size=Sum('file_size')
    )['total_size'] or 0
    analytics.storage_used_gb = total_recordings / (1024 ** 3)  # Convert to GB
    
    analytics.save()
    
    print(f"Updated system analytics for {today}")


# Scheduled task runners (would be called by cron or task queue)
def daily_analysis():
    """Run daily student analysis"""
    run_student_analysis()


def weekly_cleanup():
    """Clean up old resolved flags and analytics data"""
    # Remove resolved flags older than 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    old_flags = StudentFlag.objects.filter(
        is_resolved=True,
        resolved_at__lt=thirty_days_ago
    )
    deleted_count = old_flags.count()
    old_flags.delete()
    
    print(f"Cleaned up {deleted_count} old resolved flags")
    
    # Keep only last 90 days of system analytics
    ninety_days_ago = date.today() - timedelta(days=90)
    old_analytics = SystemAnalytics.objects.filter(date__lt=ninety_days_ago)
    deleted_count = old_analytics.count()
    old_analytics.delete()
    
    print(f"Cleaned up {deleted_count} old system analytics records")