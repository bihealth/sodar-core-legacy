import logging

from django.conf import settings
from django.core.management.base import BaseCommand  # , CommandError

# Projectroles dependency
from projectroles.models import Project

from sodarcache.models import JSONCacheItem

logger = logging.getLogger(__name__)


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
            return

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
                return

        else:
            items = JSONCacheItem.objects.all()

        item_count = items.count()

        if item_count == 0:
            logger.info('No cached data found')
            return

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
