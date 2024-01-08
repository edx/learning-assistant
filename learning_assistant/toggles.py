"""
Toggles for learning-assistant app.
"""

WAFFLE_NAMESPACE = 'learning_assistant'

# .. toggle_name: learning_assistant.enable_course_content
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable the course content integration with the learning assistant
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2024-01-08
# .. toggle_target_removal_date: 2024-01-31
# .. toggle_tickets: COSMO-80
ENABLE_COURSE_CONTENT = 'enable_course_content'


def _is_learning_assistant_waffle_flag_enabled(flag_name, course_key):
    """
    Import and return Waffle flag for enabling the summary hook.
    """
    # pylint: disable=import-outside-toplevel
    try:
        from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag
        return CourseWaffleFlag(f'{WAFFLE_NAMESPACE}.{flag_name}', __name__).is_enabled(course_key)
    except ImportError:
        return False


def course_content_enabled(course_key):
    """
    Return whether the learning_assistant.enable_course_content WaffleFlag is on.
    """
    return _is_learning_assistant_waffle_flag_enabled(ENABLE_COURSE_CONTENT, course_key)
