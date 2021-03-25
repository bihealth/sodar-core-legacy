"""REST API view permission tests for the projectroles app"""

import uuid

from django.test import override_settings
from django.urls import reverse

from projectroles.models import (
    Project,
    RoleAssignment,
    ProjectInvite,
    SODAR_CONSTANTS,
)
from projectroles.tests.test_permissions import TestProjectPermissionBase
from projectroles.tests.test_views_api import SODARAPIViewTestMixin
from projectroles.views_api import CORE_API_MEDIA_TYPE, CORE_API_DEFAULT_VERSION

from rest_framework.test import APITestCase

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
        format='json',
        data=None,
        media_type=None,
        version=None,
        knox=False,
        cleanup_method=None,
        req_kwargs=None,
    ):
        """
        Assert a response status code for url with API headers and optional
        Knox token authentication. Creates a Knox token for each user where
        needed.

        :param url: Target URL for the request
        :param users: Users to test (single user, list or tuple)
        :param status_code: Status code
        :param method: Method for request (default="GET")
        :param format: Request format (string, default="json")
        :param data: Optional data for request (dict)
        :param media_type: String (default = cls.media_type)
        :param version: String (default = cls.api_version)
        :param knox: Use Knox token auth instead of Django login (boolean)
        :param cleanup_method: Callable method to clean up data after a
               successful request
        :param req_kwargs: Optional request kwargs override (dict or None)
        """
        if cleanup_method and not callable(cleanup_method):
            raise ValueError('cleanup_method is not callable')

        def _send_request():
            req_method = getattr(self.client, method.lower(), None)
            if not req_method:
                raise ValueError('Invalid method "{}"'.format(method))
            if req_kwargs:  # Override request kwargs if set
                r_kwargs.update(req_kwargs)
            return req_method(url, **r_kwargs)

        if not isinstance(users, (list, tuple)):
            users = [users]

        for user in users:
            r_kwargs = {'format': format}
            if data:
                r_kwargs['data'] = data
            if knox and not user:  # Anonymous
                raise ValueError(
                    'Unable to test Knox token auth with anonymous user'
                )
            r_kwargs.update(self.get_accept_header(media_type, version))

            if knox:
                r_kwargs.update(self.get_token_header(self.get_token(user)))
                response = _send_request()
            elif user:
                with self.login(user):
                    response = _send_request()
            else:  # Anonymous, no knox
                response = _send_request()

            msg = 'user={}; content="{}"'.format(user, response.content)
            self.assertEqual(response.status_code, status_code, msg=msg)

            if cleanup_method:
                cleanup_method()


class TestProjectAPIPermissionBase(
    SODARAPIPermissionTestMixin, APITestCase, TestProjectPermissionBase
):
    """Base class for testing project permissions in SODAR API views"""


class TestCoreProjectAPIPermissionBase(
    SODARAPIPermissionTestMixin, APITestCase, TestProjectPermissionBase
):
    """
    Base class for testing project permissions in internal SODAR Core API views
    """

    media_type = CORE_API_MEDIA_TYPE
    api_version = CORE_API_DEFAULT_VERSION


# Tests ------------------------------------------------------------------------


class TestAPIPermissions(TestCoreProjectAPIPermissionBase):
    """Tests for projectroles API view permissions"""

    def test_project_list(self):
        """Test permissions for ProjectListAPIView"""
        url = reverse('projectroles:api_project_list')
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
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
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
        ]
        bad_users = [self.user_no_roles]
        self.assert_response_api(url, good_users, 200)
        self.assert_response_api(url, bad_users, 403)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)
        self.assert_response_api(url, bad_users, 403, knox=True)
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_project_retrieve_anon(self):
        """Test permissions for ProjectRetrieveAPIView with anonymous access"""
        url = reverse(
            'projectroles:api_project_retrieve',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 200)

    def test_project_create_root(self):
        """Test permissions for ProjectCreateAPIView with no parent"""
        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY'],
            'parent': '',
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.owner_as.user.sodar_uuid),
        }
        good_users = [self.superuser]
        bad_users = [
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]

        def _cleanup():
            p = Project.objects.filter(title=NEW_PROJECT_TITLE).first()
            if p:
                p.delete()

        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=post_data,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=post_data,
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='POST', data=post_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_project_create_root_anon(self):
        """Test permissions for ProjectCreateAPIView with no parent with anonymous access"""
        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY'],
            'parent': '',
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.owner_as.user.sodar_uuid),
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )

    def test_project_create(self):
        """Test permissions for ProjectCreateAPIView"""
        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'],
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.owner_as.user.sodar_uuid),
        }

        def _cleanup():
            p = Project.objects.filter(title=NEW_PROJECT_TITLE).first()
            if p:
                p.delete()

        good_users = [self.superuser, self.owner_as_cat.user]
        bad_users = [
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=post_data,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=post_data,
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='POST', data=post_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_project_create_anon(self):
        """Test permissions for ProjectCreateAPIView with anonymous access"""
        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'],
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.owner_as.user.sodar_uuid),
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )

    def test_project_update(self):
        """Test permissions for ProjectUpdateAPIView"""
        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.project.sodar_uuid},
        )
        put_data = {
            'title': NEW_PROJECT_TITLE,
            'type': SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'],
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.owner_as.user.sodar_uuid),
        }
        good_users = [
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response_api(
            url, good_users, 200, method='PUT', data=put_data
        )
        self.assert_response_api(
            url, bad_users, 403, method='PUT', data=put_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='PUT', data=put_data
        )
        # Test with Knox
        self.assert_response_api(
            url, good_users, 200, method='PUT', data=put_data, knox=True
        )
        self.assert_response_api(
            url, bad_users, 403, method='PUT', data=put_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='PUT', data=put_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_project_update_anon(self):
        """Test permissions for ProjectUpdateAPIView with anonymous access"""
        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.project.sodar_uuid},
        )
        put_data = {
            'title': NEW_PROJECT_TITLE,
            'type': SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'],
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.owner_as.user.sodar_uuid),
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='PUT', data=put_data
        )

    def test_role_create(self):
        """Test permissions for RoleAssignmentCreateAPIView"""
        # Create user for assignments
        assign_user = self.make_user('assign_user')
        url = reverse(
            'projectroles:api_role_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        post_data = {
            'role': SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
            'user': str(assign_user.sodar_uuid),
        }
        good_users = [
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]

        def _cleanup():
            role_as = RoleAssignment.objects.filter(
                project=self.project,
                role__name=SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
                user=assign_user,
            ).first()
            if role_as:
                role_as.delete()

        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=post_data,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=post_data,
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='POST', data=post_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_role_create_anon(self):
        """Test permissions for RoleAssignmentCreateAPIView with anonymous access"""
        assign_user = self.make_user('assign_user')
        url = reverse(
            'projectroles:api_role_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        post_data = {
            'role': SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
            'user': str(assign_user.sodar_uuid),
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )

    def test_role_update(self):
        """Test permissions for RoleAssignmentUpdateAPIView"""
        # Create user and assignment
        assign_user = self.make_user('assign_user')
        update_as = self._make_assignment(
            self.project, assign_user, self.role_contributor
        )
        url = reverse(
            'projectroles:api_role_update',
            kwargs={'roleassignment': update_as.sodar_uuid},
        )
        put_data = {
            'role': self.role_guest.name,
            'user': str(assign_user.sodar_uuid),
        }
        good_users = [
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response_api(
            url, good_users, 200, method='PUT', data=put_data
        )
        self.assert_response_api(
            url, bad_users, 403, method='PUT', data=put_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='PUT', data=put_data
        )
        # Test with Knox
        self.assert_response_api(
            url, good_users, 200, method='PUT', data=put_data, knox=True
        )
        self.assert_response_api(
            url, bad_users, 403, method='PUT', data=put_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='PUT', data=put_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_role_update_anon(self):
        """Test permissions for RoleAssignmentUpdateAPIView with anonymous access"""
        # Create user and assignment
        assign_user = self.make_user('assign_user')
        update_as = self._make_assignment(
            self.project, assign_user, self.role_contributor
        )
        url = reverse(
            'projectroles:api_role_update',
            kwargs={'roleassignment': update_as.sodar_uuid},
        )
        put_data = {
            'role': self.role_guest.name,
            'user': str(assign_user.sodar_uuid),
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='PUT', data=put_data
        )

    def test_role_delete(self):
        """Test permissions for RoleAssignmentDestroyAPIView"""
        # Create user and assignment
        assign_user = self.make_user('assign_user')
        role_uuid = uuid.uuid4()  # Ensure fixed uuid

        def _cleanup():
            update_as = self._make_assignment(
                self.project, assign_user, self.role_contributor
            )
            update_as.sodar_uuid = role_uuid
            update_as.save()

        url = reverse(
            'projectroles:api_role_destroy',
            kwargs={'roleassignment': role_uuid},
        )
        good_users = [
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        _cleanup()
        self.assert_response_api(
            url, good_users, 204, method='DELETE', cleanup_method=_cleanup
        )
        self.assert_response_api(url, bad_users, 403, method='DELETE')
        self.assert_response_api(url, self.anonymous, 401, method='DELETE')
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=_cleanup,
            knox=True,
        )
        self.assert_response_api(
            url, bad_users, 403, method='DELETE', knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 403, method='DELETE')

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_role_delete_anon(self):
        """Test permissions for RoleAssignmentDestroyAPIView with anonymous access"""
        # Create user and assignment
        assign_user = self.make_user('assign_user')
        role_uuid = uuid.uuid4()  # Ensure fixed uuid
        update_as = self._make_assignment(
            self.project, assign_user, self.role_contributor
        )
        update_as.sodar_uuid = role_uuid
        update_as.save()
        url = reverse(
            'projectroles:api_role_destroy',
            kwargs={'roleassignment': role_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 401, method='DELETE')

    def test_owner_transfer(self):
        """Test permissions for RoleAssignmentOwnerTransferAPIView"""
        # Create user for assignments
        self.new_owner = self.make_user('new_owner')
        self.new_owner_as = self._make_assignment(
            self.project, self.new_owner, self.role_contributor
        )
        url = reverse(
            'projectroles:api_role_owner_transfer',
            kwargs={'project': self.project.sodar_uuid},
        )
        post_data = {
            'new_owner': self.new_owner.username,
            'old_owner_role': SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
        }

        def _cleanup():
            self.new_owner_as.refresh_from_db()
            self.new_owner_as.role = self.role_contributor
            self.new_owner_as.save()

            self.owner_as.refresh_from_db()
            self.owner_as.role = self.role_owner
            self.owner_as.save()

        good_users = [
            self.owner_as_cat.user,
            self.owner_as.user,
        ]
        bad_users = [
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
            data=post_data,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
            data=post_data,
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='POST', data=post_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_owner_transfer_anon(self):
        """Test permissions for RoleAssignmentOwnerTransferAPIView with anonymous access"""
        # Create user for assignments
        self.new_owner = self.make_user('new_owner')
        self.new_owner_as = self._make_assignment(
            self.project, self.new_owner, self.role_contributor
        )
        url = reverse(
            'projectroles:api_role_owner_transfer',
            kwargs={'project': self.project.sodar_uuid},
        )
        post_data = {
            'new_owner': self.new_owner.username,
            'old_owner_role': SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )

    def test_invite_list(self):
        """Test permissions for ProjectInviteListAPIView"""
        url = reverse(
            'projectroles:api_invite_list',
            kwargs={'project': self.project.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response_api(url, good_users, 200)
        self.assert_response_api(url, bad_users, 403)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_invite_list_anon(self):
        """Test permissions for ProjectInviteListAPIView with anonymous access"""
        url = reverse(
            'projectroles:api_invite_list',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 401)

    def test_invite_create(self):
        """Test permissions for ProjectInviteCreateAPIView"""
        email = 'new@example.com'
        url = reverse(
            'projectroles:api_invite_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        post_data = {
            'email': email,
            'role': SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
        }
        good_users = [
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]

        def _cleanup():
            invite = ProjectInvite.objects.filter(
                email=email,
            ).first()
            if invite:
                invite.delete()

        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=post_data,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=post_data,
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='POST', data=post_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_invite_create_anon(self):
        """Test permissions for ProjectInviteCreateAPIView with anonymous access"""
        email = 'new@example.com'
        url = reverse(
            'projectroles:api_invite_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        post_data = {
            'email': email,
            'role': SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )

    def test_invite_revoke(self):
        """Test permissions for ProjectInviteRevokeAPIView"""
        self.invite = self._make_invite(
            email='new@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
        )
        url = reverse(
            'projectroles:api_invite_revoke',
            kwargs={'projectinvite': self.invite.sodar_uuid},
        )
        good_users = [
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]

        def _cleanup():
            self.invite.active = True
            self.invite.save()

        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url,
            bad_users,
            403,
            method='POST',
        )
        self.assert_response_api(
            url,
            self.anonymous,
            401,
            method='POST',
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(url, bad_users, 403, method='POST', knox=True)
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 403, method='POST')

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_invite_revoke_anon(self):
        """Test permissions for ProjectInviteRevokeAPIView with anonymous access"""
        self.invite = self._make_invite(
            email='new@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
        )
        url = reverse(
            'projectroles:api_invite_revoke',
            kwargs={'projectinvite': self.invite.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 401, method='POST')

    def test_invite_resend(self):
        """Test permissions for ProjectInviteResendAPIView"""
        self.invite = self._make_invite(
            email='new@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
        )
        url = reverse(
            'projectroles:api_invite_resend',
            kwargs={'projectinvite': self.invite.sodar_uuid},
        )
        good_users = [
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
        )
        self.assert_response_api(
            url,
            bad_users,
            403,
            method='POST',
        )
        self.assert_response_api(
            url,
            self.anonymous,
            401,
            method='POST',
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
            knox=True,
        )
        self.assert_response_api(url, bad_users, 403, method='POST', knox=True)
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 403, method='POST')

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_invite_resend_anon(self):
        """Test permissions for ProjectInviteResendAPIView with anonymous access"""
        self.invite = self._make_invite(
            email='new@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
        )
        url = reverse(
            'projectroles:api_invite_resend',
            kwargs={'projectinvite': self.invite.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 401, method='POST')

    def test_user_list(self):
        """Test permissions for UserListAPIView"""
        url = reverse('projectroles:api_user_list')
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response_api(url, good_users, 200)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)

    def test_user_current(self):
        """Test permissions for CurrentUserRetrieveAPIView"""
        url = reverse('projectroles:api_user_current')
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response_api(url, good_users, 200)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)
