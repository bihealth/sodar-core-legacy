"""SodarCache API for adding and updating cache items"""

from django.contrib.auth import get_user_model

# Projectroles dependency
from projectroles.plugins import get_active_plugins
from projectroles.utils import get_app_names

from sodarcache.models import JSONCacheItem


# Local variables
APP_NAMES = get_app_names()
LABEL_MAX_WIDTH = 32

CACHE_TYPES = ['json']

# Access Django user model
User = get_user_model()


class SodarCacheAPI:
    """SodarCache backend API to be used by Django apps."""

    # Internal functions -------------------------------------------------------

    @classmethod
    def _check_app_name(cls, app_name):
        """Check if app_name is valid, raise ValueError if not"""
        if app_name not in APP_NAMES:
            raise ValueError(
                'Unknown app name "{}" (installed apps: {})'.format(
                    app_name, ', '.join(x for x in APP_NAMES)
                )
            )

    @classmethod
    def _check_data_type(cls, data_type):
        """Check if data_type is valid, raise ValueError if not"""
        if data_type not in CACHE_TYPES:
            raise ValueError(
                'Unknown data type "{}" for a cache item '
                '(allowed types: {})'.format(
                    data_type, ', '.join(x for x in CACHE_TYPES)
                )
            )

    # API functions ------------------------------------------------------------

    @classmethod
    def get_project_cache(cls, project, data_type='json'):
        """
        Return all cached data for a project.

        :param project: Project object
        :param data_type: string stating the data type of the cache items
        :return: QuerySet
        :raise: ValueError if data_type is invalid
        """
        cls._check_data_type(data_type)
        return JSONCacheItem.objects.filter(project=project)

    @classmethod
    def update_cache(cls, name=None, project=None):
        """
        Update items by certain name within a project by calling implemented
        functions in project app plugins.

        :param project: Project object to limit update to (optional)
        :param name: Item name to limit update to (string, optional)
        """
        plugins = get_active_plugins(plugin_type='project_app')

        for plugin in plugins:
            plugin.update_cache(name, project)

    @classmethod
    def get_cache_item(cls, app_name, name, project=None):
        """
        Return cached data by app_name, name (identifier) and optional project.
        Returns None if not found.

        :param name: Item name (string)
        :param app_name: name of the app which sets the item (string)
        :param project: Project object (optional)
        :return: JSONCacheItem object
        :raise: ValueError if app_name is invalid
        """
        cls._check_app_name(app_name)

        query_string = {'app_name': app_name, 'name': name}

        if project:
            query_string['project'] = project

        return JSONCacheItem.objects.filter(**query_string).first()

    @classmethod
    def set_cache_item(
        cls, app_name, name, user, data, data_type='json', project=None
    ):
        """
        Create or update and save a cache item.

        :param app_name: name of the app which sets the item (string)
        :param name: Item name (string)
        :param user: User creating/updating the item
        :param data: item data (dict)
        :param data_type: string stating the data type of the cache items
        :param project: Project object (optional)
        :return: JSONCacheItem object
        :raise: ValueError if app_name is invalid
        :raise: ValueError if data_type is invalid
        """
        cls._check_app_name(app_name)
        cls._check_data_type(data_type)
        item = cls.get_cache_item(app_name, name, project)

        if not item:
            if data_type == 'json':
                item = JSONCacheItem()
                item.name = name
                item.app_name = app_name

        item.user = user
        item.data = data

        if project:
            item.project = project

        item.save()
        return item

    @classmethod
    def get_update_time(cls, app_name, name, project=None):
        """
        Return the time of the last update of a cache object as seconds since
        epoch.

        :param name: Item name (string)
        :param app_name: name of the app which sets the item (string)
        :param project: Project object (optional)
        :return: Float
        """
        item = cls.get_cache_item(app_name, name, project)
        return item.date_modified.timestamp() if item else None
