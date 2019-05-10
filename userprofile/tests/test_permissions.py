"""Tests for permissions in the userprofile app"""

from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import TestPermissionBase


class TestAdminAlertPermissions(TestPermissionBase):
    """Tests for AdminAlert views"""

    def setUp(self):
        # Create users
        self.superuser = self.make_user('superuser')
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()

        self.regular_user = self.make_user('regular_user')

        # No user
        self.anonymous = None

    def test_profile(self):
        """Test permissions for the user profile view"""
        url = reverse('userprofile:detail')
        good_users = [self.superuser, self.regular_user]
        bad_users = [self.anonymous]
        self.assert_render200_ok(url, good_users)
        self.assert_redirect(url, bad_users)

    def test_settings_update(self):
        """Test permissions for the user settings updating view"""
        url = reverse('userprofile:settings_update')
        good_users = [self.superuser, self.regular_user]
        bad_users = [self.anonymous]
        self.assert_render200_ok(url, good_users)
        self.assert_redirect(url, bad_users)
