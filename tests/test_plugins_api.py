"""
Test cases for the learning-assistant plugins module.
"""
from unittest.mock import patch

import ddt
from django.contrib.auth import get_user_model
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey

from learning_assistant.models import LearningAssistantCourseEnabled
from learning_assistant.plugins_api import get_allowed_operations, is_available, is_enabled, set_enabled

User = get_user_model()


@ddt.ddt
class PluginApiTests(TestCase):
    """
    Test suite for the plugins_api module.
    """
    def setUp(self):
        super().setUp()
        self.course_key = CourseKey.from_string('course-v1:edx+fake+1')
        self.user = User(username='tester', email='tester@test.com')

    @ddt.data(True, False)
    @patch('learning_assistant.plugins_api.learning_assistant_available')
    def test_is_available(self, is_available_value, learning_assistant_available_mock):
        """
        Test the is_available function of the plugins_api module.
        """
        learning_assistant_available_mock.return_value = is_available_value
        self.assertEqual(is_available(), is_available_value)

    @ddt.data(True, False)
    @patch('learning_assistant.plugins_api.learning_assistant_enabled')
    def test_is_enabled(self, is_enabled_value, learning_assistant_enabled_mock):
        """
        Test the is_enabled function of the plugins_api module.
        """
        learning_assistant_enabled_mock.return_value = is_enabled_value
        self.assertEqual(is_enabled(self.course_key), is_enabled_value)

    @ddt.data(True, False)
    def test_set_enabled_create(self, enabled_value):
        """
        Test the set_enabled function of the plugins_api module when a create should occur.
        """
        self.assertEqual(set_enabled(self.course_key, enabled_value, self.user), enabled_value)

    @ddt.data(True, False)
    def test_set_enabled_update(self, enabled_value):
        """
        Test the set_enabled function of the plugins_api module when an update should occur.
        """
        LearningAssistantCourseEnabled.objects.create(
            course_id=self.course_key,
            enabled=enabled_value
        )

        self.assertEqual(set_enabled(self.course_key, enabled_value, self.user), enabled_value)

    def test_get_allowed_operations_no_user(self):
        """
        Test the get_allowed_operations function of the plugins_api module when no user is passed as an argument.
        """
        self.assertEqual(
            get_allowed_operations(self.course_key),
            {'configure': False, 'enable': False}
        )

    @ddt.unpack
    @ddt.data(('instructor', True), ('staff', True), ('student', False))
    @patch('learning_assistant.plugins_api.get_user_role')
    def test_get_allowed_operations(self, role_value, is_staff_value, get_user_role_mock):
        """
        Test the get_allowed_operations function of the plugins_api module.
        """
        get_user_role_mock.return_value = role_value

        self.assertEqual(
            get_allowed_operations(self.course_key, self.user),
            {'configure': False, 'enable': is_staff_value}
        )
