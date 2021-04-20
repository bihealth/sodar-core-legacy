"""UI tests for the appalerts app"""

from django.urls import reverse

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
            expected, url, 'sodar-app-alert-item', 'class'
        )

    def test_alert_dismiss(self):
        """Test dismissing alert"""
        self.assertEqual(AppAlert.objects.filter(active=True).count(), 2)

        url = reverse('appalerts:list')
        self.login_and_redirect(self.regular_user, url)
        self.assertEqual(
            self.selenium.find_element_by_id('sodar-app-alert-count').text, '2'
        )
        self.assertEqual(
            self.selenium.find_element_by_id('sodar-app-alert-legend').text,
            'alerts',
        )

        button = self.selenium.find_elements_by_class_name(
            'sodar-app-alert-btn-dismiss'
        )[0]
        button.click()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.invisibility_of_element_located(
                (By.CLASS_NAME, 'sodar-app-alert-item')
            )
        )
        self.assertEqual(
            self.selenium.find_element_by_id('sodar-app-alert-count').text, '1'
        )
        self.assertEqual(
            self.selenium.find_element_by_id('sodar-app-alert-legend').text,
            'alert',
        )
        self.assertEqual(AppAlert.objects.filter(active=True).count(), 1)
