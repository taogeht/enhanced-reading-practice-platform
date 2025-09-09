from django.urls import path
from . import views

urlpatterns = [
    path('', views.StoryListView.as_view(), name='story-list'),
    path('<int:pk>/', views.StoryDetailView.as_view(), name='story-detail'),
    path('<int:story_id>/audio/<str:voice_type>/', views.serve_audio, name='serve-audio'),
]