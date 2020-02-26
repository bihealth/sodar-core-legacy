"""Tests for permissions in the userprofile app"""

from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import TestPermissionBase


class TestUserProfilePermissions(TestPermissionBase):
    """Tests for userprofile view permissions"""

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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_settings_update(self):
        """Test permissions for the user settings updating view"""
        url = reverse('userprofile:settings_update')
        good_users = [self.superuser, self.regular_user]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
