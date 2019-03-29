"""SodarProjectCache API for adding and updating cache items"""

from django.contrib.auth import get_user_model

# Projectroles dependency
from projectroles.utils import get_app_names

from sodarprojectcache.models import JsonCacheItem

from pytz import timezone

# Local variables
APP_NAMES = get_app_names()
LABEL_MAX_WIDTH = 32

CACHE_TYPES = ['json']

# Access Django user model
User = get_user_model()


class SodarProjectCacheAPI:
    """SodarProjectCache backend API to be used by Django apps."""

    #####################
    # Internal functions
    #####################

    @classmethod
    def _get_datetime(cls, naive_dt):
        """Return a printable datetime in Berlin timezone from a naive
        datetime object"""
        dt = naive_dt.replace(tzinfo=timezone('GMT'))
        dt = dt.astimezone(timezone('Europe/Berlin'))
        return dt.strftime('%Y-%m-%d %H:%M')

    # API functions ------------------------------------------------------------

    @staticmethod
    def get_project_cache(project, data_type='json'):
        """
        Return all cached data for a project.

        :param project: Project object
        :param data_type: string stating the data type of the cache items
        :return: QuerySet
        """

        if data_type not in CACHE_TYPES:
            raise ValueError(
                'Unknown data type "{}" for a cache item (allowed types: {})'.format(
                    data_type, ', '.join(x for x in CACHE_TYPES)
                )
            )

        items = JsonCacheItem.objects.filter(project=project)

        return items

    @staticmethod
    def get_cache_item(name, project=None):
        """
        Return cached data by name (identifier).

        :param name: name given by the data setting app
        :param project: Project object (optional)
        :return: JsonCacheItem object
        """

        if project:
            item = JsonCacheItem.objects.get(name=name, project=project)
        else:
            item = JsonCacheItem.objects.get(name=name)

        return item

    @staticmethod
    def set_cache_item(
        name, app_name, user, data, data_type='json', project=None
    ):
        """
        Create or update and save a cache item.

        :param name: item ID string (must match schema)
        :param app_name: ID string of app from which item was invoked (NOTE:
            should correspond to member "name" in app plugin!)
        :param user: User creating/updating the item
        :param data: item data (dict)
        :param data_type: string stating the data type of the cache items
        :param project: Project object (optional)
        :return: JsonCacheItem object
        :raise: ValueError if app_name is invalid
        :raise: ValueError if data_type is invalid
        """
        if app_name not in APP_NAMES:
            raise ValueError(
                'Unknown app name "{}" (active apps: {})'.format(
                    app_name, ', '.join(x for x in APP_NAMES)
                )
            )

        if data_type not in CACHE_TYPES:
            raise ValueError(
                'Unknown data type "{}" for a cache item (allowed types: {})'.format(
                    data_type, ', '.join(x for x in CACHE_TYPES)
                )
            )

        try:
            item = JsonCacheItem.objects.get(name=name)
        except JsonCacheItem.DoesNotExist:
            if data_type == 'json':
                item = JsonCacheItem()
                item.name = name

        item.app_name = app_name
        item.user = user
        item.data = data

        if project:
            item.project = project

        item.save()

        return item

    def get_update_time(self, name, project=None):
        """
        Return the time of the last update of a cache object.

        :param name: name given by the data setting app
        :param project: Project object (optional)
        :return: string
        """

        if project:
            item = JsonCacheItem.objects.get(name=name, project=project)
        else:
            item = JsonCacheItem.objects.get(name=name)

        update_time = self._get_datetime(item.date_modified)

        return update_time
