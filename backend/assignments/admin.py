from django.contrib import admin
from .models import Assignment, StudentAssignment


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'story', 'due_date', 'is_active', 'created_at')
    list_filter = ('is_active', 'due_date', 'created_at', 'story__grade_level')
    search_fields = ('title', 'description', 'teacher__username', 'story__title')
    readonly_fields = ('assignment_code', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('title', 'description', 'teacher', 'story')
        }),
        ('Settings', {
            'fields': ('due_date', 'max_attempts', 'is_active')
        }),
        ('Access', {
            'fields': ('assignment_code',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(StudentAssignment)
class StudentAssignmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'attempts_used', 'is_completed', 'created_at')
    list_filter = ('completed_at', 'created_at', 'assignment__story__grade_level')
    search_fields = ('student__username', 'assignment__title')
    readonly_fields = ('created_at', 'is_completed', 'can_attempt')
    
    fieldsets = (
        ('Assignment Progress', {
            'fields': ('assignment', 'student', 'attempts_used', 'completed_at')
        }),
        ('Status', {
            'fields': ('is_completed', 'can_attempt')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
