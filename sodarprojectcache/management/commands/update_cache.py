from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from projectroles.models import Project
from projectroles.plugins import get_active_plugins, get_backend_api


class Command(BaseCommand):
    help = 'Updates the cached data'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        if 'sodarprojectcache' not in settings.ENABLED_BACKEND_PLUGINS:
            print_msg('SodarProjectCache not enabled in settings, cancelled!')
            raise CommandError

        project_cache = get_backend_api('sodarprojectcache')

        if not project_cache:
            print_msg(
                'SodarProjectCache backend plugin not available, cancelled!'
            )
            raise CommandError

        plugins = get_active_plugins(plugin_type='project_app')
        projects = Project.objects.all()

        for plugin in plugins:
            for project in projects:
                plugin.update_project_cache(project)

        print_msg('Updated cached data')


def print_msg(msg):
    print('UpdateCache: {}'.format(msg))
