"""
Library for the learning_assistant app.
"""
import logging

from django.conf import settings
from django.core.cache import cache
from edx_django_utils.cache import get_cache_key
from jinja2 import BaseLoader, Environment
from opaque_keys import InvalidKeyError

from learning_assistant.constants import ACCEPTED_CATEGORY_TYPES, CATEGORY_TYPE_MAP
from learning_assistant.data import LearningAssistantCourseEnabledData
from learning_assistant.models import LearningAssistantCourseEnabled
from learning_assistant.platform_imports import (
    block_get_children,
    block_leaf_filter,
    get_cache_course_data,
    get_cache_course_run_data,
    get_single_block,
    get_text_transcript,
    traverse_block_pre_order,
)
from learning_assistant.text_utils import html_to_text

log = logging.getLogger(__name__)


def _extract_block_contents(child, category):
    """
    Process the child contents based on its category.

    Returns a string or None if there are no contents available.
    """
    if category == 'html':
        content_html = child.get_html()
        text = html_to_text(content_html)
        return text

    if category == 'video':
        transcript = get_text_transcript(child)  # may be None
        return transcript

    return None


def _leaf_filter(block):
    """
    Return only leaf nodes of a particular category.
    """
    is_leaf = block_leaf_filter(block)
    category = block.category

    return is_leaf and category in ACCEPTED_CATEGORY_TYPES


def _get_children_contents(block):
    """
    Given a specific block, return the content type and text of a pre-order traversal of the blocks children.
    """
    leaf_nodes = traverse_block_pre_order(block, block_get_children, _leaf_filter)

    length = 0
    items = []

    for node in leaf_nodes:
        category = node.category
        content = _extract_block_contents(node, category)

        if content:
            length += len(content)
            items.append({
                'content_type': CATEGORY_TYPE_MAP.get(category),
                'content_text': content,
            })

    return length, items


def get_block_content(request, user_id, course_id, unit_usage_key):
    """
    Public wrapper for retrieving the content of a given block's children.

    Returns
        length - the cummulative length of a block's children's content
        items - a list of dictionaries containing the content type and text for each child
    """
    cache_key = get_cache_key(
        resource='learning_assistant',
        user_id=user_id,
        course_id=course_id,
        unit_usage_key=unit_usage_key
    )
    cache_data = cache.get(cache_key)

    if not isinstance(cache_data, dict):
        block = get_single_block(request, user_id, course_id, unit_usage_key)
        length, items = _get_children_contents(block)
        cache_data = {'content_length': length, 'content_items': items}
        cache.set(cache_key, cache_data, getattr(settings, 'LEARNING_ASSISTANT_CACHE_TIMEOUT', 360))

    return cache_data['content_length'], cache_data['content_items']


def render_prompt_template(request, user_id, course_run_id, unit_usage_key, course_id, template_string):
    """
    Return a rendered prompt template.
    """
    unit_content = ''

    if unit_usage_key:
        try:
            _, unit_content = get_block_content(request, user_id, course_run_id, unit_usage_key)
        except InvalidKeyError:
            log.warning(
                'Failed to retrieve course content for course_id=%(course_run_id)s because of '
                'invalid unit_id=%(unit_usage_key)s',
                {'course_run_id': course_run_id, 'unit_usage_key': unit_usage_key}
            )

    course_data = get_cache_course_data(course_id, ['skill_names', 'title'])
    skill_names = course_data['skill_names']
    title = course_data['title']

    template = Environment(loader=BaseLoader).from_string(template_string)
    data = template.render(unit_content=unit_content, skill_names=skill_names, title=title)
    return data


def learning_assistant_available():
    """
    Return whether or not the learning assistant is available via django setting or course waffle flag.
    """
    return getattr(settings, 'LEARNING_ASSISTANT_AVAILABLE', False)


def learning_assistant_enabled(course_key):
    """
    Return whether the Learning Assistant is enabled in the course represented by the course_key.

    The Learning Assistant is enabled if the feature is available (i.e. appropriate CourseWaffleFlag is enabled) and
    either there is no override in the LearningAssistantCourseEnabled table or there is an enabled value in the
    LearningAssistantCourseEnabled table.

    Arguments:
        * course_key: (CourseKey): the course's key

    Returns:
        * bool: whether the Learning Assistant is enabled
    """
    try:
        obj = LearningAssistantCourseEnabled.objects.get(course_id=course_key)
        enabled = obj.enabled
    except LearningAssistantCourseEnabled.DoesNotExist:
        # Currently, the Learning Assistant defaults to enabled if there is no override.
        enabled = True

    return learning_assistant_available() and enabled


def set_learning_assistant_enabled(course_key, enabled):
    """
    Set whether the Learning Assistant is enabled and return a representation of the created data.

    Arguments:
        * course_key: (CourseKey): the course's key
        * enabled (bool): whether the Learning Assistant should be enabled

    Returns:
        * bool: whether the Learning Assistant is enabled
    """
    obj, _ = LearningAssistantCourseEnabled.objects.update_or_create(
        course_id=course_key,
        defaults={'enabled': enabled}
    )

    return LearningAssistantCourseEnabledData(
        course_key=obj.course_id,
        enabled=obj.enabled
    )


def get_course_id(course_run_id):
    """
    Given a course run id (str), return the associated course key.
    """
    course_data = get_cache_course_run_data(course_run_id, ['course'])
    course_key = course_data['course']
    return course_key
