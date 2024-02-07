"""
Data classes for the Learning Assistant application.
"""
from attrs import field, frozen, validators
from opaque_keys.edx.keys import CourseKey


@frozen
class LearningAssistantCourseEnabledData:
    """
    Data class representing whether Learning Assistant is enabled in a course.
    """

    course_key: CourseKey = field(validator=validators.instance_of(CourseKey))
    enabled: bool = field(validator=validators.instance_of(bool))
