from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from .models import User, Class, ClassMembership
from .serializers import (
    UserSerializer, UserCreateSerializer, LoginSerializer,
    ClassSerializer, ClassListSerializer, StudentSerializer
)
from security.serializers import SecureLoginSerializer, SecureRegistrationSerializer
from security.validators import validate_api_input
import logging

logger = logging.getLogger('security')


class RegisterView(generics.CreateAPIView):
    """User registration endpoint with enhanced security"""
    queryset = User.objects.all()
    serializer_class = SecureRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Enhanced registration with security logging"""
        # Log registration attempt
        client_ip = self.get_client_ip(request)
        logger.info(f"Registration attempt from IP {client_ip}")
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Create user
            user_data = serializer.validated_data
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                user_type=user_data['user_type'],
                school=user_data.get('school', '')
            )
            
            # Log successful registration
            logger.info(f"User {user.username} registered successfully from IP {client_ip}")
            
            # Create token
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        # Log failed registration
        logger.warning(f"Failed registration attempt from IP {client_ip}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """Enhanced user login endpoint with security logging"""
    client_ip = get_client_ip(request)
    
    # Log login attempt
    username = request.data.get('username', 'unknown')
    logger.info(f"Login attempt for user '{username}' from IP {client_ip}")
    
    serializer = SecureLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Log successful login
        logger.info(f"Successful login for user '{user.username}' from IP {client_ip}")
        
        # Update user's last login
        from django.utils import timezone
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })
    
    # Log failed login
    logger.warning(f"Failed login attempt for user '{username}' from IP {client_ip}: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


def get_client_ip(request):
    """Utility function to get client IP"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """User logout endpoint"""
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Successfully logged out'})
    except:
        return Response({'error': 'Error logging out'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile_view(request):
    """Get current user profile"""
    return Response(UserSerializer(request.user).data)


# Class Management Views

class TeacherClassListView(generics.ListCreateAPIView):
    """List and create classes for teachers"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ClassSerializer
        return ClassListSerializer
    
    def get_queryset(self):
        if self.request.user.is_teacher:
            return Class.objects.filter(teacher=self.request.user, is_active=True)
        return Class.objects.none()


class ClassDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete class details"""
    serializer_class = ClassSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_teacher:
            return Class.objects.filter(teacher=self.request.user)
        return Class.objects.none()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_student_to_class(request, class_id):
    """Add a student to a class"""
    if not request.user.is_teacher:
        return Response({'error': 'Only teachers can add students to classes'}, status=403)
    
    class_obj = get_object_or_404(Class, id=class_id, teacher=request.user)
    student_id = request.data.get('student_id')
    
    if not student_id:
        return Response({'error': 'student_id is required'}, status=400)
    
    try:
        student = User.objects.get(id=student_id, user_type='student')
        membership, created = ClassMembership.objects.get_or_create(
            class_instance=class_obj,
            student=student,
            defaults={'is_active': True}
        )
        
        if not created and not membership.is_active:
            membership.is_active = True
            membership.save()
        
        return Response({
            'message': 'Student added to class successfully',
            'created': created
        })
        
    except User.DoesNotExist:
        return Response({'error': 'Student not found'}, status=404)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_student_from_class(request, class_id, student_id):
    """Remove a student from a class"""
    if not request.user.is_teacher:
        return Response({'error': 'Only teachers can remove students from classes'}, status=403)
    
    class_obj = get_object_or_404(Class, id=class_id, teacher=request.user)
    
    try:
        membership = ClassMembership.objects.get(
            class_instance=class_obj,
            student_id=student_id
        )
        membership.is_active = False
        membership.save()
        
        return Response({'message': 'Student removed from class successfully'})
        
    except ClassMembership.DoesNotExist:
        return Response({'error': 'Student is not in this class'}, status=404)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_students(request):
    """Search for students to add to classes"""
    if not request.user.is_teacher:
        return Response({'error': 'Only teachers can search students'}, status=403)
    
    query = request.GET.get('q', '')
    if len(query) < 2:
        return Response({'results': []})
    
    students = User.objects.filter(
        user_type='student',
        username__icontains=query
    )[:10]
    
    return Response({
        'results': StudentSerializer(students, many=True).data
    })
