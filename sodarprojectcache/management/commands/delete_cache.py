from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from sodarprojectcache.models import JsonCacheItem


class Command(BaseCommand):
    help = 'Deletes the cached data'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        if 'sodarprojectcache' not in settings.ENABLED_BACKEND_PLUGINS:
            print_msg('SodarProjectCache not enabled in settings, cancelled!')
            raise CommandError

        items = JsonCacheItem.objects.all()

        items.delete()

        print_msg('Deleted all cached data')


def print_msg(msg):
    print('DeleteCache: {}'.format(msg))
