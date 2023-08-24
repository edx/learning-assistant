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

    # text prompt, that may contain course related information
    prompt = models.TextField(blank=True, null=True)

    @classmethod
    def get_prompt_by_course_id(cls, course_id):
        """
        Return a text prompt for a given course id.
        """
        try:
            prompt_object = cls.objects.get(course_id=course_id)
            prompt = prompt_object.prompt
        except cls.DoesNotExist:
            prompt = None
        return prompt
