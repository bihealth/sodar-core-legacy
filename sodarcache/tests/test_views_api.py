"""Tests for API views in the sodarcache app"""

import json

from django.urls import reverse
from django.forms.models import model_to_dict

# Projectroles dependency
from projectroles.models import Role, SODAR_CONSTANTS
from projectroles.plugins import get_backend_api

from sodarcache.models import JSONCacheItem
from sodarcache.tests.test_models import (
    TestJsonCacheItemBase,
    JsonCacheItemMixin,
)


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
TEST_APP_NAME = 'sodarcache'


class TestViewsBase(JsonCacheItemMixin, TestJsonCacheItemBase):
    """Base class for sodarcache view testing"""

    def setUp(self):
        super().setUp()
        self.cache_backend = get_backend_api('sodar_cache')

        # Init roles
        self.role_owner = Role.objects.get_or_create(name=PROJECT_ROLE_OWNER)[0]
        self.role_delegate = Role.objects.get_or_create(
            name=PROJECT_ROLE_DELEGATE
        )[0]
        self.role_contributor = Role.objects.get_or_create(
            name=PROJECT_ROLE_CONTRIBUTOR
        )[0]
        self.role_guest = Role.objects.get_or_create(name=PROJECT_ROLE_GUEST)[0]

        # Init superuser
        self.user = self.make_user('superuser')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        # Init project
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        # Init cache item
        self.item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )


class TestSodarCacheGetAPIView(TestViewsBase):
    """Tests for the sodarcache item getting API view"""

    def test_get_wrong_item(self):
        values = {'app_name': TEST_APP_NAME, 'name': 'not_test_item'}

        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'sodarcache:cache_get',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )
        self.assertEqual(response.status_code, 404)

    def test_get_item(self):
        values = {'app_name': TEST_APP_NAME, 'name': 'test_item'}

        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'sodarcache:cache_get',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )

        expected = {
            'project_uuid': str(self.project.sodar_uuid),
            'user_uuid': str(self.user_owner.sodar_uuid),
            'name': 'test_item',
            'data': {'test_key': 'test_val'},
            'sodar_uuid': str(self.item.sodar_uuid),
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected)


class TestSodarCacheSetAPIView(TestViewsBase):
    """Tests for the sodarcache item setting API view"""

    def test_set_item(self):
        """Test creating a new cache item"""
        values = {
            'app_name': TEST_APP_NAME,
            'name': 'new_test_item',
            'data': json.dumps({'test_key': 'test_val'}),
        }

        # Assert precondition
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'sodarcache:cache_set',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(JSONCacheItem.objects.all().count(), 2)

        item = JSONCacheItem.objects.get(name='new_test_item')
        self.assertIsNotNone(item)

        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': TEST_APP_NAME,
            'user': self.user.pk,
            'name': 'new_test_item',
            'data': json.dumps({'test_key': 'test_val'}),
            'sodar_uuid': item.sodar_uuid,
        }

        model_dict = model_to_dict(item)
        self.assertEqual(model_dict, expected)

    def test_update_item(self):
        """Test updating a cache item"""
        values = {
            'app_name': TEST_APP_NAME,
            'name': 'test_item',
            'data': json.dumps({'test_key': 'test_val_updated'}),
        }

        # Assert precondition
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'sodarcache:cache_set',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)

        item = JSONCacheItem.objects.get(name='test_item')
        self.assertIsNotNone(item)

        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': TEST_APP_NAME,
            'user': self.user.pk,
            'name': 'test_item',
            'data': json.dumps({'test_key': 'test_val_updated'}),
            'sodar_uuid': item.sodar_uuid,
        }

        model_dict = model_to_dict(item)
        self.assertEqual(model_dict, expected)


class TestSodarCacheGetDateAPIView(TestViewsBase):
    """Tests for the sodarcache item update time getting API view"""

    def test_get_time(self):
        # Assert precondition
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)

        values = {'app_name': TEST_APP_NAME, 'name': 'test_item'}

        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'sodarcache:cache_get_date',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )

        expected = self.cache_backend.get_update_time(
            app_name=TEST_APP_NAME, name='test_item'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['update_time'], expected)
