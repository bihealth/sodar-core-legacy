"""Tests for views in the siteinfo app"""

from django.urls import reverse

from test_plus.test import TestCase


class TestViewsBase(TestCase):
    """Base class for view testing"""

    def setUp(self):
        # Create users
        self.superuser = self.make_user('superuser')
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()

        self.regular_user = self.make_user('regular_user')

        # No user
        self.anonymous = None


class TestSiteInfoView(TestViewsBase):
    """Tests for the site info view"""

    def test_render(self):
        """Test rendering of the site info view"""
        with self.login(self.superuser):
            response = self.client.get(reverse('siteinfo:info'))
            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(response.context['project_plugins'])
            self.assertIsNotNone(response.context['site_plugins'])
            self.assertIsNotNone(response.context['backend_plugins'])
            self.assertIsNotNone(response.context['settings_core'])
