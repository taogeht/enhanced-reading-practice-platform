from rest_framework import serializers
from .models import Assignment, StudentAssignment
from stories.serializers import StoryListSerializer


class AssignmentSerializer(serializers.ModelSerializer):
    story = StoryListSerializer(read_only=True)
    story_id = serializers.IntegerField(write_only=True)
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'story', 'story_id',
            'teacher_name', 'assignment_code', 'due_date',
            'max_attempts', 'is_active', 'created_at'
        ]
        read_only_fields = ['teacher', 'assignment_code', 'created_at']
    
    def create(self, validated_data):
        validated_data['teacher'] = self.context['request'].user
        return super().create(validated_data)


class StudentAssignmentSerializer(serializers.ModelSerializer):
    assignment = AssignmentSerializer(read_only=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    
    class Meta:
        model = StudentAssignment
        fields = [
            'id', 'assignment', 'student_name', 'attempts_used',
            'completed_at', 'is_completed', 'can_attempt', 'created_at'
        ]


class StudentAssignmentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for student's assignment view"""
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    story_title = serializers.CharField(source='assignment.story.title', read_only=True)
    story_id = serializers.IntegerField(source='assignment.story.id', read_only=True)
    due_date = serializers.DateTimeField(source='assignment.due_date', read_only=True)
    
    class Meta:
        model = StudentAssignment
        fields = [
            'id', 'assignment_title', 'story_title', 'story_id',
            'due_date', 'attempts_used', 'is_completed',
            'can_attempt', 'created_at'
        ]