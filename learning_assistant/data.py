"""
Data classes for the Learning Assistant application.
"""
from datetime import datetime

from attrs import field, frozen, validators
from opaque_keys.edx.keys import CourseKey


@frozen
class LearningAssistantCourseEnabledData:
    """
    Data class representing whether Learning Assistant is enabled in a course.
    """

    course_key: CourseKey = field(validator=validators.instance_of(CourseKey))
    enabled: bool = field(validator=validators.instance_of(bool))


@frozen
class LearningAssistantAuditTrialData:
    """
    Data class representing an audit learner's trial of the Learning Assistant.
    """

    user_id: int = field(validator=validators.instance_of(int))
    start_date: datetime = field(validator=validators.optional(validators.instance_of(datetime)))
    expiration_date: datetime = field(validator=validators.optional(validators.instance_of(datetime)))
