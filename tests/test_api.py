"""
Test cases for the learning-assistant api module.
"""
from django.test import TestCase

from learning_assistant.api import get_deserialized_prompt_content_by_course_id, get_setup_messages
from learning_assistant.models import CoursePrompt


class LearningAssistantAPITests(TestCase):
    """
    Test suite for the api module
    """

    def setUp(self):
        self.course_id = 'course-v1:edx+test+23'
        self.prompt = ["This is a Prompt", "This is another Prompt"]
        self.course_prompt = CoursePrompt.objects.create(
            course_id=self.course_id,
            json_prompt_content=self.prompt,
        )
        return super().setUp()

    def test_get_deserialized_prompt_valid_course_id(self):
        prompt_content = get_deserialized_prompt_content_by_course_id(self.course_id)
        expected_content = self.prompt
        self.assertEqual(prompt_content, expected_content)

    def test_get_deserialized_prompt_invalid_course_id(self):
        prompt_content = get_deserialized_prompt_content_by_course_id('course-v1:edx+fake+19')
        self.assertIsNone(prompt_content)

    def test_get_setup_messages(self):
        setup_messages = get_setup_messages(self.course_id)
        expected_messages = [{'role': 'system', 'content': x} for x in self.prompt]
        self.assertEqual(setup_messages, expected_messages)

    def test_get_setup_messages_invalid_course_id(self):
        setup_messages = get_setup_messages('course-v1:edx+fake+19')
        self.assertIsNone(setup_messages)
