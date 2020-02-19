import json
import logging
import urllib.request

from django.contrib import auth
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from projectroles.models import RemoteSite, SODAR_CONSTANTS
from projectroles.remote_projects import RemoteProjectAPI
from projectroles.views_api import CORE_API_MEDIA_TYPE, CORE_API_DEFAULT_VERSION

User = auth.get_user_model()
logger = logging.getLogger(__name__)


# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']


class Command(BaseCommand):
    help = 'Synchronizes user and project data from a remote site.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        if getattr(settings, 'PROJECTROLES_DISABLE_CATEGORIES', False):
            logger.info(
                'Project categories and nesting disabled, '
                'remote sync disabled'
            )
            return

        if settings.PROJECTROLES_SITE_MODE != SITE_MODE_TARGET:
            logger.error('Site not in TARGET mode, unable to sync')
            return

        try:
            site = RemoteSite.objects.get(mode=SITE_MODE_SOURCE)

        except RemoteSite.DoesNotExist:
            logger.error('No source site defined, unable to sync')
            return

        if getattr(settings, 'PROJECTROLES_ALLOW_LOCAL_USERS', False):
            logger.info(
                'PROJECTROLES_ALLOW_LOCAL_USERS=True, will sync '
                'roles for existing local users'
            )

        logger.info(
            'Retrieving data from remote site "{}" ({})..'.format(
                site.name, site.get_url()
            )
        )

        api_url = site.get_url() + reverse(
            'projectroles:api_remote_get', kwargs={'secret': site.secret}
        )

        try:
            api_req = urllib.request.Request(api_url)
            api_req.add_header(
                'accept',
                '{}; version={}'.format(
                    CORE_API_MEDIA_TYPE, CORE_API_DEFAULT_VERSION
                ),
            )
            response = urllib.request.urlopen(api_req)
            remote_data = json.loads(response.read())

        except Exception as ex:
            logger.error(
                'Unable to retrieve data from remote site: {}'.format(ex)
            )
            return

        remote_api = RemoteProjectAPI()
        remote_api.sync_source_data(site, remote_data)
        logger.info('Syncremote command OK')
