"""Tests for permissions in the adminalerts app"""
from django.http import HttpResponseBadRequest
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import TestPermissionBase

from .test_models import AdminAlertMixin


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

    def test_alert_create(self):
        """Test permissions for AdminAlert creation"""
        url = reverse('adminalerts:create')
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_alert_update(self):
        """Test permissions for AdminAlert updating"""
        url = reverse(
            'adminalerts:update', kwargs={'uuid': self.alert.sodar_uuid}
        )
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_alert_delete(self):
        """Test permissions for AdminAlert deletion"""
        url = reverse(
            'adminalerts:delete', kwargs={'uuid': self.alert.sodar_uuid}
        )
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_alert_list(self):
        """Test permissions for AdminAlert list"""
        url = reverse('adminalerts:list')
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_alert_detail(self):
        """Test permissions for AdminAlert details"""
        url = reverse(
            'adminalerts:detail', kwargs={'uuid': self.alert.sodar_uuid}
        )
        good_users = [self.superuser, self.regular_user]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_alert_activation(self):
        """Test permissions for AdminAlert activation API view"""
        url = reverse('adminalerts:api_alert_activation')
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(
            url, good_users, HttpResponseBadRequest.status_code, method='POST'
        )
        self.assert_response(url, bad_users, 302)
