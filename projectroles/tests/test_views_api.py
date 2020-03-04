"""REST API view tests for the projectroles app"""
import base64
import json
import pytz

from django.conf import settings
from django.forms.models import model_to_dict
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from knox.models import AuthToken

from test_plus.test import APITestCase

from projectroles import views_api
from projectroles.models import Project, Role, RoleAssignment, SODAR_CONSTANTS
from projectroles.plugins import change_plugin_status, get_backend_api
from projectroles.remote_projects import RemoteProjectAPI
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
)
from projectroles.tests.test_views import (
    TestViewsBase,
    PROJECT_TYPE_CATEGORY,
    PROJECT_TYPE_PROJECT,
    PROJECT_ROLE_OWNER,
    PROJECT_ROLE_DELEGATE,
    PROJECT_ROLE_CONTRIBUTOR,
    PROJECT_ROLE_GUEST,
    REMOTE_SITE_NAME,
    REMOTE_SITE_URL,
    SITE_MODE_TARGET,
    REMOTE_SITE_DESC,
    REMOTE_SITE_SECRET,
)
from projectroles.utils import build_secret, set_user_group


CORE_API_MEDIA_TYPE_INVALID = 'application/vnd.bihealth.invalid'
CORE_API_VERSION_INVALID = '9.9.9'

INVALID_UUID = '11111111-1111-1111-1111-111111111111'
NEW_CATEGORY_TITLE = 'New Category'
NEW_PROJECT_TITLE = 'New Project'
UPDATED_TITLE = 'Updated Title'
UPDATED_DESC = 'Updated description'
UPDATED_README = 'Updated readme'


# Base Classes -----------------------------------------------------------------


class SODARAPIViewTestMixin:
    """
    Mixin for SODAR and SODAR Core API views with accept headers, knox token
    authorization and general helper methods.
    """

    # Copied from Knox tests
    @classmethod
    def _get_basic_auth_header(cls, username, password):
        return (
            'Basic %s'
            % base64.b64encode(
                ('%s:%s' % (username, password)).encode('ascii')
            ).decode()
        )

    @classmethod
    def get_token(cls, user, full_result=False):
        """
        Get or create a knox token for a user.

        :param user: User object
        :param full_result: Return full result of AuthToken creation if True
        :return: Token string or AuthToken creation tuple
        """
        result = AuthToken.objects.create(user=user)
        return result if full_result else result[1]

    @classmethod
    def get_serialized_user(cls, user):
        """
        Return serialization for a user.

        :param user: User object
        :return: Dict
        """
        return {
            'email': user.email,
            'name': user.name,
            'sodar_uuid': str(user.sodar_uuid),
            'username': user.username,
        }

    @classmethod
    def get_drf_datetime(cls, obj_dt):
        """
        Return datetime in DRF compatible format.

        :param obj_dt: Object DateTime field
        :return: String
        """
        return timezone.localtime(
            obj_dt, pytz.timezone(settings.TIME_ZONE)
        ).isoformat()

    @classmethod
    def get_accept_header(
        cls,
        media_type=views_api.CORE_API_MEDIA_TYPE,
        version=views_api.CORE_API_DEFAULT_VERSION,
    ):
        """
        Return version accept header based on the media type and version string.

        :param media_type: String (default = SODAR Core default media type)
        :param version: String (default = SODAR Core default version)
        :return: Dict
        """
        return {'HTTP_ACCEPT': '{}; version={}'.format(media_type, version)}

    @classmethod
    def get_token_header(cls, token):
        """
        Return auth header based on token.

        :param token: Token string
        :return: Dict
        """
        return {'HTTP_AUTHORIZATION': 'token {}'.format(token)}

    # TODO: TBD: Do we need this for anything?
    def login_knox(self, user, password):
        """
        Login with Knox.

        :param user: User object
        :param password: Password (string)
        :return: Token returned by Knox on successful login
        """
        response = self.client.post(
            reverse('login_knox'),
            HTTP_AUTHORIZATION=self._get_basic_auth_header(
                user.username, password
            ),
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        return response.data['token']

    def request_knox(
        self,
        url,
        method='GET',
        data=None,
        token=None,
        media_type=views_api.CORE_API_MEDIA_TYPE,
        version=views_api.CORE_API_DEFAULT_VERSION,
    ):
        """
        Perform a HTTP request with Knox token auth.

        :param url: URL for the request
        :param method: Request method (string, default="GET")
        :param data: Optional data for request (dict)
        :param token: Knox token string (if None, use self.knox_token)
        :param media_type: String (default = SODAR Core default media type)
        :param version: String (default = SODAR Core default version)
        :return: Response object
        """
        if not token:
            token = self.knox_token

        req_kwargs = {
            **self.get_accept_header(media_type, version),
            **self.get_token_header(token),
        }

        if data:
            req_kwargs['data'] = data

        req_method = getattr(self.client, method.lower(), None)

        if not req_method:
            raise ValueError('Unsupported method "{}"'.format(method))

        return req_method(url, **req_kwargs)


class TestAPIViewsBase(
    ProjectMixin, RoleAssignmentMixin, SODARAPIViewTestMixin, APITestCase
):
    """Base API test view with knox authentication"""

    def setUp(self):
        # Force disabling of taskflow plugin if it's available
        if get_backend_api('taskflow'):
            change_plugin_status(
                name='taskflow', status=1, plugin_type='backend'  # 0 = Disabled
            )

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

        # Set up category and project with owner role assignments
        self.category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.cat_owner_as = self._make_assignment(
            self.category, self.user, self.role_owner
        )
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        # Get knox token for self.user
        self.knox_token = self.get_token(self.user)


# Tests ------------------------------------------------------------------------


class TestProjectListAPIView(TestAPIViewsBase):
    """Tests for ProjectListAPIView"""

    def test_get(self):
        """Test ProjectListAPIView get() as project owner"""
        url = reverse('projectroles:api_project_list')
        response = self.request_knox(url)

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)
        expected = [
            {
                'title': self.category.title,
                'type': self.category.type,
                'parent': None,
                'description': self.category.description,
                'readme': '',
                'submit_status': self.category.submit_status,
                'roles': {
                    str(self.cat_owner_as.sodar_uuid): {
                        'user': {
                            'username': self.user.username,
                            'name': self.user.name,
                            'email': self.user.email,
                            'sodar_uuid': str(self.user.sodar_uuid),
                        },
                        'role': PROJECT_ROLE_OWNER,
                    }
                },
                'sodar_uuid': str(self.category.sodar_uuid),
            },
            {
                'title': self.project.title,
                'type': self.project.type,
                'parent': str(self.category.sodar_uuid),
                'description': self.project.description,
                'readme': '',
                'submit_status': self.project.submit_status,
                'roles': {
                    str(self.owner_as.sodar_uuid): {
                        'user': {
                            'username': self.user.username,
                            'name': self.user.name,
                            'email': self.user.email,
                            'sodar_uuid': str(self.user.sodar_uuid),
                        },
                        'role': PROJECT_ROLE_OWNER,
                    }
                },
                'sodar_uuid': str(self.project.sodar_uuid),
            },
        ]
        self.assertEqual(response_data, expected)

    def test_get_no_roles(self):
        """Test ProjectListAPIView get() without roles"""
        user_no_roles = self.make_user('user_no_roles')
        url = reverse('projectroles:api_project_list')
        response = self.request_knox(url, token=self.get_token(user_no_roles))

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 0)

    def test_get_limited_roles(self):
        """Test ProjectListAPIView get() with only one role"""
        user_no_roles = self.make_user('user_no_roles')
        self._make_assignment(
            self.project, user_no_roles, self.role_contributor
        )
        url = reverse('projectroles:api_project_list')
        response = self.request_knox(url, token=self.get_token(user_no_roles))

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)


class TestProjectRetrieveAPIView(TestAPIViewsBase):
    """Tests for ProjectRetrieveAPIView"""

    def test_get_category(self):
        """Test ProjectRetrieveAPIView get() with a category"""
        url = reverse(
            'projectroles:api_project_retrieve',
            kwargs={'project': self.category.sodar_uuid},
        )
        response = self.request_knox(url)

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        expected = {
            'title': self.category.title,
            'type': self.category.type,
            'parent': None,
            'description': self.category.description,
            'readme': '',
            'submit_status': self.category.submit_status,
            'roles': {
                str(self.cat_owner_as.sodar_uuid): {
                    'user': {
                        'username': self.user.username,
                        'name': self.user.name,
                        'email': self.user.email,
                        'sodar_uuid': str(self.user.sodar_uuid),
                    },
                    'role': PROJECT_ROLE_OWNER,
                }
            },
            'sodar_uuid': str(self.category.sodar_uuid),
        }
        self.assertEqual(response_data, expected)

    def test_get_project(self):
        """Test ProjectRetrieveAPIView get() with a project"""
        url = reverse(
            'projectroles:api_project_retrieve',
            kwargs={'project': self.project.sodar_uuid},
        )
        response = self.request_knox(url)

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        expected = {
            'title': self.project.title,
            'type': self.project.type,
            'parent': str(self.category.sodar_uuid),
            'description': self.project.description,
            'readme': '',
            'submit_status': self.project.submit_status,
            'roles': {
                str(self.owner_as.sodar_uuid): {
                    'user': {
                        'username': self.user.username,
                        'name': self.user.name,
                        'email': self.user.email,
                        'sodar_uuid': str(self.user.sodar_uuid),
                    },
                    'role': PROJECT_ROLE_OWNER,
                }
            },
            'sodar_uuid': str(self.project.sodar_uuid),
        }
        self.assertEqual(response_data, expected)


class TestProjectCreateAPIView(TestAPIViewsBase):
    """Tests for ProjectCreateAPIView"""

    def test_create_category(self):
        """Test creating a root category"""

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_CATEGORY_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': '',
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(url, method='POST', data=post_data)

        # Assert response and project status
        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(Project.objects.count(), 3)

        # Assert object content
        new_category = Project.objects.get(title=NEW_CATEGORY_TITLE)
        model_dict = model_to_dict(new_category)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': new_category.pk,
            'title': new_category.title,
            'type': new_category.type,
            'parent': None,
            'description': new_category.description,
            'readme': new_category.readme.raw,
            'submit_status': SODAR_CONSTANTS['SUBMIT_STATUS_OK'],
            'sodar_uuid': new_category.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)

        # Assert role assignment
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=new_category, user=self.user, role=self.role_owner
            ).count(),
            1,
        )

        # Assert API response
        expected = {
            'title': NEW_CATEGORY_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'description': new_category.description,
            'readme': new_category.readme.raw,
            'sodar_uuid': str(new_category.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_create_category_nested(self):
        """Test creating a category under an existing category"""

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_CATEGORY_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(url, method='POST', data=post_data)

        # Assert response and project status
        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(Project.objects.count(), 3)

        # Assert object content
        new_category = Project.objects.get(title=NEW_CATEGORY_TITLE)
        model_dict = model_to_dict(new_category)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': new_category.pk,
            'title': new_category.title,
            'type': new_category.type,
            'parent': self.category.pk,
            'description': new_category.description,
            'readme': new_category.readme.raw,
            'submit_status': SODAR_CONSTANTS['SUBMIT_STATUS_OK'],
            'sodar_uuid': new_category.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)

        # Assert role assignment
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=new_category, user=self.user, role=self.role_owner
            ).count(),
            1,
        )

        # Assert API response
        expected = {
            'title': NEW_CATEGORY_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': str(self.category.sodar_uuid),
            'description': new_category.description,
            'readme': new_category.readme.raw,
            'sodar_uuid': str(new_category.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_create_project(self):
        """Test creating a project under an existing category"""

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(url, method='POST', data=post_data)

        # Assert response and project status
        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(Project.objects.count(), 3)

        # Assert object content
        new_project = Project.objects.get(title=NEW_PROJECT_TITLE)
        model_dict = model_to_dict(new_project)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': new_project.pk,
            'title': new_project.title,
            'type': new_project.type,
            'parent': self.category.pk,
            'description': new_project.description,
            'readme': new_project.readme.raw,
            'submit_status': SODAR_CONSTANTS['SUBMIT_STATUS_OK'],
            'sodar_uuid': new_project.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)

        # Assert role assignment
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=new_project, user=self.user, role=self.role_owner
            ).count(),
            1,
        )

        # Assert API response
        expected = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'description': new_project.description,
            'readme': new_project.readme.raw,
            'sodar_uuid': str(new_project.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_create_project_root(self):
        """Test creating a project in root (should fail)"""

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': None,
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(url, method='POST', data=post_data)

        # Assert response and project status
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 2)

    @override_settings(PROJECTROLES_DISABLE_CATEGORIES=True)
    def test_create_project_disable_categories(self):
        """Test creating a project in root with disabled categories"""

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': '',
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(url, method='POST', data=post_data)

        # Assert response and project status
        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(Project.objects.count(), 3)

    def test_create_project_duplicate_title(self):
        """Test creating a project with a title already in category (should fail)"""

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': self.project.title,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(url, method='POST', data=post_data)

        # Assert response and project status
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 2)

    def test_create_project_unknown_user(self):
        """Test creating a project with a non-existent user (should fail)"""

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'owner': INVALID_UUID,
        }
        response = self.request_knox(url, method='POST', data=post_data)

        # Assert response and project status
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 2)

    def test_create_project_unknown_parent(self):
        """Test creating a project with a non-existent parent category (should fail)"""

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': INVALID_UUID,
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(url, method='POST', data=post_data)

        # Assert response and project status
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 2)

    def test_create_project_invalid_parent(self):
        """Test creating a project with a project as parent (should fail)"""

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.project.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(url, method='POST', data=post_data)

        # Assert response and project status
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 2)


class TestProjectUpdateAPIView(TestAPIViewsBase):
    """Tests for ProjectUpdateAPIView"""

    def test_put_category(self):
        """Test put() for category updating"""
        new_owner = self.make_user('new_owner')

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.category.sodar_uuid},
        )
        put_data = {
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': '',
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'owner': str(new_owner.sodar_uuid),
        }
        response = self.request_knox(url, method='PUT', data=put_data)

        # Assert response and project status
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(Project.objects.count(), 2)

        # Assert object content
        self.category.refresh_from_db()
        model_dict = model_to_dict(self.category)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': self.category.pk,
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'submit_status': SODAR_CONSTANTS['SUBMIT_STATUS_OK'],
            'sodar_uuid': self.category.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)

        # Assert role assignment
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.category).count(), 1
        )
        self.assertEqual(self.category.get_owner().user, new_owner)

        # Assert API response
        expected = {
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'submit_status': SODAR_CONSTANTS['SUBMIT_STATUS_OK'],
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'roles': {
                str(self.category.get_owner().sodar_uuid): {
                    'role': PROJECT_ROLE_OWNER,
                    'user': self.get_serialized_user(new_owner),
                }
            },
            'sodar_uuid': str(self.category.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_put_project(self):
        """Test put() for project updating"""
        new_owner = self.make_user('new_owner')

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.project.sodar_uuid},
        )
        put_data = {
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'owner': str(new_owner.sodar_uuid),
        }
        response = self.request_knox(url, method='PUT', data=put_data)

        # Assert response and project status
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(Project.objects.count(), 2)

        # Assert object content
        self.project.refresh_from_db()
        model_dict = model_to_dict(self.project)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': self.project.pk,
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': self.category.pk,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'submit_status': SODAR_CONSTANTS['SUBMIT_STATUS_OK'],
            'sodar_uuid': self.project.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)

        # Assert role assignment
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 1
        )
        self.assertEqual(self.project.get_owner().user, new_owner)

        # Assert API response
        expected = {
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'submit_status': SODAR_CONSTANTS['SUBMIT_STATUS_OK'],
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'roles': {
                str(self.project.get_owner().sodar_uuid): {
                    'role': PROJECT_ROLE_OWNER,
                    'user': self.get_serialized_user(new_owner),
                }
            },
            'sodar_uuid': str(self.project.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_patch_category(self):
        """Test patch() for updating category metadata"""

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.category.sodar_uuid},
        )
        patch_data = {
            'title': UPDATED_TITLE,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
        }
        response = self.request_knox(url, method='PATCH', data=patch_data)

        # Assert response and project status
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(Project.objects.count(), 2)

        # Assert object content
        self.category.refresh_from_db()
        model_dict = model_to_dict(self.category)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': self.category.pk,
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'submit_status': SODAR_CONSTANTS['SUBMIT_STATUS_OK'],
            'sodar_uuid': self.category.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)

        # Assert role assignment
        self.assertEqual(self.category.get_owner().user, self.user)

        # Assert API response
        expected = {
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'submit_status': SODAR_CONSTANTS['SUBMIT_STATUS_OK'],
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'roles': {
                str(self.category.get_owner().sodar_uuid): {
                    'role': PROJECT_ROLE_OWNER,
                    'user': self.get_serialized_user(self.user),
                }
            },
            'sodar_uuid': str(self.category.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_patch_project(self):
        """Test patch() for updating project metadata"""

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.project.sodar_uuid},
        )
        patch_data = {
            'title': UPDATED_TITLE,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
        }
        response = self.request_knox(url, method='PATCH', data=patch_data)

        # Assert response and project status
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(Project.objects.count(), 2)

        # Assert object content
        self.project.refresh_from_db()
        model_dict = model_to_dict(self.project)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': self.project.pk,
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': self.category.pk,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'submit_status': SODAR_CONSTANTS['SUBMIT_STATUS_OK'],
            'sodar_uuid': self.project.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)

        # Assert role assignment
        self.assertEqual(self.project.get_owner().user, self.user)

        # Assert API response
        expected = {
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'submit_status': SODAR_CONSTANTS['SUBMIT_STATUS_OK'],
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'roles': {
                str(self.project.get_owner().sodar_uuid): {
                    'role': PROJECT_ROLE_OWNER,
                    'user': self.get_serialized_user(self.user),
                }
            },
            'sodar_uuid': str(self.project.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_patch_project_owner(self):
        """Test patch() for updating project owner"""
        new_owner = self.make_user('new_owner')

        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.project.sodar_uuid},
        )
        patch_data = {'owner': str(new_owner.sodar_uuid)}
        response = self.request_knox(url, method='PATCH', data=patch_data)

        # Assert response
        self.assertEqual(response.status_code, 200, msg=response.content)

        # Assert role assignment
        self.project.refresh_from_db()
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 1
        )
        self.assertEqual(self.project.get_owner().user, new_owner)

        # Assert roles in API response
        expected = {
            str(self.project.get_owner().sodar_uuid): {
                'role': PROJECT_ROLE_OWNER,
                'user': self.get_serialized_user(new_owner),
            }
        }
        self.assertEqual(json.loads(response.content)['roles'], expected)

    def test_patch_project_move(self):
        """Test patch() for moving project under a different category"""

        new_category = self._make_project(
            'NewCategory', PROJECT_TYPE_CATEGORY, None
        )
        self._make_assignment(new_category, self.user, self.role_owner)
        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.project.sodar_uuid},
        )
        patch_data = {'parent': str(new_category.sodar_uuid)}
        response = self.request_knox(url, method='PATCH', data=patch_data)

        # Assert response
        self.assertEqual(response.status_code, 200, msg=response.content)

        # Assert object content
        self.project.refresh_from_db()
        model_dict = model_to_dict(self.project)
        self.assertEqual(model_dict['parent'], new_category.pk)

        # Assert role assignment
        self.assertEqual(self.project.get_owner().user, self.user)

        # Assert API response
        self.assertEqual(
            json.loads(response.content)['parent'], str(new_category.sodar_uuid)
        )

    def test_patch_project_move_unallowed(self):
        """Test patch() for moving project without permissions (should fail)"""

        new_category = self._make_project(
            'NewCategory', PROJECT_TYPE_CATEGORY, None
        )
        new_owner = self.make_user('new_owner')
        self._make_assignment(new_category, new_owner, self.role_owner)
        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.project.sodar_uuid},
        )
        patch_data = {'parent': str(new_category.sodar_uuid)}
        # Disable superuser status from self.user and perform request
        self.user.is_superuser = False
        self.user.save()
        response = self.request_knox(url, method='PATCH', data=patch_data)

        # Assert response
        self.assertEqual(response.status_code, 403, msg=response.content)

    def test_patch_project_type_change(self):
        """Test patch() with a changed project type (should fail)"""
        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.project.sodar_uuid},
        )
        patch_data = {'type': PROJECT_TYPE_CATEGORY}
        response = self.request_knox(url, method='PATCH', data=patch_data)

        # Assert response
        self.assertEqual(response.status_code, 400, msg=response.content)


class TestUserListAPIView(TestAPIViewsBase):
    """Tests for UserListAPIView"""

    def setUp(self):
        super().setUp()
        # Create additional users
        self.domain_user = self.make_user('domain_user@domain')
        set_user_group(self.domain_user)
        set_user_group(self.user)  # Set system group for default user

    def test_get(self):
        """Test UserListAPIView get() as a regular user"""
        url = reverse('projectroles:api_user_list')
        response = self.request_knox(
            url, token=self.get_token(self.domain_user)
        )

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)  # System users not returned
        expected = [
            {
                'username': self.domain_user.username,
                'name': self.domain_user.name,
                'email': self.domain_user.email,
                'sodar_uuid': str(self.domain_user.sodar_uuid),
            }
        ]
        self.assertEqual(response_data, expected)

    def test_get_superuser(self):
        """Test UserListAPIView get() as a superuser"""
        url = reverse('projectroles:api_user_list')
        response = self.request_knox(url)  # Default token is for superuser

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)
        expected = [
            {
                'username': self.user.username,
                'name': self.user.name,
                'email': self.user.email,
                'sodar_uuid': str(self.user.sodar_uuid),
            },
            {
                'username': self.domain_user.username,
                'name': self.domain_user.name,
                'email': self.domain_user.email,
                'sodar_uuid': str(self.domain_user.sodar_uuid),
            },
        ]
        self.assertEqual(response_data, expected)


class TestRemoteProjectGetAPIView(
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    SODARAPIViewTestMixin,
    TestViewsBase,
):
    """Tests for remote project getting API view"""

    def setUp(self):
        super().setUp()

        # Set up projects
        self.category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.cat_owner_as = self._make_assignment(
            self.category, self.user, self.role_owner
        )
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.project_owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        # Create target site
        self.target_site = self._make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )

        # Create remote project
        self.remote_project = self._make_remote_project(
            site=self.target_site,
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO'],
        )

        self.remote_api = RemoteProjectAPI()

    def test_get(self):
        """Test retrieving project data to the target site"""

        response = self.client.get(
            reverse(
                'projectroles:api_remote_get',
                kwargs={'secret': REMOTE_SITE_SECRET},
            )
        )

        self.assertEqual(response.status_code, 200)

        expected = self.remote_api.get_target_data(self.target_site)
        response_dict = json.loads(response.content.decode('utf-8'))

        self.assertEqual(response_dict, expected)

    def test_get_invalid_secret(self):
        """Test retrieving project data with an invalid secret (should fail)"""

        response = self.client.get(
            reverse(
                'projectroles:api_remote_get', kwargs={'secret': build_secret()}
            )
        )

        self.assertEqual(response.status_code, 401)

    def test_api_versioning(self):
        """Test SODAR API Access with correct version headers"""
        # TODO: Test with a more simple SODAR API view once implemented

        response = self.client.get(
            reverse(
                'projectroles:api_remote_get',
                kwargs={'secret': REMOTE_SITE_SECRET},
            ),
            **self.get_accept_header(),
        )

        self.assertEqual(response.status_code, 200)

    def test_api_versioning_invalid_version(self):
        """Test SODAR API Access with unsupported version (should fail)"""
        # TODO: Test with a more simple SODAR API view once implemented

        response = self.client.get(
            reverse(
                'projectroles:api_remote_get',
                kwargs={'secret': REMOTE_SITE_SECRET},
            ),
            **self.get_accept_header(version=CORE_API_VERSION_INVALID),
        )

        self.assertEqual(response.status_code, 406)

    def test_api_versioning_invalid_media_type(self):
        """Test SODAR API Access with unsupported media type (should fail)"""
        # TODO: Test with a more simple SODAR API view once implemented

        response = self.client.get(
            reverse(
                'projectroles:api_remote_get',
                kwargs={'secret': REMOTE_SITE_SECRET},
            ),
            **self.get_accept_header(media_type=CORE_API_MEDIA_TYPE_INVALID),
        )

        self.assertEqual(response.status_code, 406)
