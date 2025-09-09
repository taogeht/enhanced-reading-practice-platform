from rest_framework import serializers
from .models import Story, AudioFile


class AudioFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioFile
        fields = ['id', 'voice_type', 'file_path', 'duration', 'file_size']


class StorySerializer(serializers.ModelSerializer):
    audio_files = AudioFileSerializer(many=True, read_only=True)
    
    class Meta:
        model = Story
        fields = [
            'id', 'title', 'content', 'grade_level', 'difficulty',
            'word_count', 'estimated_reading_time', 'audio_files',
            'created_at'
        ]


class StoryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for story list views"""
    audio_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = [
            'id', 'title', 'grade_level', 'difficulty',
            'word_count', 'estimated_reading_time', 'audio_count'
        ]
    
    def get_audio_count(self, obj):
        return obj.audio_files.count()