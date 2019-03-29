"""Tests for the API in the sodarprojectcache app"""

from django.forms.models import model_to_dict

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import get_backend_api


from .test_models import TestJsonCacheItemBase, JsonCacheItemMixin
from ..models import JsonCacheItem


# Global constants from settings
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


class TestSodarProjectCacheAPI(JsonCacheItemMixin, TestJsonCacheItemBase):
    """Testing sodarprojectcache API class"""

    def setUp(self):
        super().setUp()
        self.project_cache = get_backend_api('sodarprojectcache')

    def test_add_cache_item(self):
        """Test creating a cache item"""

        # Assert precondition
        self.assertEqual(JsonCacheItem.objects.all().count(), 0)

        item = self.project_cache.set_cache_item(
            project=self.project,
            app_name='sodarprojectcache',
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )

        # Assert object status after insert
        self.assertEqual(JsonCacheItem.objects.all().count(), 1)

        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': 'sodarprojectcache',
            'user': self.user_owner.pk,
            'name': 'test_item',
            'data': {'test_key': 'test_val'},
            'sodar_uuid': item.sodar_uuid,
        }

        self.assertEqual(model_to_dict(item), expected)

    def test_add_cache_item_invalid_app(self):
        """Test adding an event with an invalid app name"""

        # Assert preconditions
        self.assertEqual(JsonCacheItem.objects.all().count(), 0)

        with self.assertRaises(ValueError):
            self.project_cache.set_cache_item(
                project=self.project,
                app_name='NON-EXISTING APP NAME',
                user=self.user_owner,
                name='test_item',
                data={'test_key': 'test_val'},
            )

        # Assert object status
        self.assertEqual(JsonCacheItem.objects.all().count(), 0)

    def test_add_cache_item_invalid_data(self):
        """Test adding an event with an invalid app name"""

        # Assert preconditions
        self.assertEqual(JsonCacheItem.objects.all().count(), 0)

        with self.assertRaises(ValueError):
            self.project_cache.set_cache_item(
                project=self.project,
                app_name='NON-EXISTING APP NAME',
                user=self.user_owner,
                name='test_item',
                data_type='INVALID DATA TYPE',
                data={'test_key': 'test_val'},
            )

        # Assert object status
        self.assertEqual(JsonCacheItem.objects.all().count(), 0)

    def test_set_cache_value(self):
        """Test updating a cache item"""

        # Assert precondition
        self.assertEqual(JsonCacheItem.objects.all().count(), 0)

        item = self.project_cache.set_cache_item(
            project=self.project,
            app_name='sodarprojectcache',
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )

        # Assert object status after insert
        self.assertEqual(JsonCacheItem.objects.all().count(), 1)

        update_item = self.project_cache.set_cache_item(
            project=self.project,
            app_name='sodarprojectcache',
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'new_test_val'},
        )

        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': 'sodarprojectcache',
            'user': self.user_owner.pk,
            'name': 'test_item',
            'data': {'test_key': 'new_test_val'},
            'sodar_uuid': item.sodar_uuid,
        }

        self.assertEqual(model_to_dict(update_item), expected)

    def test_get_cache_item(self):
        """Test getting a cache item"""

        # Assert precondition
        self.assertEqual(JsonCacheItem.objects.all().count(), 0)

        item = self.project_cache.set_cache_item(
            project=self.project,
            app_name='sodarprojectcache',
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )

        # Assert object status after insert
        self.assertEqual(JsonCacheItem.objects.all().count(), 1)

        get_item = self.project_cache.get_cache_item(
            name='test_item', project=self.project
        )

        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': 'sodarprojectcache',
            'user': self.user_owner.pk,
            'name': 'test_item',
            'data': {'test_key': 'test_val'},
            'sodar_uuid': item.sodar_uuid,
        }

        self.assertEqual(model_to_dict(get_item), expected)

    def test_get_project_cache(self):
        """Test getting all cache item of a project"""

        first_item = self.project_cache.set_cache_item(
            project=self.project,
            app_name='sodarprojectcache',
            user=self.user_owner,
            name='test_item1',
            data={'test_key1': 'test_val1'},
        )

        second_item = self.project_cache.set_cache_item(
            project=self.project,
            app_name='sodarprojectcache',
            user=self.user_owner,
            name='test_item2',
            data={'test_key2': 'test_val2'},
        )

        project_items = self.project_cache.get_project_cache(
            project=self.project, data_type='json'
        )

        self.assertEqual(project_items.count(), 2)
        self.assertIn(first_item, project_items)
        self.assertIn(second_item, project_items)

    def test_get_update_time(self):
        """Test getting the time of the latest update of a cache item"""

        item = self.project_cache.set_cache_item(
            project=self.project,
            app_name='sodarprojectcache',
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )

        update_time = self.project_cache.get_update_time(
            name='test_item', project=self.project
        )

        self.assertEqual(
            update_time, self.project_cache._get_datetime(item.date_modified)
        )
