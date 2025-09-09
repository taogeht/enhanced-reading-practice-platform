from rest_framework import serializers
from .models import Recording
from stories.serializers import StoryListSerializer


class RecordingSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)
    story_title = serializers.CharField(source='story.title', read_only=True)
    audio_file = serializers.CharField(source='file_path', read_only=True)
    
    class Meta:
        model = Recording
        fields = [
            'id', 'student', 'student_name', 'student_username',
            'story', 'story_title', 'assignment', 'file_path', 'audio_file',
            'duration', 'status', 'grade', 'fluency_score', 'accuracy_score',
            'teacher_feedback', 'reviewed_by', 'reviewed_at', 'attempt_number',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['student', 'created_at', 'file_path', 'duration', 'audio_file']


class RecordingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new recordings"""
    
    class Meta:
        model = Recording
        fields = ['story', 'assignment', 'file_path', 'duration', 'file_size']
        
    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)


class RecordingListSerializer(serializers.ModelSerializer):
    """Simplified serializer for recording lists"""
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)
    story_title = serializers.CharField(source='story.title', read_only=True)
    audio_file = serializers.CharField(source='file_path', read_only=True)
    
    class Meta:
        model = Recording
        fields = [
            'id', 'student_name', 'student_username', 'story_title', 'status',
            'grade', 'teacher_feedback', 'duration', 'audio_file', 'attempt_number',
            'created_at', 'updated_at'
        ]


class RecordingReviewSerializer(serializers.Serializer):
    """Serializer for recording review data"""
    recording_id = serializers.IntegerField()
    feedback = serializers.CharField(max_length=1000)
    grade = serializers.ChoiceField(choices=['excellent', 'good', 'needs_practice'])
    fluency_score = serializers.IntegerField(min_value=1, max_value=5)
    accuracy_score = serializers.IntegerField(min_value=1, max_value=5)