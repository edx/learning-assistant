"""
Utils file for learning-assistant.
"""
import json
import logging

import requests
from django.conf import settings
from requests.exceptions import ConnectTimeout
from rest_framework import status as http_status

log = logging.getLogger(__name__)


def get_chat_response(message_list):
    """
    Pass message list to chat endpoint, as defined by the CHAT_COMPLETION_API setting.
    """
    completion_endpoint = getattr(settings, 'CHAT_COMPLETION_API', None)
    completion_endpoint_key = getattr(settings, 'CHAT_COMPLETION_API_KEY', None)
    if completion_endpoint and completion_endpoint_key:
        headers = {'Content-Type': 'application/json', 'x-api-key': completion_endpoint_key}
        connect_timeout = getattr(settings, 'CHAT_COMPLETION_API_CONNECT_TIMEOUT', 1)
        read_timeout = getattr(settings, 'CHAT_COMPLETION_API_READ_TIMEOUT', 15)
        body = {'message_list': message_list}

        try:
            response = requests.post(
                completion_endpoint,
                headers=headers,
                data=json.dumps(body),
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
