"""
V1 API Views.
"""
import logging

from django.conf import settings
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
    CourseMode = None
    CourseEnrollment = None
    get_user_role = None

from learning_assistant.api import (
    audit_trial_is_expired,
    get_audit_trial,
    get_course_id,
    get_message_history,
    get_or_create_audit_trial,
    learning_assistant_enabled,
    render_prompt_template,
    save_chat_message,
)
from learning_assistant.models import LearningAssistantMessage
from learning_assistant.serializers import MessageSerializer
from learning_assistant.toggles import chat_history_enabled
from learning_assistant.utils import get_audit_trial_length_days, get_chat_response, user_role_is_staff

log = logging.getLogger(__name__)


class CourseChatView(APIView):
    """
    View to retrieve chat response.

    Accepts: [POST]

    Path: /learning_assistant/v1/course_id/{course_run_id}

    Parameters:
        * course_run_id: the ID of the course

    Responses:
        * 200: OK
        * 400: Malformed Request - Course ID is not a valid course ID.
        * 403: Forbidden - Learning assistant not enabled for course or learner does not have a valid enrollment or is
                           not staff.
    """

    authentication_classes = (SessionAuthentication, JwtAuthentication,)
    permission_classes = (IsAuthenticated,)

    def _get_next_message(self, request, courserun_key, course_run_id):
        """
        Generate the next message to be returned by the learning assistant.
        """
        message_list = request.data

        # Check that the last message in the list corresponds to a user
        new_user_message = message_list[-1]
        if new_user_message['role'] != LearningAssistantMessage.USER_ROLE:
            return Response(
                status=http_status.HTTP_400_BAD_REQUEST,
                data={'detail': "Expects user role on last message."}
            )

        user_id = request.user.id

        if chat_history_enabled(courserun_key):
            save_chat_message(courserun_key, user_id, LearningAssistantMessage.USER_ROLE, new_user_message['content'])

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
        unit_id = request.query_params.get('unit_id')

        prompt_template = render_prompt_template(
            request, request.user.id, course_run_id, unit_id, course_id, template_string
        )
        status_code, message = get_chat_response(prompt_template, message_list)

        if chat_history_enabled(courserun_key):
            save_chat_message(courserun_key, user_id, LearningAssistantMessage.ASSISTANT_ROLE, message['content'])

        return Response(status=status_code, data=message)

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

        # If user does not have a verified enrollment record, or is not staff, they should not have full access
        user_role = get_user_role(request.user, courserun_key)
        enrollment_object = CourseEnrollment.get_enrollment(request.user, courserun_key)
        enrollment_mode = enrollment_object.mode if enrollment_object else None

        # If the user is in a verified course mode or is staff, return the next message
        if (
            # Here we include CREDIT_MODES and NO_ID_PROFESSIONAL_MODE, as CourseMode.VERIFIED_MODES on its own
            # doesn't match what we count as "verified modes" in the frontend component.
            enrollment_mode in CourseMode.VERIFIED_MODES + CourseMode.CREDIT_MODES
            + [CourseMode.NO_ID_PROFESSIONAL_MODE]
            or user_role_is_staff(user_role)
        ):
            return self._get_next_message(request, courserun_key, course_run_id)

        # If user has an audit enrollment record, get or create their trial. If the trial is not expired, return the
        # next message. Otherwise, return 403
        elif enrollment_mode in CourseMode.UPSELL_TO_VERIFIED_MODES:  # AUDIT, HONOR
            audit_trial = get_or_create_audit_trial(request.user)
            is_user_audit_trial_expired = audit_trial_is_expired(enrollment_object, audit_trial)
            if is_user_audit_trial_expired:
                return Response(
                    status=http_status.HTTP_403_FORBIDDEN,
                    data={'detail': 'The audit trial for this user has expired.'}
                )
            else:
                return self._get_next_message(request, courserun_key, course_run_id)

        # If user has a course mode that is not verified & not meant to access to the learning assistant, return 403
        # This covers the other course modes: UNPAID_EXECUTIVE_EDUCATION & UNPAID_BOOTCAMP
        else:
            return Response(
                status=http_status.HTTP_403_FORBIDDEN,
                data={'detail': 'Must be staff or have valid enrollment.'}
            )


class LearningAssistantEnabledView(APIView):
    """
    View to retrieve whether the Learning Assistant is enabled for a course.

    This endpoint returns a boolean representing whether the Learning Assistant feature is enabled in a course
    represented by the course_run_id, which is provided in the URL.

    Accepts: [GET]

    Path: /learning_assistant/v1/course_id/{course_run_id}/enabled

    Parameters:
        * course_run_id: the ID of the course

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
    represented by the course_run_id, which is provided in the URL.

    Accepts: [GET]

    Path: /learning_assistant/v1/course_id/{course_run_id}/history

    Parameters:
        * course_run_id: the ID of the course

    Responses:
        * 200: OK
        * 400: Malformed Request - Course ID is not a valid course ID.
        * 403: Forbidden - Learning assistant not enabled for course or learner does not have a valid enrollment or is
                           not staff.
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

        # If chat history is disabled, we return no messages as response.
        if not chat_history_enabled(courserun_key):
            return Response(status=http_status.HTTP_200_OK, data=[])

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

        user = request.user

        message_count = int(request.GET.get('message_count', 50))
        message_history = get_message_history(courserun_key, user, message_count)
        data = MessageSerializer(message_history, many=True).data
        return Response(status=http_status.HTTP_200_OK, data=data)


class LearningAssistantChatSummaryView(APIView):
    """
    View to retrieve data about a learner's session with the Learning Assistant.

    This endpoint returns all the data necessary for the Learning Assistant to function, including the following
    information.
        * whether the Learning Assistant is enabled
        * message history information, if the learner is eligible to use the Learning Assistant
        * audit trial information

    Accepts: [GET]

    Path: /learning_assistant/v1/course_id/{course_run_id}/chat-summary

    Parameters:
        * course_run_id: the ID of the course

    Responses:
        * 200: OK
        * 400: Malformed Request - Course ID is not a valid course ID.
    """

    authentication_classes = (SessionAuthentication, JwtAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, course_run_id):
        """
        Given a course run ID, return all the data necessary for the Learning Assistant to fuction.

        The response will be in the following format.

        {
            "enabled": true,
            "message_history": [
                {
                    "role": "user",
                    "content": "test message from user",
                    "timestamp": "2024-12-02T15:04:17.495928Z"
                },
                {
                    "role": "assistant",
                    "content": "test message from assistant",
                    "timestamp": "2024-12-02T15:04:40.084584Z"
                }
            ],
            "audit_trial": {
                "start_date": "2024-12-02T14:59:16.148236Z",
                "expiration_date": "2024-12-26T14:59:16.148236Z",
            },
            "audit_trial_length_days": 14
        }
        """
        try:
            courserun_key = CourseKey.from_string(course_run_id)
        except InvalidKeyError:
            return Response(
                status=http_status.HTTP_400_BAD_REQUEST,
                data={'detail': 'Course ID is not a valid course ID.'}
            )

        data = {}
        user = request.user

        # Get whether the Learning Assistant is enabled.
        data['enabled'] = learning_assistant_enabled(courserun_key)

        # Get message history.
        # If user does not have a verified enrollment record or is does not have an active audit trial, or is not staff,
        # then they should not have access to the message history.
        user_role = get_user_role(user, courserun_key)
        enrollment_object = CourseEnrollment.get_enrollment(request.user, courserun_key)
        enrollment_mode = enrollment_object.mode if enrollment_object else None

        # Here we include CREDIT_MODES and NO_ID_PROFESSIONAL_MODE, as CourseMode.VERIFIED_MODES on its own
        # doesn't match what we count as "verified modes" in the frontend component. We also include AUDIT and HONOR to
        # ensure learners with audit trials see message history if the trial is non-expired.
        valid_full_access_modes = (
            CourseMode.VERIFIED_MODES +
            CourseMode.CREDIT_MODES +
            [CourseMode.NO_ID_PROFESSIONAL_MODE]
        )
        valid_trial_access_modes = CourseMode.UPSELL_TO_VERIFIED_MODES

        # Get audit trial. Note that we do not want to create an audit trial when calling this endpoint.
        audit_trial = get_audit_trial(request.user)

        # If the learner doesn't meet criteria to use the Learning Assistant, or if the chat history is disabled, we
        # return no messages in the response.
        message_history_data = []

        has_trial_access = (
            enrollment_mode in valid_trial_access_modes
            and audit_trial
            and not audit_trial_is_expired(enrollment_object, audit_trial)
        )

        if (
            (
                (enrollment_mode in valid_full_access_modes)
                or has_trial_access
                or user_role_is_staff(user_role)
            )
            and chat_history_enabled(courserun_key)
        ):
            message_count = int(request.GET.get('message_count', 50))
            message_history = get_message_history(courserun_key, user, message_count)
            message_history_data = MessageSerializer(message_history, many=True).data

        data['message_history'] = message_history_data

        # Get audit trial.
        trial = get_audit_trial(user)

        trial_data = {}
        if trial:
            trial_data['start_date'] = trial.start_date
            trial_data['expiration_date'] = trial.expiration_date

        data['audit_trial'] = trial_data

        data['audit_trial_length_days'] = get_audit_trial_length_days()

        return Response(status=http_status.HTTP_200_OK, data=data)
