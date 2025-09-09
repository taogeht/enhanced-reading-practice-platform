from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Class Management
    path('classes/', views.TeacherClassListView.as_view(), name='teacher-classes'),
    path('classes/<int:pk>/', views.ClassDetailView.as_view(), name='class-detail'),
    path('classes/<int:class_id>/add-student/', views.add_student_to_class, name='add-student-to-class'),
    path('classes/<int:class_id>/remove-student/<int:student_id>/', views.remove_student_from_class, name='remove-student-from-class'),
    path('search-students/', views.search_students, name='search-students'),
]