"""
V1 API Views.
"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import status as http_status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

try:
    from common.djangoapps.course_modes.models import CourseMode
    from common.djangoapps.student.models import CourseEnrollment
    from lms.djangoapps.courseware.access import get_user_role
except ImportError:
    pass

from learning_assistant.api import (
    get_course_id,
    get_message_history,
    learning_assistant_enabled,
    render_prompt_template,
)
from learning_assistant.models import LearningAssistantMessage
from learning_assistant.serializers import MessageSerializer
from learning_assistant.utils import get_chat_response, user_role_is_staff

log = logging.getLogger(__name__)
User = get_user_model()


class CourseChatView(APIView):
    """
    View to retrieve chat response.
    """

    authentication_classes = (SessionAuthentication, JwtAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, course_run_id):
        """
        Given a course run ID, retrieve a chat response for that course.

        Expected POST data: {
            [
                {'role': 'user', 'content': 'What is 2+2?'},
                {'role': 'assistant', 'content': '4'}
            ]
        }
        """
        try:
            courserun_key = CourseKey.from_string(course_run_id)
        except InvalidKeyError:
            return Response(
                status=http_status.HTTP_400_BAD_REQUEST,
                data={'detail': 'Course ID is not a valid course ID.'}
            )

        if not learning_assistant_enabled(courserun_key):
            return Response(
                status=http_status.HTTP_403_FORBIDDEN,
                data={'detail': 'Learning assistant not enabled for course.'}
            )

        # If user does not have an enrollment record, or is not staff, they should not have access
        user_role = get_user_role(request.user, courserun_key)
        enrollment_object = CourseEnrollment.get_enrollment(request.user, courserun_key)
        enrollment_mode = enrollment_object.mode if enrollment_object else None
        if (
            (enrollment_mode not in CourseMode.VERIFIED_MODES)
            and not user_role_is_staff(user_role)
        ):
            return Response(
                status=http_status.HTTP_403_FORBIDDEN,
                data={'detail': 'Must be staff or have valid enrollment.'}
            )

        unit_id = request.query_params.get('unit_id')

        message_list = request.data

        # Check that the last message in the list corresponds to a user
        new_user_message = message_list[-1]
        if new_user_message['role'] != LearningAssistantMessage.USER_ROLE:
            return Response(
                status=http_status.HTTP_400_BAD_REQUEST,
                data={'detail': "Expects user role on last message."}
            )

        serializer = MessageSerializer(data=message_list, many=True)

        # serializer will not be valid in the case that the message list contains any roles other than
        # `user` or `assistant`
        if not serializer.is_valid():
            return Response(
                status=http_status.HTTP_400_BAD_REQUEST,
                data={'detail': 'Invalid data', 'errors': serializer.errors}
            )

        log.info(
            'Attempting to retrieve chat response for user_id=%(user_id)s in course_id=%(course_id)s',
            {
                'user_id': request.user.id,
                'course_id': course_run_id
            }
        )

        course_id = get_course_id(course_run_id)

        template_string = getattr(settings, 'LEARNING_ASSISTANT_PROMPT_TEMPLATE', '')

        prompt_template = render_prompt_template(
            request, request.user.id, course_run_id, unit_id, course_id, template_string
        )
        status_code, message = get_chat_response(prompt_template, message_list)

        user = User.objects.get(id=request.user.id)  # Based on the previous code, user exists.

        # Save the user message to the database.
        LearningAssistantMessage.objects.create(
            user=user,
            role=LearningAssistantMessage.USER_ROLE,
            content=new_user_message['content'],
        )

        # Save the assistant response to the database.
        LearningAssistantMessage.objects.create(
            user=user,
            role=LearningAssistantMessage.ASSISTANT_ROLE,
            content=message['content'],
        )

        return Response(status=status_code, data=message)


class LearningAssistantEnabledView(APIView):
    """
    View to retrieve whether the Learning Assistant is enabled for a course.

    This endpoint returns a boolean representing whether the Learning Assistant feature is enabled in a course
    represented by the course_key, which is provided in the URL.

    Accepts: [GET]

    Path: /learning_assistant/v1/course_id/{course_key}/enabled

    Parameters:
        * course_key: the ID of the course

    Responses:
        * 200: OK
        * 400: Malformed Request - Course ID is not a valid course ID.
    """

    authentication_classes = (SessionAuthentication, JwtAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, course_run_id):
        """
        Given a course run ID, retrieve whether the Learning Assistant is enabled for the corresponding course.

        The response will be in the following format.

            {'enabled': <bool>}
        """
        try:
            courserun_key = CourseKey.from_string(course_run_id)
        except InvalidKeyError:
            return Response(
                status=http_status.HTTP_400_BAD_REQUEST,
                data={'detail': 'Course ID is not a valid course ID.'}
            )

        data = {
            'enabled': learning_assistant_enabled(courserun_key),
        }

        return Response(status=http_status.HTTP_200_OK, data=data)


class LearningAssistantMessageHistoryView(APIView):
    """
    View to retrieve the message history for user in a course.

    This endpoint returns the message history stored in the LearningAssistantMessage table in a course
    represented by the course_key, which is provided in the URL.

    Accepts: [GET]

    Path: /learning_assistant/v1/course_id/{course_key}/history

    Parameters:
        * course_key: the ID of the course

    Responses:
        * 200: OK
        * 400: Malformed Request - Course ID is not a valid course ID.
    """

    authentication_classes = (SessionAuthentication, JwtAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, course_run_id):
        """
        Given a course run ID, retrieve the message history for the corresponding user.

        The response will be in the following format.

            [{'role': 'assistant', 'content': 'something'}]
        """
        try:
            courserun_key = CourseKey.from_string(course_run_id)
        except InvalidKeyError:
            return Response(
                status=http_status.HTTP_400_BAD_REQUEST,
                data={'detail': 'Course ID is not a valid course ID.'}
            )

        if not learning_assistant_enabled(courserun_key):
            return Response(
                status=http_status.HTTP_403_FORBIDDEN,
                data={'detail': 'Learning assistant not enabled for course.'}
            )

        # If user does not have an enrollment record, or is not staff, they should not have access
        user_role = get_user_role(request.user, courserun_key)
        enrollment_object = CourseEnrollment.get_enrollment(request.user, courserun_key)
        enrollment_mode = enrollment_object.mode if enrollment_object else None
        if (
            (enrollment_mode not in CourseMode.VERIFIED_MODES)
            and not user_role_is_staff(user_role)
        ):
            return Response(
                status=http_status.HTTP_403_FORBIDDEN,
                data={'detail': 'Must be staff or have valid enrollment.'}
            )

        course_id = get_course_id(course_run_id)
        user = request.user

        message_count = int(request.GET.get('message_count', 50))
        message_history = get_message_history(course_id, user, message_count)
        data = MessageSerializer(message_history, many=True).data
        return Response(status=http_status.HTTP_200_OK, data=data)
