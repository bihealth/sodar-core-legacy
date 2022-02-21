"""UI view tests for the tokens app"""

from django.contrib.messages import get_messages
from django.urls import reverse

from knox.models import AuthToken

from test_plus.test import TestCase

from tokens.views import TOKEN_CREATE_MSG, TOKEN_DELETE_MSG


class TestUserTokenListView(TestCase):
    """Tests for UserTokenListView"""

    def setUp(self):
        self.user = self.make_user()

    def _make_token(self):
        self.tokens = [AuthToken.objects.create(self.user, None)]

    def test_list_empty(self):
        """Test rendering the list view without tokens"""
        with self.login(self.user):
            response = self.get('tokens:list')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_list_one(self):
        """Test rendering the list view with one token"""
        self._make_token()
        with self.login(self.user):
            response = self.get('tokens:list')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)


class TestUserTokenCreateView(TestCase):
    """Tests for UserTokenCreateView"""

    def setUp(self):
        self.user = self.make_user()

    def test_get(self):
        """Test rendering the creation form"""
        with self.login(self.user):
            response = self.get('tokens:create')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["form"])

    def test_post_no_ttl(self):
        """Test creating an authentication token with TTL=0"""
        self.assertEqual(AuthToken.objects.count(), 0)
        with self.login(self.user):
            response = self.post('tokens:create', data={'ttl': 0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AuthToken.objects.count(), 1)
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            TOKEN_CREATE_MSG,
        )

    def test_post_ttl(self):
        """Test creating an authentication token with TTL != 0"""
        self.assertEqual(AuthToken.objects.count(), 0)
        with self.login(self.user):
            response = self.post('tokens:create', data={'ttl': 10})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AuthToken.objects.count(), 1)
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            TOKEN_CREATE_MSG,
        )


class TestUserTokenDeleteView(TestCase):
    """Tests for UserTokenDeleteView"""

    def setUp(self):
        self.user = self.make_user()
        AuthToken.objects.create(user=self.user)
        self.token = AuthToken.objects.first()

    def test_get(self):
        """Test rendering the deletion form"""
        with self.login(self.user):
            response = self.get('tokens:delete', pk=self.token.pk)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        """Test token deletion"""
        self.assertEqual(AuthToken.objects.count(), 1)
        with self.login(self.user):
            response = self.post('tokens:delete', pk=self.token.pk)
        self.response_302(response)
        self.assertRedirects(
            response, reverse('tokens:list'), fetch_redirect_response=False
        )
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            TOKEN_DELETE_MSG,
        )
