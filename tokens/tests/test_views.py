"""View tests for the tokens app"""


from django.urls import reverse

from knox.models import AuthToken

from test_plus.test import TestCase


class TestUserTokenListView(TestCase):
    """Tests for UserTokenListView"""

    def setUp(self):
        self.user = self.make_user()

    def _make_token(self):
        self.tokens = [AuthToken.objects.create(self.user, None)]

    def test_list_empty(self):
        """Test that rendering the list view without any tokens works"""
        with self.login(self.user):
            response = self.get('tokens:list')
        self.response_200(response)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_list_one(self):
        """Test that rendering the list view with one token works"""
        self._make_token()
        with self.login(self.user):
            response = self.get('tokens:list')
        self.response_200(response)
        self.assertEqual(len(response.context['object_list']), 1)


class TestUserTokenCreateView(TestCase):
    """Tests for UserTokenCreateView"""

    def setUp(self):
        self.user = self.make_user()

    def test_get(self):
        """Test that showing the creation form works"""
        with self.login(self.user):
            response = self.get('tokens:create')
        self.response_200(response)
        self.assertIsNotNone(response.context["form"])

    def test_post_success_no_ttl(self):
        """Test creating an authentication token with TTL=0 works"""
        self.assertEqual(AuthToken.objects.count(), 0)
        with self.login(self.user):
            response = self.post('tokens:create', data={'ttl': 0})
        self.response_200(response)
        self.assertEqual(AuthToken.objects.count(), 1)

    def test_post_success_with_ttl(self):
        """Test creating an authentication token with TTL != 0 works"""
        self.assertEqual(AuthToken.objects.count(), 0)
        with self.login(self.user):
            response = self.post('tokens:create', data={'ttl': 10})
        self.response_200(response)
        self.assertEqual(AuthToken.objects.count(), 1)


class TestUserTokenDeleteView(TestCase):
    """Tests for UserTokenDeleteView"""

    def setUp(self):
        self.user = self.make_user()
        AuthToken.objects.create(user=self.user)
        self.token = AuthToken.objects.first()

    def test_get(self):
        """Test that showing the deletion form works"""
        with self.login(self.user):
            response = self.get('tokens:delete', pk=self.token.pk)
        self.response_200(response)

    def test_post_success(self):
        """Test that deleting a token works"""
        self.assertEqual(AuthToken.objects.count(), 1)
        with self.login(self.user):
            response = self.post('tokens:delete', pk=self.token.pk)
        self.response_302(response)
        self.assertRedirects(
            response, reverse('tokens:list'), fetch_redirect_response=False
        )
