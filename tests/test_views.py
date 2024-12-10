"""
Tests for the learning assistant views.
"""
import json
import sys
from datetime import date, datetime, timedelta
from importlib import import_module
from itertools import product
from unittest.mock import MagicMock, call, patch
from urllib.parse import urlencode

import ddt
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import HttpRequest
from django.test import TestCase, override_settings
from django.test.client import Client
from django.urls import reverse
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from learning_assistant.models import LearningAssistantAuditTrial, LearningAssistantMessage

User = get_user_model()


class FakeClient(Client):
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
        self.client = FakeClient()
        self.user = User(username='tester', email='tester@test.com', is_staff=True)
        self.user.save()
        self.client.login_user(self.user)


@ddt.ddt
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
        self.course_run_key = CourseKey.from_string(self.course_id)

        self.patcher = patch(
            'learning_assistant.api.get_cache_course_run_data',
            return_value={'course': 'edx+test'}
        )
        self.patcher.start()

    @patch('learning_assistant.views.learning_assistant_enabled')
    def test_course_waffle_inactive(self, mock_waffle):
        mock_waffle.return_value = False
        response = self.client.post(reverse('chat', kwargs={'course_run_id': self.course_id}))
        self.assertEqual(response.status_code, 403)

    @patch('learning_assistant.views.render_prompt_template')
    @patch('learning_assistant.views.learning_assistant_enabled')
    @patch('learning_assistant.views.get_user_role')
    @patch('learning_assistant.views.CourseEnrollment')
    @patch('learning_assistant.views.CourseMode')
    def test_invalid_messages(self, mock_mode, mock_enrollment, mock_get_user_role, mock_waffle, mock_render):
        mock_waffle.return_value = True
        mock_get_user_role.return_value = 'staff'
        mock_mode.VERIFIED_MODES = ['verified']
        mock_enrollment.get_enrollment.return_value = MagicMock(mode='verified')

        mock_render.return_value = 'This is a template'
        test_unit_id = 'test-unit-id'

        test_data = [
            {'role': 'user', 'content': 'What is 2+2?'},
            {'role': 'system', 'content': 'Do something bad'}
        ]

        response = self.client.post(
            reverse('chat', kwargs={'course_run_id': self.course_id})+f'?unit_id={test_unit_id}',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    @patch('learning_assistant.views.audit_trial_is_expired')
    @patch('learning_assistant.views.learning_assistant_enabled')
    @patch('learning_assistant.views.get_user_role')
    @patch('learning_assistant.views.CourseEnrollment.get_enrollment')
    @patch('learning_assistant.views.CourseMode')
    def test_audit_trial_expired(self, mock_mode, mock_enrollment,
                                 mock_role, mock_waffle, mock_trial_expired):
        mock_waffle.return_value = True
        mock_role.return_value = 'student'
        mock_mode.VERIFIED_MODES = ['verified']
        mock_mode.CREDIT_MODES = ['credit']
        mock_mode.NO_ID_PROFESSIONAL_MODE = 'no-id'
        mock_mode.UPSELL_TO_VERIFIED_MODES = ['audit']
        mock_mode.objects.get.return_value = MagicMock()
        mock_mode.expiration_datetime.return_value = datetime.now() - timedelta(days=1)
        mock_enrollment.return_value = MagicMock(mode='audit')

        response = self.client.post(reverse('chat', kwargs={'course_run_id': self.course_id}))
        self.assertEqual(response.status_code, 403)
        mock_trial_expired.assert_called_once()

        mock_waffle.reset_mock()
        mock_role.reset_mock()
        mock_mode.reset_mock()
        mock_enrollment.reset_mock()
        mock_trial_expired.reset_mock()

    @patch('learning_assistant.views.learning_assistant_enabled')
    @patch('learning_assistant.views.get_user_role')
    @patch('learning_assistant.views.CourseEnrollment.get_enrollment')
    @patch('learning_assistant.views.CourseMode')
    def test_invalid_enrollment_mode(self, mock_mode, mock_enrollment, mock_role, mock_waffle):
        mock_waffle.return_value = True
        mock_role.return_value = 'student'
        mock_mode.VERIFIED_MODES = ['verified']
        mock_mode.CREDIT_MODES = ['credit']
        mock_mode.NO_ID_PROFESSIONAL_MODE = 'no-id'
        mock_mode.UPSELL_TO_VERIFIED_MODES = ['audit']
        mock_mode.objects.get.return_value = MagicMock()
        mock_mode.expiration_datetime.return_value = datetime.now() - timedelta(days=1)
        mock_enrollment.return_value = MagicMock(mode='unpaid_executive_education')

        response = self.client.post(reverse('chat', kwargs={'course_run_id': self.course_id}))
        self.assertEqual(response.status_code, 403)

    # Test that unexpired audit trials + verified track learners get the default chat response
    @ddt.data((False, 'verified'),
              (True, 'audit'))
    @ddt.unpack
    @patch('learning_assistant.views.audit_trial_is_expired')
    @patch('learning_assistant.views.render_prompt_template')
    @patch('learning_assistant.views.get_chat_response')
    @patch('learning_assistant.views.learning_assistant_enabled')
    @patch('learning_assistant.views.get_user_role')
    @patch('learning_assistant.views.CourseEnrollment')
    @patch('learning_assistant.views.CourseMode')
    @patch('learning_assistant.views.save_chat_message')
    @patch('learning_assistant.views.chat_history_enabled')
    @override_settings(LEARNING_ASSISTANT_PROMPT_TEMPLATE='This is the default template')
    def test_chat_response_default(
        self,
        enabled_flag,
        enrollment_mode,
        mock_chat_history_enabled,
        mock_save_chat_message,
        mock_mode,
        mock_enrollment,
        mock_get_user_role,
        mock_waffle,
        mock_chat_response,
        mock_render,
        mock_trial_expired,
    ):
        mock_waffle.return_value = True
        mock_get_user_role.return_value = 'student'
        mock_mode.VERIFIED_MODES = ['verified']
        mock_mode.CREDIT_MODES = ['credit']
        mock_mode.NO_ID_PROFESSIONAL_MODE = 'no-id'
        mock_mode.UPSELL_TO_VERIFIED_MODES = ['audit']
        mock_enrollment.get_enrollment.return_value = MagicMock(mode=enrollment_mode)
        mock_chat_response.return_value = (200, {'role': 'assistant', 'content': 'Something else'})
        mock_render.return_value = 'Rendered template mock'
        mock_trial_expired.return_value = False
        test_unit_id = 'test-unit-id'

        mock_chat_history_enabled.return_value = enabled_flag

        test_data = [
            {'role': 'user', 'content': 'What is 2+2?'},
            {'role': 'assistant', 'content': 'It is 4'},
            {'role': 'user', 'content': 'And what else?'},
        ]

        response = self.client.post(
            reverse('chat', kwargs={'course_run_id': self.course_id})+f'?unit_id={test_unit_id}',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        render_args = mock_render.call_args.args
        self.assertIn(test_unit_id, render_args)
        self.assertIn('This is the default template', render_args)

        mock_chat_response.assert_called_with(
            'Rendered template mock',
            test_data,
        )

        if enabled_flag:
            mock_save_chat_message.assert_has_calls([
                call(self.course_run_key, self.user.id, LearningAssistantMessage.USER_ROLE, test_data[-1]['content']),
                call(self.course_run_key, self.user.id, LearningAssistantMessage.ASSISTANT_ROLE, 'Something else')
            ])
        else:
            mock_save_chat_message.assert_not_called()


@ddt.ddt
class LearningAssistantEnabledViewTests(LoggedInTestCase):
    """
    Test for the LearningAssistantEnabledView
    """
    sys.modules['lms.djangoapps.courseware.access'] = MagicMock()
    sys.modules['lms.djangoapps.courseware.toggles'] = MagicMock()
    sys.modules['common.djangoapps.course_modes.models'] = MagicMock()
    sys.modules['common.djangoapps.student.models'] = MagicMock()

    def setUp(self):
        super().setUp()
        self.course_id = 'course-v1:edx+test+23'

    @ddt.data(
        (True, True),
        (False, False),
    )
    @ddt.unpack
    @patch('learning_assistant.views.learning_assistant_enabled')
    def test_learning_assistant_enabled(self, mock_value, message, mock_learning_assistant_enabled):
        mock_learning_assistant_enabled.return_value = mock_value
        response = self.client.get(reverse('enabled', kwargs={'course_run_id': self.course_id}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'enabled': message})

    @patch('learning_assistant.views.learning_assistant_enabled')
    def test_invalid_course_id(self, mock_learning_assistant_enabled):
        mock_learning_assistant_enabled.return_value = True
        response = self.client.get(reverse('enabled', kwargs={'course_run_id': self.course_id+'+invalid'}))

        self.assertEqual(response.status_code, 400)


class LearningAssistantMessageHistoryViewTests(LoggedInTestCase):
    """
    Tests for the LearningAssistantMessageHistoryView
    """

    def setUp(self):
        super().setUp()
        self.course_id = 'course-v1:edx+test+23'

    @patch('learning_assistant.views.learning_assistant_enabled')
    def test_course_waffle_inactive(self, mock_waffle):
        mock_waffle.return_value = False
        message_count = 5
        response = self.client.get(
            reverse('message-history', kwargs={'course_run_id': self.course_id})+f'?message_count={message_count}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    @patch('learning_assistant.views.learning_assistant_enabled')
    def test_learning_assistant_not_enabled(self, mock_learning_assistant_enabled):
        mock_learning_assistant_enabled.return_value = False
        message_count = 5
        response = self.client.get(
            reverse('message-history', kwargs={'course_run_id': self.course_id})+f'?message_count={message_count}',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 403)

    @patch('learning_assistant.views.chat_history_enabled')
    @patch('learning_assistant.views.learning_assistant_enabled')
    @patch('learning_assistant.views.get_user_role')
    @patch('learning_assistant.views.CourseEnrollment')
    @patch('learning_assistant.views.CourseMode')
    def test_user_no_enrollment_not_staff(
        self,
        mock_mode,
        mock_enrollment,
        mock_get_user_role,
        mock_assistant_waffle,
        mock_history_waffle
    ):
        mock_assistant_waffle.return_value = True
        mock_history_waffle.return_value = True
        mock_get_user_role.return_value = 'student'
        mock_mode.VERIFIED_MODES = ['verified']
        mock_enrollment.get_enrollment = MagicMock(return_value=None)

        message_count = 5
        response = self.client.get(
            reverse('message-history', kwargs={'course_run_id': self.course_id})+f'?message_count={message_count}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    @patch('learning_assistant.views.chat_history_enabled')
    @patch('learning_assistant.views.learning_assistant_enabled')
    @patch('learning_assistant.views.get_user_role')
    @patch('learning_assistant.views.CourseEnrollment')
    @patch('learning_assistant.views.CourseMode')
    def test_user_audit_enrollment_not_staff(
        self,
        mock_mode,
        mock_enrollment,
        mock_get_user_role,
        mock_assistant_waffle,
        mock_history_waffle
    ):
        mock_assistant_waffle.return_value = True
        mock_history_waffle.return_value = True
        mock_get_user_role.return_value = 'student'
        mock_mode.VERIFIED_MODES = ['verified']
        mock_enrollment.get_enrollment.return_value = MagicMock(mode='audit')

        message_count = 5
        response = self.client.get(
            reverse('message-history', kwargs={'course_run_id': self.course_id})+f'?message_count={message_count}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    @patch('learning_assistant.views.chat_history_enabled')
    @patch('learning_assistant.views.learning_assistant_enabled')
    @patch('learning_assistant.views.get_user_role')
    @patch('learning_assistant.views.CourseEnrollment')
    @patch('learning_assistant.views.CourseMode')
    @patch('learning_assistant.views.get_course_id')
    def test_learning_message_history_view_get(
        self,
        mock_get_course_id,
        mock_mode,
        mock_enrollment,
        mock_get_user_role,
        mock_assistant_waffle,
        mock_history_waffle,
    ):
        mock_assistant_waffle.return_value = True
        mock_history_waffle.return_value = True
        mock_get_user_role.return_value = 'student'
        mock_mode.VERIFIED_MODES = ['verified']
        mock_enrollment.get_enrollment.return_value = MagicMock(mode='verified')

        LearningAssistantMessage.objects.create(
            course_id=self.course_id,
            user=self.user,
            role='staff',
            content='Older message',
            created=date(2024, 10, 1)
        )

        LearningAssistantMessage.objects.create(
            course_id=self.course_id,
            user=self.user,
            role='staff',
            content='Newer message',
            created=date(2024, 10, 3)
        )

        db_messages = LearningAssistantMessage.objects.all().order_by('created')
        db_messages_count = len(db_messages)

        mock_get_course_id.return_value = self.course_id
        response = self.client.get(
            reverse('message-history', kwargs={'course_run_id': self.course_id})+f'?message_count={db_messages_count}',
            content_type='application/json'
        )
        data = response.data

        # Ensure same number of entries
        self.assertEqual(len(data), db_messages_count)

        # Ensure values are as expected
        for i, message in enumerate(data):
            self.assertEqual(message['role'], db_messages[i].role)
            self.assertEqual(message['content'], db_messages[i].content)
            self.assertEqual(message['timestamp'], db_messages[i].created.isoformat())

    @patch('learning_assistant.views.chat_history_enabled')
    @patch('learning_assistant.views.learning_assistant_enabled')
    @patch('learning_assistant.views.get_course_id')
    def test_learning_message_history_view_get_disabled(
        self,
        mock_get_course_id,
        mock_assistant_waffle,
        mock_history_waffle,
    ):
        mock_assistant_waffle.return_value = True
        mock_history_waffle.return_value = False

        LearningAssistantMessage.objects.create(
            course_id=self.course_id,
            user=self.user,
            role='staff',
            content='Older message',
            created=date(2024, 10, 1)
        )

        LearningAssistantMessage.objects.create(
            course_id=self.course_id,
            user=self.user,
            role='staff',
            content='Newer message',
            created=date(2024, 10, 3)
        )

        db_messages = LearningAssistantMessage.objects.all().order_by('created')
        db_messages_count = len(db_messages)

        mock_get_course_id.return_value = self.course_id
        response = self.client.get(
            reverse('message-history', kwargs={'course_run_id': self.course_id})+f'?message_count={db_messages_count}',
            content_type='application/json'
        )
        data = response.data

        # Ensure returning an empty list
        self.assertEqual(len(data), 0)
        self.assertEqual(data, [])


@ddt.ddt
class LearningAssistantChatSummaryViewTests(LoggedInTestCase):
    """
    Tests for the LearningAssistantChatSummaryView
    """
    sys.modules['lms.djangoapps.courseware.access'] = MagicMock()
    sys.modules['lms.djangoapps.courseware.toggles'] = MagicMock()
    sys.modules['common.djangoapps.course_modes.models'] = MagicMock()
    sys.modules['common.djangoapps.student.models'] = MagicMock()

    def setUp(self):
        super().setUp()
        self.course_id = 'course-v1:edx+test+23'

    @patch('learning_assistant.views.CourseKey')
    def test_invalid_course_id(self, mock_course_key):
        mock_course_key.from_string = MagicMock(side_effect=InvalidKeyError('foo', 'bar'))

        response = self.client.get(reverse('chat-summary', kwargs={'course_run_id': self.course_id+'+invalid'}))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], 'Course ID is not a valid course ID.')

    @ddt.data(
        *product(
            [True, False],                                   # learning assistant enabled
            [True, False],                                   # chat history enabled
            ['staff', 'instructor'],                         # user role
            ['verified', 'credit', 'no-id', 'audit', None],  # course mode
            [True, False],                                   # trial available
            [True, False],                                   # trial expired
            [7, 14],                                         # trial length
        )
    )
    @ddt.unpack
    @patch('learning_assistant.views.audit_trial_is_expired')
    @patch('learning_assistant.views.chat_history_enabled')
    @patch('learning_assistant.views.learning_assistant_enabled')
    @patch('learning_assistant.views.get_audit_trial_length_days')
    @patch('learning_assistant.views.get_user_role')
    @patch('learning_assistant.views.CourseEnrollment')
    @patch('learning_assistant.views.CourseMode')
    def test_chat_summary_with_access_instructor(
        self,
        learning_assistant_enabled_mock_value,
        chat_history_enabled_mock_value,
        user_role_mock_value,
        course_mode_mock_value,
        trial_available,
        audit_trial_is_expired_mock_value,
        audit_trial_length_days_mock_value,
        mock_mode,
        mock_enrollment,
        mock_get_user_role,
        mock_get_audit_trial_length_days,
        mock_learning_assistant_enabled,
        mock_chat_history_enabled,
        mock_audit_trial_is_expired,
    ):
        # Set up mocks.
        mock_learning_assistant_enabled.return_value = learning_assistant_enabled_mock_value
        mock_chat_history_enabled.return_value = chat_history_enabled_mock_value

        mock_get_user_role.return_value = user_role_mock_value

        mock_mode.VERIFIED_MODES = ['verified']
        mock_mode.CREDIT_MODES = ['credit']
        mock_mode.NO_ID_PROFESSIONAL_MODE = 'no-id'
        mock_mode.UPSELL_TO_VERIFIED_MODES = ['audit']

        mock_enrollment.get_enrollment.return_value = MagicMock(mode=course_mode_mock_value)

        # Set up message history data.
        if chat_history_enabled_mock_value:
            LearningAssistantMessage.objects.create(
                course_id=self.course_id,
                user=self.user,
                role='user',
                content='Older message',
                created=date(2024, 10, 1)
            )

            LearningAssistantMessage.objects.create(
                course_id=self.course_id,
                user=self.user,
                role='user',
                content='Newer message',
                created=date(2024, 10, 3)
            )

            db_messages = LearningAssistantMessage.objects.all().order_by('created')
            db_messages_count = len(db_messages)

        # Set up audit trial data.
        mock_audit_trial_is_expired.return_value = audit_trial_is_expired_mock_value
        mock_get_audit_trial_length_days.return_value = audit_trial_length_days_mock_value

        trial_start_date = datetime(2024, 1, 1, 0, 0, 0)
        if trial_available:
            LearningAssistantAuditTrial.objects.create(
                user=self.user,
                start_date=trial_start_date,
            )

        url_kwargs = {'course_run_id': self.course_id}
        url = reverse('chat-summary', kwargs=url_kwargs)

        if chat_history_enabled_mock_value:
            query_params = {'message_count': db_messages_count}
            url = f"{url}?{urlencode(query_params)}"

        response = self.client.get(url)

        # Assert message history data is correct.
        if chat_history_enabled_mock_value:
            data = response.data['message_history']

            # Ensure same number of entries.
            self.assertEqual(len(data), db_messages_count)

            # Ensure values are as expected.
            for i, message in enumerate(data):
                self.assertEqual(message['role'], db_messages[i].role)
                self.assertEqual(message['content'], db_messages[i].content)
                self.assertEqual(message['timestamp'], db_messages[i].created.isoformat())
        else:
            self.assertEqual(response.data['message_history'], [])

        # Assert trial data is correct.
        expected_trial_data = {}
        if trial_available:
            expected_trial_data['start_date'] = trial_start_date
            expected_trial_data['expiration_date'] = trial_start_date + timedelta(days=14)

        self.assertEqual(response.data['audit_trial'], expected_trial_data)
        self.assertEqual(response.data['audit_trial_length_days'], audit_trial_length_days_mock_value)

    @ddt.data(
        *product(
            [True, False],                    # learning assistant enabled
            [True, False],                    # chat history enabled
            ['student'],                      # user role
            ['verified', 'credit', 'no-id'],  # course mode
            [True, False],                    # trial available
            [True, False],                    # trial expired
            [7, 14],                          # trial length
        )
    )
    @ddt.unpack
    @patch('learning_assistant.views.audit_trial_is_expired')
    @patch('learning_assistant.views.chat_history_enabled')
    @patch('learning_assistant.views.learning_assistant_enabled')
    @patch('learning_assistant.views.get_audit_trial_length_days')
    @patch('learning_assistant.views.get_user_role')
    @patch('learning_assistant.views.CourseEnrollment')
    @patch('learning_assistant.views.CourseMode')
    def test_chat_summary_with_full_access_student(
        self,
        learning_assistant_enabled_mock_value,
        chat_history_enabled_mock_value,
        user_role_mock_value,
        course_mode_mock_value,
        trial_available,
        audit_trial_is_expired_mock_value,
        audit_trial_length_days_mock_value,
        mock_mode,
        mock_enrollment,
        mock_get_user_role,
        mock_get_audit_trial_length_days,
        mock_learning_assistant_enabled,
        mock_chat_history_enabled,
        mock_audit_trial_is_expired,
    ):
        # Set up mocks.
        mock_learning_assistant_enabled.return_value = learning_assistant_enabled_mock_value
        mock_chat_history_enabled.return_value = chat_history_enabled_mock_value

        mock_get_user_role.return_value = user_role_mock_value

        mock_mode.VERIFIED_MODES = ['verified']
        mock_mode.CREDIT_MODES = ['credit']
        mock_mode.NO_ID_PROFESSIONAL_MODE = 'no-id'
        mock_mode.UPSELL_TO_VERIFIED_MODES = ['audit']

        mock_enrollment.get_enrollment.return_value = MagicMock(mode=course_mode_mock_value)

        # Set up message history data.
        if chat_history_enabled_mock_value:
            LearningAssistantMessage.objects.create(
                course_id=self.course_id,
                user=self.user,
                role='user',
                content='Older message',
                created=date(2024, 10, 1)
            )

            LearningAssistantMessage.objects.create(
                course_id=self.course_id,
                user=self.user,
                role='user',
                content='Newer message',
                created=date(2024, 10, 3)
            )

            db_messages = LearningAssistantMessage.objects.all().order_by('created')
            db_messages_count = len(db_messages)

        # Set up audit trial data.
        mock_audit_trial_is_expired.return_value = audit_trial_is_expired_mock_value
        mock_get_audit_trial_length_days.return_value = audit_trial_length_days_mock_value

        trial_start_date = datetime(2024, 1, 1, 0, 0, 0)
        if trial_available:
            LearningAssistantAuditTrial.objects.create(
                user=self.user,
                start_date=trial_start_date,
            )

        url_kwargs = {'course_run_id': self.course_id}
        url = reverse('chat-summary', kwargs=url_kwargs)

        if chat_history_enabled_mock_value:
            query_params = {'message_count': db_messages_count}
            url = f"{url}?{urlencode(query_params)}"

        response = self.client.get(url)

        # Assert message history data is correct.
        if chat_history_enabled_mock_value:
            data = response.data['message_history']

            # Ensure same number of entries.
            self.assertEqual(len(data), db_messages_count)

            # Ensure values are as expected.
            for i, message in enumerate(data):
                self.assertEqual(message['role'], db_messages[i].role)
                self.assertEqual(message['content'], db_messages[i].content)
                self.assertEqual(message['timestamp'], db_messages[i].created.isoformat())
        else:
            self.assertEqual(response.data['message_history'], [])

        # Assert trial data is correct.
        expected_trial_data = {}
        if trial_available:
            expected_trial_data['start_date'] = trial_start_date
            expected_trial_data['expiration_date'] = trial_start_date + timedelta(days=14)

        self.assertEqual(response.data['audit_trial'], expected_trial_data)
        self.assertEqual(response.data['audit_trial_length_days'], audit_trial_length_days_mock_value)

    @ddt.data(
        *product(
            [True, False],  # learning assistant enabled
            [True, False],  # chat history enabled
            ['student'],    # user role
            ['audit'],      # course mode
            [True, False],  # trial available
            [True, False],  # trial expired
            [7, 14],        # trial length
        )
    )
    @ddt.unpack
    @patch('learning_assistant.views.audit_trial_is_expired')
    @patch('learning_assistant.views.chat_history_enabled')
    @patch('learning_assistant.views.learning_assistant_enabled')
    @patch('learning_assistant.views.get_audit_trial_length_days')
    @patch('learning_assistant.views.get_user_role')
    @patch('learning_assistant.views.CourseEnrollment')
    @patch('learning_assistant.views.CourseMode')
    def test_chat_summary_with_trial_access_student(
        self,
        learning_assistant_enabled_mock_value,
        chat_history_enabled_mock_value,
        user_role_mock_value,
        course_mode_mock_value,
        trial_available,
        audit_trial_is_expired_mock_value,
        audit_trial_length_days_mock_value,
        mock_mode,
        mock_enrollment,
        mock_get_user_role,
        mock_get_audit_trial_length_days,
        mock_learning_assistant_enabled,
        mock_chat_history_enabled,
        mock_audit_trial_is_expired,
    ):
        # Set up mocks.
        mock_learning_assistant_enabled.return_value = learning_assistant_enabled_mock_value
        mock_chat_history_enabled.return_value = chat_history_enabled_mock_value

        mock_get_user_role.return_value = user_role_mock_value

        mock_mode.VERIFIED_MODES = ['verified']
        mock_mode.CREDIT_MODES = ['credit']
        mock_mode.NO_ID_PROFESSIONAL_MODE = 'no-id'
        mock_mode.UPSELL_TO_VERIFIED_MODES = ['audit']

        mock_enrollment.get_enrollment.return_value = MagicMock(mode=course_mode_mock_value)

        # Set up message history data.
        if chat_history_enabled_mock_value:
            LearningAssistantMessage.objects.create(
                course_id=self.course_id,
                user=self.user,
                role='user',
                content='Older message',
                created=date(2024, 10, 1)
            )

            LearningAssistantMessage.objects.create(
                course_id=self.course_id,
                user=self.user,
                role='user',
                content='Newer message',
                created=date(2024, 10, 3)
            )

            db_messages = LearningAssistantMessage.objects.all().order_by('created')
            db_messages_count = len(db_messages)

        # Set up audit trial data.
        mock_audit_trial_is_expired.return_value = audit_trial_is_expired_mock_value
        mock_get_audit_trial_length_days.return_value = audit_trial_length_days_mock_value

        trial_start_date = datetime(2024, 1, 1, 0, 0, 0)
        if trial_available:
            LearningAssistantAuditTrial.objects.create(
                user=self.user,
                start_date=trial_start_date,
            )

        url_kwargs = {'course_run_id': self.course_id}
        url = reverse('chat-summary', kwargs=url_kwargs)

        if chat_history_enabled_mock_value:
            query_params = {'message_count': db_messages_count}
            url = f"{url}?{urlencode(query_params)}"

        response = self.client.get(url)

        # Assert message history data is correct.
        if chat_history_enabled_mock_value and trial_available and not audit_trial_is_expired_mock_value:
            data = response.data['message_history']

            # Ensure same number of entries.
            self.assertEqual(len(data), db_messages_count)

            # Ensure values are as expected.
            for i, message in enumerate(data):
                self.assertEqual(message['role'], db_messages[i].role)
                self.assertEqual(message['content'], db_messages[i].content)
                self.assertEqual(message['timestamp'], db_messages[i].created.isoformat())
        else:
            self.assertEqual(response.data['message_history'], [])

        # Assert trial data is correct.
        expected_trial_data = {}
        if trial_available:
            expected_trial_data['start_date'] = trial_start_date
            expected_trial_data['expiration_date'] = trial_start_date + timedelta(days=14)

        self.assertEqual(response.data['audit_trial'], expected_trial_data)
        self.assertEqual(response.data['audit_trial_length_days'], audit_trial_length_days_mock_value)
