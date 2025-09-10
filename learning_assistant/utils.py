"""
Utils file for learning-assistant.
"""
import copy
import json
import logging
from datetime import datetime

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils.translation import get_language
from optimizely import Optimizely
from requests.exceptions import ConnectTimeout, ConnectionError, ReadTimeout, Timeout
from rest_framework import status as http_status

from learning_assistant.constants import (
    CHAT_API_ERROR_MESSAGES,
    DEFAULT_CHARS_PER_TOKEN,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_READ_TIMEOUT,
    JSON_PADDING_TOKENS,
    LMS_DATETIME_FORMAT,
    MAX_RETRY_ATTEMPTS,
    TOKEN_ESTIMATION_CACHE_TIMEOUT,
)
from learning_assistant.toggles import v2_endpoint_enabled

log = logging.getLogger(__name__)


def estimated_message_tokens(message, use_cache=True):
    """
    Estimates how many tokens are in a given message.
    
    Args:
        message (str): The message to estimate tokens for
        use_cache (bool): Whether to use caching for repeated estimations
        
    Returns:
        int: Estimated number of tokens
        
    Raises:
        ValueError: If message is not a string or is empty
    """
    if not isinstance(message, str):
        raise ValueError("Message must be a string")
    
    if not message.strip():
        return JSON_PADDING_TOKENS
    
    # Use cache for repeated estimations if enabled
    if use_cache:
        cache_key = f"token_estimation:{hash(message)}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
    
    chars_per_token = getattr(settings, 'CHAT_COMPLETION_CHARS_PER_TOKEN', DEFAULT_CHARS_PER_TOKEN)
    json_padding = getattr(settings, 'CHAT_COMPLETION_JSON_PADDING_TOKENS', JSON_PADDING_TOKENS)

    # More accurate estimation considering whitespace
    non_whitespace_chars = len(message.replace(' ', '').replace('\n', '').replace('\t', ''))
    estimated_tokens = int(non_whitespace_chars / chars_per_token) + json_padding
    
    # Cache the result if caching is enabled
    if use_cache:
        cache.set(cache_key, estimated_tokens, TOKEN_ESTIMATION_CACHE_TIMEOUT)
    
    return estimated_tokens


def get_reduced_message_list(prompt_template, message_list):
    """
    If messages are larger than allotted token amount, return a smaller list of messages.
    
    Args:
        prompt_template (str): The system prompt template
        message_list (list): List of message dictionaries with 'content' key
        
    Returns:
        list: Reduced list of messages that fit within token limits
        
    Raises:
        ValueError: If inputs are invalid
    """
    if not isinstance(prompt_template, str):
        raise ValueError("Prompt template must be a string")
    
    if not isinstance(message_list, list):
        raise ValueError("Message list must be a list")
    
    # Validate message structure
    for i, message in enumerate(message_list):
        if not isinstance(message, dict) or 'content' not in message:
            raise ValueError(f"Message at index {i} must be a dictionary with 'content' key")
        if not isinstance(message['content'], str):
            raise ValueError(f"Message content at index {i} must be a string")
    
    try:
        total_system_tokens = estimated_message_tokens(prompt_template)
    except ValueError as e:
        log.error(f"Error estimating tokens for prompt template: {e}")
        raise

    max_tokens = getattr(settings, 'CHAT_COMPLETION_MAX_TOKENS', 16385)
    response_tokens = getattr(settings, 'CHAT_COMPLETION_RESPONSE_TOKENS', 1000)
    remaining_tokens = max_tokens - response_tokens - total_system_tokens

    if remaining_tokens <= 0:
        log.warning("No tokens remaining for messages after system prompt")
        return []

    new_message_list = []
    # use copy of list, as it is modified as part of the reduction
    message_list_copy = copy.deepcopy(message_list)
    total_message_tokens = 0

    while total_message_tokens < remaining_tokens and len(message_list_copy) != 0:
        new_message = message_list_copy.pop()
        try:
            message_tokens = estimated_message_tokens(new_message['content'])
        except ValueError as e:
            log.warning(f"Skipping message due to token estimation error: {e}")
            continue
            
        total_message_tokens += message_tokens
        if total_message_tokens >= remaining_tokens:
            break

        # insert message at beginning of list, because we are traversing the message list from most recent to oldest
        new_message_list.insert(0, new_message)

    log.info(f"Reduced message list from {len(message_list)} to {len(new_message_list)} messages")
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
    
    Args:
        prompt_template (str): The system prompt template
        message_list (list): List of message dictionaries
        
    Returns:
        tuple: (status_code, response_data) where status_code is HTTP status 
               and response_data is either the chat response or error message
               
    Raises:
        ValueError: If inputs are invalid
    """
    # Input validation
    if not isinstance(prompt_template, str) or not prompt_template.strip():
        raise ValueError("Prompt template must be a non-empty string")
    
    if not isinstance(message_list, list):
        raise ValueError("Message list must be a list")
    
    completion_endpoint = getattr(settings, 'CHAT_COMPLETION_API_V2', None) if v2_endpoint_enabled() \
        else getattr(settings, 'CHAT_COMPLETION_API', None)
        
    if not completion_endpoint:
        log.error("Chat completion API endpoint is not configured")
        return http_status.HTTP_404_NOT_FOUND, CHAT_API_ERROR_MESSAGES['api_unavailable']

    headers = {'Content-Type': 'application/json'}
    connect_timeout = getattr(settings, 'CHAT_COMPLETION_API_CONNECT_TIMEOUT', DEFAULT_CONNECT_TIMEOUT)
    read_timeout = getattr(settings, 'CHAT_COMPLETION_API_READ_TIMEOUT', DEFAULT_READ_TIMEOUT)
    max_retries = getattr(settings, 'CHAT_COMPLETION_API_MAX_RETRIES', MAX_RETRY_ATTEMPTS)

    try:
        body = create_request_body(prompt_template, message_list)
    except (ValueError, TypeError) as e:
        log.error(f"Error creating request body: {e}")
        return http_status.HTTP_400_BAD_REQUEST, CHAT_API_ERROR_MESSAGES['invalid_request']

    last_exception = None
    
    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            log.info(f"Attempting chat API request (attempt {attempt + 1}/{max_retries})")
            
            response = requests.post(
                completion_endpoint,
                headers=headers,
                data=json.dumps(body),
                timeout=(connect_timeout, read_timeout)
            )
            
            # Handle HTTP error status codes
            if response.status_code == 429:
                log.warning(f"Rate limit exceeded (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    continue
                return http_status.HTTP_429_TOO_MANY_REQUESTS, CHAT_API_ERROR_MESSAGES['rate_limit_exceeded']
            
            if response.status_code >= 500:
                log.warning(f"Server error {response.status_code} (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    continue
                return response.status_code, CHAT_API_ERROR_MESSAGES['service_error']
            
            if response.status_code >= 400:
                log.error(f"Client error {response.status_code}: {response.text}")
                return response.status_code, CHAT_API_ERROR_MESSAGES['invalid_request']
            
            # Parse response
            try:
                response_json = response.json()
            except (json.JSONDecodeError, ValueError) as e:
                log.error(f"Invalid JSON response: {e}")
                return http_status.HTTP_502_BAD_GATEWAY, CHAT_API_ERROR_MESSAGES['invalid_response']
            
            # Normalize response format
            chat = [response_json]

            log.info("Successfully received chat API response")
            return response.status_code, chat
            
        except ConnectTimeout as e:
            last_exception = e
            log.warning(f"Connection timeout (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                continue
                
        except ReadTimeout as e:
            last_exception = e
            log.warning(f"Read timeout (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                continue
                
        except ConnectionError as e:
            last_exception = e
            log.warning(f"Connection error (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                continue
                
        except Exception as e:
            last_exception = e
            log.error(f"Unexpected error (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                continue
    
    # If we've exhausted all retries, return appropriate error
    if isinstance(last_exception, (ConnectTimeout, ReadTimeout)):
        error_message = CHAT_API_ERROR_MESSAGES['connection_timeout']
        status_code = http_status.HTTP_504_GATEWAY_TIMEOUT
    elif isinstance(last_exception, ConnectionError):
        error_message = CHAT_API_ERROR_MESSAGES['connection_error']
        status_code = http_status.HTTP_502_BAD_GATEWAY
    else:
        error_message = CHAT_API_ERROR_MESSAGES['service_error']
        status_code = http_status.HTTP_502_BAD_GATEWAY
    
    log.error(f"All {max_retries} attempts failed. Last error: {str(last_exception)}")
    return status_code, error_message


def user_role_is_staff(role):
    """
    Return whether the user role parameter represents that of a staff member.

    Arguments:
    * role (str): the user's role

    Returns:
    * bool: whether the user's role is that of a staff member
    """
    return role in ('staff', 'instructor')


def get_optimizely_variation(user_id, enrollment_mode):
    """
    Return whether or not optimizely experiment is enabled, and which variation a user belongs to.

    Arguments:
    * user_id
    * enrollment_mode

    Returns:
    * {
        'enabled': whether or not experiment is enabled,
        'variation_key': what variation a user is assigned to
      }
    """
    if not getattr(settings, 'OPTIMIZELY_FULLSTACK_SDK_KEY', None):
        enabled = False
        variation_key = None
    else:
        optimizely_client = optimizely.Optimizely(sdk_key=settings.OPTIMIZELY_FULLSTACK_SDK_KEY)
        user = optimizely_client.create_user_context(str(user_id),
                                                     {'lms_language_preference': get_language(),
                                                      'lms_enrollment_mode': enrollment_mode})
        decision = user.decide(getattr(settings, 'OPTIMIZELY_LEARNING_ASSISTANT_TRIAL_EXPERIMENT_KEY', ''))
        enabled = decision.enabled
        variation_key = decision.variation_key

    return {'enabled': enabled, 'variation_key': variation_key}


def get_audit_trial_length_days(user_id, enrollment_mode):
    """
    Return the length of an audit trial in days.

    Arguments:
    * user_id
    * enrollment_mode

    Returns:
    * int: the length of an audit trial in days
    """
    variation = get_optimizely_variation(user_id, enrollment_mode)

    # For the sake of the experiment on the backend, the only difference in behavior should be for the 28 day variation.
    # This is because the control group will never see the audit experience, so the value being returned here does not
    # matter, and the 14 day variation can use the default trial length of 14 days.
    if (
        variation['enabled']
        and variation['variation_key'] == getattr(settings, 'OPTIMIZELY_LEARNING_ASSISTANT_TRIAL_VARIATION_KEY_28', '')
    ):
        trial_length_days = 28
    else:
        default_trial_length_days = 14
        trial_length_days = getattr(settings, 'LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS', default_trial_length_days)

    if trial_length_days is None:
        trial_length_days = default_trial_length_days

    # If LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS is set to a negative number, assume it should be 0.
    # pylint: disable=consider-using-max-builtin, no-else-return
    trial_length_days = max(trial_length_days, 0)
        trial_length_days = 0

    return trial_length_days


def parse_lms_datetime(datetime_string):
    """
    Parse an LMS datetime into a timezone-aware, Python datetime object.

    Arguments:
        datetime_string: A string to be parsed.
    """
    if datetime_string is None:
        return None

    try:
        parsed_datetime = datetime.strptime(datetime_string, LMS_DATETIME_FORMAT)
    except ValueError:
        return None

    return parsed_datetime
