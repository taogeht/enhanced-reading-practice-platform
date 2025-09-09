from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from authentication.models import Class
from .models import Assignment, StudentAssignment
from .serializers import AssignmentSerializer, StudentAssignmentSerializer, StudentAssignmentListSerializer


class StudentAssignmentListView(generics.ListAPIView):
    """List assignments for the current student"""
    serializer_class = StudentAssignmentListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_student:
            return StudentAssignment.objects.filter(
                student=self.request.user
            ).order_by('-created_at')
        return StudentAssignment.objects.none()


class TeacherAssignmentListView(generics.ListCreateAPIView):
    """List and create assignments for teachers"""
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_teacher:
            return Assignment.objects.filter(
                teacher=self.request.user
            ).order_by('-created_at')
        return Assignment.objects.none()


class AssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete assignment details"""
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_teacher:
            return Assignment.objects.filter(teacher=self.request.user)
        return Assignment.objects.none()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_class_assignment(request):
    """Create an assignment for an entire class"""
    if not request.user.is_teacher:
        return Response({'error': 'Only teachers can create class assignments'}, status=403)
    
    class_id = request.data.get('class_id')
    story_id = request.data.get('story_id')
    title = request.data.get('title')
    description = request.data.get('description', '')
    due_date = request.data.get('due_date')
    max_attempts = request.data.get('max_attempts', 3)
    
    if not all([class_id, story_id, title]):
        return Response({'error': 'class_id, story_id, and title are required'}, status=400)
    
    try:
        class_obj = Class.objects.get(id=class_id, teacher=request.user, is_active=True)
        
        with transaction.atomic():
            # Create the assignment
            assignment = Assignment.objects.create(
                teacher=request.user,
                story_id=story_id,
                class_assigned=class_obj,
                title=title,
                description=description,
                due_date=due_date,
                max_attempts=max_attempts
            )
            
            # Create StudentAssignment records for all active students in the class
            active_students = class_obj.students.filter(classmembership__is_active=True)
            student_assignments = []
            
            for student in active_students:
                student_assignments.append(
                    StudentAssignment(
                        assignment=assignment,
                        student=student
                    )
                )
            
            StudentAssignment.objects.bulk_create(student_assignments)
            
            return Response({
                'message': f'Assignment created and assigned to {len(student_assignments)} students',
                'assignment': AssignmentSerializer(assignment).data
            }, status=201)
            
    except Class.DoesNotExist:
        return Response({'error': 'Class not found or not owned by teacher'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def join_assignment(request):
    """Student joins an assignment using assignment code"""
    if not request.user.is_student:
        return Response({'error': 'Only students can join assignments'}, status=403)
    
    assignment_code = request.data.get('assignment_code')
    if not assignment_code:
        return Response({'error': 'Assignment code is required'}, status=400)
    
    try:
        assignment = Assignment.objects.get(
            assignment_code=assignment_code,
            is_active=True
        )
        
        student_assignment, created = StudentAssignment.objects.get_or_create(
            assignment=assignment,
            student=request.user
        )
        
        if created:
            return Response({'message': 'Successfully joined assignment'}, status=201)
        else:
            return Response({'message': 'Already joined this assignment'}, status=200)
            
    except Assignment.DoesNotExist:
        return Response({'error': 'Invalid assignment code'}, status=404)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def assignment_progress(request, assignment_id):
    """Get progress overview for an assignment (for teachers)"""
    if not request.user.is_teacher:
        return Response({'error': 'Only teachers can view assignment progress'}, status=403)
    
    try:
        assignment = Assignment.objects.get(id=assignment_id, teacher=request.user)
        student_assignments = StudentAssignment.objects.filter(assignment=assignment)
        
        total_students = student_assignments.count()
        completed_count = student_assignments.filter(completed_at__isnull=False).count()
        pending_count = total_students - completed_count
        
        # Get submission statistics
        from recordings.models import Recording
        recordings = Recording.objects.filter(assignment=assignment)
        total_recordings = recordings.count()
        reviewed_recordings = recordings.filter(status='reviewed').count()
        pending_review = recordings.filter(status='pending').count()
        
        return Response({
            'assignment': AssignmentSerializer(assignment).data,
            'progress': {
                'total_students': total_students,
                'completed': completed_count,
                'pending': pending_count,
                'completion_rate': (completed_count / total_students * 100) if total_students > 0 else 0
            },
            'recordings': {
                'total': total_recordings,
                'reviewed': reviewed_recordings,
                'pending_review': pending_review
            }
        })
        
    except Assignment.DoesNotExist:
        return Response({'error': 'Assignment not found'}, status=404)
