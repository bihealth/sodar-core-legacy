"""REST API view tests for the projectroles app"""
import base64
import json
import pytz

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from knox.models import AuthToken

from test_plus.test import APITestCase

from projectroles import views_api
from projectroles.models import Role, SODAR_CONSTANTS
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

    def get_knox(
        self,
        url,
        token=None,
        media_type=views_api.CORE_API_MEDIA_TYPE,
        version=views_api.CORE_API_DEFAULT_VERSION,
    ):
        """
        Perform a HTTP GET request with Knox token auth.

        :param url: URL for getting
        :param token: Knox token string (if None, use self.knox_token)
        :param media_type: String (default = SODAR Core default media type)
        :param version: String (default = SODAR Core default version)
        :return: Response object
        """
        if not token:
            token = self.knox_token

        return self.client.get(
            url,
            **self.get_accept_header(media_type, version),
            **self.get_token_header(token),
        )


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
        response = self.get_knox(url)

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
                'readme': None,
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
                'readme': None,
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
        response = self.get_knox(url, token=self.get_token(user_no_roles))

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
        response = self.get_knox(url, token=self.get_token(user_no_roles))

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)


class TestProjectRetrieveAPIView(TestAPIViewsBase):
    """Tests for ProjectRetrieveAPIView"""

    def test_get_project(self):
        """Test ProjectRetrieveAPIView get() with a project"""
        url = reverse(
            'projectroles:api_project_retrieve',
            kwargs={'project': self.project.sodar_uuid},
        )
        response = self.get_knox(url)

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        expected = {
            'title': self.project.title,
            'type': self.project.type,
            'parent': str(self.category.sodar_uuid),
            'description': self.project.description,
            'readme': None,
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

    def test_get_category(self):
        """Test ProjectRetrieveAPIView get() with a category"""
        url = reverse(
            'projectroles:api_project_retrieve',
            kwargs={'project': self.category.sodar_uuid},
        )
        response = self.get_knox(url)

        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        expected = {
            'title': self.category.title,
            'type': self.category.type,
            'parent': None,
            'description': self.category.description,
            'readme': None,
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
        response = self.get_knox(url, token=self.get_token(self.domain_user))

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
        response = self.get_knox(url)  # Default token is for superuser

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
