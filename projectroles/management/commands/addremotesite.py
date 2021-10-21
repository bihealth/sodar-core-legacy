import re
import sys

from django.contrib import auth
from django.core.management.base import BaseCommand
from django.db import transaction

from projectroles.management.logging import ManagementCommandLogger
from projectroles.models import RemoteSite, SODAR_CONSTANTS


User = auth.get_user_model()
logger = ManagementCommandLogger(__name__)


# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_PEER = SODAR_CONSTANTS['SITE_MODE_PEER']


class Command(BaseCommand):
    help = 'Creates a remote site from given arguments'

    def add_arguments(self, parser):
        # ---------------------------
        # RemoteSite Model Argumments
        # ---------------------------
        parser.add_argument(
            '-n',
            '--name',
            dest='name',
            type=str,
            required=True,
            help='Name of the remote site',
        )
        parser.add_argument(
            '-u',
            '--url',
            dest='url',
            type=str,
            required=True,
            help='URL of the remote site. Can be provided without protocol '
            'prefix, defaults to HTTP',
        )
        parser.add_argument(
            '-m',
            '--mode',
            dest='mode',
            type=str,
            required=True,
            help='Mode of the remote site',
        )
        parser.add_argument(
            '-d',
            '--description',
            dest='description',
            type=str,
            required=False,
            default='',
            help='Description of the remote site',
        )
        parser.add_argument(
            '-t',
            '--token',
            dest='secret',
            type=str,
            required=True,
            help='Secret token of the remote site',
        )
        parser.add_argument(
            '-ud',
            '--user-display',
            dest='user_display',
            default=True,
            required=False,
            type=bool,
            help='User display of the remote site',
        )
        # --------------------
        # Additional Arguments
        # --------------------
        parser.add_argument(
            '-s',
            '--suppress-error',
            dest='suppress_error',
            required=False,
            default=False,
            action='store_true',
            help='Suppresses error if site already exists',
        )

    def handle(self, *args, **options):
        logger.info('Creating remote site..')
        name = options['name']
        url = options['url']
        # Validate url
        if not url.startswith('http://') and not url.startswith('https://'):
            url = ''.join(['http://', url])
        pattern = re.compile(r'(http|https)://.*\..*')
        if not pattern.match(url):
            logger.error('Invalid URL "{}"'.format(url))
            sys.exit(1)

        mode = options['mode'].upper()
        # Validate mode
        if mode not in [SITE_MODE_SOURCE, SITE_MODE_TARGET]:
            if mode in [SITE_MODE_PEER]:
                logger.error('Creating PEER sites is not allowed')
            else:
                logger.error('Unkown mode "{}"'.format(mode))
            sys.exit(1)

        description = options['description']
        secret = options['secret']
        user_diplsay = options['user_display']
        suppress_error = options['suppress_error']

        # Validate whether site exists
        name_exists = bool(len(RemoteSite.objects.filter(name=name)))
        url_exists = bool(len(RemoteSite.objects.filter(url=url)))
        if name_exists or url_exists:
            err_msg = 'Remote site exists with {} "{}"'.format(
                'name' if name_exists else 'URL', name if name_exists else url
            )
            if not suppress_error:
                logger.error(err_msg)
                sys.exit(1)
            else:
                logger.info(err_msg)
                sys.exit(0)

        with transaction.atomic():
            create_values = {
                'name': name,
                'url': url,
                'mode': mode,
                'description': description,
                'secret': secret,
                'user_display': user_diplsay,
            }
            site = RemoteSite.objects.create(**create_values)

        logger.info(
            'Created remote site "{}" with mode {}'.format(site.name, site.mode)
        )
