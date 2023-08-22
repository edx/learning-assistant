"""
Tests for the utils functions
"""
import json
from unittest.mock import MagicMock, patch

import ddt
import responses
from django.conf import settings
from django.test import TestCase, override_settings
from requests.exceptions import ConnectTimeout

from learning_assistant.utils import get_chat_response


@ddt.ddt
class GetChatResponseTests(TestCase):
    """
    Tests for the get_chat_response util function
    """
    def setUp(self):
        super().setUp()
        self.message_list = [
            {'role': 'assistant', 'content': 'Hello'},
            {'role': 'user', 'content': 'Goodbye'},
        ]

    @override_settings(CHAT_COMPLETION_API=None)
    def test_no_endpoint_setting(self):
        status_code, message = get_chat_response(self.message_list)
        self.assertEqual(status_code, 404)
        self.assertEqual(message, 'Completion endpoint is not defined.')

    @override_settings(CHAT_COMPLETION_API_KEY=None)
    def test_no_endpoint_key_setting(self):
        status_code, message = get_chat_response(self.message_list)
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

        status_code, message = get_chat_response(self.message_list)
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

        status_code, message = get_chat_response(self.message_list)
        self.assertEqual(status_code, 500)
        self.assertEqual(message, message_response)

    @ddt.data(
        ConnectionError,
        ConnectTimeout
    )
    @patch('learning_assistant.utils.requests')
    def test_timeout(self, exception, mock_requests):
        mock_requests.post = MagicMock(side_effect=exception())
        status_code, _ = get_chat_response(self.message_list)
        self.assertEqual(status_code, 502)

    @patch('learning_assistant.utils.requests')
    def test_post_request_structure(self, mock_requests):
        mock_requests.post = MagicMock()

        completion_endpoint = settings.CHAT_COMPLETION_API
        connect_timeout = settings.CHAT_COMPLETION_API_CONNECT_TIMEOUT
        read_timeout = settings.CHAT_COMPLETION_API_READ_TIMEOUT
        headers = {'Content-Type': 'application/json', 'x-api-key': settings.CHAT_COMPLETION_API_KEY}
        body = json.dumps({'message_list': self.message_list})

        get_chat_response(self.message_list)
        mock_requests.post.assert_called_with(
            completion_endpoint,
            headers=headers,
            data=body,
            timeout=(connect_timeout, read_timeout)
        )
