"""UI tests for the tokens app"""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from knox.models import AuthToken
from selenium.webdriver.common.by import By


# Projectroles dependency
from projectroles.tests.test_ui import TestUIBase


class TestTokenList(TestUIBase):
    """Tests for token list"""

    def setUp(self):
        super().setUp()
        # Create users
        self.superuser = self._make_user('superuser', True)
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()
        self.regular_user = self._make_user('regular_user', False)

        # Create tokens
        self.token = AuthToken.objects.create(
            self.regular_user, timedelta(days=5)
        )[0]
        self.token_no_expiry = AuthToken.objects.create(
            self.regular_user, None
        )[0]

    def test_list_items(self):
        """Test visibility of items in token list"""
        expected = [(self.superuser, 0), (self.regular_user, 2)]
        url = reverse('tokens:list')
        self.assert_element_count(expected, url, 'sodar-tk-list-item', 'class')

    def test_list_expiry(self):
        """Test token expiry dates in token list"""
        url = reverse('tokens:list')
        self.login_and_redirect(self.regular_user, url)
        items = self.selenium.find_elements(By.CLASS_NAME, 'sodar-tk-list-item')
        self.assertEqual(len(items), 2)
        expiry_time = timezone.localtime(self.token.expiry).strftime(
            '%Y-%m-%d %H:%M'
        )
        values = []
        for item in items:
            values.append(item.find_elements(By.TAG_NAME, 'td')[2].text)
        self.assertCountEqual(values, ['Never', expiry_time])
