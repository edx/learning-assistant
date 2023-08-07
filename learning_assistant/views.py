"""
V1 API Views.
"""
import logging

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import status as http_status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

try:
    from common.djangoapps.course_modes.models import CourseMode
    from common.djangoapps.student.models import CourseEnrollment
    from lms.djangoapps.courseware.access import get_user_role
    from lms.djangoapps.courseware.toggles import learning_assistant_is_active
except ImportError:
    # If the waffle flag is false, the endpoint will force an early return.
    learning_assistant_is_active = False

from learning_assistant.api import get_prompt_by_course_id
from learning_assistant.serializers import MessageSerializer
from learning_assistant.utils import get_chat_response

log = logging.getLogger(__name__)


class CourseChatView(APIView):
    """
    View to retrieve chat response.
    """

    authentication_classes = (SessionAuthentication, JwtAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, course_id):
        """
        Given a course ID, retrieve a chat response for that course.

        Expected POST data: {
            [
                {'role': 'user', 'content': 'What is 2+2?'},
                {'role': 'assistant', 'content': '4'}
            ]
        }
        """
        if not learning_assistant_is_active(course_id):
            return Response(
                status=http_status.HTTP_403_FORBIDDEN,
                data={'detail': 'Learning assistant not enabled for course.'}
            )

        # If user does not have a verified enrollment, or is not staff, they should not have access
        user_role = get_user_role(request.user, course_id)
        enrollment_object = CourseEnrollment.get_enrollment(request.user, course_id)
        enrollment_mode = enrollment_object.mode if enrollment_object else None
        if (
            (enrollment_mode not in CourseMode.VERIFIED_MODES)
            and user_role not in ('staff', 'instructor')
        ):
            return Response(
                status=http_status.HTTP_403_FORBIDDEN,
                data={'detail': 'Must be staff or have valid enrollment.'}
            )

        prompt_text = get_prompt_by_course_id(course_id)
        if not prompt_text:
            return Response(
                status=http_status.HTTP_404_NOT_FOUND,
                data={'detail': 'Learning assistant not enabled for course.'}
            )

        message_list = request.data
        serializer = MessageSerializer(data=message_list, many=True)

        # serializer will not be valid in the case that the message list contains any roles other than
        # `user` or `assistant`
        if not serializer.is_valid():
            return Response(
                status=http_status.HTTP_400_BAD_REQUEST,
                data={'detail': 'Invalid data', 'errors': serializer.errors}
            )

        # append system message to beginning of message list
        message_setup = [{
            'role': 'system',
            'content': prompt_text
        }]

        log.info(
            'Attempting to retrieve chat response for user_id=%(user_id)s in course_id=%(course_id)s',
            {
                'user_id': request.user.id,
                'course_id': course_id
            }
        )
        status_code, message = get_chat_response(message_setup + message_list)

        return Response(status=status_code, data=message)