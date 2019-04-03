import logging

from django.conf import settings
from django.core.management.base import BaseCommand  # , CommandError

from projectroles.plugins import get_active_plugins, get_backend_api

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Updates cached data from external services'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        if 'sodar_cache' not in settings.ENABLED_BACKEND_PLUGINS:
            logger.error(
                'SodarCache backend not enabled in settings, cancelled!'
            )
            return

        cache_backend = get_backend_api('sodar_cache')

        if not cache_backend:
            logger.error('SodarCache backend plugin not available, cancelled!')
            return

        plugins = get_active_plugins(plugin_type='project_app')

        for plugin in plugins:
            plugin.update_cache()

        logger.info('Updated cached data for all projects and apps')
