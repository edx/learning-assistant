"""
Constants for the learning_assistant app.
"""
# Pulled from edx-platform. Will correctly capture both old- and new-style
# course ID strings.
INTERNAL_COURSE_KEY_PATTERN = r'([^/+]+(?:/|\+)[^/+]+(?:/|\+)[^/?]+)'

EXTERNAL_COURSE_KEY_PATTERN = r'([A-Za-z0-9-_:]+)'

COURSE_ID_PATTERN = fr'(?P<course_run_id>({INTERNAL_COURSE_KEY_PATTERN}|{EXTERNAL_COURSE_KEY_PATTERN}))'

ACCEPTED_CATEGORY_TYPES = ['html', 'video']
CATEGORY_TYPE_MAP = {
    "html": "TEXT",
    "video": "VIDEO",
}

AUDIT_TRIAL_MAX_DAYS = 14

LMS_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

# Error handling constants
CHAT_API_ERROR_MESSAGES = {
    'connection_timeout': 'Connection to chat completion API timed out. Please try again.',
    'connection_error': 'Failed to connect to chat completion API. Please check your network connection.',
    'invalid_response': 'Received invalid response from chat completion API.',
    'api_unavailable': 'Chat completion API is currently unavailable.',
    'rate_limit_exceeded': 'Rate limit exceeded. Please wait before making another request.',
    'invalid_request': 'Invalid request format sent to chat completion API.',
    'service_error': 'Chat completion service encountered an error.',
}

# Request timeout constants
DEFAULT_CONNECT_TIMEOUT = 1
DEFAULT_READ_TIMEOUT = 15
MAX_RETRY_ATTEMPTS = 3

# Token estimation constants
DEFAULT_CHARS_PER_TOKEN = 3.5
JSON_PADDING_TOKENS = 8
TOKEN_ESTIMATION_CACHE_TIMEOUT = 300  # 5 minutes

# Cache key prefixes
CACHE_KEY_PREFIXES = {
    'learning_assistant': 'learning_assistant',
    'token_estimation': 'token_estimation',
    'chat_response': 'chat_response',
}
