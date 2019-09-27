"""Tests for the project settings API in the projectroles app"""

from test_plus.test import TestCase

from ..models import Role, AppSetting, SODAR_CONSTANTS
from ..plugins import get_app_plugin
from ..app_settings import AppSettingAPI
from .test_models import ProjectMixin, RoleAssignmentMixin, AppSettingMixin

# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SUBMIT_STATUS_OK = SODAR_CONSTANTS['SUBMIT_STATUS_OK']
SUBMIT_STATUS_PENDING = SODAR_CONSTANTS['SUBMIT_STATUS_PENDING']
SUBMIT_STATUS_PENDING_TASKFLOW = SODAR_CONSTANTS['SUBMIT_STATUS_PENDING']
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']

# Local settings
EXISTING_SETTING = 'project_bool_setting'
EXAMPLE_APP_NAME = 'example_project_app'

# App settings API
app_settings = AppSettingAPI()


class TestAppSettingAPI(
    ProjectMixin, RoleAssignmentMixin, AppSettingMixin, TestCase
):
    """Tests for AppSettingAPI"""

    # NOTE: This assumes an example app is available

    def setUp(self):
        # Init project
        self.project = self._make_project(
            title='TestProject', type=PROJECT_TYPE_PROJECT, parent=None
        )

        # Init role
        self.role_owner = Role.objects.get(name=PROJECT_ROLE_OWNER)

        # Init user & role
        self.user = self.make_user('owner')
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        # Init test setting
        setting_str_kwarg = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'str_setting',
            'setting_type': 'STRING',
            'value': 'test',
            'update_value': 'better test',
            'non_valid_value': False,
        }
        setting_int_kwarg = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'int_setting',
            'setting_type': 'INTEGER',
            'value': 210,
            'update_value': 420,
            'non_valid_value': 'Nan',
        }
        setting_bool_kwarg = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'bool_setting',
            'setting_type': 'BOOLEAN',
            'value': True,
            'update_value': False,
            'non_valid_value': 69,
        }
        setting_json_kwarg = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'json_setting',
            'setting_type': 'JSON',
            'value': {'Test': 'often'},
            'update_value': {'Test_more': 'often_always'},
            'non_valid_value': self.project,
        }
        self.settings = [
            setting_int_kwarg,
            setting_json_kwarg,
            setting_str_kwarg,
            setting_bool_kwarg,
        ]
        for s in self.settings:
            self._make_setting(
                app_name=s['app_name'],
                name=s['name'],
                setting_type=s['setting_type'],
                value=s['value'],
                value_json=s['value'],
                project=s['project'],
            )

    def test_get_project_setting(self):
        """Test get_app_setting()"""
        for setting in self.settings:
            val = app_settings.get_app_setting(
                app_name=setting['app_name'],
                setting_name=setting['name'],
                project=setting['project'],
            )
            self.assertEqual(setting['value'], val)

    def test_get_project_setting_default(self):
        """Test get_app_setting() with default value for existing setting"""
        app_plugin = get_app_plugin(EXAMPLE_APP_NAME)
        default_val = app_plugin.app_settings[EXISTING_SETTING]['default']

        val = app_settings.get_app_setting(
            app_name=EXAMPLE_APP_NAME,
            setting_name=EXISTING_SETTING,
            project=self.project,
        )

        self.assertEqual(val, default_val)

    def test_get_project_setting_nonexisting(self):
        """Test get_app_setting() with an non-existing setting"""
        with self.assertRaises(KeyError):
            app_settings.get_app_setting(
                app_name=EXAMPLE_APP_NAME,
                setting_name='NON-EXISTING SETTING',
                project=self.project,
            )

    def test_set_project_setting(self):
        """Test set_app_setting()"""

        for setting in self.settings:
            ret = app_settings.set_app_setting(
                app_name=setting['app_name'],
                setting_name=setting['name'],
                project=setting['project'],
                value=setting['update_value'],
            )
            self.assertEqual(ret, True)

            val = app_settings.get_app_setting(
                app_name=setting['app_name'],
                setting_name=setting['name'],
                project=setting['project'],
            )
            self.assertEqual(val, setting['update_value'])

    def test_set_project_setting_unchanged(self):
        """Test set_app_setting() with an unchnaged value"""

        for setting in self.settings:
            ret = app_settings.set_app_setting(
                app_name=setting['app_name'],
                setting_name=setting['name'],
                project=setting['project'],
                value=setting['value'],
            )
            self.assertEqual(ret, False)

            val = app_settings.get_app_setting(
                app_name=setting['app_name'],
                setting_name=setting['name'],
                project=setting['project'],
            )
            self.assertEqual(val, setting['value'])

    def test_set_project_setting_new(self):
        """Test set_app_setting() with a new but defined setting"""

        # Assert precondition
        with self.assertRaises(AppSetting.DoesNotExist):
            AppSetting.objects.get(
                app_plugin=get_app_plugin(EXAMPLE_APP_NAME).get_model(),
                project=self.project,
                name=EXISTING_SETTING,
            )

        ret = app_settings.set_app_setting(
            app_name=EXAMPLE_APP_NAME,
            setting_name=EXISTING_SETTING,
            value=True,
            project=self.project,
        )

        # Asset postconditions
        self.assertEqual(ret, True)
        val = app_settings.get_app_setting(
            app_name=EXAMPLE_APP_NAME,
            setting_name=EXISTING_SETTING,
            project=self.project,
        )
        self.assertEqual(True, val)

        setting = AppSetting.objects.get(
            app_plugin=get_app_plugin(EXAMPLE_APP_NAME).get_model(),
            project=self.project,
            name=EXISTING_SETTING,
        )
        self.assertIsInstance(setting, AppSetting)

    def test_set_project_setting_undefined(self):
        """Test set_app_setting() with an undefined setting (should fail)"""
        with self.assertRaises(KeyError):
            app_settings.set_app_setting(
                app_name=EXAMPLE_APP_NAME,
                setting_name='new_setting',
                value='new',
                project=self.project,
            )

    def test_validator(self):
        """Test validate_setting() with type BOOLEAN"""
        for setting in self.settings:
            self.assertEqual(
                app_settings.validate_setting(
                    setting['setting_type'], setting['value']
                ),
                True,
            )
            if setting['setting_type'] == 'STRING':
                continue
            with self.assertRaises(ValueError):
                app_settings.validate_setting(
                    setting['setting_type'], setting['non_valid_value']
                )

    def test_validate_project_setting_int(self):
        """Test validate_setting() with type INTEGER"""
        self.assertEqual(app_settings.validate_setting('INTEGER', 170), True)
        # NOTE: String is also OK if it corresponds to an int
        self.assertEqual(app_settings.validate_setting('INTEGER', '170'), True)

        with self.assertRaises(ValueError):
            app_settings.validate_setting('INTEGER', 'not an integer')

    def test_validate_project_setting_invalid(self):
        """Test validate_setting() with an invalid type"""
        with self.assertRaises(ValueError):
            app_settings.validate_setting('INVALID_TYPE', 'value')

    def test_get_setting_defs_project(self):
        """Test get_setting_defs() with the PROJECT scope"""
        app_plugin = get_app_plugin(EXAMPLE_APP_NAME)
        expected = {
            'project_bool_setting': {
                'scope': APP_SETTING_SCOPE_PROJECT,
                'type': 'BOOLEAN',
                'default': False,
                'description': 'Example project setting',
                'user_modifiable': True,
            },
            'project_json_setting': {
                'scope': APP_SETTING_SCOPE_PROJECT,
                'type': 'JSON',
                'default': {
                    'Example': 'Value',
                    'list': [1, 2, 3, 4, 5],
                    'level_6': False,
                },
                'description': 'Example project setting for JSON. Will accept '
                'anything that json.dumps() can.',
                'user_modifiable': True,
            },
            'project_hidden_setting': {
                'scope': APP_SETTING_SCOPE_PROJECT,
                'type': 'STRING',
                'label': 'Hidden project setting',
                'default': '',
                'description': 'Should not be displayed in forms',
                'user_modifiable': False,
            },
        }
        defs = app_settings.get_setting_defs(
            app_plugin, APP_SETTING_SCOPE_PROJECT
        )
        self.assertEqual(defs, expected)

    def test_get_setting_defs_user(self):
        """Test get_setting_defs() with the USER scope"""
        app_plugin = get_app_plugin(EXAMPLE_APP_NAME)
        expected = {
            'user_str_setting': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'STRING',
                'label': 'String example',
                'default': '',
                'description': 'Example user setting',
                'user_modifiable': True,
            },
            'user_int_setting': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'INTEGER',
                'label': 'Int example',
                'default': 0,
                'user_modifiable': True,
            },
            'user_bool_setting': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'BOOLEAN',
                'label': 'Bool Example',
                'default': False,
                'user_modifiable': True,
            },
            'user_json_setting': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'JSON',
                'label': 'Json example',
                'default': {
                    'Example': 'Value',
                    'list': [1, 2, 3, 4, 5],
                    'level_6': False,
                },
                'description': 'Example project setting for JSON. Will accept '
                'anything that json.dumps() can.',
                'user_modifiable': True,
            },
            'user_hidden_setting': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'STRING',
                'label': 'Hidden user setting',
                'default': '',
                'description': 'Should not be displayed in forms',
                'user_modifiable': False,
            },
        }
        defs = app_settings.get_setting_defs(app_plugin, APP_SETTING_SCOPE_USER)
        self.assertEqual(defs, expected)

    def test_get_setting_defs_modifiable(self):
        """Test get_setting_defs() with the user_modifiable arg"""
        app_plugin = get_app_plugin(EXAMPLE_APP_NAME)
        defs = app_settings.get_setting_defs(
            app_plugin, APP_SETTING_SCOPE_PROJECT
        )
        self.assertEqual(len(defs), 3)
        defs = app_settings.get_setting_defs(
            app_plugin, APP_SETTING_SCOPE_PROJECT, user_modifiable=True
        )
        self.assertEqual(len(defs), 2)

    def test_get_setting_defs_invalid(self):
        """Test get_setting_defs() with an invalid scope"""
        app_plugin = get_app_plugin(EXAMPLE_APP_NAME)

        with self.assertRaises(ValueError):
            app_settings.get_setting_defs(app_plugin, 'Ri4thai8aez5ooRa')

    def test_get_all_defaults_project(self):
        """Test get_all_defaults() with the PROJECT scope"""
        prefix = 'settings.{}.'.format(EXAMPLE_APP_NAME)
        defaults = app_settings.get_all_defaults(APP_SETTING_SCOPE_PROJECT)
        self.assertEqual(defaults[prefix + 'project_bool_setting'], False)

    def test_get_all_defaults_user(self):
        """Test get_all_defaults() with the USER scope"""
        prefix = 'settings.{}.'.format(EXAMPLE_APP_NAME)
        defaults = app_settings.get_all_defaults(APP_SETTING_SCOPE_USER)
        self.assertEqual(defaults[prefix + 'user_str_setting'], '')
        self.assertEqual(defaults[prefix + 'user_int_setting'], 0)
        self.assertEqual(defaults[prefix + 'user_bool_setting'], False)
