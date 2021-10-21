import sys

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

# Projectroles dependency
from projectroles.management.logging import ManagementCommandLogger
from projectroles.models import Project
from projectroles.plugins import get_active_plugins, get_backend_api


logger = ManagementCommandLogger(__name__)


class Command(BaseCommand):
    help = 'Synchronizes cached data from external services'

    def add_arguments(self, parser):
        parser.add_argument(
            '-p',
            '--project',
            metavar='UUID',
            type=str,
            help='Limit sync to a project',
        )

    def handle(self, *args, **options):

        if 'sodar_cache' not in settings.ENABLED_BACKEND_PLUGINS:
            logger.error(
                'SodarCache backend not enabled in settings, cancelled'
            )
            sys.exit(1)

        cache_backend = get_backend_api('sodar_cache')
        if not cache_backend:
            logger.error('SodarCache backend plugin not available, cancelled')
            sys.exit(1)

        update_kwargs = {}

        if options.get('project'):
            try:
                project = Project.objects.get(sodar_uuid=options['project'])
                update_kwargs['project'] = project
                logger.info(
                    'Limiting sync to project "{}" ({})"'.format(
                        project.title, project.sodar_uuid
                    )
                )
            except Project.DoesNotExist:
                logger.error(
                    'Project not found with UUID={}'.format(options['project'])
                )
                sys.exit(1)
            except ValidationError:
                logger.error('Not a valid UUID: {}'.format(options['project']))
                sys.exit(1)

        if not update_kwargs:
            logger.info('Synchronizing cache for all projects')

        plugins = get_active_plugins(plugin_type='project_app')
        errors = False

        for plugin in plugins:
            try:
                plugin.update_cache(**update_kwargs)
            except Exception as ex:
                logger.error(
                    'Update failed for plugin "{}": "{}"'.format(
                        plugin.name, ex
                    )
                )
                errors = True

        logger.info(
            'Cache synchronization {}'.format(
                'finished with errors (see logs)' if errors else 'OK'
            )
        )
