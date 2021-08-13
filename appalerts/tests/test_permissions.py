"""Permission tests for the appalerts app"""

from django.urls import reverse


# Projectroles dependency
from projectroles.tests.test_permissions import TestPermissionBase

from appalerts.tests.test_models import AppAlertMixin


class TestAppAlertPermissions(AppAlertMixin, TestPermissionBase):
    """Tests for AppAlert permissions"""

    def setUp(self):
        # Create users
        self.superuser = self.make_user('superuser')
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()
        self.regular_user = self.make_user('regular_user')
        self.no_alert_user = self.make_user('no_alert_user')
        # No user
        self.anonymous = None
        # Create alert
        self.alert = self._make_app_alert(
            user=self.regular_user, url=reverse('home')
        )

    def test_list(self):
        """Test permissions for the alert list view"""
        url = reverse('appalerts:list')
        good_users = [
            self.superuser,
            self.regular_user,
            self.no_alert_user,
        ]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_redirect(self):
        """Test permissions for the alert list view"""
        url = reverse(
            'appalerts:redirect', kwargs={'appalert': self.alert.sodar_uuid}
        )
        bad_url = reverse('appalerts:list')
        good_users = [self.regular_user]
        bad_users = [self.superuser, self.no_alert_user, self.anonymous]
        self.assert_response(
            url, good_users, 302, redirect_user=reverse('home')
        )
        self.assert_response(url, bad_users, 302, redirect_user=bad_url)

    def test_ajax_status(self):
        """Test permissions for the alert status ajax view"""
        url = reverse('appalerts:ajax_status')
        good_users = [self.superuser, self.regular_user, self.no_alert_user]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 403)

    def test_ajax_dismiss(self):
        """Test permissions for the alert dismiss ajax view"""
        url = reverse(
            'appalerts:ajax_dismiss', kwargs={'appalert': self.alert.sodar_uuid}
        )
        good_users = [self.regular_user]
        bad_users = [self.superuser, self.no_alert_user]
        self.assert_response(url, good_users, 200, method='POST')
        self.assert_response(url, bad_users, 404, method='POST')
        self.assert_response(url, self.anonymous, 403, method='POST')
