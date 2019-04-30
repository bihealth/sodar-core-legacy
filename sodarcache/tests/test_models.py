"""Tests for models in the sodarcache app"""

from test_plus.test import TestCase
from django.forms.models import model_to_dict

# Projectroles dependency
from projectroles.models import Role, SODAR_CONSTANTS
from projectroles.tests.test_models import ProjectMixin, RoleAssignmentMixin

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


class JsonCacheItemMixin:
    """Helper mixin for JSONCacheItem creation"""

    @classmethod
    def _make_item(cls, project, app_name, name, user, data):
        values = {
            'project': project,
            'app_name': app_name,
            'user': user,
            'name': name,
            'data': data,
        }
        result = JSONCacheItem(**values)
        result.save()
        return result


class TestJsonCacheItemBase(ProjectMixin, RoleAssignmentMixin, TestCase):
    def setUp(self):
        # Make owner user
        self.user_owner = self.make_user('owner')

        # Init project, role and assignment
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.role_owner = Role.objects.get_or_create(name=PROJECT_ROLE_OWNER)[0]
        self.role_delegate = Role.objects.get_or_create(
            name=PROJECT_ROLE_DELEGATE
        )[0]
        self.assignment_owner = self._make_assignment(
            self.project, self.user_owner, self.role_owner
        )


class TestJsonCacheItem(JsonCacheItemMixin, TestJsonCacheItemBase):
    def setUp(self):
        super().setUp()

        self.item = self._make_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )

    def test_initialization(self):
        expected = {
            'id': self.item.pk,
            'project': self.project.pk,
            'app_name': TEST_APP_NAME,
            'name': 'test_item',
            'user': self.user_owner.pk,
            'sodar_uuid': self.item.sodar_uuid,
            'data': {'test_key': 'test_val'},
        }

        self.assertEqual(model_to_dict(self.item), expected)

    def test__str__(self):
        expected = 'TestProject: sodarcache: test_item'
        self.assertEqual(str(self.item), expected)

    def test__repr__(self):
        expected = "JSONCacheItem('TestProject', 'sodarcache', 'test_item')"
        self.assertEqual(repr(self.item), expected)

    def test__repr__no_project(self):
        """Test __repr__() with no project"""

        new_item = self._make_item(
            project=None,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name='test_item2',
            data={'test_key': 'test_val'},
        )

        expected = "JSONCacheItem('N/A', 'sodarcache', 'test_item2')"
        self.assertEqual(repr(new_item), expected)
