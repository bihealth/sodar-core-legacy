"""View tests for the appalerts app"""

from django.urls import reverse

from test_plus.test import TestCase

from appalerts.tests.test_models import AppAlertMixin


class TestViewsBase(AppAlertMixin, TestCase):
    """Base class for appalerts view testing"""

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


class TestAppAlertListView(TestViewsBase):
    """Tests for the alert list view"""

    def test_render_superuser(self):
        """Test rendering of the alert list view as superuser"""
        with self.login(self.superuser):
            response = self.client.get(reverse('appalerts:list'))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['object_list'].count(), 0)

    def test_render_regular_user(self):
        """Test rendering as user with an assigned alert"""
        with self.login(self.regular_user):
            response = self.client.get(reverse('appalerts:list'))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['object_list'].count(), 1)
            self.assertEqual(
                response.context['object_list'][0].pk, self.alert.pk
            )

    def test_render_no_alert_user(self):
        """Test rendering of the alert list view as user without alerts"""
        with self.login(self.no_alert_user):
            response = self.client.get(reverse('appalerts:list'))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['object_list'].count(), 0)


class TestAppAlertRedirectView(TestViewsBase):
    """Tests for the alert redirect view"""

    list_url = reverse('appalerts:list')

    def test_redirect_superuser(self):
        """Test redirecting as superuser"""
        self.assertEqual(self.alert.active, True)
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    'appalerts:redirect',
                    kwargs={'appalert': self.alert.sodar_uuid},
                )
            )
            self.assertRedirects(response, self.list_url)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.active, True)

    def test_redirect_regular_user(self):
        """Test redirecting as user with assigned alert"""
        self.assertEqual(self.alert.active, True)
        with self.login(self.regular_user):
            response = self.client.get(
                reverse(
                    'appalerts:redirect',
                    kwargs={'appalert': self.alert.sodar_uuid},
                )
            )
            self.assertRedirects(response, self.alert.url)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.active, False)

    def test_redirect_no_alert_user(self):
        """Test redirecting as user without alerts"""
        self.assertEqual(self.alert.active, True)
        with self.login(self.no_alert_user):
            response = self.client.get(
                reverse(
                    'appalerts:redirect',
                    kwargs={'appalert': self.alert.sodar_uuid},
                )
            )
            self.assertRedirects(response, self.list_url)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.active, True)


class TestAppAlertStatusAjaxView(TestViewsBase):
    """Tests for the alert status ajax view"""

    def test_get_user_with_alerts(self):
        """Test GET as user with alert assigned"""
        with self.login(self.regular_user):
            response = self.client.get(reverse('appalerts:ajax_status'))
            self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['alerts'], 1)

    def test_get_user_no_alerts(self):
        """Test GET as user without alert assigned"""
        with self.login(self.no_alert_user):
            response = self.client.get(reverse('appalerts:ajax_status'))
            self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['alerts'], 0)


class TestAppAlertDismissAjaxView(TestViewsBase):
    """Tests for the alert dismissal ajax view"""

    def test_post_superuser(self):
        """Test post as superuser"""
        self.assertEqual(self.alert.active, True)
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    'appalerts:ajax_dismiss',
                    kwargs={'appalert': self.alert.sodar_uuid},
                )
            )
            self.assertEqual(response.status_code, 404)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.active, True)

    def test_post_regular_user(self):
        """Test post as user with assigned alert"""
        self.assertEqual(self.alert.active, True)
        with self.login(self.regular_user):
            response = self.client.post(
                reverse(
                    'appalerts:ajax_dismiss',
                    kwargs={'appalert': self.alert.sodar_uuid},
                )
            )
            self.assertEqual(response.status_code, 200)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.active, False)

    def test_post_no_alert_user(self):
        """Test post as user without alerts"""
        self.assertEqual(self.alert.active, True)
        with self.login(self.no_alert_user):
            response = self.client.post(
                reverse(
                    'appalerts:ajax_dismiss',
                    kwargs={'appalert': self.alert.sodar_uuid},
                )
            )
            self.assertEqual(response.status_code, 404)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.active, True)

    def test_post_regular_user_all(self):
        """Test post as user dismissing all alerts"""
        self.assertEqual(self.alert.active, True)
        with self.login(self.regular_user):
            response = self.client.post(reverse('appalerts:ajax_dismiss_all'))
            self.assertEqual(response.status_code, 200)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.active, False)

    def test_post_no_alert_user_all(self):
        """Test post as user without alerts trying to dismiss all"""
        self.assertEqual(self.alert.active, True)
        with self.login(self.no_alert_user):
            response = self.client.post(reverse('appalerts:ajax_dismiss_all'))
            self.assertEqual(response.status_code, 404)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.active, True)
