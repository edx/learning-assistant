"""
Toggles for learning-assistant app.
"""
try:
    from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag
except ImportError:
    # mock out flag to avoid import errors during testing
    class Flag:
        """Temp class for mocking out django flags for testing purposes."""

        def __init__(self, name, var_name):  # pylint: disable=unused-argument
            """Mock init."""
            self.name = name

    CourseWaffleFlag = Flag


WAFFLE_NAMESPACE = 'learning_assistant'

# .. toggle_name: learning_assistant.enable_course_content
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable the course content integration with the learning assistant
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2024-01-08
# .. toggle_target_removal_date: 2022-01-31
# .. toggle_tickets: COSMO-80
ENABLE_COURSE_CONTENT = CourseWaffleFlag(f'{WAFFLE_NAMESPACE}.enable_course_content', __name__)
