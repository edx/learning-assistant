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
    extract_message_content,
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
    def test_200_response_single_object(self):
        message_response = {'role': 'assistant', 'content': 'See you later!'}
        responses.add(
            responses.POST,
            settings.CHAT_COMPLETION_API,
            status=200,
            body=json.dumps(message_response),
        )

        status_code, message = self.get_response()
        self.assertEqual(status_code, 200)
        # Single objects are returned as-is
        self.assertEqual(message, message_response)

    @responses.activate
    def test_200_response_list_object(self):
        message_response = [
            {'role': 'assistant', 'content': 'Hello!'},
            {'role': 'assistant', 'content': 'See you later!'}
        ]
        responses.add(
            responses.POST,
            settings.CHAT_COMPLETION_API,
            status=200,
            body=json.dumps(message_response),
        )

        status_code, message = self.get_response()
        self.assertEqual(status_code, 200)
        # Lists are returned as-is
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
        # Error messages are returned as-is
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

    @ddt.data(
        # (v2_enabled, response_data, description)
        (False, {'role': 'assistant', 'content': 'v1 response'}, 'v1 single dict'),
        (True, [{'role': 'assistant', 'content': 'v2 response'}], 'v2 array of dicts'),
        (True, {'role': 'assistant', 'content': 'v2 dict'}, 'v2 unexpected dict format'),
    )
    @ddt.unpack
    @responses.activate
    @patch('learning_assistant.utils.v2_endpoint_enabled')
    def test_endpoint_response_formats(self, v2_enabled, response_data, description, mock_v2_enabled):
        """Test that both v1 and v2 endpoint response formats are handled correctly."""
        mock_v2_enabled.return_value = v2_enabled

        endpoint = settings.CHAT_COMPLETION_API_V2 if v2_enabled else settings.CHAT_COMPLETION_API
        responses.add(
            responses.POST,
            endpoint,
            status=200,
            body=json.dumps(response_data),
        )

        status_code, message = self.get_response()
        self.assertEqual(status_code, 200, f"Failed for {description}")
        self.assertEqual(message, response_data, f"Response mismatch for {description}")


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


@ddt.ddt
class ExtractMessageContentTests(TestCase):
    """
    Tests for the extract_message_content utility function
    """

    @patch('learning_assistant.utils.v2_endpoint_enabled')
    def test_v2_endpoint_with_list_dict_message(self, mock_v2_enabled):
        """Test v2 endpoint with list containing dict messages"""
        mock_v2_enabled.return_value = True

        message = [
            {'role': 'assistant', 'content': 'First message'},
            {'role': 'assistant', 'content': 'Last message'}
        ]

        result = extract_message_content(message)
        self.assertEqual(result, 'Last message')

    @patch('learning_assistant.utils.v2_endpoint_enabled')
    def test_v2_endpoint_with_list_non_dict_message(self, mock_v2_enabled):
        """Test v2 endpoint with list containing non-dict messages"""
        mock_v2_enabled.return_value = True

        message = ['First message', 'Last message']

        result = extract_message_content(message)
        self.assertEqual(result, 'Last message')

    @patch('learning_assistant.utils.v2_endpoint_enabled')
    def test_v2_endpoint_with_empty_list(self, mock_v2_enabled):
        """Test v2 endpoint with empty list"""
        mock_v2_enabled.return_value = True

        message = []

        result = extract_message_content(message)
        self.assertEqual(result, '')

    @patch('learning_assistant.utils.v2_endpoint_enabled')
    def test_v2_endpoint_with_dict_missing_content(self, mock_v2_enabled):
        """Test v2 endpoint with dict message missing content key"""
        mock_v2_enabled.return_value = True

        message = [{'role': 'assistant'}]

        result = extract_message_content(message)
        self.assertEqual(result, '')

    @patch('learning_assistant.utils.v2_endpoint_enabled')
    def test_v1_endpoint_with_dict_message(self, mock_v2_enabled):
        """Test v1 endpoint with dict message containing content"""
        mock_v2_enabled.return_value = False

        message = {'role': 'assistant', 'content': 'v1 response'}

        result = extract_message_content(message)
        self.assertEqual(result, 'v1 response')

    @patch('learning_assistant.utils.v2_endpoint_enabled')
    def test_v1_endpoint_with_dict_missing_content(self, mock_v2_enabled):
        """Test v1 endpoint with dict message missing content key"""
        mock_v2_enabled.return_value = False

        message = {'role': 'assistant'}

        result = extract_message_content(message)
        self.assertEqual(result, "{'role': 'assistant'}")

    @patch('learning_assistant.utils.v2_endpoint_enabled')
    def test_fallback_with_string_message(self, mock_v2_enabled):
        """Test fallback case with string message"""
        mock_v2_enabled.return_value = False

        message = 'Error: Something went wrong'

        result = extract_message_content(message)
        self.assertEqual(result, 'Error: Something went wrong')

    @patch('learning_assistant.utils.v2_endpoint_enabled')
    def test_fallback_with_none_message(self, mock_v2_enabled):
        """Test fallback case with None message"""
        mock_v2_enabled.return_value = False

        message = None

        result = extract_message_content(message)
        self.assertEqual(result, 'None')

    @patch('learning_assistant.utils.v2_endpoint_enabled')
    def test_v2_endpoint_mixed_message_types(self, mock_v2_enabled):
        """Test v2 endpoint with mixed message types in list"""
        mock_v2_enabled.return_value = True

        message = [
            'First string message',
            {'role': 'assistant', 'content': 'Dict message'},
            'Last string message'
        ]

        result = extract_message_content(message)
        self.assertEqual(result, 'Last string message')
