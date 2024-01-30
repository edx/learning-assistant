"""
URLs for learning_assistant.
"""
from django.urls import re_path

from learning_assistant.constants import COURSE_ID_PATTERN
from learning_assistant.views import CourseChatView, LearningAssistantEnabledView

app_name = 'learning_assistant'

urlpatterns = [
    re_path(
        fr'learning_assistant/v1/course_id/{COURSE_ID_PATTERN}$',
        CourseChatView.as_view(),
        name='chat'
    ),
    re_path(
        fr'learning_assistant/v1/course_id/{COURSE_ID_PATTERN}/enabled',
        LearningAssistantEnabledView.as_view(),
        name='enabled',
    ),
]
