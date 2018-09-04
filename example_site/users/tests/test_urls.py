from django.core.urlresolvers import reverse, resolve

from test_plus.test import TestCase


class TestUserURLs(TestCase):
    """Test URL patterns for users app."""

    def setUp(self):
        self.user = self.make_user()

    def test_detail_reverse(self):
        """users:user_detail should reverse to /users/testuser."""
        self.assertEqual(
            reverse('users:user_detail', kwargs={'username': 'testuser'}),
            '/users/testuser')

    def test_detail_resolve(self):
        """/users/testuser should resolve to users:user_detail."""
        self.assertEqual(
            resolve('/users/testuser').view_name, 'users:user_detail')
