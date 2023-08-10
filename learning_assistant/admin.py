"""
Django Admin pages.
"""
from django.contrib import admin

from learning_assistant.models import CoursePrompt


@admin.register(CoursePrompt)
class CoursePromptAdmin(admin.ModelAdmin):
    """
    Admin panel for course prompts.
    """

    list_display = ('id', 'course_id')
