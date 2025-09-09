from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import timedelta, date
from .models import StudentFlag, StudentAnalytics, SystemAnalytics
from .serializers import (
    StudentFlagSerializer, StudentAnalyticsSerializer, 
    SystemAnalyticsSerializer, FlagResolutionSerializer
)
from .tasks import run_student_analysis
from .reports import (
    generate_class_performance_report, generate_student_progress_report,
    generate_teacher_summary_report, generate_school_wide_report,
    generate_gradebook_export
)


class StudentFlagListView(generics.ListAPIView):
    """List student flags for teachers"""
    serializer_class = StudentFlagSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_teacher:
            # Get flags for students in teacher's classes
            from authentication.models import Class
            teacher_classes = Class.objects.filter(teacher=self.request.user)
            student_ids = []
            for cls in teacher_classes:
                student_ids.extend(cls.students.values_list('id', flat=True))
            
            return StudentFlag.objects.filter(
                student_id__in=student_ids
            ).select_related('student', 'resolved_by')
        elif self.request.user.is_admin:
            return StudentFlag.objects.all().select_related('student', 'resolved_by')
        return StudentFlag.objects.none()


class StudentAnalyticsListView(generics.ListAPIView):
    """List student analytics for teachers"""
    serializer_class = StudentAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_teacher:
            # Get analytics for students in teacher's classes
            from authentication.models import Class
            teacher_classes = Class.objects.filter(teacher=self.request.user)
            student_ids = []
            for cls in teacher_classes:
                student_ids.extend(cls.students.values_list('id', flat=True))
            
            return StudentAnalytics.objects.filter(
                student_id__in=student_ids
            ).select_related('student')
        elif self.request.user.is_admin:
            return StudentAnalytics.objects.all().select_related('student')
        return StudentAnalytics.objects.none()


class SystemAnalyticsListView(generics.ListAPIView):
    """List system analytics (admin only)"""
    serializer_class = SystemAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_admin:
            # Return last 30 days of analytics
            return SystemAnalytics.objects.all()[:30]
        return SystemAnalytics.objects.none()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def resolve_flag(request, flag_id):
    """Resolve a student flag"""
    if not request.user.is_teacher and not request.user.is_admin:
        return Response(
            {'error': 'Only teachers and administrators can resolve flags'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        flag = StudentFlag.objects.get(id=flag_id, is_resolved=False)
        
        # Check if teacher has permission for this student
        if request.user.is_teacher:
            from authentication.models import Class
            teacher_classes = Class.objects.filter(teacher=request.user)
            student_ids = []
            for cls in teacher_classes:
                student_ids.extend(cls.students.values_list('id', flat=True))
            
            if flag.student.id not in student_ids:
                return Response(
                    {'error': 'You do not have permission to resolve this flag'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
    except StudentFlag.DoesNotExist:
        return Response(
            {'error': 'Flag not found or already resolved'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = FlagResolutionSerializer(data=request.data)
    if serializer.is_valid():
        flag.resolve(
            resolved_by=request.user,
            notes=serializer.validated_data.get('resolution_notes', '')
        )
        return Response({'message': 'Flag resolved successfully'})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def trigger_analysis(request):
    """Manually trigger student analysis (admin only)"""
    if not request.user.is_admin:
        return Response(
            {'error': 'Only administrators can trigger analysis'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Trigger the analysis task
    run_student_analysis()
    
    return Response({'message': 'Student analysis triggered successfully'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_summary(request):
    """Get summary data for analytics dashboard"""
    if not request.user.is_teacher and not request.user.is_admin:
        return Response(
            {'error': 'Access denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    if request.user.is_teacher:
        # Get summary for teacher's students
        from authentication.models import Class
        teacher_classes = Class.objects.filter(teacher=request.user)
        student_ids = []
        for cls in teacher_classes:
            student_ids.extend(cls.students.values_list('id', flat=True))
        
        flags = StudentFlag.objects.filter(
            student_id__in=student_ids, 
            is_resolved=False
        )
        
        analytics = StudentAnalytics.objects.filter(student_id__in=student_ids)
        
    else:  # Admin
        flags = StudentFlag.objects.filter(is_resolved=False)
        analytics = StudentAnalytics.objects.all()
    
    # Calculate summary statistics
    summary = {
        'total_flags': flags.count(),
        'high_priority_flags': flags.filter(severity='high').count(),
        'urgent_flags': flags.filter(severity='urgent').count(),
        'students_needing_attention': analytics.filter(
            Q(submission_rate__lt=70) | 
            Q(days_since_last_submission__gt=7) |
            Q(avg_fluency_score__lt=2.0) |
            Q(missed_deadline_count__gt=2)
        ).count(),
        'flag_distribution': dict(flags.values_list('flag_type').annotate(count=Count('id'))),
        'average_completion_rate': analytics.aggregate(
            avg_rate=Avg('submission_rate')
        )['avg_rate'] or 0,
        'students_by_trend': dict(analytics.values_list('improvement_trend').annotate(count=Count('id'))),
    }
    
    return Response(summary)


# Bulk Report Generation Views

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def class_performance_report(request, class_id):
    """Generate class performance report"""
    if not request.user.is_teacher and not request.user.is_admin:
        return Response(
            {'error': 'Access denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if teacher has permission for this class
    if request.user.is_teacher:
        from authentication.models import Class
        try:
            class_obj = Class.objects.get(id=class_id, teacher=request.user)
        except Class.DoesNotExist:
            return Response(
                {'error': 'Class not found or access denied'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    format_type = request.GET.get('format', 'csv')
    report = generate_class_performance_report(class_id, format_type)
    
    if report is None:
        return Response(
            {'error': 'Class not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    return report


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def student_progress_report(request, student_id):
    """Generate student progress report"""
    if not request.user.is_teacher and not request.user.is_admin:
        return Response(
            {'error': 'Access denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if teacher has permission for this student
    if request.user.is_teacher:
        from authentication.models import Class
        teacher_classes = Class.objects.filter(teacher=request.user)
        student_ids = []
        for cls in teacher_classes:
            student_ids.extend(cls.students.values_list('id', flat=True))
        
        if int(student_id) not in student_ids:
            return Response(
                {'error': 'Student not found or access denied'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    format_type = request.GET.get('format', 'csv')
    report = generate_student_progress_report(student_id, format_type)
    
    if report is None:
        return Response(
            {'error': 'Student not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    return report


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def teacher_summary_report(request):
    """Generate teacher summary report"""
    if not request.user.is_teacher:
        return Response(
            {'error': 'Only teachers can generate this report'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    format_type = request.GET.get('format', 'csv')
    report = generate_teacher_summary_report(request.user.id, format_type)
    
    if report is None:
        return Response(
            {'error': 'Failed to generate report'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return report


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def school_wide_report(request):
    """Generate school-wide report (admin only)"""
    if not request.user.is_admin:
        return Response(
            {'error': 'Only administrators can generate school-wide reports'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    format_type = request.GET.get('format', 'csv')
    report = generate_school_wide_report(format_type)
    
    return report


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def gradebook_export(request, class_id):
    """Generate gradebook export for LMS integration"""
    if not request.user.is_teacher and not request.user.is_admin:
        return Response(
            {'error': 'Access denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if teacher has permission for this class
    if request.user.is_teacher:
        from authentication.models import Class
        try:
            class_obj = Class.objects.get(id=class_id, teacher=request.user)
        except Class.DoesNotExist:
            return Response(
                {'error': 'Class not found or access denied'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    format_type = request.GET.get('format', 'csv')
    report = generate_gradebook_export(class_id, format_type)
    
    if report is None:
        return Response(
            {'error': 'Class not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    return report


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def available_reports(request):
    """Get list of available reports for current user"""
    reports = []
    
    if request.user.is_teacher:
        from authentication.models import Class
        teacher_classes = Class.objects.filter(teacher=request.user, is_active=True)
        
        reports = [
            {
                'type': 'teacher_summary',
                'title': 'Teacher Summary Report',
                'description': 'Overview of all your classes and students',
                'endpoint': '/analytics/reports/teacher-summary/'
            }
        ]
        
        for class_obj in teacher_classes:
            reports.extend([
                {
                    'type': 'class_performance',
                    'title': f'{class_obj.name} - Performance Report',
                    'description': f'Detailed performance data for {class_obj.name}',
                    'endpoint': f'/analytics/reports/class/{class_obj.id}/performance/',
                    'class_id': class_obj.id
                },
                {
                    'type': 'gradebook_export',
                    'title': f'{class_obj.name} - Gradebook Export',
                    'description': f'LMS-compatible gradebook for {class_obj.name}',
                    'endpoint': f'/analytics/reports/class/{class_obj.id}/gradebook/',
                    'class_id': class_obj.id
                }
            ])
    
    elif request.user.is_admin:
        reports = [
            {
                'type': 'school_wide',
                'title': 'School-Wide Analytics Report',
                'description': 'Comprehensive analytics for the entire school',
                'endpoint': '/analytics/reports/school-wide/'
            },
            {
                'type': 'teacher_summary',
                'title': 'Teacher Summary Report',
                'description': 'Overview of all teachers and classes',
                'endpoint': '/analytics/reports/teacher-summary/'
            }
        ]
    
    return Response({'available_reports': reports})