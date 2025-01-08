"""
Utils file for learning-assistant.
"""
import copy
import json
import logging

import requests
from django.conf import settings
from requests.exceptions import ConnectTimeout
from rest_framework import status as http_status

from learning_assistant.toggles import v2_endpoint_enabled

log = logging.getLogger(__name__)


def _estimated_message_tokens(message):
    """
    Estimates how many tokens are in a given message.
    """
    chars_per_token = 3.5
    json_padding = 8

    return int((len(message) - message.count(' ')) / chars_per_token) + json_padding


def get_reduced_message_list(prompt_template, message_list):
    """
    If messages are larger than allotted token amount, return a smaller list of messages.
    """
    total_system_tokens = _estimated_message_tokens(prompt_template)

    max_tokens = getattr(settings, 'CHAT_COMPLETION_MAX_TOKENS', 16385)
    response_tokens = getattr(settings, 'CHAT_COMPLETION_RESPONSE_TOKENS', 1000)
    remaining_tokens = max_tokens - response_tokens - total_system_tokens

    new_message_list = []
    # use copy of list, as it is modified as part of the reduction
    message_list_copy = copy.deepcopy(message_list)
    total_message_tokens = 0

    while total_message_tokens < remaining_tokens and len(message_list_copy) != 0:
        new_message = message_list_copy.pop()
        total_message_tokens += _estimated_message_tokens(new_message['content'])
        if total_message_tokens >= remaining_tokens:
            break

        # insert message at beginning of list, because we are traversing the message list from most recent to oldest
        new_message_list.insert(0, new_message)

    return new_message_list


def create_request_body(prompt_template, message_list):
    """
    Form request body to be passed to the chat endpoint.
    """
    messages = get_reduced_message_list(prompt_template, message_list)

    response_body = {
        'message_list': [{'role': 'system', 'content': prompt_template}] + messages,
    }

    if v2_endpoint_enabled():
        response_body = {
            'client_id': getattr(settings, 'CHAT_COMPLETION_CLIENT_ID', 'edx_olc_la'),
            'system_message': prompt_template,
            'messages': messages,
        }

    return response_body


def get_chat_response(prompt_template, message_list):
    """
    Pass message list to chat endpoint, as defined by the CHAT_COMPLETION_API setting.
    """
    completion_endpoint = getattr(settings, 'CHAT_COMPLETION_API_V2', None) if v2_endpoint_enabled() \
        else getattr(settings, 'CHAT_COMPLETION_API', None)
    if completion_endpoint:
        headers = {'Content-Type': 'application/json'}
        connect_timeout = getattr(settings, 'CHAT_COMPLETION_API_CONNECT_TIMEOUT', 1)
        read_timeout = getattr(settings, 'CHAT_COMPLETION_API_READ_TIMEOUT', 15)

        body = create_request_body(prompt_template, message_list)

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


def user_role_is_staff(role):
    """
    Return whether the user role parameter represents that of a staff member.

    Arguments:
    * role (str): the user's role

    Returns:
    * bool: whether the user's role is that of a staff member
    """
    return role in ('staff', 'instructor')


def get_audit_trial_length_days():
    """
    Return the length of an audit trial in days.

    Arguments:
    * None

    Returns:
    * int: the length of an audit trial in days
    """
    default_trial_length_days = 14

    trial_length_days = getattr(settings, 'LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS', default_trial_length_days)

    if trial_length_days is None:
        trial_length_days = default_trial_length_days

    # If LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS is set to a negative number, assume it should be 0.
    # pylint: disable=consider-using-max-builtin
    if trial_length_days < 0:
        trial_length_days = 0

    return trial_length_days
