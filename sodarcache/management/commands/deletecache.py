import logging

from django.conf import settings
from django.core.management.base import BaseCommand  # , CommandError

from sodarcache.models import JSONCacheItem

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Deletes cached data from external services'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        if 'sodar_cache' not in settings.ENABLED_BACKEND_PLUGINS:
            logger.error(
                'SodarCache backend not enabled in settings, cancelled!'
            )
            return

        items = JSONCacheItem.objects.all()
        items.delete()
        logger.info('Deleted cached data from all projects')
