"""Tests for Ajax view permissions in the adminalerts app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import TestPermissionBase

from adminalerts.tests.test_models import AdminAlertMixin


class TestAdminAlertPermissions(AdminAlertMixin, TestPermissionBase):
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

        # Create alert
        self.alert = self._make_alert(
            message='alert',
            user=self.superuser,
            description='description',
            active=True,
        )

    def test_active_toggle(self):
        """Test permissions for AdminAlert activation API view"""
        url = reverse(
            'adminalerts:ajax_active_toggle',
            kwargs={'adminalert': self.alert.sodar_uuid},
        )
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200, method='POST')
        self.assert_response(url, bad_users, 403, method='POST')

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_active_toggle_anon(self):
        """Test permissions for AdminAlert activation API view with anonymous access"""
        url = reverse(
            'adminalerts:ajax_active_toggle',
            kwargs={'adminalert': self.alert.sodar_uuid},
        )
        self.assert_response(url, self.anonymous, 403, method='POST')
