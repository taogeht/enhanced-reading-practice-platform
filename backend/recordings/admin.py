from django.contrib import admin
from .models import Recording


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ('student', 'story', 'status', 'grade', 'duration', 'created_at')
    list_filter = ('status', 'created_at', 'reviewed_at', 'story__grade_level')
    search_fields = ('student__username', 'story__title', 'teacher_feedback')
    readonly_fields = ('created_at', 'updated_at', 'file_size', 'duration')
    
    fieldsets = (
        ('Recording Information', {
            'fields': ('student', 'story', 'assignment', 'file_path')
        }),
        ('File Details', {
            'fields': ('file_size', 'duration')
        }),
        ('Review', {
            'fields': ('status', 'grade', 'teacher_feedback', 'reviewed_by', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif hasattr(request.user, 'user_type') and request.user.user_type == 'teacher':
            return qs.filter(story__assignments__teacher=request.user)
        return qs.none()
