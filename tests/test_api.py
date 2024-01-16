"""
Test cases for the learning-assistant api module.
"""
from unittest.mock import MagicMock, patch

import ddt
from django.core.cache import cache
from django.test import TestCase
from opaque_keys.edx.keys import UsageKey

from learning_assistant.api import (
    _extract_block_contents,
    _get_children_contents,
    _leaf_filter,
    get_block_content,
    render_prompt_template,
)

fake_transcript = 'This is the text version from the transcript'


class FakeChild:
    """Fake child block for testing"""
    transcript_download_format = 'txt'

    def __init__(self, category, test_id='test-id', test_html='<div>This is a test</div>'):
        self.category = category
        self.published_on = 'published-on-{}'.format(test_id)
        self.edited_on = 'edited-on-{}'.format(test_id)
        self.scope_ids = lambda: None
        self.scope_ids.def_id = 'def-id-{}'.format(test_id)
        self.html = test_html
        self.transcript = fake_transcript

    def get_html(self):
        if self.category == 'html':
            return self.html

        return None


class FakeBlock:
    "Fake block for testing, returns given children"
    def __init__(self, children):
        self.children = children
        self.scope_ids = lambda: None
        self.scope_ids.usage_id = UsageKey.from_string('block-v1:edX+A+B+type@vertical+block@verticalD')

    def get_children(self):
        return self.children


@ddt.ddt
class GetBlockContentAPITests(TestCase):
    """
    Test suite for the get_block_content api function.
    """

    def setUp(self):
        cache.clear()

        self.children = [
            FakeChild('html', '01', '''
                        <p>
                            Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                            Vivamus dapibus elit lacus, at vehicula arcu vehicula in.
                            In id felis arcu. Maecenas elit quam, volutpat cursus pharetra vel, tempor at lorem.
                            Fusce luctus orci quis tempor aliquet.
                        </p>'''),
            FakeChild('html', '02', '''
                        <Everything on the content on this child is inside a tag, so parsing it would return almost>
                            Nothing
                        </The quick brown fox jumps over the lazy dog>'''),
            FakeChild('video', '03'),
            FakeChild('unknown', '04')
        ]
        self.block = FakeBlock(self.children)

        self.course_id = 'course-v1:edx+test+23'

    @ddt.data(
        ('video', True),
        ('html', True),
        ('unknown', False)
    )
    @ddt.unpack
    @patch('learning_assistant.api.block_leaf_filter')
    def test_block_leaf_filter(self, category, expected_value, mock_leaf_filter):
        mock_leaf_filter.return_value = True

        block = FakeChild(category)

        is_leaf = _leaf_filter(block)
        self.assertEqual(is_leaf, expected_value)

    @ddt.data(
        'video',
        'html',
        'unknown'
    )
    @patch('learning_assistant.api.html_to_text')
    @patch('learning_assistant.api.get_text_transcript')
    def test_extract_block_contents(self, category, mock_html, mock_transcript):
        mock_return = 'This is the block content'
        mock_html.return_value = mock_return
        mock_transcript.return_value = mock_return

        block = FakeChild(category)

        block_content = _extract_block_contents(block, category)

        if category in ['html', 'video']:
            self.assertEqual(block_content, mock_return)
        else:
            self.assertIsNone(block_content)

    @patch('learning_assistant.api.traverse_block_pre_order')
    @patch('learning_assistant.api.html_to_text')
    @patch('learning_assistant.api.get_text_transcript')
    def test_get_children_contents(self, mock_transcript, mock_html, mock_traversal):
        mock_traversal.return_value = self.children
        block_content = 'This is the block content'
        mock_html.return_value = block_content
        mock_transcript.return_value = block_content

        length, items = _get_children_contents(self.block)

        expected_items = [
            {'content_type': 'TEXT', 'content_text': block_content},
            {'content_type': 'TEXT', 'content_text': block_content},
            {'content_type': 'VIDEO', 'content_text': block_content}
        ]

        # expected length should be equivalent to the sum of the content length in each of the 3 child blocks
        # that are either video or html
        self.assertEqual(length, len(block_content) * 3)
        self.assertEqual(len(items), 3)
        self.assertEqual(items, expected_items)

    @patch('learning_assistant.api.get_single_block')
    @patch('learning_assistant.api._get_children_contents')
    def test_get_block_content(self, mock_get_children_contents, mock_get_single_block):
        mock_get_single_block.return_value = self.block

        block_content = 'This is the block content'
        content_items = [{'content_type': 'TEXT', 'content_text': block_content}]
        mock_get_children_contents.return_value = (len(block_content), content_items)

        # mock arguments that are passed through to `get_single_block` function. the value of these
        # args does not matter for this test right now, as the `get_single_block` function is entirely mocked.
        request = MagicMock()
        user_id = 1
        course_id = self.course_id
        unit_usage_key = 'block-v1:edX+A+B+type@vertical+block@verticalD'

        length, items = get_block_content(request, user_id, course_id, unit_usage_key)

        mock_get_children_contents.assert_called_once()
        mock_get_children_contents.assert_called_with(self.block)

        self.assertEqual(length, len(block_content))
        self.assertEqual(items, content_items)

        # call get_block_content again with same args to assert that cache is used
        length, items = get_block_content(request, user_id, course_id, unit_usage_key)

        # assert that the mock for _get_children_contents has not been called again,
        # as subsequent calls should hit the cache
        mock_get_children_contents.assert_called_once()
        self.assertEqual(length, len(block_content))
        self.assertEqual(items, content_items)

    @ddt.data(
        ('This is content.', True),
        ('', True),
        ('This is content.', False),
        ('', False),
    )
    @ddt.unpack
    @patch('learning_assistant.toggles._is_learning_assistant_waffle_flag_enabled')
    @patch('learning_assistant.api.get_block_content')
    def test_render_prompt_template(self, unit_content, flag_enabled, mock_get_content, mock_is_flag_enabled):
        mock_get_content.return_value = (len(unit_content), unit_content)
        mock_is_flag_enabled.return_value = flag_enabled

        # mock arguments that are passed through to `get_block_content` function. the value of these
        # args does not matter for this test right now, as the `get_block_content` function is entirely mocked.
        request = MagicMock()
        user_id = 1
        course_id = self.course_id
        unit_usage_key = 'block-v1:edX+A+B+type@vertical+block@verticalD'

        prompt_text = render_prompt_template(request, user_id, course_id, unit_usage_key)

        if unit_content and flag_enabled:
            self.assertIn(unit_content, prompt_text)
        else:
            self.assertNotIn('The following text is useful.', prompt_text)
