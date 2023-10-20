"""
Django management command to generate course prompts.
"""
import json
import logging
from posixpath import join as urljoin

from django.conf import settings
from django.core.management.base import BaseCommand
from edx_rest_api_client.client import OAuthAPIClient
from opaque_keys.edx.keys import CourseKey

from learning_assistant.models import CoursePrompt

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django Management command to create a set of course prompts
    """

    def add_arguments(self, parser):

        # list of course ids
        parser.add_argument(
            '--course_ids',
            dest='course_ids',
            help='Comma separated list of course_ids to generate. Only newer style course ids can be supplied.',
        )

        # pre-message
        parser.add_argument(
            '--pre_message',
            dest='pre_message',
            help='Message to prepend to course topics',
        )

        parser.add_argument(
            '--skills_descriptor',
            dest='skills_descriptor',
            help='Message that describes skill structure'
        )

        # post-message
        parser.add_argument(
            '--post_message',
            dest='post_message',
            help='Message to append to course topics',
        )

    @staticmethod
    def _get_discovery_api_client():
        """
        Returns an API client which can be used to make Catalog API requests.
        """
        return OAuthAPIClient(
            base_url=settings.DISCOVERY_BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL,
            client_id=settings.DISCOVERY_BACKEND_SERVICE_EDX_OAUTH2_KEY,
            client_secret=settings.DISCOVERY_BACKEND_SERVICE_EDX_OAUTH2_SECRET,
        )

    def handle(self, *args, **options):
        """
        Management command entry point.

        This command is meant to generate a small (<500) set of course prompts. If a larger number of prompts
        should be created, consider adding batching to this command.

        As of now, this command supports a limited structure of course prompt, such that each prompt is composed of
        three messages: the pre message, skills message, and post message. Should we need more messages in the future,
        and want to use this management command, the structure of the command args should be updated.
        """
        course_ids = options['course_ids']
        pre_message = options['pre_message']
        skills_descriptor = options['skills_descriptor']
        post_message = options['post_message']

        client = self._get_discovery_api_client()

        course_ids_list = course_ids.split(',')
        for course_run_id in course_ids_list:
            course_key = CourseKey.from_string(course_run_id)

            # discovery API requires course keys, not course run keys
            course_id = f'{course_key.org}+{course_key.course}'

            url = urljoin(
                settings.DISCOVERY_BASE_URL,
                'api/v1/courses/{course_id}'.format(course_id=course_id)
            )
            response_data = client.get(url).json()
            title = response_data['title']
            skill_names = response_data['skill_names']

            # create restructured dictionary with data
            course_dict = {'title': title, 'topics': skill_names}

            # append descriptor message and decode json dict into a string
            skills_message = skills_descriptor + json.dumps(course_dict)

            # finally, create list of prompt messages and save
            prompt_messages = [pre_message, skills_message, post_message]
            CoursePrompt.objects.update_or_create(
                course_id=course_run_id, defaults={'json_prompt_content': prompt_messages}
            )

            logger.info('Updated course prompt for course_run_id=%s', course_run_id)
