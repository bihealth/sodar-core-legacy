"""UI tests for the appalerts app"""

import time

from django.urls import reverse

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

# Projectroles dependency
from projectroles.tests.test_ui import TestUIBase

from appalerts.models import AppAlert
from appalerts.tests.test_models import AppAlertMixin


class TestAlertUIBase(AppAlertMixin, TestUIBase):
    def setUp(self):
        super().setUp()
        # Create users
        self.superuser = self._make_user('superuser', superuser=True)
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()
        self.regular_user = self._make_user('regular_user')
        self.no_alert_user = self._make_user('no_alert_user')
        # No user
        self.anonymous = None
        # Create alerts
        self.alert = self._make_app_alert(
            user=self.regular_user, url=reverse('home')
        )
        self.alert2 = self._make_app_alert(
            user=self.regular_user, url=reverse('home')
        )


class TestListView(TestAlertUIBase):
    """Tests for the admin alert list view"""

    def test_render(self):
        """Test existence of alert items in list"""
        expected = [
            (self.superuser, 0),
            (self.regular_user, 2),
            (self.no_alert_user, 0),
        ]
        url = reverse('appalerts:list')
        self.assert_element_count(
            expected,
            url,
            'alert alert-info sodar-app-alert-item',
            'class',
            exact=True,
        )

    def test_alert_dismiss(self):
        """Test dismissing alert"""
        self.assertEqual(AppAlert.objects.filter(active=True).count(), 2)

        url = reverse('appalerts:list')
        self.login_and_redirect(self.regular_user, url)
        self.assertEqual(
            self.selenium.find_element(By.ID, 'sodar-app-alert-count').text, '2'
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, 'sodar-app-alert-legend').text,
            'alerts',
        )

        button = self.selenium.find_elements(
            By.CLASS_NAME, 'sodar-app-alert-btn-dismiss-single'
        )[0]
        button.click()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.invisibility_of_element_located(
                (By.CLASS_NAME, 'sodar-app-alert-item')
            )
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, 'sodar-app-alert-count').text, '1'
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, 'sodar-app-alert-legend').text,
            'alert',
        )
        self.assertEqual(AppAlert.objects.filter(active=True).count(), 1)
        self.assertFalse(
            self.selenium.find_element(
                By.ID, 'sodar-app-alert-empty'
            ).is_displayed()
        )

    def test_alert_dismiss_all(self):
        """Test dismissing all alerts for the user"""
        self.assertEqual(AppAlert.objects.filter(active=True).count(), 2)

        url = reverse('appalerts:list')
        self.login_and_redirect(self.regular_user, url)
        self.assertEqual(
            self.selenium.find_element(By.ID, 'sodar-app-alert-count').text, '2'
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, 'sodar-app-alert-legend').text,
            'alerts',
        )

        self.selenium.find_element(
            By.ID, 'sodar-app-alert-btn-dismiss-all'
        ).click()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.invisibility_of_element_located(
                (By.CLASS_NAME, 'sodar-app-alert-item')
            )
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, 'sodar-app-alert-count').text, ''
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, 'sodar-app-alert-legend').text,
            '',
        )
        self.assertEqual(AppAlert.objects.filter(active=True).count(), 0)
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.visibility_of_element_located((By.ID, 'sodar-app-alert-empty'))
        )
        self.assertTrue(
            self.selenium.find_element(
                By.ID, 'sodar-app-alert-empty'
            ).is_displayed()
        )

    def test_alert_reload(self):
        """Test displaying reload link for new alerts"""
        AppAlert.objects.filter(active=True).delete()
        self.assertEqual(AppAlert.objects.filter(active=True).count(), 0)

        url = reverse('appalerts:list')
        self.login_and_redirect(self.regular_user, url)
        self.assertTrue(
            self.selenium.find_element(
                By.ID, 'sodar-app-alert-empty'
            ).is_displayed()
        )
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-app-alert-reload')

        self._make_app_alert(user=self.regular_user, url=reverse('home'))

        WebDriverWait(self.selenium, self.wait_time).until(
            ec.visibility_of_element_located((By.ID, 'sodar-app-alert-reload'))
        )
        self.assertTrue(
            self.selenium.find_element(
                By.ID, 'sodar-app-alert-reload'
            ).is_displayed()
        )


class TestTitlebarBadge(TestAlertUIBase):
    """Tests for the site titlebar badge"""

    def test_render(self):
        """Test existence of alert badge for user with alerts"""
        url = reverse('home')
        self.login_and_redirect(self.regular_user, url)
        alert_badge = self.selenium.find_element(By.ID, 'sodar-app-alert-badge')
        self.assertIsNotNone(alert_badge)
        self.assertTrue(alert_badge.is_displayed())
        alert_count = self.selenium.find_element(By.ID, 'sodar-app-alert-count')
        alert_legend = self.selenium.find_element(
            By.ID, 'sodar-app-alert-legend'
        )
        self.assertEqual(alert_count.text, '2')
        self.assertEqual(alert_legend.text, 'alerts')

    def test_render_no_alerts(self):
        """Test existence of alert badge for user without alerts"""
        url = reverse('home')
        self.login_and_redirect(self.no_alert_user, url)
        alert_badge = self.selenium.find_element(By.ID, 'sodar-app-alert-badge')
        self.assertIsNotNone(alert_badge)
        self.assertFalse(alert_badge.is_displayed())

    def test_render_add(self):
        """Test adding an alert for user with alerts"""
        url = reverse('home')
        self.login_and_redirect(self.regular_user, url)
        alert_count = self.selenium.find_element(By.ID, 'sodar-app-alert-count')
        alert_legend = self.selenium.find_element(
            By.ID, 'sodar-app-alert-legend'
        )
        self.assertEqual(alert_count.text, '2')
        self.assertEqual(alert_legend.text, 'alerts')

        self._make_app_alert(user=self.regular_user, url=reverse('home'))
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.text_to_be_present_in_element(
                (By.ID, 'sodar-app-alert-count'), '3'
            )
        )
        self.assertEqual(alert_count.text, '3')
        self.assertEqual(alert_legend.text, 'alerts')

    def test_render_delete(self):
        """Test deleting an alert from user with alerts"""
        url = reverse('home')
        self.login_and_redirect(self.regular_user, url)
        alert_count = self.selenium.find_element(By.ID, 'sodar-app-alert-count')
        alert_legend = self.selenium.find_element(
            By.ID, 'sodar-app-alert-legend'
        )
        self.assertEqual(alert_count.text, '2')
        self.assertEqual(alert_legend.text, 'alerts')

        self.alert2.delete()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.text_to_be_present_in_element(
                (By.ID, 'sodar-app-alert-count'), '1'
            )
        )
        self.assertEqual(alert_count.text, '1')
        self.assertEqual(alert_legend.text, 'alert')

    def test_render_delete_all(self):
        """Test deleting all alerts from user with alerts"""
        url = reverse('home')
        self.login_and_redirect(self.regular_user, url)
        alert_badge = self.selenium.find_element(By.ID, 'sodar-app-alert-badge')
        self.assertTrue(alert_badge.is_displayed())

        self.alert.delete()
        self.alert2.delete()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.invisibility_of_element_located((By.ID, 'sodar-app-alert-badge'))
        )
        self.assertFalse(alert_badge.is_displayed())

    def test_render_add_no_alerts(self):
        """Test adding an alert for user without prior alerts"""
        url = reverse('home')
        self.login_and_redirect(self.no_alert_user, url)
        alert_badge = self.selenium.find_element(By.ID, 'sodar-app-alert-badge')
        self.assertFalse(alert_badge.is_displayed())

        self._make_app_alert(user=self.no_alert_user, url=reverse('home'))
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.visibility_of_element_located((By.ID, 'sodar-app-alert-badge'))
        )
        self.assertTrue(alert_badge.is_displayed())

        alert_count = self.selenium.find_element(By.ID, 'sodar-app-alert-count')
        alert_legend = self.selenium.find_element(
            By.ID, 'sodar-app-alert-legend'
        )
        self.assertEqual(alert_count.text, '1')
        self.assertEqual(alert_legend.text, 'alert')

    def test_alert_dismiss_all(self):
        """Test dismissing all alerts for the user"""
        self.assertEqual(AppAlert.objects.filter(active=True).count(), 2)

        url = reverse('home')
        self.login_and_redirect(self.regular_user, url)

        self.selenium.find_element(
            By.ID, 'sodar-app-alert-badge-btn-dismiss'
        ).click()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.invisibility_of_element_located(
                (By.CLASS_NAME, 'sodar-app-alert-legend')
            )
        )
        time.sleep(2)  # HACK: Timing issue, must wait just in case
        self.assertEqual(AppAlert.objects.filter(active=True).count(), 0)
