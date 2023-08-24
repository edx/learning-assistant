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
