from django.urls import path
from . import views

urlpatterns = [
    path('student/', views.StudentRecordingListView.as_view(), name='student-recordings'),
    path('teacher/', views.TeacherRecordingListView.as_view(), name='teacher-recordings'),
    path('<int:pk>/', views.RecordingDetailView.as_view(), name='recording-detail'),
    path('<int:recording_id>/review/', views.submit_recording_review, name='recording-review'),
]