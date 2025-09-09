from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Class, ClassMembership


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'user_type', 'grade_level', 'school', 'is_active')
    list_filter = ('user_type', 'grade_level', 'school', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'grade_level', 'school')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'grade_level', 'school')
        }),
    )


class ClassMembershipInline(admin.TabularInline):
    model = ClassMembership
    extra = 0
    raw_id_fields = ('student',)


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'grade_level', 'school_year', 'student_count', 'is_active', 'created_at')
    list_filter = ('grade_level', 'school_year', 'is_active', 'created_at')
    search_fields = ('name', 'teacher__username', 'teacher__first_name', 'teacher__last_name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ClassMembershipInline]
    
    fieldsets = (
        ('Class Information', {
            'fields': ('name', 'teacher', 'grade_level', 'school_year')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = 'Students'
