"""Tests for the API in the sodarcache app"""

from django.forms.models import model_to_dict

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import get_backend_api


from .test_models import TestJsonCacheItemBase, JsonCacheItemMixin
from ..models import JSONCacheItem


# Global constants from settings
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
TEST_APP_NAME = 'sodarcache'
INVALID_APP_NAME = 'timeline'  # Valid app name but but no data is created


class TestSodarCacheAPI(JsonCacheItemMixin, TestJsonCacheItemBase):
    """Testing sodarcache API class"""

    def setUp(self):
        super().setUp()
        self.cache_backend = get_backend_api('sodar_cache')

    def test_add_cache_item(self):
        """Test creating a cache item"""

        # Assert precondition
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)

        item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )

        # Assert object status after insert
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)

        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': 'sodarcache',
            'user': self.user_owner.pk,
            'name': 'test_item',
            'data': {'test_key': 'test_val'},
            'sodar_uuid': item.sodar_uuid,
        }

        self.assertEqual(model_to_dict(item), expected)

    def test_add_cache_item_invalid_app(self):
        """Test adding an event with an invalid app name"""

        # Assert preconditions
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)

        with self.assertRaises(ValueError):
            self.cache_backend.set_cache_item(
                project=self.project,
                app_name='NON-EXISTING APP NAME',
                user=self.user_owner,
                name='test_item',
                data={'test_key': 'test_val'},
            )

        # Assert object status
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)

    def test_add_cache_item_invalid_data(self):
        """Test adding an event with an invalid app name"""

        # Assert preconditions
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)

        with self.assertRaises(ValueError):
            self.cache_backend.set_cache_item(
                project=self.project,
                app_name='NON-EXISTING APP NAME',
                user=self.user_owner,
                name='test_item',
                data_type='INVALID DATA TYPE',
                data={'test_key': 'test_val'},
            )

        # Assert object status
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)

    def test_set_cache_value(self):
        """Test updating a cache item"""

        # Assert precondition
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)

        item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )

        # Assert object status after insert
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)

        update_item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'new_test_val'},
        )

        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': 'sodarcache',
            'user': self.user_owner.pk,
            'name': 'test_item',
            'data': {'test_key': 'new_test_val'},
            'sodar_uuid': item.sodar_uuid,
        }

        self.assertEqual(model_to_dict(update_item), expected)

    def test_set_cache_value_no_user(self):
        """Test updating a cache with no user"""

        # Assert precondition
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)

        item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            name='test_item',
            data={'test_key': 'test_val'},
        )

        # Assert object status after insert
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)

        update_item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            name='test_item',
            data={'test_key': 'new_test_val'},
        )

        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': 'sodarcache',
            'user': None,
            'name': 'test_item',
            'data': {'test_key': 'new_test_val'},
            'sodar_uuid': item.sodar_uuid,
        }

        self.assertEqual(model_to_dict(update_item), expected)

    def test_get_cache_item(self):
        """Test getting a cache item"""

        # Assert precondition
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)

        item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )

        # Assert object status after insert
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)

        get_item = self.cache_backend.get_cache_item(
            app_name=TEST_APP_NAME, name='test_item', project=self.project
        )

        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': 'sodarcache',
            'user': self.user_owner.pk,
            'name': 'test_item',
            'data': {'test_key': 'test_val'},
            'sodar_uuid': item.sodar_uuid,
        }

        self.assertEqual(model_to_dict(get_item), expected)

    def test_get_project_cache(self):
        """Test getting all cache item of a project"""
        first_item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name='test_item1',
            data={'test_key1': 'test_val1'},
        )

        second_item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name='test_item2',
            data={'test_key2': 'test_val2'},
        )

        project_items = self.cache_backend.get_project_cache(
            project=self.project, data_type='json'
        )

        self.assertEqual(project_items.count(), 2)
        self.assertIn(first_item, project_items)
        self.assertIn(second_item, project_items)

    def test_get_update_time(self):
        """Test getting the time of the latest update of a cache item"""
        item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )

        update_time = self.cache_backend.get_update_time(
            app_name=TEST_APP_NAME, name='test_item', project=self.project
        )

        self.assertEqual(update_time, item.date_modified.timestamp())

    def test_delete(self):
        """Test delete_cache() with no arguments"""
        self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        delete_status = self.cache_backend.delete_cache()
        self.assertEqual(delete_status, 1)
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)

    def test_delete_app(self):
        """Test delete_cache() with app name argument"""
        self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        delete_status = self.cache_backend.delete_cache(app_name=TEST_APP_NAME)
        self.assertEqual(delete_status, 1)
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)

    def test_delete_app_empty(self):
        """Test delete_cache() on an app name without created items"""
        self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        delete_status = self.cache_backend.delete_cache(
            app_name=INVALID_APP_NAME
        )
        self.assertEqual(delete_status, 0)
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)

    def test_delete_project(self):
        """Test delete_cache() with project argument"""
        self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        delete_status = self.cache_backend.delete_cache(project=self.project)
        self.assertEqual(delete_status, 1)
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)

    def test_delete_project_empty(self):
        """Test delete_cache() on a project without created items"""
        new_project = self._make_project(
            'NewProject', PROJECT_TYPE_PROJECT, None
        )
        self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        delete_status = self.cache_backend.delete_cache(project=new_project)
        self.assertEqual(delete_status, 0)
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
