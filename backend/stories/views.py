from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import FileResponse, Http404
from django.conf import settings
import os
from .models import Story, AudioFile
from .serializers import StorySerializer, StoryListSerializer, AudioFileSerializer


class StoryListView(generics.ListAPIView):
    """List all active stories, optionally filtered by grade level"""
    serializer_class = StoryListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Story.objects.filter(is_active=True)
        grade_level = self.request.query_params.get('grade_level', None)
        if grade_level:
            queryset = queryset.filter(grade_level=grade_level)
        return queryset


class StoryDetailView(generics.RetrieveAPIView):
    """Get detailed story information including audio files"""
    queryset = Story.objects.filter(is_active=True)
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def serve_audio(request, story_id, voice_type):
    """Serve audio files for stories"""
    try:
        audio_file = AudioFile.objects.get(
            story_id=story_id,
            voice_type=voice_type
        )
        
        file_path = os.path.join(settings.MEDIA_ROOT, audio_file.file_path)
        
        if not os.path.exists(file_path):
            raise Http404("Audio file not found")
        
        return FileResponse(
            open(file_path, 'rb'),
            content_type='audio/mpeg',
            filename=f"{audio_file.story.title}_{voice_type}.mp3"
        )
    except AudioFile.DoesNotExist:
        raise Http404("Audio file not found")
