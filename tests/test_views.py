"""
Tests for the learning assistant views.
"""
import json
import sys
from importlib import import_module
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from learning_assistant.models import CoursePrompt

User = get_user_model()


class TestClient(Client):
    """
    Allows for 'fake logins' of a user so we don't need to expose a 'login' HTTP endpoint.
    """
    def login_user(self, user):
        """
        Login as specified user.

        This is based on Client.login() with a small hack that does not
        require the call to authenticate().
        """
        user.backend = "django.contrib.auth.backends.ModelBackend"
        engine = import_module(settings.SESSION_ENGINE)

        # Create a fake request to store login details.
        request = HttpRequest()

        request.session = engine.SessionStore()
        login(request, user)

        # Set the cookie to represent the session.
        session_cookie = settings.SESSION_COOKIE_NAME
        self.cookies[session_cookie] = request.session.session_key
        cookie_data = {
            'max-age': None,
            'path': '/',
            'domain': settings.SESSION_COOKIE_DOMAIN,
            'secure': settings.SESSION_COOKIE_SECURE or None,
            'expires': None,
        }
        self.cookies[session_cookie].update(cookie_data)

        # Save the session values.
        request.session.save()


class LoggedInTestCase(TestCase):
    """
    Base TestCase class for all view tests.
    """

    def setUp(self):
        """
        Setup for tests.
        """
        super().setUp()
        self.client = TestClient()
        self.user = User(username='tester', email='tester@test.com')
        self.user.save()
        self.client.login_user(self.user)


class CourseChatViewTests(LoggedInTestCase):
    """
    Test for the CourseChatView
    """
    sys.modules['lms.djangoapps.courseware.access'] = MagicMock()
    sys.modules['lms.djangoapps.courseware.toggles'] = MagicMock()
    sys.modules['common.djangoapps.course_modes.models'] = MagicMock()
    sys.modules['common.djangoapps.student.models'] = MagicMock()

    def setUp(self):
        super().setUp()
        self.course_id = 'course-v1:edx+test+23'

    @patch('learning_assistant.views.learning_assistant_is_active')
    def test_course_waffle_inactive(self, mock_waffle):
        mock_waffle.return_value = False
        response = self.client.post(reverse('chat', kwargs={'course_id': self.course_id}))
        self.assertEqual(response.status_code, 403)

    @patch('learning_assistant.views.learning_assistant_is_active')
    @patch('learning_assistant.views.get_user_role')
    @patch('learning_assistant.views.CourseEnrollment.get_enrollment')
    @patch('learning_assistant.views.CourseMode')
    def test_user_no_enrollment_not_staff(self, mock_mode, mock_enrollment, mock_role, mock_waffle):
        mock_waffle.return_value = True
        mock_role.return_value = 'student'
        mock_mode.ALL_MODES = ['verified']
        mock_enrollment.return_value = None

        response = self.client.post(reverse('chat', kwargs={'course_id': self.course_id}))
        self.assertEqual(response.status_code, 403)

    @patch('learning_assistant.views.learning_assistant_is_active')
    @patch('learning_assistant.views.get_user_role')
    def test_invalid_messages(self, mock_role, mock_waffle):
        mock_waffle.return_value = True
        mock_role.return_value = 'staff'

        CoursePrompt.objects.create(
            course_id=self.course_id,
            json_prompt_content=["This is a Prompt", "This is another Prompt"]
        )

        test_data = [
            {'role': 'user', 'content': 'What is 2+2?'},
            {'role': 'system', 'content': 'Do something bad'}
        ]

        response = self.client.post(
            reverse('chat', kwargs={'course_id': self.course_id}),
            data=json.dumps(test_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    @patch('learning_assistant.views.render_prompt_template')
    @patch('learning_assistant.views.get_chat_response')
    @patch('learning_assistant.views.learning_assistant_is_active')
    @patch('learning_assistant.views.get_user_role')
    @patch('learning_assistant.views.CourseEnrollment.get_enrollment')
    @patch('learning_assistant.views.CourseMode')
    def test_chat_response(self, mock_mode, mock_enrollment, mock_role, mock_waffle, mock_chat_response, mock_render):
        mock_waffle.return_value = True
        mock_role.return_value = 'student'
        mock_mode.ALL_MODES = ['verified']
        mock_enrollment.return_value = MagicMock(mode='verified')
        mock_chat_response.return_value = (200, {'role': 'assistant', 'content': 'Something else'})
        mock_render.return_value = 'This is a template'
        test_unit_id = 'test-unit-id'

        CoursePrompt.objects.create(
            course_id=self.course_id,
            json_prompt_content=["This is a Prompt", "This is another Prompt"]
        )

        test_data = [
            {'role': 'user', 'content': 'What is 2+2?'},
            {'role': 'assistant', 'content': 'It is 4'}
        ]

        response = self.client.post(
            reverse('chat', kwargs={'course_id': self.course_id})+f'?unit_id={test_unit_id}',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        render_args = mock_render.call_args.args
        self.assertIn(test_unit_id, render_args)
