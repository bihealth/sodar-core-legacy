import json
import sys
import urllib.request

from django.contrib import auth
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from projectroles.models import RemoteSite, SODAR_CONSTANTS
from projectroles.remote_projects import RemoteProjectAPI

User = auth.get_user_model()


# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']


class Command(BaseCommand):
    help = 'Synchronizes user and project data from a remote site.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        if (
            hasattr(settings, 'PROJECTROLES_DISABLE_CATEGORIES')
            and settings.PROJECTROLES_DISABLE_CATEGORIES
        ):
            sys.exit(
                'Project categories and nesting disabled, '
                'remote sync disabled'
            )

        if settings.PROJECTROLES_SITE_MODE != SITE_MODE_TARGET:
            sys.exit('Site not in TARGET mode, unable to sync')

        try:
            site = RemoteSite.objects.get(mode=SITE_MODE_SOURCE)

        except RemoteSite.DoesNotExist:
            sys.exit('No source site defined, unable to sync')

        print(
            'Retrieving data from remote site "{}" ({})..'.format(
                site.name, site.url
            )
        )

        api_url = site.url + reverse(
            'projectroles:api_remote_get', kwargs={'secret': site.secret}
        )

        try:
            response = urllib.request.urlopen(api_url)
            remote_data = json.loads(response.read())

        except Exception as ex:
            sys.exit('Unable to retrieve data from remote site: {}'.format(ex))

        remote_api = RemoteProjectAPI()
        remote_api.sync_source_data(site, remote_data)
        print('Syncremote command OK')
