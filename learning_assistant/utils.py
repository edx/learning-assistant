"""
Utils file for learning-assistant.
"""
import logging

import requests
from django.conf import settings
from requests.exceptions import ConnectTimeout
from rest_framework import status as http_status

from learning_assistant.dev_utils import generate_response

log = logging.getLogger(__name__)


def get_chat_response(message_list):
    """
    Pass message list to chat endpoint, as defined by the CHAT_COMPLETION_API setting.
    """
    if auto_response_for_testing_enabled():
        auto_response = generate_response()
        return http_status.HTTP_200_OK, auto_response

    completion_endpoint = getattr(settings, 'CHAT_COMPLETION_API', None)
    if completion_endpoint:
        headers = {'Content-Type': 'application/json'}
        connect_timeout = getattr(settings, 'CHAT_COMPLETION_API_CONNECT_TIMEOUT', 1)
        read_timeout = getattr(settings, 'CHAT_COMPLETION_API_READ_TIMEOUT', 10)

        try:
            response = requests.post(
                completion_endpoint,
                headers=headers,
                data=message_list,
                timeout=(connect_timeout, read_timeout)
            )
            chat = response.json()
            response_status = response.status_code
        except (ConnectTimeout, ConnectionError) as e:
            error_message = str(e)
            connection_message = 'Failed to connect to chat completion API.'
            log.error(
                '%(connection_message)s %(error)s',
                {'connection_message': connection_message, 'error': error_message}
            )
            chat = connection_message
            response_status = http_status.HTTP_502_BAD_GATEWAY
    else:
        response_status = http_status.HTTP_404_NOT_FOUND
        chat = 'Completion endpoint is not defined.'

    return response_status, chat


def auto_response_for_testing_enabled():
    """
    If AUTOMATIC_CHAT_RESPONSE_FOR_TESTING is True, we want to skip making a request to the chat completion endpoint.

    Bypass passing anything to the chat completion endpoint, as that endpoint is defined via a setting that
    is not available in the dev environment.
    """
    return settings.FEATURES.get('AUTOMATIC_CHAT_RESPONSE_FOR_TESTING')
