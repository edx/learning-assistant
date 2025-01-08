"""
Toggles for learning-assistant app.
"""

WAFFLE_NAMESPACE = 'learning_assistant'

# .. toggle_name: learning_assistant.enable_chat_history
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable the chat history with the learning assistant
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2024-10-30
# .. toggle_target_removal_date: 2024-12-31
# .. toggle_tickets: COSMO-436
ENABLE_CHAT_HISTORY = 'enable_chat_history'

# .. toggle_name: learning_assistant.enable_v2_endpoint
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable use of the internal Xpert platform v2 endpoint
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2025-01-06
# .. toggle_target_removal_date: 2025-01-31
ENABLE_V2_ENDPOINT = 'enable_v2_endpoint'


def _is_learning_assistant_waffle_flag_enabled(flag_name, course_key=None):
    """
    Import and return Waffle flag for enabling the summary hook.
    """
    # pylint: disable=import-outside-toplevel
    try:
        from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag
        return CourseWaffleFlag(f'{WAFFLE_NAMESPACE}.{flag_name}', __name__).is_enabled(course_key)
    except ImportError:
        return False


def chat_history_enabled(course_key):
    """
    Return whether the learning_assistant.enable_chat_history WaffleFlag is on.
    """
    return _is_learning_assistant_waffle_flag_enabled(ENABLE_CHAT_HISTORY, course_key)


def v2_endpoint_enabled():
    """
    Return whether the learning_assistant.enable_v2_endpoint WaffleFlag is on.
    """
    return _is_learning_assistant_waffle_flag_enabled(ENABLE_V2_ENDPOINT)
