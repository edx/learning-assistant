"""
Tests for the utils functions
"""
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import ddt
import responses
from django.conf import settings
from django.test import TestCase, override_settings
from requests.exceptions import ConnectTimeout

from learning_assistant.constants import LMS_DATETIME_FORMAT
from learning_assistant.utils import (
    get_audit_trial_length_days,
    get_chat_response,
    get_optimizely_variation,
    get_reduced_message_list,
    parse_lms_datetime,
    user_role_is_staff,
)


@ddt.ddt
class GetChatResponseTests(TestCase):
    """
    Tests for the get_chat_response util function
    """
    def setUp(self):
        super().setUp()

        self.prompt_template = 'This is a prompt.'

        self.message_list = [{'role': 'assistant', 'content': 'Hello'}, {'role': 'user', 'content': 'Goodbye'}]
        self.course_id = 'edx+test'

    def get_response(self):
        return get_chat_response(self.prompt_template, self.message_list)

    @override_settings(CHAT_COMPLETION_API=None)
    def test_no_endpoint_setting(self):
        status_code, message = self.get_response()
        self.assertEqual(status_code, 404)
        self.assertEqual(message, 'Completion endpoint is not defined.')

    @responses.activate
    def test_200_response(self):
        message_response = {'role': 'assistant', 'content': 'See you later!'}
        responses.add(
            responses.POST,
            settings.CHAT_COMPLETION_API,
            status=200,
            body=json.dumps(message_response),
        )

        status_code, message = self.get_response()
        self.assertEqual(status_code, 200)
        self.assertEqual(message, message_response)

    @responses.activate
    def test_non_200_response(self):
        message_response = "Server error"
        responses.add(
            responses.POST,
            settings.CHAT_COMPLETION_API,
            status=500,
            body=json.dumps(message_response),
        )

        status_code, message = self.get_response()
        self.assertEqual(status_code, 500)
        self.assertEqual(message, message_response)

    @ddt.data(
        ConnectionError,
        ConnectTimeout
    )
    @patch('learning_assistant.utils.requests')
    def test_timeout(self, exception, mock_requests):
        mock_requests.post = MagicMock(side_effect=exception())
        status_code, _ = self.get_response()
        self.assertEqual(status_code, 502)

    @patch('learning_assistant.utils.requests')
    def test_post_request_structure(self, mock_requests):
        mock_requests.post = MagicMock()

        completion_endpoint = settings.CHAT_COMPLETION_API
        connect_timeout = settings.CHAT_COMPLETION_API_CONNECT_TIMEOUT
        read_timeout = settings.CHAT_COMPLETION_API_READ_TIMEOUT
        headers = {'Content-Type': 'application/json'}

        response_body = {
            'message_list': [{'role': 'system', 'content': self.prompt_template}] + self.message_list,
        }

        self.get_response()
        mock_requests.post.assert_called_with(
            completion_endpoint,
            headers=headers,
            data=json.dumps(response_body),
            timeout=(connect_timeout, read_timeout)
        )

    @patch('learning_assistant.utils.v2_endpoint_enabled')
    @patch('learning_assistant.utils.requests')
    def test_post_request_structure_v2_endpoint(self, mock_requests, mock_v2_enabled):
        mock_requests.post = MagicMock()
        mock_v2_enabled.return_value = True

        completion_endpoint_v2 = settings.CHAT_COMPLETION_API_V2
        connect_timeout = settings.CHAT_COMPLETION_API_CONNECT_TIMEOUT
        read_timeout = settings.CHAT_COMPLETION_API_READ_TIMEOUT
        headers = {'Content-Type': 'application/json'}

        response_body = {
            'client_id': 'edx_olc_la',
            'system_message': self.prompt_template,
            'messages': self.message_list,
        }

        self.get_response()
        mock_requests.post.assert_called_with(
            completion_endpoint_v2,
            headers=headers,
            data=json.dumps(response_body),
            timeout=(connect_timeout, read_timeout)
        )


class GetReducedMessageListTests(TestCase):
    """
    Tests for the _reduced_message_list helper function
    """
    def setUp(self):
        super().setUp()
        self.prompt_template = 'This is a prompt.'
        self.message_list = [
            {'role': 'assistant', 'content': 'Hello'},
            {'role': 'user', 'content': 'Goodbye'},
        ]

    @override_settings(CHAT_COMPLETION_MAX_TOKENS=30)
    @override_settings(CHAT_COMPLETION_RESPONSE_TOKENS=1)
    def test_message_list_reduced(self):
        """
        If the number of tokens in the message list is greater than allowed, assert that messages are removed
        """
        # pass in copy of list, as it is modified as part of the reduction
        reduced_message_list = get_reduced_message_list(self.prompt_template, self.message_list)
        self.assertEqual(len(reduced_message_list), 1)
        self.assertEqual(
            reduced_message_list,
            self.message_list[-1:]
        )

    def test_message_list(self):
        reduced_message_list = get_reduced_message_list(self.prompt_template, self.message_list)
        self.assertEqual(len(reduced_message_list), 2)
        self.assertEqual(
            reduced_message_list,
            self.message_list
        )


@ddt.ddt
class UserRoleIsStaffTests(TestCase):
    """
    Tests for the user_role_is_staff helper function.
    """
    @ddt.data(('instructor', True), ('staff', True), ('student', False))
    @ddt.unpack
    def test_user_role_is_staff(self, role, expected_value):
        self.assertEqual(user_role_is_staff(role), expected_value)


@ddt.ddt
class GetAuditTrialLengthDaysTests(TestCase):
    """
    Tests for the get_audit_trial_length_days helper function.
    """
    @ddt.data(
        (None, 14),
        (0, 0),
        (-7, 0),
        (7, 7),
        (14, 14),
        (28, 28),
    )
    @ddt.unpack
    def test_get_audit_trial_length_days_with_value(self, setting_value, expected_value):
        with patch.object(settings, 'LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS', setting_value):
            self.assertEqual(get_audit_trial_length_days(1, 'verified'), expected_value)

    @override_settings()
    def test_get_audit_trial_length_days_no_setting(self):
        del settings.LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS
        self.assertEqual(get_audit_trial_length_days(1, 'verified'), 14)

    # mock optimizely function
    @ddt.data(
        ('variation', 28),
        ('control', 14),
    )
    @ddt.unpack
    @patch('learning_assistant.utils.get_optimizely_variation')
    def test_get_audit_trial_length_days_experiment(self, variation_key, expected_value, mock_get_optimizely_variation):
        mock_get_optimizely_variation.return_value = {'enabled': True, 'variation_key': variation_key}
        with patch.object(settings, 'OPTIMIZELY_LEARNING_ASSISTANT_TRIAL_VARIATION_KEY_28', 'variation'):
            self.assertEqual(get_audit_trial_length_days(1, 'verified'), expected_value)


class GetOptimizelyVariationTests(TestCase):
    """
    Tests for the get_optimizely_variation helper function.
    """

    def test_no_sdk_key(self):
        expected_value = {'enabled': False, 'variation_key': None}
        self.assertEqual(get_optimizely_variation(1, 'verified'), expected_value)

    @patch('learning_assistant.utils.optimizely')
    def test_return_variation(self, mock_optimizely):
        mock_decision = MagicMock(enabled=True, variation_key='variation')
        mock_decide = MagicMock(return_value=mock_decision)
        mock_user = MagicMock(decide=mock_decide)
        mock_create_user_context = MagicMock(return_value=mock_user)
        mock_optimizely_client = MagicMock(create_user_context=mock_create_user_context)
        mock_optimizely.Optimizely = MagicMock(return_value=mock_optimizely_client)

        with patch.object(settings, 'OPTIMIZELY_FULLSTACK_SDK_KEY', 'sdk_key'):
            expected_value = {'enabled': True, 'variation_key': 'variation'}
            self.assertEqual(get_optimizely_variation(1, 'verified'), expected_value)


class ParseLMSDatetimeTests(TestCase):
    """
    Tests for the parse_lms_datetime helper function.
    """

    def test_correct_date(self):
        expected_value = datetime(1982, 12, 7, 14, 00, 00)
        stringified = expected_value.strftime(LMS_DATETIME_FORMAT)

        response = parse_lms_datetime(stringified)

        self.assertEqual(response, expected_value)

    def test_wrong_date(self):
        expected_value = None

        response = parse_lms_datetime('when I get my homework done')

        self.assertEqual(response, expected_value)
