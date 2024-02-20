"""
Concrete implementations of abstract methods of the CourseApp plugin ABC, for use by the LearningAssistantCourseApp.

Because the LearningAssistantCourseApp plugin inherits from the CourseApp class, which is imported from the
edx-platform, we cannot test that plugin directly, because pytest will run outside the platform context.
Instead, the CourseApp abstract methods are implemented here and
imported into and used by the LearningAssistantCourseApp. This way, these implementations can be tested.
"""

from learning_assistant.api import (
    learning_assistant_available,
    learning_assistant_enabled,
    set_learning_assistant_enabled,
)
from learning_assistant.platform_imports import get_user_role
from learning_assistant.utils import user_role_is_staff


def is_available():
    """
    Return a boolean indicating this course app's availability for a given course.

    If an app is not available, it will not show up in the UI at all for that course,
    and it will not be possible to enable/disable/configure it, unless the platform wide setting
    LEARNING_ASSISTANT_AVAILABLE is set to True.

    Args:
        course_key (CourseKey): Course key for course whose availability is being checked.

    Returns:
        bool: Availability status of app.
    """
    return learning_assistant_available()


def is_enabled(course_key):
    """
    Return if this course app is enabled for the provided course.

    Args:
        course_key (CourseKey): The course key for the course you
            want to check the status of.

    Returns:
        bool: The status of the course app for the specified course.
    """
    return learning_assistant_enabled(course_key)


# pylint: disable=unused-argument
def set_enabled(course_key, enabled, user):
    """
    Update the status of this app for the provided course and return the new status.

    Args:
        course_key (CourseKey): The course key for the course for which the app should be enabled.
        enabled (bool): The new status of the app.
        user (User): The user performing this operation.

    Returns:
        bool: The new status of the course app.
    """
    obj = set_learning_assistant_enabled(course_key, enabled)

    return obj.enabled


def get_allowed_operations(course_key, user=None):
    """
    Return a dictionary of available operations for this app.

    Not all apps will support being configured, and some may support
    other operations via the UI. This will list, the minimum whether
    the app can be enabled/disabled and whether it can be configured.

    Args:
        course_key (CourseKey): The course key for a course.
        user (User): The user for which the operation is to be tested.

    Returns:
        A dictionary that has keys like 'enable', 'configure' etc
        with values indicating whether those operations are allowed.

        get_allowed_operations: function that returns a dictionary of the form
                                {'enable': <bool>, 'configure': <bool>}.
    """
    if not user:
        return {'configure': False, 'enable': False}
    else:
        user_role = get_user_role(user, course_key)
        is_staff = user_role_is_staff(user_role)

    return {'configure': False, 'enable': is_staff}
