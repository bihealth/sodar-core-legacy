"""Tests for management commands in the projectroles Django app"""

from django.core.management import call_command
from djangoplugins.models import Plugin

from test_plus.test import TestCase

from projectroles.management.commands.cleanappsettings import (
    get_api_settings,
    get_db_settings,
    is_setting_undefined,
    get_setting_str,
    get_undefined_settings,
)
from projectroles.models import Role, SODAR_CONSTANTS, AppSetting
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleAssignmentMixin,
    AppSettingMixin,
)

# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

EXAMPLE_APP_NAME = 'example_project_app'


class TestCleanAppSettings(
    ProjectMixin, RoleAssignmentMixin, AppSettingMixin, TestCase
):
    """Test command cleanappsettings and associated functions"""

    def _make_undefined_setting(self):
        """Create database setting not reflected in the AppSetting dict"""
        ghost = AppSetting(
            app_plugin=self.plugin,
            project=self.project,
            name='ghost',
            type='BOOLEAN',
            value=True,
        )
        ghost.save()
        return ghost

    def setUp(self):
        super().setUp()

        self.maxDiff = None

        # Init roles
        self.role_owner = Role.objects.get_or_create(name=PROJECT_ROLE_OWNER)[0]
        self.role_delegate = Role.objects.get_or_create(
            name=PROJECT_ROLE_DELEGATE
        )[0]
        self.role_contributor = Role.objects.get_or_create(
            name=PROJECT_ROLE_CONTRIBUTOR
        )[0]
        self.role_guest = Role.objects.get_or_create(name=PROJECT_ROLE_GUEST)[0]

        # Init users
        self.user_owner = self.make_user('owner')
        self.user_owner.email = 'owner_user@example.com'
        self.user_owner.save()

        # Init projects
        self.category = self._make_project(
            'top_category', PROJECT_TYPE_CATEGORY, None
        )
        self.cat_owner_as = self._make_assignment(
            self.category, self.user_owner, self.role_owner
        )

        self.project = self._make_project(
            'sub_project', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self._make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        self.plugin = Plugin.objects.get(name='example_project_app')

        # Init test setting
        self.setting_str_values = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_str_setting',
            'setting_type': 'STRING',
            'value': 'test',
            'update_value': 'better test',
            'non_valid_value': False,
        }
        self.setting_int_values = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_int_setting',
            'setting_type': 'INTEGER',
            'value': 0,
            'update_value': 170,
            'non_valid_value': 'Nan',
        }
        self.setting_bool_values = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_bool_setting',
            'setting_type': 'BOOLEAN',
            'value': False,
            'update_value': True,
            'non_valid_value': 170,
        }
        self.setting_json_values = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_json_setting',
            'setting_type': 'JSON',
            'value': {
                'Example': 'Value',
                'list': [1, 2, 3, 4, 5],
                'level_6': False,
            },
            'update_value': {'Test_more': 'often_always'},
            'non_valid_value': self.project,
        }
        self.setting_iprestrict_values = {
            'app_name': 'projectroles',
            'project': self.project,
            'name': 'ip_restrict',
            'setting_type': 'BOOLEAN',
            'value': False,
            'update_value': True,
            'non_valid_value': 170,
        }
        self.settings = [
            self.setting_int_values,
            self.setting_json_values,
            self.setting_str_values,
            self.setting_bool_values,
            self.setting_iprestrict_values,
        ]
        for s in self.settings:
            self._make_setting(
                app_name=s['app_name'],
                name=s['name'],
                setting_type=s['setting_type'],
                value=s['value'] if s['setting_type'] != 'JSON' else '',
                value_json=s['value'] if s['setting_type'] == 'JSON' else {},
                project=s['project'],
            )

    def test_get_api_settings(self):
        """Test get_api_settings()"""
        settings = get_api_settings()
        self.assertDictEqual(
            settings,
            {
                self.project: [
                    'settings.example_project_app.project_str_setting',
                    'settings.example_project_app.project_int_setting',
                    'settings.example_project_app.project_str_setting_options',
                    'settings.example_project_app.project_int_setting_options',
                    'settings.example_project_app.project_bool_setting',
                    'settings.example_project_app.project_json_setting',
                    'settings.example_project_app.project_hidden_setting',
                    'settings.example_project_app.project_hidden_json_setting',
                    'settings.filesfolders.allow_public_links',
                    'settings.projectroles.ip_restrict',
                    'settings.projectroles.ip_allowlist',
                ]
            },
        )

    def test_get_db_settings(self):
        """Test get_db_settings()"""
        settings = get_db_settings()
        self.assertListEqual(list(settings), list(AppSetting.objects.all()))

    def test_is_setting_undefined_true(self):
        """Test is_setting_undefined() being True"""
        ghost = self._make_undefined_setting()
        api_settings = get_api_settings()
        self.assertTrue(is_setting_undefined(ghost, api_settings))

    def test_is_setting_undefined_false(self):
        """Test is_setting_undefined() being False"""
        api_settings = get_api_settings()
        db_settings = get_db_settings()
        self.assertFalse(
            is_setting_undefined(db_settings.first(), api_settings)
        )

    def test_get_setting_str(self):
        """ Test get_setting_str()"""
        settings = get_db_settings()
        setting_str = get_setting_str(
            settings.filter(name='project_str_setting').first()
        )
        self.assertEqual(
            setting_str, 'settings.example_project_app.project_str_setting'
        )

    def test_get_setting_str_projecroles(self):
        """ Test get_setting_str()"""
        settings = get_db_settings()
        setting_str = get_setting_str(
            settings.get(app_plugin=None, name='ip_restrict')
        )
        self.assertEqual(setting_str, 'settings.projectroles.ip_restrict')

    def test_get_database_ghost_app_settings_no_ghost(self):
        """Test get_undefined_settings() with no ghost setting"""
        api_settings = get_api_settings()
        db_settings = get_db_settings()
        ghosts = get_undefined_settings(api_settings, db_settings)

        self.assertEqual(len(ghosts), 0)

    def test_get_database_ghost_app_settings_one_ghost(self):
        """Test get_undefined_settings() with one ghost setting"""
        self._make_undefined_setting()

        api_settings = get_api_settings()
        db_settings = get_db_settings()
        ghosts = get_undefined_settings(api_settings, db_settings)

        self.assertEqual(len(ghosts), 1)
        self.assertEqual(ghosts[0].name, 'ghost')
        self.assertEqual(ghosts[0].app_plugin.name, self.plugin.name)

    def test_command_cleanappsettings(self):
        """Test the cleanappsetting commmand"""
        self._make_undefined_setting()

        with self.assertLogs(
            'projectroles.management.commands.cleanappsettings', level='INFO'
        ) as cm:
            call_command('cleanappsettings')
            self.assertEqual(
                cm.output,
                [
                    (
                        'INFO:'
                        'projectroles.management.commands.cleanappsettings:'
                        'Removing undefined app setting: '
                        'settings.example_project_app.ghost'
                    )
                ],
            )
