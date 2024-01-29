"""
Database models for learning_assistant.
"""
from django.db import models
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField


class LearningAssistantCourseEnabled(TimeStampedModel):
    """
    This model stores whether the Learning Assistant is enabled for a particular course ID.

    For now, the purpose of this model is to store overrides added by course team members. By default, the Learning
    Assistant will be enabled via a CourseWaffleFlag. This model will store whether course team members have manually
    disabled the Learning Assistant.

    .. no_pii: This model has no PII.
    """

    # course ID with for the course in which the Learning Assistant is enabled or disabled
    course_id = CourseKeyField(max_length=255, db_index=True, unique=True)

    enabled = models.BooleanField()
