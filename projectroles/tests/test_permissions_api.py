"""REST API view permission tests for the projectroles app"""

import json

from django.core.urlresolvers import reverse

from projectroles.models import Project, SODAR_CONSTANTS
from projectroles.tests.test_permissions import TestProjectPermissionBase
from projectroles.tests.test_views_api import SODARAPIViewTestMixin
from projectroles.views_api import CORE_API_MEDIA_TYPE, CORE_API_DEFAULT_VERSION


NEW_PROJECT_TITLE = 'New Project'


# Base Classes and Mixins ------------------------------------------------------


class SODARAPIPermissionTestMixin(SODARAPIViewTestMixin):
    """Mixin for permission testing with knox auth"""

    def assert_response_api(
        self,
        url,
        users,
        status_code,
        method='GET',
        data=None,
        media_type=CORE_API_MEDIA_TYPE,
        version=CORE_API_DEFAULT_VERSION,
        knox=False,
    ):
        """
        Assert a response status code for url with API headers and optional
        Knox token authentication. Creates a Knox token for each user where
        needed.

        :param url: Target URL for the request
        :param users: Users to test (single user, list or tuple)
        :param status_code: Status code
        :param method: Method for request (default='GET')
        :param data: Optional data for request (dict)
        :param media_type: String (default = SODAR Core default media type)
        :param version: String (default = SODAR Core default version)
        :param knox: Use Knox token auth instead of Django login (boolean)
        """

        def _send_request():
            if method.upper() == 'GET':
                return self.client.get(url, **req_kwargs)

            elif method.upper() == 'POST':
                return self.client.post(url, **req_kwargs)

            else:
                raise ValueError('Method "{}" not supported'.format(method))

        if not isinstance(users, (list, tuple)):
            users = [users]

        for user in users:
            req_kwargs = {}

            if data:
                req_kwargs['data'] = data

            if knox and not user:  # Anonymous
                raise ValueError(
                    'Unable to test Knox token auth with anonymous user'
                )

            req_kwargs.update(self.get_accept_header(media_type, version))

            if knox:
                req_kwargs.update(self.get_token_header(self.get_token(user)))
                response = _send_request()

            elif user:
                with self.login(user):
                    response = _send_request()

            else:  # Anonymous, no knox
                response = _send_request()

            msg = 'user={}; content="{}"'.format(
                user, json.loads(response.content)
            )
            self.assertEqual(response.status_code, status_code, msg=msg)


# Tests ------------------------------------------------------------------------


class TestAPIPermissions(
    SODARAPIPermissionTestMixin, TestProjectPermissionBase
):
    """Tests for projectroles API view permissions"""

    def test_project_list(self):
        """Test permissions for ProjectListAPIView"""
        url = reverse('projectroles:api_project_list')
        good_users = [
            self.superuser,
            self.as_owner.user,
            self.as_delegate.user,
            self.as_contributor.user,
            self.as_guest.user,
            self.user_no_roles,
        ]
        self.assert_response_api(url, good_users, 200)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)

    def test_project_retrieve(self):
        """Test permissions for ProjectRetrieveAPIView"""
        url = reverse(
            'projectroles:api_project_retrieve',
            kwargs={'project': self.project.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.as_owner.user,
            self.as_delegate.user,
            self.as_contributor.user,
            self.as_guest.user,
        ]
        bad_users = [self.user_no_roles]
        self.assert_response_api(url, good_users, 200)
        self.assert_response_api(url, bad_users, 403)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)
        self.assert_response_api(url, bad_users, 403, knox=True)

    def test_project_create(self):
        """Test permissions for ProjectCreateAPIView"""
        # TODO: Set up a better way to test perms for data-altering API views
        url = reverse(
            'projectroles:api_project_create',
            kwargs={'project': self.category.sodar_uuid},
        )
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'],
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.as_owner.user.sodar_uuid),
        }
        bad_users = [
            self.as_delegate.user,
            self.as_contributor.user,
            self.as_guest.user,
            self.user_no_roles,
        ]

        # Test with good users (delete object after creation)
        self.assert_response_api(
            url, self.superuser, 201, method='POST', data=post_data
        )
        Project.objects.get(title=NEW_PROJECT_TITLE).delete()
        self.assert_response_api(
            url, self.as_owner.user, 201, method='POST', data=post_data
        )
        Project.objects.get(title=NEW_PROJECT_TITLE).delete()

        # Test with bad users
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )

        # Test with Knox
        self.assert_response_api(
            url, self.superuser, 201, method='POST', data=post_data, knox=True
        )
        Project.objects.get(title=NEW_PROJECT_TITLE).delete()
        self.assert_response_api(
            url,
            self.as_owner.user,
            201,
            method='POST',
            data=post_data,
            knox=True,
        )
        Project.objects.get(title=NEW_PROJECT_TITLE).delete()
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data, knox=True
        )

    def test_user_list(self):
        """Test permissions for UserListAPIView"""
        url = reverse('projectroles:api_user_list')
        good_users = [
            self.superuser,
            self.as_owner.user,
            self.as_delegate.user,
            self.as_contributor.user,
            self.as_guest.user,
            self.user_no_roles,
        ]
        self.assert_response_api(url, good_users, 200)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)
