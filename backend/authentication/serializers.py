from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Class, ClassMembership


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'user_type', 'grade_level', 'school', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm', 'user_type',
            'grade_level', 'school'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include username and password.')


class StudentSerializer(serializers.ModelSerializer):
    """Simplified student serializer for class management"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'grade_level', 'email']


class ClassMembershipSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    
    class Meta:
        model = ClassMembership
        fields = ['id', 'student', 'joined_at', 'is_active']


class ClassSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    student_count = serializers.SerializerMethodField()
    students = StudentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Class
        fields = [
            'id', 'name', 'teacher', 'teacher_name', 'grade_level',
            'school_year', 'student_count', 'students', 'is_active',
            'created_at'
        ]
        read_only_fields = ['teacher', 'created_at']
    
    def get_student_count(self, obj):
        return obj.students.filter(classmembership__is_active=True).count()
    
    def create(self, validated_data):
        validated_data['teacher'] = self.context['request'].user
        return super().create(validated_data)


class ClassListSerializer(serializers.ModelSerializer):
    """Simplified class serializer for list views"""
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    student_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = [
            'id', 'name', 'teacher_name', 'grade_level',
            'school_year', 'student_count', 'is_active', 'created_at'
        ]
    
    def get_student_count(self, obj):
        return obj.students.filter(classmembership__is_active=True).count()