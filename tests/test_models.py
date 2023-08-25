#!/usr/bin/env python
"""
Tests for the `learning-assistant` models module.
"""
from django.test import TestCase

from learning_assistant.models import CoursePrompt


class CoursePromptTests(TestCase):
    """
    Test suite for the CoursePrompt model
    """

    def setUp(self):
        self.course_id = 'course-v1:edx+test+23'
        self.prompt = ["This is a Prompt", "This is another Prompt"]
        self.course_prompt = CoursePrompt.objects.create(
            course_id=self.course_id,
            json_prompt_content=self.prompt,
        )
        return super().setUp()

    def test_get_prompt_by_course_id(self):
        """
        Test that a prompt can be retrieved by course ID
        """
        prompt = CoursePrompt.get_json_prompt_content_by_course_id(self.course_id)
        self.assertEqual(prompt, self.prompt)

    def test_get_prompt_by_course_id_invalid(self):
        """
        Test that None is returned if the given course ID does not exist
        """
        prompt = CoursePrompt.get_json_prompt_content_by_course_id('course-v1:edx+fake+19')
        self.assertIsNone(prompt)
