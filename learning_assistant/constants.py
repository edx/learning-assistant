"""
Constants for the learning_assistant app.
"""
# Pulled from edx-platform. Will correctly capture both old- and new-style
# course ID strings.
INTERNAL_COURSE_KEY_PATTERN = r'([^/+]+(/|\+)[^/+]+(/|\+)[^/?]+)'

EXTERNAL_COURSE_KEY_PATTERN = r'([A-Za-z0-9-_:]+)'

COURSE_ID_PATTERN = rf'(?P<course_run_id>({INTERNAL_COURSE_KEY_PATTERN}|{EXTERNAL_COURSE_KEY_PATTERN}))'

ACCEPTED_CATEGORY_TYPES = ['html', 'video']
CATEGORY_TYPE_MAP = {
    "html": "TEXT",
    "video": "VIDEO",
}


class GptModels:
    GPT_3_5_TURBO = 'gpt-3.5-turbo'
    GPT_3_5_TURBO_0125 = 'gpt-3.5-turbo-0125'
    GPT_4o = 'gpt-4o'


class ResponseVariations:
    GPT4_UPDATED_PROMPT = 'updated_prompt'
