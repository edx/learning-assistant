"""
Tests for the retire_user_messages management command
"""
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from learning_assistant.models import LearningAssistantMessage

User = get_user_model()


class RetireUserMessagesTests(TestCase):
    """
    Tests for the retire_user_messages command.
    """

    def setUp(self):
        """
        Build up test data
        """
        super().setUp()
        self.user = User(username='tester', email='tester@test.com')
        self.user.save()

        self.course_id = 'course-v1:edx+test+23'

        LearningAssistantMessage.objects.create(
            user=self.user,
            course_id=self.course_id,
            role='user',
            content='Hello',
            created=datetime.now() - timedelta(days=60)
        )

        LearningAssistantMessage.objects.create(
            user=self.user,
            course_id=self.course_id,
            role='user',
            content='Hello',
            created=datetime.now() - timedelta(days=2)
        )

        LearningAssistantMessage.objects.create(
            user=self.user,
            course_id=self.course_id,
            role='user',
            content='Hello',
            created=datetime.now() - timedelta(days=4)
        )

    def test_run_command(self):
        """
        Run the management command
        """
        current_messages = LearningAssistantMessage.objects.filter()
        self.assertEqual(len(current_messages), 3)

        call_command(
            'retire_user_messages',
            batch_size=2,
            sleep_time=0,
        )

        current_messages = LearningAssistantMessage.objects.filter()
        self.assertEqual(len(current_messages), 2)
