"""REST API view permission tests for the projectroles app"""

from django.core.urlresolvers import reverse

from projectroles.tests.test_permissions import TestProjectPermissionBase
from projectroles.tests.test_views_api import SODARAPIViewTestMixin
from projectroles.views_api import CORE_API_MEDIA_TYPE, CORE_API_DEFAULT_VERSION


# Base Classes and Mixins ------------------------------------------------------


class SODARAPIPermissionTestMixin(SODARAPIViewTestMixin):
    """Mixin for permission testing with knox auth"""

    def assert_response_api(
        self,
        url,
        users,
        status_code,
        method='GET',
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
        :param media_type: String (default = SODAR Core default media type)
        :param version: String (default = SODAR Core default version)
        :param knox: Use Knox token auth instead of Django login (boolean)
        """
        req_headers = {}

        def _send_request():
            if method.upper() == 'GET':
                return self.client.get(url, **req_headers)

            elif method.upper() == 'POST':
                return self.client.post(url, **req_headers)

            else:
                raise ValueError('Method "{}" not supported'.format(method))

        if not isinstance(users, (list, tuple)):
            users = [users]

        for user in users:
            if knox and not user:  # Anonymous
                raise ValueError(
                    'Unable to test Knox token auth with anonymous user'
                )

            req_headers = self.get_accept_header(media_type, version)

            if knox:
                req_headers.update(self.get_token_header(self.get_token(user)))
                response = _send_request()

            elif user:
                with self.login(user):
                    response = _send_request()

            else:  # Anonymous, no knox
                response = _send_request()

            msg = 'user={}'.format(user)
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
