from django.contrib import admin
from .models import Story, AudioFile


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'grade_level', 'difficulty', 'word_count', 'is_active', 'created_at')
    list_filter = ('grade_level', 'difficulty', 'is_active', 'created_at')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Story Information', {
            'fields': ('title', 'content', 'grade_level', 'difficulty')
        }),
        ('Metrics', {
            'fields': ('word_count', 'estimated_reading_time')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(AudioFile)
class AudioFileAdmin(admin.ModelAdmin):
    list_display = ('story', 'voice_type', 'duration', 'file_size', 'created_at')
    list_filter = ('voice_type', 'created_at')
    search_fields = ('story__title', 'file_path')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Audio Information', {
            'fields': ('story', 'voice_type', 'file_path')
        }),
        ('File Details', {
            'fields': ('file_size', 'duration')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
