import logging

from django.core.management.base import BaseCommand

from projectroles.app_settings import AppSettingAPI
from projectroles.models import AppSetting, Project

logger = logging.getLogger(__name__)

# App settings API
app_settings = AppSettingAPI()


def get_api_settings():
    return {
        project: [
            app_setting
            for app_setting in app_settings.get_all_settings(project)
        ]
        for project in Project.objects.filter(type='PROJECT')
    }


def get_db_settings():
    return AppSetting.objects.filter(user=None)


def is_setting_undefined(db_setting, api_settings):
    return get_setting_str(db_setting) not in api_settings.get(
        db_setting.project, []
    )


def get_setting_str(db_setting):
    return '.'.join(
        [
            'settings',
            'projectroles'
            if db_setting.app_plugin is None
            else db_setting.app_plugin.name,
            db_setting.name,
        ]
    )


def get_undefined_settings(api_settings, db_settings):
    return [s for s in db_settings if is_setting_undefined(s, api_settings)]


class Command(BaseCommand):
    help = 'Cleans up undefined app settings from the database.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        api_settings = get_api_settings()
        db_settings = get_db_settings()
        ghosts = get_undefined_settings(api_settings, db_settings)

        for ghost in ghosts:
            logger.info(
                'Removing undefined app setting: {}'.format(
                    get_setting_str(ghost)
                )
            )
            ghost.delete()
