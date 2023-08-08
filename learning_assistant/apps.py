"""
learning_assistant Django application initialization.
"""

from django.apps import AppConfig


class LearningAssistantConfig(AppConfig):
    """
    Configuration for the learning_assistant Django application.
    """

    name = 'learning_assistant'

    plugin_app = {
        'url_config': {
            'lms.djangoapp': {
                'namespace': 'learning_assistant',
                'regex': '^api/',
                'relative_path': 'urls',
            },
        }
    }
