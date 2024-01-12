"""
Django Admin pages.
"""
from django.contrib import admin

from learning_assistant.models import CoursePrompt, LearningAssistantCourseEnabled


@admin.register(CoursePrompt)
class CoursePromptAdmin(admin.ModelAdmin):
    """
    Admin panel for course prompts.
    """

    list_display = ('id', 'course_id')


@admin.register(LearningAssistantCourseEnabled)
class LearningAssistantCourseEnabledAdmin(admin.ModelAdmin):
    """
    Admin panel for the LearningAssistantCourseEnabled model.
    """
