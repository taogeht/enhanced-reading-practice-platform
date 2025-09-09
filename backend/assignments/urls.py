from django.urls import path
from . import views

urlpatterns = [
    path('student/', views.StudentAssignmentListView.as_view(), name='student-assignments'),
    path('teacher/', views.TeacherAssignmentListView.as_view(), name='teacher-assignments'),
    path('<int:pk>/', views.AssignmentDetailView.as_view(), name='assignment-detail'),
    path('join/', views.join_assignment, name='join-assignment'),
    path('create-class-assignment/', views.create_class_assignment, name='create-class-assignment'),
    path('<int:assignment_id>/progress/', views.assignment_progress, name='assignment-progress'),
]