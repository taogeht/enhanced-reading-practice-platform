from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from .models import Recording
from .serializers import RecordingSerializer, RecordingCreateSerializer, RecordingListSerializer, RecordingReviewSerializer


class StudentRecordingListView(generics.ListCreateAPIView):
    """List student's recordings and create new ones"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RecordingCreateSerializer
        return RecordingListSerializer
    
    def get_queryset(self):
        if self.request.user.is_student:
            return Recording.objects.filter(student=self.request.user)
        return Recording.objects.none()


class TeacherRecordingListView(generics.ListAPIView):
    """List recordings for teacher review"""
    serializer_class = RecordingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_teacher:
            return Recording.objects.filter(
                assignment__teacher=self.request.user
            ).order_by('-created_at')
        return Recording.objects.none()


class RecordingDetailView(generics.RetrieveUpdateAPIView):
    """Get and update recording details (for teacher feedback)"""
    serializer_class = RecordingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_teacher:
            return Recording.objects.filter(assignment__teacher=self.request.user)
        elif self.request.user.is_student:
            return Recording.objects.filter(student=self.request.user)
        return Recording.objects.none()
    
    def perform_update(self, serializer):
        if self.request.user.is_teacher:
            serializer.save(
                reviewed_by=self.request.user,
                reviewed_at=timezone.now(),
                status='reviewed'
            )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_recording_review(request, recording_id):
    """Submit a review for a recording"""
    if not request.user.is_teacher:
        return Response(
            {'error': 'Only teachers can submit reviews'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        recording = Recording.objects.get(
            id=recording_id,
            assignment__teacher=request.user
        )
    except Recording.DoesNotExist:
        return Response(
            {'error': 'Recording not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = RecordingReviewSerializer(data=request.data)
    if serializer.is_valid():
        # Update recording with review data
        recording.grade = serializer.validated_data['grade']
        recording.fluency_score = serializer.validated_data['fluency_score']
        recording.accuracy_score = serializer.validated_data['accuracy_score']
        recording.teacher_feedback = serializer.validated_data['feedback']
        recording.reviewed_by = request.user
        recording.reviewed_at = timezone.now()
        recording.status = 'reviewed'
        recording.save()
        
        return Response({'message': 'Review submitted successfully'})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
