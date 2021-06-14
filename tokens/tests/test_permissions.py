"""Permission tests for the tokens app"""

from django.test import override_settings
from django.urls import reverse

from knox.models import AuthToken

# Projectroles dependency
from projectroles.tests.test_permissions import TestPermissionBase


class TestTokenPermissions(TestPermissionBase):
    """Tests for token view permissions"""

    def setUp(self):
        # Create users
        self.superuser = self.make_user('superuser')
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()
        self.regular_user = self.make_user('regular_user')
        # No user
        self.anonymous = None

    def test_list(self):
        """Test permissions for token list"""
        url = reverse('tokens:list')
        good_users = [self.superuser, self.regular_user]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_list_anon(self):
        """Test permissions for token list with anonymous access"""
        url = reverse('tokens:list')
        good_users = [self.superuser, self.regular_user]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_create(self):
        """Test permissions for token creation"""
        url = reverse('tokens:create')
        good_users = [self.superuser, self.regular_user]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_create_anon(self):
        """Test permissions for token creation with anonymous access"""
        url = reverse('tokens:create')
        good_users = [self.superuser, self.regular_user]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_delete(self):
        """Test permissions for token deletion"""
        token = AuthToken.objects.create(self.regular_user, None)
        url = reverse('tokens:delete', kwargs={'pk': token[0].pk})
        good_users = [self.regular_user]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
