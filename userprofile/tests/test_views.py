"""Tests for views in the userprofile Django app"""

from django.core.urlresolvers import reverse
from django.test import RequestFactory

from test_plus.test import TestCase

from projectroles.app_settings import AppSettingAPI
from projectroles.tests.test_models import EXAMPLE_APP_NAME, AppSettingMixin


# App settings API
app_settings = AppSettingAPI()


class TestViewsBase(TestCase):
    """Base class for view testing"""

    def setUp(self):
        self.req_factory = RequestFactory()

        # Init superuser
        self.user = self.make_user('superuser')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()


# View tests -------------------------------------------------------------------


class TestUserDetailView(TestViewsBase):
    """Tests for the user profile detail view"""

    def test_render(self):
        """Test to ensure the user profile detail view renders correctly"""
        with self.login(self.user):
            response = self.client.get(reverse('userprofile:detail'))
        self.assertEqual(response.status_code, 200)

        self.assertIsNotNone(response.context['user_settings'])


class TestUserSettingsForm(AppSettingMixin, TestViewsBase):
    """Tests for the user settings form."""

    # NOTE: This assumes an example app is available
    def setUp(self):
        # Init user & role
        self.user = self.make_user('owner')

        # Init test setting
        self.setting_str = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='user_str_setting',
            setting_type='STRING',
            value='test',
            user=self.user,
        )

        # Init integer setting
        self.setting_int = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='user_int_setting',
            setting_type='INTEGER',
            value=170,
            user=self.user,
        )

        # Init boolean setting
        self.setting_bool = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='user_bool_setting',
            setting_type='BOOLEAN',
            value=True,
            user=self.user,
        )

        # Init json setting
        self.setting_json = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='user_json_setting',
            setting_type='JSON',
            value=None,
            value_json={'Test': 'More'},
            user=self.user,
        )

    def testGet(self):
        with self.login(self.user):
            response = self.client.get(reverse('userprofile:settings_update'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'])
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.%s.user_str_setting' % EXAMPLE_APP_NAME
            )
        )
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.%s.user_int_setting' % EXAMPLE_APP_NAME
            )
        )
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.%s.user_bool_setting' % EXAMPLE_APP_NAME
            )
        )
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.%s.user_json_setting' % EXAMPLE_APP_NAME
            )
        )

    def testPost(self):
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME, 'user_str_setting', user=self.user
            ),
            'test',
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME, 'user_int_setting', user=self.user
            ),
            170,
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME, 'user_bool_setting', user=self.user
            ),
            True,
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME, 'user_json_setting', user=self.user
            ),
            {'Test': 'More'},
        )

        values = {
            'settings.%s.user_str_setting' % EXAMPLE_APP_NAME: 'another-text',
            'settings.%s.user_int_setting' % EXAMPLE_APP_NAME: '123',
            'settings.%s.user_bool_setting' % EXAMPLE_APP_NAME: False,
            'settings.%s.user_json_setting'
            % EXAMPLE_APP_NAME: '{"Test": "Less"}',
        }

        with self.login(self.user):
            response = self.client.post(
                reverse('userprofile:settings_update'), values
            )

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(response, reverse('userprofile:detail'))

        # Assert settings state after update
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME, 'user_str_setting', user=self.user
            ),
            'another-text',
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME, 'user_int_setting', user=self.user
            ),
            123,
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME, 'user_bool_setting', user=self.user
            ),
            False,
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME, 'user_json_setting', user=self.user
            ),
            {'Test': 'Less'},
        )
