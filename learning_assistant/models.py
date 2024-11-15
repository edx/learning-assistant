"""
Database models for learning_assistant.
"""
from django.contrib.auth import get_user_model
from django.db import models
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField

USER_MODEL = get_user_model()


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


class LearningAssistantMessage(TimeStampedModel):
    """
    This model stores messages sent to and received from the learning assistant.

    .. pii: content
    .. pii_types: other
    .. pii_retirement: third_party
    """

    USER_ROLE = 'user'
    ASSISTANT_ROLE = 'assistant'

    Roles = (
        (USER_ROLE, USER_ROLE),
        (ASSISTANT_ROLE, ASSISTANT_ROLE),
    )

    course_id = CourseKeyField(max_length=255, db_index=True)
    user = models.ForeignKey(USER_MODEL, db_index=True, on_delete=models.CASCADE)
    role = models.CharField(choices=Roles, max_length=64)
    content = models.TextField()


class LearningAssistantAuditTrial(TimeStampedModel):
    """
    This model stores the trial period for an audit learner using the learning assistant.

    A LearningAssistantAuditTrial instance will be created on a per user basis,
    when an audit learner first sends a message using Xpert LA.

    .. no_pii: This model has no PII.
    """

    # Unique constraint since each user should only have one trial
    user = models.ForeignKey(USER_MODEL, db_index=True, on_delete=models.CASCADE, unique=True)
    start_date = models.DateTimeField()
