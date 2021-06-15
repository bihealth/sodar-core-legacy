"""UI tests for the userprofile app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_ui import TestUIBase


@override_settings(AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE')
class TestUserDetails(TestUIBase):
    """Tests for user details page"""

    def setUp(self):
        super().setUp()
        # Create users
        self.local_user = self._make_user('local_user', False)
        self.ldap_user = self._make_user('user@EXAMPLE', False)

    def test_update_button(self):
        """Test existence of user update button"""
        url = reverse('userprofile:detail')
        expected = [(self.local_user, 1), (self.ldap_user, 0)]
        self.assert_element_count(expected, url, 'sodar-user-update-btn')
