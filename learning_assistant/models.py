"""
Database models for learning_assistant.
"""
from django.db import models
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField


class CoursePrompt(TimeStampedModel):
    """
    This model represents a mapping between a particular course ID and a text prompt associated with the course ID.

    .. no_pii: This model has no PII.
    """

    # course ID with which the text prompt is associated
    course_id = CourseKeyField(max_length=255, db_index=True, unique=True)

    # a json representation of the prompt message content
    json_prompt_content = models.JSONField(null=True)

    @classmethod
    def get_json_prompt_content_by_course_id(cls, course_id):
        """
        Return a json representation of a prompt for a given course id.
        """
        try:
            prompt_object = cls.objects.get(course_id=course_id)
            json_prompt_content = prompt_object.json_prompt_content
        except cls.DoesNotExist:
            json_prompt_content = None
        return json_prompt_content


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
