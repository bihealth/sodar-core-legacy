"""UI tests for the adminalerts app"""

from django.urls import reverse
from django.utils import timezone

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

# Projectroles dependency
from projectroles.tests.test_ui import TestUIBase

from adminalerts.tests.test_models import AdminAlertMixin


class TestAlertUIBase(AdminAlertMixin, TestUIBase):
    def setUp(self):
        super().setUp()
        # Create users
        self.superuser = self._make_user('superuser', True)
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()

        self.regular_user = self._make_user('regular_user', False)

        # Create alert
        self.alert = self._make_alert(
            message='alert',
            user=self.superuser,
            description='description',
            active=True,
        )


class TestAlertMessage(TestAlertUIBase):
    """Tests for the admin alert message"""

    def test_message(self):
        """Test visibility of alert message in home view"""
        expected = [(self.superuser, 1), (self.regular_user, 1)]
        url = reverse('home')
        self.assert_element_count(
            expected, url, 'sodar-alert-site-app', 'class'
        )

    def test_message_inactive(self):
        """Test visibility of an inactive alert message"""
        self.alert.active = 0
        self.alert.save()

        expected = [(self.superuser, 0), (self.regular_user, 0)]
        url = reverse('home')
        self.assert_element_count(
            expected, url, 'sodar-alert-site-app', 'class'
        )

    def test_message_expired(self):
        """Test visibility of an expired alert message"""
        self.alert.date_expire = timezone.now() - timezone.timedelta(days=1)
        self.alert.save()

        expected = [(self.superuser, 0), (self.regular_user, 0)]
        url = reverse('home')
        self.assert_element_count(
            expected, url, 'sodar-alert-site-app', 'class'
        )

    def test_message_login(self):
        """Test visibility of alert in login view with auth requirement"""
        self.selenium.get(self.build_selenium_url(reverse('login')))
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.CLASS_NAME, 'sodar-alert-site-app')

    def test_message_login_no_auth(self):
        """Test visibility of alert in login view without auth requirement"""
        self.alert.require_auth = False
        self.alert.save()

        self.selenium.get(self.build_selenium_url(reverse('login')))
        self.assertIsNotNone(
            self.selenium.find_element(By.CLASS_NAME, 'sodar-alert-site-app')
        )


class TestListView(TestAlertUIBase):
    """Tests for the admin alert list view"""

    def test_list_items(self):
        """Test existence of items in list"""
        expected = [(self.superuser, 1)]
        url = reverse('adminalerts:list')
        self.assert_element_count(expected, url, 'sodar-aa-alert-item', 'id')

    def test_list_buttons(self):
        """Test existence of buttons in list"""
        expected = [(self.superuser, 1)]
        url = reverse('adminalerts:list')
        self.assert_element_count(expected, url, 'sodar-aa-alert-buttons', 'id')
