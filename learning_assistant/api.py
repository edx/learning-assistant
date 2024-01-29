"""
Library for the learning_assistant app.
"""
import logging

from django.conf import settings
from django.core.cache import cache
from edx_django_utils.cache import get_cache_key
from jinja2 import BaseLoader, Environment
from opaque_keys.edx.keys import CourseKey

from learning_assistant.constants import ACCEPTED_CATEGORY_TYPES, CATEGORY_TYPE_MAP
from learning_assistant.models import LearningAssistantCourseEnabled
from learning_assistant.platform_imports import (
    block_get_children,
    block_leaf_filter,
    get_single_block,
    get_text_transcript,
    learning_assistant_available,
    traverse_block_pre_order,
)
from learning_assistant.text_utils import html_to_text
from learning_assistant.toggles import course_content_enabled

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


def render_prompt_template(request, user_id, course_id, unit_usage_key):
    """
    Return a rendered prompt template, specified by the LEARNING_ASSISTANT_PROMPT_TEMPLATE setting.
    """
    unit_content = ''

    course_run_key = CourseKey.from_string(course_id)
    if unit_usage_key and course_content_enabled(course_run_key):
        _, unit_content = get_block_content(request, user_id, course_id, unit_usage_key)

    template_string = getattr(settings, 'LEARNING_ASSISTANT_PROMPT_TEMPLATE', '')
    template = Environment(loader=BaseLoader).from_string(template_string)
    data = template.render(unit_content=unit_content)
    return data


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

    return learning_assistant_available(course_key) and enabled
