"""
Django Admin pages.
"""
from django.contrib import admin

from learning_assistant.models import LearningAssistantCourseEnabled


@admin.register(LearningAssistantCourseEnabled)
class LearningAssistantCourseEnabledAdmin(admin.ModelAdmin):
    """
    Admin panel for the LearningAssistantCourseEnabled model.
    """
