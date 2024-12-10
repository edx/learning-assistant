""""
Django management command to remove LearningAssistantMessage objects
if they have reached their expiration date.
"""
import logging
import time
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

from learning_assistant.models import LearningAssistantMessage

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django Management command to remove expired messages.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch_size',
            action='store',
            dest='batch_size',
            type=int,
            default=300,
            help='Maximum number of messages to remove. '
                 'This helps avoid overloading the database while updating large amount of data.'
        )
        parser.add_argument(
            '--sleep_time',
            action='store',
            dest='sleep_time',
            type=int,
            default=10,
            help='Sleep time in seconds between update of batches'
        )

    def handle(self, *args, **options):
        """
        Management command entry point.
        """
        batch_size = options['batch_size']
        sleep_time = options['sleep_time']

        expiry_date = datetime.now() - timedelta(days=getattr(settings, 'LEARNING_ASSISTANT_MESSAGES_EXPIRY', 30))

        total_deleted = 0
        deleted_count = None

        while deleted_count != 0:
            ids_to_delete = LearningAssistantMessage.objects.filter(
                created__lte=expiry_date
            ).values_list('id', flat=True)[:batch_size]

            ids_to_delete = list(ids_to_delete)
            delete_queryset = LearningAssistantMessage.objects.filter(
                id__in=ids_to_delete
            )
            deleted_count, _ = delete_queryset.delete()

            total_deleted += deleted_count
            log.info(f'{deleted_count} messages deleted.')
            time.sleep(sleep_time)

        log.info(f'Job completed. {total_deleted} messages deleted.')
