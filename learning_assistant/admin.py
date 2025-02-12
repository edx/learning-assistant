"""
Django Admin pages.
"""
from django.contrib import admin

from learning_assistant.models import LearningAssistantAuditTrial, LearningAssistantCourseEnabled


@admin.register(LearningAssistantCourseEnabled)
class LearningAssistantCourseEnabledAdmin(admin.ModelAdmin):
    """
    Admin panel for the LearningAssistantCourseEnabled model.
    """


@admin.register(LearningAssistantAuditTrial)
class LearningAssistantAuditTrialAdmin(admin.ModelAdmin):
    """
    Admin panel for the LearningAssistantAuditTrial model.

    NOTE: When viewed in admin, these datetimes are in UTC.
    Please take this into account when reading/modifying entries.
    """

    list_display = ('user', 'start_date', 'expiration_date')
    raw_id_fields = ('user',)
    search_fields = ('user__username',)

    class Meta:
        """
        Meta for the LearningAssistantAuditTrial admin panel.
        """

        model = LearningAssistantAuditTrial
        fields = ('user', 'start_date', 'expiration_date')
