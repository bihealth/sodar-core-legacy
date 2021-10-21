import sys

from django.conf import settings
from django.core.management.base import BaseCommand  # , CommandError

# Projectroles dependency
from projectroles.management.logging import ManagementCommandLogger
from projectroles.models import Project

from sodarcache.models import JSONCacheItem

logger = ManagementCommandLogger(__name__)


class Command(BaseCommand):
    help = 'Deletes cached data from external services'

    def add_arguments(self, parser):
        parser.add_argument(
            '-p',
            '--project',
            metavar='UUID',
            type=str,
            help='Limit deletion to a project',
        )

    def handle(self, *args, **options):
        if 'sodar_cache' not in settings.ENABLED_BACKEND_PLUGINS:
            logger.error(
                'SodarCache backend not enabled in settings, cancelled!'
            )
            sys.exit(1)

        project = None

        if options.get('project'):
            try:
                project = Project.objects.get(sodar_uuid=options['project'])
                logger.info(
                    'Limiting deletion to project "{}" ({})"'.format(
                        project.title, project.sodar_uuid
                    )
                )
                items = JSONCacheItem.objects.filter(project=project)
            except Project.DoesNotExist:
                logger.error(
                    'Project not found with UUID={}'.format(options['project'])
                )
                sys.exit(1)
        else:
            items = JSONCacheItem.objects.all()

        item_count = items.count()
        if item_count == 0:
            logger.info('No cached data found')
            sys.exit(0)

        items.delete()
        logger.info(
            'Deleted {} cached data item{} from {}'.format(
                item_count,
                's' if item_count != 1 else '',
                'project "{}" ({})'.format(
                    project.full_title, project.sodar_uuid
                )
                if project
                else 'all projects',
            )
        )
