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
