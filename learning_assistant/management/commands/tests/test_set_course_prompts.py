"""
Tests for the set_course_prompts management command.
"""
import json
from posixpath import join as urljoin
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from learning_assistant.models import CoursePrompt


class SetCoursePromptsTests(TestCase):
    """Test set_course_prompts command"""
    command = 'set_course_prompts'

    def setUp(self):
        self.pre_message = 'This is the first message'
        self.skills_descriptor = 'These are the skills: '
        self.post_message = 'This message comes after'
        self.course_ids = 'course-v1:edx+test+23,course-v1:edx+test+24'
        self.course_title = 'Intro to Testing'
        self.skill_names = ['Testing', 'Computers', 'Coding']

    def get_mock_discovery_response(self):
        """
        Create scaled down mock of discovery response
        """
        response_data = {
            'title': self.course_title,
            'skill_names': self.skill_names
        }
        return response_data

    @patch('learning_assistant.management.commands.set_course_prompts.Command._get_discovery_api_client')
    def test_course_prompts_created(self, mock_get_discovery_client):
        """
        Assert that course prompts are created by calling management command.
        """
        mock_client = MagicMock()
        mock_get_discovery_client.return_value = mock_client
        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: self.get_mock_discovery_response()  # pylint: disable=unnecessary-lambda
        )

        call_command(
            self.command,
            course_ids=self.course_ids,
            pre_message=self.pre_message,
            skills_descriptor=self.skills_descriptor,
            post_message=self.post_message,
        )

        # assert that discovery api was called with course id, not course run id
        expected_url = urljoin(
            settings.DISCOVERY_BASE_URL,
            'api/v1/courses/{course_id}'.format(course_id='edx+test')
        )
        mock_client.get.assert_any_call(expected_url)
        mock_client.get.assert_called()

        # assert that number of prompts created is equivalent to number of courses passed in to command
        prompts = CoursePrompt.objects.filter()
        self.assertEqual(len(prompts), len(self.course_ids.split(',')))

        # assert structure of prompt
        course_prompt = prompts[0].json_prompt_content
        self.assertEqual(len(course_prompt), 3)

        skills_message = self.skills_descriptor + json.dumps({'title': self.course_title, 'topics': self.skill_names})
        expected_response = [self.pre_message, skills_message, self.post_message]
        self.assertEqual(course_prompt, expected_response)
