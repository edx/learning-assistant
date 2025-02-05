"""
These settings are here to use during tests, because django requires them.

In a real-world use case, apps in this project are installed into other
Django applications, so these settings will not be used.
"""

from os.path import abspath, dirname, join


def root(*args):
    """
    Get the absolute path of the given path relative to the project root.
    """
    return join(abspath(dirname(__file__)), *args)


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'default.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'learning_assistant',
)

LOCALE_PATHS = [
    root('learning_assistant', 'conf', 'locale'),
]

ROOT_URLCONF = 'learning_assistant.urls'

SECRET_KEY = 'insecure-secret-key'

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': False,
    'OPTIONS': {
        'context_processors': [
            'django.contrib.auth.context_processors.auth',  # this is required for admin
            'django.contrib.messages.context_processors.messages',  # this is required for admin
        ],
    },
}]

CHAT_COMPLETION_API = 'https://test.edx.org/'
CHAT_COMPLETION_API_V2 = 'https://test.edx.org/v2'
CHAT_COMPLETION_API_CONNECT_TIMEOUT = 0.5
CHAT_COMPLETION_API_READ_TIMEOUT = 10

DISCOVERY_BASE_URL = 'http://edx.devstack.discovery:18381'
DISCOVERY_BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL = 'http://edx.devstack.lms:18000/oauth2'
DISCOVERY_BACKEND_SERVICE_EDX_OAUTH2_KEY = 'discovery-backend-service-key'
DISCOVERY_BACKEND_SERVICE_EDX_OAUTH2_SECRET = 'discovery-backend-service-secret'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

LEARNING_ASSISTANT_PROMPT_TEMPLATE = (
    "This is a prompt. {% if unit_content %}"
    "The following text is useful."
    "\""
    "{{ unit_content }}"
    "\""
    "{% endif %}"
    "{{ skill_names }}"
    "{{ title }}"
)

LEARNING_ASSISTANT_AVAILABLE = True

LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS = 14

OPTIMIZELY_FULL_STACK_SDK_KEY = ''
OPTIMIZELY_LEARNING_ASSISTANT_TRIAL_VARIATION_KEY = 'variation'
OPTIMIZELY_LEARNING_ASSISTANT_TRIAL_EXPERIMENT_KEY = 'experiment'
