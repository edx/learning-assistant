"""
Test cases for the learning-assistant api module.
"""
import itertools
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import ddt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from freezegun import freeze_time
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey

from learning_assistant.api import (
    _extract_block_contents,
    _get_children_contents,
    _leaf_filter,
    audit_trial_is_expired,
    get_audit_trial,
    get_audit_trial_expiration_date,
    get_block_content,
    get_message_history,
    get_or_create_audit_trial,
    learning_assistant_available,
    learning_assistant_enabled,
    render_prompt_template,
    save_chat_message,
    set_learning_assistant_enabled,
)
from learning_assistant.data import LearningAssistantAuditTrialData, LearningAssistantCourseEnabledData
from learning_assistant.models import (
    LearningAssistantAuditTrial,
    LearningAssistantCourseEnabled,
    LearningAssistantMessage,
)

fake_transcript = 'This is the text version from the transcript'
User = get_user_model()


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

        self.course_run_id = 'course-v1:edx+test+23'

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
        course_id = self.course_run_id
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
        'This is content.',
        ''
    )
    @patch('learning_assistant.api.get_cache_course_data')
    @patch('learning_assistant.api.get_block_content')
    def test_render_prompt_template(self, unit_content, mock_get_content, mock_cache):
        mock_get_content.return_value = (len(unit_content), unit_content)
        skills_content = ['skills']
        title = 'title'
        mock_cache.return_value = {'skill_names': skills_content, 'title': title}

        # mock arguments that are passed through to `get_block_content` function. the value of these
        # args does not matter for this test right now, as the `get_block_content` function is entirely mocked.
        request = MagicMock()
        user_id = 1
        course_run_id = self.course_run_id
        unit_usage_key = 'block-v1:edX+A+B+type@vertical+block@verticalD'
        course_id = 'edx+test'
        template_string = getattr(settings, 'LEARNING_ASSISTANT_PROMPT_TEMPLATE', '')

        prompt_text = render_prompt_template(
            request, user_id, course_run_id, unit_usage_key, course_id, template_string
        )

        if unit_content:
            self.assertIn(unit_content, prompt_text)
        else:
            self.assertNotIn('The following text is useful.', prompt_text)
        self.assertIn(str(skills_content), prompt_text)
        self.assertIn(title, prompt_text)

    @patch('learning_assistant.api.get_cache_course_data', MagicMock())
    @patch('learning_assistant.api.get_block_content')
    def test_render_prompt_template_invalid_unit_key(self, mock_get_content):
        mock_get_content.side_effect = InvalidKeyError('foo', 'bar')

        # mock arguments that are passed through to `get_block_content` function. the value of these
        # args does not matter for this test right now, as the `get_block_content` function is entirely mocked.
        request = MagicMock()
        user_id = 1
        course_run_id = self.course_run_id
        unit_usage_key = 'block-v1:edX+A+B+type@vertical+block@verticalD'
        course_id = 'edx+test'
        template_string = getattr(settings, 'LEARNING_ASSISTANT_PROMPT_TEMPLATE', '')

        prompt_text = render_prompt_template(
            request, user_id, course_run_id, unit_usage_key, course_id, template_string
        )

        self.assertNotIn('The following text is useful.', prompt_text)


@ddt.ddt
class TestLearningAssistantCourseEnabledApi(TestCase):
    """
    Test suite for save_chat_message.
    """

    def setUp(self):
        super().setUp()

        self.test_user = User.objects.create(username='username', password='password')
        self.course_run_key = CourseKey.from_string('course-v1:edx+test+23')

    @ddt.data(
        (LearningAssistantMessage.USER_ROLE, 'What is the meaning of life, the universe and everything?'),
        (LearningAssistantMessage.ASSISTANT_ROLE, '42'),
    )
    @ddt.unpack
    def test_save_chat_message(self, chat_role, message):
        save_chat_message(self.course_run_key, self.test_user.id, chat_role, message)

        row = LearningAssistantMessage.objects.all().last()

        self.assertEqual(row.course_id, self.course_run_key)
        self.assertEqual(row.role, chat_role)
        self.assertEqual(row.content, message)


@ddt.ddt
class LearningAssistantCourseEnabledApiTests(TestCase):
    """
    Test suite for learning_assistant_available, learning_assistant_enabled, and set_learning_assistant_enabled.
    """

    def setUp(self):
        super().setUp()
        self.course_key = CourseKey.from_string('course-v1:edx+fake+1')

    @ddt.data(
        (True, True, True, True),
        (True, True, False, False),
        (True, False, True, False),
        (True, False, False, False),
        (False, True, True, True),
        (False, False, True, True),
        (False, True, False, False),
        (False, False, False, False),
    )
    @ddt.unpack
    @patch('learning_assistant.api.learning_assistant_available')
    def test_learning_assistant_enabled(
        self,
        obj_exists,
        obj_value,
        learning_assistant_available_value,
        expected_value,
        learning_assistant_available_mock,
    ):
        learning_assistant_available_mock.return_value = learning_assistant_available_value

        if obj_exists:
            set_learning_assistant_enabled(self.course_key, obj_value)

        self.assertEqual(
            learning_assistant_enabled(self.course_key),
            expected_value
        )

    @ddt.idata(itertools.product((True, False), (True, False)))
    @ddt.unpack
    def test_set_learning_assistant_enabled(self, obj_exists, obj_value):
        if obj_exists:
            LearningAssistantCourseEnabled.objects.create(
                course_id=self.course_key,
                # Set the opposite of the desired end value to test that it is changed properly.
                enabled=not obj_value,
            )

        expected_value = LearningAssistantCourseEnabledData(
            self.course_key,
            obj_value,
        )

        return_value = set_learning_assistant_enabled(self.course_key, obj_value)

        self.assertEqual(
            return_value,
            expected_value,
        )

        obj = LearningAssistantCourseEnabled.objects.get(course_id=self.course_key)
        self.assertEqual(obj.enabled, obj_value)

    @ddt.data(
        True,
        False
    )
    def test_learning_assistant_available(self, learning_assistant_available_setting_value):
        with override_settings(LEARNING_ASSISTANT_AVAILABLE=learning_assistant_available_setting_value):
            return_value = learning_assistant_available()

        expected_value = learning_assistant_available_setting_value
        self.assertEqual(return_value, expected_value)


@ddt.ddt
class GetMessageHistoryTests(TestCase):
    """
    Test suite for get_message_history.
    """

    def setUp(self):
        super().setUp()
        self.course_key = CourseKey.from_string('course-v1:edx+fake+1')
        self.user = User(username='tester', email='tester@test.com')
        self.user.save()

        self.role = 'verified'

    def test_get_message_history(self):
        message_count = 5
        for i in range(1, message_count + 1):
            LearningAssistantMessage.objects.create(
                course_id=self.course_key,
                user=self.user,
                role=self.role,
                content=f'Content of message {i}',
            )

        return_value = get_message_history(self.course_key, self.user, message_count)

        expected_value = list(LearningAssistantMessage.objects.filter(
            course_id=self.course_key, user=self.user).order_by('-created')[:message_count])[::-1]

        # Ensure same number of entries
        self.assertEqual(len(return_value), len(expected_value))

        # Ensure values are as expected for all LearningAssistantMessage instances
        for i, return_value in enumerate(return_value):
            self.assertEqual(return_value.course_id, expected_value[i].course_id)
            self.assertEqual(return_value.user, expected_value[i].user)
            self.assertEqual(return_value.role, expected_value[i].role)
            self.assertEqual(return_value.content, expected_value[i].content)

    @ddt.data(
        0, 1, 5, 10, 50
    )
    def test_get_message_history_message_count(self, actual_message_count):
        for i in range(1, actual_message_count + 1):
            LearningAssistantMessage.objects.create(
                course_id=self.course_key,
                user=self.user,
                role=self.role,
                content=f'Content of message {i}',
            )

        message_count_parameter = 5
        return_value = get_message_history(self.course_key, self.user, message_count_parameter)

        expected_value = LearningAssistantMessage.objects.filter(
            course_id=self.course_key, user=self.user).order_by('-created')[:message_count_parameter]

        # Ensure same number of entries
        self.assertEqual(len(return_value), len(expected_value))

    def test_get_message_history_user_difference(self):
        # Default Message
        LearningAssistantMessage.objects.create(
            course_id=self.course_key,
            user=self.user,
            role=self.role,
            content='Expected content of message',
        )

        # New message w/ new user
        new_user = User(username='not_tester', email='not_tester@test.com')
        new_user.save()
        LearningAssistantMessage.objects.create(
            course_id=self.course_key,
            user=new_user,
            role=self.role,
            content='Expected content of message',
        )

        message_count = 2
        return_value = get_message_history(self.course_key, self.user, message_count)

        expected_value = LearningAssistantMessage.objects.filter(
            course_id=self.course_key, user=self.user).order_by('-created')[:message_count]

        # Ensure we filtered one of the two present messages
        self.assertNotEqual(len(return_value), LearningAssistantMessage.objects.count())

        # Ensure same number of entries
        self.assertEqual(len(return_value), len(expected_value))

        # Ensure values are as expected for all LearningAssistantMessage instances
        for i, return_value in enumerate(return_value):
            self.assertEqual(return_value.course_id, expected_value[i].course_id)
            self.assertEqual(return_value.user, expected_value[i].user)
            self.assertEqual(return_value.role, expected_value[i].role)
            self.assertEqual(return_value.content, expected_value[i].content)

    def test_get_message_course_id_differences(self):
        # Default Message
        LearningAssistantMessage.objects.create(
            course_id=self.course_key,
            user=self.user,
            role=self.role,
            content='Expected content of message',
        )

        # New message
        wrong_course_id = 'course-v1:wrong+id+1'
        LearningAssistantMessage.objects.create(
            course_id=wrong_course_id,
            user=self.user,
            role=self.role,
            content='Expected content of message',
        )

        message_count = 2
        return_value = get_message_history(self.course_key, self.user, message_count)

        expected_value = LearningAssistantMessage.objects.filter(
            course_id=self.course_key, user=self.user).order_by('-created')[:message_count]

        # Ensure we filtered one of the two present messages
        self.assertNotEqual(len(return_value), LearningAssistantMessage.objects.count())

        # Ensure same number of entries
        self.assertEqual(len(return_value), len(expected_value))

        # Ensure values are as expected for all LearningAssistantMessage instances
        for i, return_value in enumerate(return_value):
            self.assertEqual(return_value.course_id, expected_value[i].course_id)
            self.assertEqual(return_value.user, expected_value[i].user)
            self.assertEqual(return_value.role, expected_value[i].role)
            self.assertEqual(return_value.content, expected_value[i].content)


@ddt.ddt
class GetAuditTrialExpirationDateTests(TestCase):
    """
    Test suite for get_audit_trial_expiration_date.
    """

    @ddt.data(
        (datetime(2024, 1, 1, 0, 0, 0), datetime(2024, 1, 2, 0, 0, 0), 1),
        (datetime(2024, 1, 18, 0, 0, 0), datetime(2024, 1, 19, 0, 0, 0), 1),
        (datetime(2024, 1, 1, 0, 0, 0), datetime(2024, 1, 8, 0, 0, 0), 7),
        (datetime(2024, 1, 18, 0, 0, 0), datetime(2024, 1, 25, 0, 0, 0), 7),
        (datetime(2024, 1, 1, 0, 0, 0), datetime(2024, 1, 15, 0, 0, 0), 14),
        (datetime(2024, 1, 18, 0, 0, 0), datetime(2024, 2, 1, 0, 0, 0), 14),
    )
    @ddt.unpack
    @patch('learning_assistant.api.get_audit_trial_length_days')
    def test_expiration_date(
        self, start_date,
        expected_expiration_date,
        trial_length_days,
        mock_get_audit_trial_length_days
    ):
        mock_get_audit_trial_length_days.return_value = trial_length_days
        expiration_date = get_audit_trial_expiration_date(start_date)
        self.assertEqual(expected_expiration_date, expiration_date)


class GetAuditTrialTests(TestCase):
    """
    Test suite for get_audit_trial.
    """

    @freeze_time('2024-01-01')
    def setUp(self):
        super().setUp()
        self.user = User(username='tester', email='tester@test.com')
        self.user.save()

    def test_exists(self):
        start_date = datetime.now()

        LearningAssistantAuditTrial.objects.create(
            user=self.user,
            start_date=start_date
        )

        expected_return = LearningAssistantAuditTrialData(
            user_id=self.user.id,
            start_date=start_date,
            expiration_date=start_date + timedelta(days=settings.LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS)
        )
        self.assertEqual(expected_return, get_audit_trial(self.user))

    def test_not_exists(self):
        other_user = User(username='other-tester', email='other-tester@test.com')
        other_user.save()

        self.assertIsNone(get_audit_trial(self.user))


class GetOrCreateAuditTrialTests(TestCase):
    """
    Test suite for get_or_create_audit_trial.
    """

    def setUp(self):
        super().setUp()
        self.user = User(username='tester', email='tester@test.com')
        self.user.save()

    @freeze_time('2024-01-01')
    def test_exists(self):
        start_date = datetime.now()

        LearningAssistantAuditTrial.objects.create(
            user=self.user,
            start_date=start_date
        )

        expected_return = LearningAssistantAuditTrialData(
            user_id=self.user.id,
            start_date=start_date,
            expiration_date=start_date + timedelta(days=settings.LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS)
        )
        self.assertEqual(expected_return, get_or_create_audit_trial(self.user))

    @freeze_time('2024-01-01')
    def test_not_exists(self):
        other_user = User(username='other-tester', email='other-tester@test.com')
        other_user.save()

        start_date = datetime.now()
        expected_return = LearningAssistantAuditTrialData(
            user_id=self.user.id,
            start_date=start_date,
            expiration_date=start_date + timedelta(days=settings.LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS)
        )

        self.assertEqual(expected_return, get_or_create_audit_trial(self.user))


@ddt.ddt
class CheckIfAuditTrialIsExpiredTests(TestCase):
    """
    Test suite for audit_trial_is_expired.
    """

    def setUp(self):
        super().setUp()
        self.course_key = CourseKey.from_string('course-v1:edx+fake+1')
        self.user = User(username='tester', email='tester@test.com')
        self.user.save()

    @freeze_time('2024-01-01 00:00:01 UTC')
    def test_upgrade_deadline_expired(self):
        today = datetime.now(tz=timezone.utc)
        mock_enrollment = MagicMock()
        mock_enrollment.upgrade_deadline = today - timedelta(days=1)  # yesterday

        start_date = today
        audit_trial_data = LearningAssistantAuditTrialData(
            user_id=self.user.id,
            start_date=start_date,
            expiration_date=start_date + timedelta(days=settings.LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS),
        )

        self.assertEqual(audit_trial_is_expired(mock_enrollment, audit_trial_data), True)

    @freeze_time('2024-01-01 00:00:01 UTC')
    def test_upgrade_deadline_none(self):
        today = datetime.now(tz=timezone.utc)
        mock_enrollment = MagicMock()
        mock_enrollment.upgrade_deadline = None

        # Verify that the audit trial data is considered when determining whether an audit trial is expired and not the
        # upgrade deadline.
        start_date = today
        audit_trial_data = LearningAssistantAuditTrialData(
            user_id=self.user.id,
            start_date=start_date,
            expiration_date=start_date + timedelta(days=settings.LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS),
        )

        self.assertEqual(audit_trial_is_expired(mock_enrollment, audit_trial_data), False)

        start_date = today - timedelta(days=settings.LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS + 1)
        audit_trial_data = LearningAssistantAuditTrialData(
            user_id=self.user.id,
            start_date=start_date,
            expiration_date=start_date + timedelta(days=settings.LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS),
        )

        self.assertEqual(audit_trial_is_expired(mock_enrollment, audit_trial_data), True)

    @ddt.data(
        # exactly the trial deadline
        datetime(year=2024, month=1, day=1, tzinfo=timezone.utc) -
        timedelta(days=settings.LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS),
        # 1 day more than trial deadline
        datetime(year=2024, month=1, day=1, tzinfo=timezone.utc) -
        timedelta(days=settings.LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS + 1),
    )
    @freeze_time('2024-01-01 00:00:01 UTC')
    def test_audit_trial_expired(self, start_date):
        today = datetime.now(tz=timezone.utc)
        mock_enrollment = MagicMock()
        mock_enrollment.upgrade_deadline = today + timedelta(days=1)  # tomorrow

        audit_trial_data = LearningAssistantAuditTrialData(
            user_id=self.user.id,
            start_date=start_date,
            expiration_date=get_audit_trial_expiration_date(start_date),
        )

        self.assertEqual(audit_trial_is_expired(mock_enrollment, audit_trial_data), True)

    @freeze_time('2024-01-01 00:00:01 UTC')
    def test_audit_trial_unexpired(self):
        today = datetime.now(tz=timezone.utc)
        mock_enrollment = MagicMock()
        mock_enrollment.upgrade_deadline = today + timedelta(days=1)  # tomorrow

        start_date = today - timedelta(days=settings.LEARNING_ASSISTANT_AUDIT_TRIAL_LENGTH_DAYS - 1)
        audit_trial_data = LearningAssistantAuditTrialData(
            user_id=self.user.id,
            start_date=start_date,
            expiration_date=get_audit_trial_expiration_date(start_date),
        )

        self.assertEqual(audit_trial_is_expired(mock_enrollment, audit_trial_data), False)
