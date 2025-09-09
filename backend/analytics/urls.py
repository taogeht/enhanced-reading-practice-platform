from django.urls import path
from . import views

urlpatterns = [
    path('flags/', views.StudentFlagListView.as_view(), name='student-flags'),
    path('flags/<int:flag_id>/resolve/', views.resolve_flag, name='resolve-flag'),
    path('student-analytics/', views.StudentAnalyticsListView.as_view(), name='student-analytics'),
    path('system-analytics/', views.SystemAnalyticsListView.as_view(), name='system-analytics'),
    path('dashboard-summary/', views.dashboard_summary, name='dashboard-summary'),
    path('trigger-analysis/', views.trigger_analysis, name='trigger-analysis'),
    
    # Report generation endpoints
    path('reports/available/', views.available_reports, name='available-reports'),
    path('reports/class/<int:class_id>/performance/', views.class_performance_report, name='class-performance-report'),
    path('reports/class/<int:class_id>/gradebook/', views.gradebook_export, name='gradebook-export'),
    path('reports/student/<int:student_id>/progress/', views.student_progress_report, name='student-progress-report'),
    path('reports/teacher-summary/', views.teacher_summary_report, name='teacher-summary-report'),
    path('reports/school-wide/', views.school_wide_report, name='school-wide-report'),
]