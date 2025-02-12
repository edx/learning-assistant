"""
Django Admin pages.
"""
from datetime import timedelta

from django.conf import settings
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

    @admin.display(description="Expiration Date")
    def expiration_date(self):
        """
        Generate the expiration date for the LearningAssistantAuditTrial based on the start_date.
        """
        # pylint: disable-next=no-member
        return self.start_date + timedelta(days=settings.LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS)

    list_display = ('user', 'start_date', expiration_date)
    raw_id_fields = ('user',)
    search_fields = ('user__username',)

    class Meta:
        """
        Meta for the LearningAssistantAuditTrial admin panel.
        """

        model = LearningAssistantAuditTrial
        fields = ('user', 'start_date',)
