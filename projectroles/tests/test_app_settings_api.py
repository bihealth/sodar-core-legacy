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
APP_SETTING_SCOPE_PROJECT_USER = SODAR_CONSTANTS[
    'APP_SETTING_SCOPE_PROJECT_USER'
]

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
        self.maxDiff = None

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

        # Init test project settings
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
        self.setting_str_values_options = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_str_setting_options',
            'setting_type': 'STRING',
            'value': 'string1',
            'options': [
                'string1',
                'string2',
            ],  # Options must match the entry in example_project_app.plugins.ProjectAppPlugin
            'update_value': 'string2',
            'non_valid_value': 'string3',
        }
        self.setting_int_values_options = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_int_setting_options',
            'setting_type': 'INTEGER',
            'value': 0,
            'options': [
                0,
                1,
            ],  # Options must match the entry in example_project_app.plugins.ProjectAppPlugin
            'update_value': 1,
            'non_valid_value': 2,
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

        # Init test user settings
        self.user_setting_str_values = {
            'app_name': EXAMPLE_APP_NAME,
            'user': self.user,
            'name': 'user_str_setting',
            'setting_type': 'STRING',
            'value': 'test',
            'update_value': 'better test',
            'non_valid_value': False,
        }
        self.user_setting_int_values = {
            'app_name': EXAMPLE_APP_NAME,
            'user': self.user,
            'name': 'user_int_setting',
            'setting_type': 'INTEGER',
            'value': 0,
            'update_value': 170,
            'non_valid_value': 'Nan',
        }
        self.user_setting_str_values_options = {
            'app_name': EXAMPLE_APP_NAME,
            'user': self.user,
            'name': 'user_str_setting_options',
            'setting_type': 'STRING',
            'value': 'string1',
            'update_value': 'string2',
            'options': [
                'string1',
                'string2',
            ],  # Options must match the entry in example_project_app.plugins.ProjectAppPlugin
            'non_valid_value': False,
        }
        self.user_setting_int_values_options = {
            'app_name': EXAMPLE_APP_NAME,
            'user': self.user,
            'name': 'user_int_setting_options',
            'setting_type': 'INTEGER',
            'value': 0,
            'update_value': 1,
            'options': [
                0,
                1,
            ],  # Options must match the entry in example_project_app.plugins.ProjectAppPlugin
            'non_valid_value': 'Nan',
        }
        self.user_setting_bool_values = {
            'app_name': EXAMPLE_APP_NAME,
            'user': self.user,
            'name': 'user_bool_setting',
            'setting_type': 'BOOLEAN',
            'value': False,
            'update_value': True,
            'non_valid_value': 170,
        }
        self.user_setting_json_values = {
            'app_name': EXAMPLE_APP_NAME,
            'user': self.user,
            'name': 'user_json_setting',
            'setting_type': 'JSON',
            'value': {
                'Example': 'Value',
                'list': [1, 2, 3, 4, 5],
                'level_6': False,
            },
            'update_value': {'Test_more': 'often_always'},
            'non_valid_value': self.project,
        }

        # Init test project-user settings
        self.project_user_setting_str_values = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'user': self.user,
            'name': 'project_user_string_setting',
            'setting_type': 'STRING',
            'value': 'test',
            'update_value': 'better test',
            'non_valid_value': False,
        }
        self.project_user_setting_int_values = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'user': self.user,
            'name': 'project_user_int_setting',
            'setting_type': 'INTEGER',
            'value': 0,
            'update_value': 170,
            'non_valid_value': 'Nan',
        }
        self.project_user_setting_bool_values = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'user': self.user,
            'name': 'project_user_bool_setting',
            'setting_type': 'BOOLEAN',
            'value': False,
            'update_value': True,
            'non_valid_value': 170,
        }
        self.project_user_setting_json_values = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'user': self.user,
            'name': 'project_user_json_setting',
            'setting_type': 'JSON',
            'value': {
                'Example': 'Value',
                'list': [1, 2, 3, 4, 5],
                'level_6': False,
            },
            'update_value': {'Test_more': 'often_always'},
            'non_valid_value': self.project,
        }

        self.settings = [
            self.setting_int_values,
            self.setting_int_values_options,
            self.setting_json_values,
            self.setting_str_values,
            self.setting_str_values_options,
            self.setting_bool_values,
            self.user_setting_int_values,
            self.user_setting_int_values_options,
            self.user_setting_json_values,
            self.user_setting_str_values,
            self.user_setting_str_values_options,
            self.user_setting_bool_values,
            self.project_user_setting_int_values,
            self.project_user_setting_json_values,
            self.project_user_setting_str_values,
            self.project_user_setting_bool_values,
        ]
        for s in self.settings:
            data = {
                'app_name': s['app_name'],
                'name': s['name'],
                'setting_type': s['setting_type'],
                'value': s['value'] if s['setting_type'] != 'JSON' else '',
                'value_json': s['value'] if s['setting_type'] == 'JSON' else {},
            }
            if 'project' in s:
                data['project'] = s['project']
            if 'user' in s:
                data['user'] = s['user']
            self._make_setting(**data)

    def test_get_project_setting(self):
        """Test get_app_setting()"""
        for setting in self.settings:
            data = {
                'app_name': setting['app_name'],
                'setting_name': setting['name'],
            }
            if 'project' in setting:
                data['project'] = setting['project']
            if 'user' in setting:
                data['user'] = setting['user']
            val = app_settings.get_app_setting(**data)
            self.assertEqual(val, setting['value'])

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

    def test_get_project_setting_post_safe(self):
        """Test get_app_setting() with JSON setting and post_safe=True"""
        val = app_settings.get_app_setting(
            app_name=self.setting_json_values['app_name'],
            setting_name=self.setting_json_values['name'],
            project=self.setting_json_values['project'],
            post_safe=True,
        )
        self.assertEqual(type(val), str)

    def test_set_project_setting(self):
        """Test set_app_setting()"""

        for setting in self.settings:
            data = {
                'app_name': setting['app_name'],
                'setting_name': setting['name'],
            }
            if 'project' in setting:
                data['project'] = setting['project']
            if 'user' in setting:
                data['user'] = setting['user']

            update_data = dict(data)
            update_data['value'] = setting['update_value']

            ret = app_settings.set_app_setting(**update_data)
            self.assertEqual(ret, True)

            val = app_settings.get_app_setting(**data)
            self.assertEqual(val, setting['update_value'])

    def test_set_project_setting_unchanged(self):
        """Test set_app_setting() with an unchanged value"""

        for setting in self.settings:
            data = {
                'app_name': setting['app_name'],
                'setting_name': setting['name'],
            }
            if 'project' in setting:
                data['project'] = setting['project']
            if 'user' in setting:
                data['user'] = setting['user']

            update_data = dict(data)
            update_data['value'] = setting['value']

            ret = app_settings.set_app_setting(**update_data)
            self.assertEqual(
                ret,
                False,
                msg='setting={}.{}'.format(
                    setting['app_name'], setting['name']
                ),
            )

            val = app_settings.get_app_setting(**data)
            self.assertEqual(
                val,
                setting['value'],
                msg='setting={}.{}'.format(
                    setting['app_name'], setting['name']
                ),
            )

    def test_set_project_setting_new(self):
        """Test set_app_setting() with a new but defined setting"""

        # Assert precondition
        val = AppSetting.objects.get(
            app_plugin=get_app_plugin(EXAMPLE_APP_NAME).get_model(),
            project=self.project,
            name=EXISTING_SETTING,
        ).value
        self.assertEqual(bool(int(val)), False)

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

    def test_set_multi_project_user_settings(self):
        """Test set_app_setting() with multiple instances of a project-user setting"""

        # Set up second user
        new_user = self.make_user('new_user')

        ret = app_settings.set_app_setting(
            app_name=EXAMPLE_APP_NAME,
            setting_name='project_user_string_setting',
            project=self.project,
            user=self.user,
            value=True,
        )
        self.assertEqual(ret, True)

        ret = app_settings.set_app_setting(
            app_name=EXAMPLE_APP_NAME,
            setting_name='project_user_string_setting',
            project=self.project,
            user=new_user,
            value=True,
        )
        self.assertEqual(ret, True)

    def test_validator(self):
        """Test validate_setting() with type BOOLEAN"""
        for setting in self.settings:
            self.assertEqual(
                app_settings.validate_setting(
                    setting['setting_type'],
                    setting['value'],
                    setting.get('options'),
                ),
                True,
            )
            if setting['setting_type'] == 'STRING':
                continue
            with self.assertRaises(ValueError):
                app_settings.validate_setting(
                    setting['setting_type'],
                    setting['non_valid_value'],
                    setting.get('options'),
                )

    def test_validate_project_setting_int(self):
        """Test validate_setting() with type INTEGER"""
        self.assertEqual(
            app_settings.validate_setting('INTEGER', 170, None), True
        )
        # NOTE: String is also OK if it corresponds to an int
        self.assertEqual(
            app_settings.validate_setting('INTEGER', '170', None), True
        )

        with self.assertRaises(ValueError):
            app_settings.validate_setting('INTEGER', 'not an integer', None)

    def test_validate_project_setting_invalid(self):
        """Test validate_setting() with an invalid type"""
        with self.assertRaises(ValueError):
            app_settings.validate_setting('INVALID_TYPE', 'value', None)

    def test_get_setting_def_plugin(self):
        """Test get_setting_def() with a plugin"""
        app_plugin = get_app_plugin(EXAMPLE_APP_NAME)
        expected = {
            'scope': APP_SETTING_SCOPE_PROJECT,
            'type': 'STRING',
            'label': 'String setting',
            'default': '',
            'description': 'Example string project setting',
            'placeholder': 'Example string',
            'user_modifiable': True,
        }
        s_def = app_settings.get_setting_def(
            'project_str_setting', plugin=app_plugin
        )
        self.assertEqual(s_def, expected)

    def test_get_setting_def_app_name(self):
        """Test get_setting_def() with an app name"""
        expected = {
            'scope': APP_SETTING_SCOPE_PROJECT,
            'type': 'STRING',
            'label': 'String setting',
            'default': '',
            'description': 'Example string project setting',
            'placeholder': 'Example string',
            'user_modifiable': True,
        }
        s_def = app_settings.get_setting_def(
            'project_str_setting', app_name=EXAMPLE_APP_NAME
        )
        self.assertEqual(s_def, expected)

    def test_get_setting_def_user(self):
        """Test get_setting_def() with a user setting"""
        expected = {
            'scope': APP_SETTING_SCOPE_USER,
            'type': 'STRING',
            'label': 'String setting',
            'default': '',
            'description': 'Example string user setting',
            'placeholder': 'Example string',
            'user_modifiable': True,
        }
        s_def = app_settings.get_setting_def(
            'user_str_setting', app_name=EXAMPLE_APP_NAME
        )
        self.assertEqual(s_def, expected)

    def test_get_setting_def_invalid(self):
        """Test get_setting_def() with innvalid input"""
        with self.assertRaises(ValueError):
            app_settings.get_setting_def(
                'non_existing_setting', app_name=EXAMPLE_APP_NAME
            )

        with self.assertRaises(ValueError):
            app_settings.get_setting_def(
                'project_str_setting', app_name='non_existing_app_name'
            )

        # Both app_name and plugin unset
        with self.assertRaises(ValueError):
            app_settings.get_setting_def('project_str_setting')

    def test_get_setting_defs_project(self):
        """Test get_setting_defs() with the PROJECT scope"""
        expected = {
            'project_str_setting': {
                'scope': APP_SETTING_SCOPE_PROJECT,
                'type': 'STRING',
                'label': 'String setting',
                'default': '',
                'description': 'Example string project setting',
                'placeholder': 'Example string',
                'user_modifiable': True,
            },
            'project_int_setting': {
                'scope': APP_SETTING_SCOPE_PROJECT,
                'type': 'INTEGER',
                'label': 'Integer setting',
                'default': 0,
                'description': 'Example integer project setting',
                'placeholder': 0,
                'user_modifiable': True,
                'widget_attrs': {'class': 'text-success'},
            },
            'project_str_setting_options': {
                'scope': APP_SETTING_SCOPE_PROJECT,
                'type': 'STRING',
                'label': 'String setting',
                'default': 'string1',
                'options': ['string1', 'string2'],
                'description': 'Example string project setting with options',
                'user_modifiable': True,
            },
            'project_int_setting_options': {
                'scope': APP_SETTING_SCOPE_PROJECT,
                'type': 'INTEGER',
                'label': 'Integer setting',
                'default': 0,
                'options': [0, 1],
                'description': 'Example integer project setting with options',
                'user_modifiable': True,
                'widget_attrs': {'class': 'text-success'},
            },
            'project_bool_setting': {
                'scope': APP_SETTING_SCOPE_PROJECT,
                'type': 'BOOLEAN',
                'label': 'Boolean setting',
                'default': False,
                'description': 'Example boolean project setting',
                'user_modifiable': True,
            },
            'project_global_setting': {
                'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
                'type': 'BOOLEAN',
                'label': 'Global boolean setting',
                'default': False,
                'description': 'Example global boolean project setting',
                'user_modifiable': True,
                'local': False,
            },
            'project_json_setting': {
                'scope': APP_SETTING_SCOPE_PROJECT,
                'type': 'JSON',
                'label': 'JSON setting',
                'default': {
                    'Example': 'Value',
                    'list': [1, 2, 3, 4, 5],
                    'level_6': False,
                },
                'description': 'Example JSON project setting',
                'user_modifiable': True,
                'widget_attrs': {'class': 'text-danger'},
            },
            'project_hidden_setting': {
                'scope': APP_SETTING_SCOPE_PROJECT,
                'type': 'STRING',
                'label': 'Hidden setting',
                'default': '',
                'description': 'Example hidden project setting',
                'user_modifiable': False,
            },
            'project_hidden_json_setting': {
                'scope': APP_SETTING_SCOPE_PROJECT,
                'type': 'JSON',
                'label': 'Hidden JSON setting',
                'description': 'Example hidden JSON project setting',
                'user_modifiable': False,
            },
        }
        defs = app_settings.get_setting_defs(
            APP_SETTING_SCOPE_PROJECT, app_name=EXAMPLE_APP_NAME
        )
        self.assertEqual(defs, expected)

    def test_get_setting_defs_user(self):
        """Test get_setting_defs() with the USER scope"""
        expected = {
            'user_str_setting': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'STRING',
                'label': 'String setting',
                'default': '',
                'description': 'Example string user setting',
                'placeholder': 'Example string',
                'user_modifiable': True,
            },
            'user_int_setting': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'INTEGER',
                'label': 'Integer setting',
                'default': 0,
                'description': 'Example integer user setting',
                'placeholder': 0,
                'user_modifiable': True,
                'widget_attrs': {'class': 'text-success'},
            },
            'user_str_setting_options': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'STRING',
                'label': 'String setting',
                'default': 'string1',
                'options': ['string1', 'string2'],
                'description': 'Example string user setting with options',
                'user_modifiable': True,
            },
            'user_int_setting_options': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'INTEGER',
                'label': 'Integer setting',
                'default': 0,
                'options': [0, 1],
                'description': 'Example integer user setting with options',
                'user_modifiable': True,
                'widget_attrs': {'class': 'text-success'},
            },
            'user_bool_setting': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'BOOLEAN',
                'label': 'Boolean setting',
                'default': False,
                'description': 'Example boolean user setting',
                'user_modifiable': True,
            },
            'user_json_setting': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'JSON',
                'label': 'JSON setting',
                'default': {
                    'Example': 'Value',
                    'list': [1, 2, 3, 4, 5],
                    'level_6': False,
                },
                'description': 'Example JSON user setting',
                'user_modifiable': True,
                'widget_attrs': {'class': 'text-danger'},
            },
            'user_hidden_setting': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'STRING',
                'default': '',
                'description': 'Example hidden user setting',
                'user_modifiable': False,
            },
        }
        defs = app_settings.get_setting_defs(
            APP_SETTING_SCOPE_USER, app_name=EXAMPLE_APP_NAME
        )
        self.assertEqual(defs, expected)

    def test_get_setting_defs_project_user(self):
        """Test get_setting_defs() with the PROJECT_USER scope"""
        expected = {
            'project_user_string_setting': {
                'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT_USER'],
                'type': 'STRING',
                'default': '',
                'description': 'Example string project user setting',
            },
            'project_user_int_setting': {
                'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT_USER'],
                'type': 'INTEGER',
                'default': '',
                'description': 'Example int project user setting',
            },
            'project_user_bool_setting': {
                'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT_USER'],
                'type': 'BOOLEAN',
                'default': '',
                'description': 'Example bool project user setting',
            },
            'project_user_json_setting': {
                'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT_USER'],
                'type': 'JSON',
                'default': '',
                'description': 'Example json project user setting',
            },
        }
        defs = app_settings.get_setting_defs(
            APP_SETTING_SCOPE_PROJECT_USER, app_name=EXAMPLE_APP_NAME
        )
        self.assertEqual(defs, expected)

    def test_get_setting_defs_modifiable(self):
        """Test get_setting_defs() with the user_modifiable arg"""
        defs = app_settings.get_setting_defs(
            APP_SETTING_SCOPE_PROJECT, app_name=EXAMPLE_APP_NAME
        )
        self.assertEqual(len(defs), 9)
        defs = app_settings.get_setting_defs(
            APP_SETTING_SCOPE_PROJECT,
            app_name=EXAMPLE_APP_NAME,
            user_modifiable=True,
        )
        self.assertEqual(len(defs), 7)

    def test_get_setting_defs_invalid_scope(self):
        """Test get_setting_defs() with an invalid scope"""
        with self.assertRaises(ValueError):
            app_settings.get_setting_defs(
                'Ri4thai8aez5ooRa', app_name=EXAMPLE_APP_NAME
            )

    def test_get_all_defaults_project(self):
        """Test get_all_defaults() with the PROJECT scope"""
        prefix = 'settings.{}.'.format(EXAMPLE_APP_NAME)
        defaults = app_settings.get_all_defaults(APP_SETTING_SCOPE_PROJECT)
        self.assertEqual(defaults[prefix + 'project_str_setting'], '')
        self.assertEqual(defaults[prefix + 'project_int_setting'], 0)
        self.assertEqual(defaults[prefix + 'project_bool_setting'], False)
        self.assertEqual(
            defaults[prefix + 'project_json_setting'],
            {'Example': 'Value', 'list': [1, 2, 3, 4, 5], 'level_6': False},
        )

    def test_get_all_defaults_user(self):
        """Test get_all_defaults() with the USER scope"""
        prefix = 'settings.{}.'.format(EXAMPLE_APP_NAME)
        defaults = app_settings.get_all_defaults(APP_SETTING_SCOPE_USER)
        self.assertEqual(defaults[prefix + 'user_str_setting'], '')
        self.assertEqual(defaults[prefix + 'user_int_setting'], 0)
        self.assertEqual(defaults[prefix + 'user_bool_setting'], False)
        self.assertEqual(
            defaults[prefix + 'user_json_setting'],
            {'Example': 'Value', 'list': [1, 2, 3, 4, 5], 'level_6': False},
        )

    def test_delete_setting_scope_user_params_none(self):
        self.assertEqual(AppSetting.objects.count(), 16)
        app_settings.delete_setting(EXAMPLE_APP_NAME, 'user_str_setting')
        self.assertEqual(AppSetting.objects.count(), 15)

    def test_delete_setting_scope_user_params_user(self):
        self.assertEqual(AppSetting.objects.count(), 16)
        app_settings.delete_setting(
            EXAMPLE_APP_NAME, 'user_str_setting', user=self.user
        )
        self.assertEqual(AppSetting.objects.count(), 15)

    def test_delete_setting_scope_user_params_project(self):
        with self.assertRaises(ValueError):
            app_settings.delete_setting(
                EXAMPLE_APP_NAME, 'user_str_setting', project=self.project
            )

    def test_delete_setting_scope_user_params_user_project(self):
        with self.assertRaises(ValueError):
            app_settings.delete_setting(
                EXAMPLE_APP_NAME,
                'user_str_setting',
                project=self.project,
                user=self.user,
            )

    def test_delete_setting_scope_project_user_params_none(self):
        self.assertEqual(AppSetting.objects.count(), 16)
        app_settings.delete_setting(
            EXAMPLE_APP_NAME, 'project_user_string_setting'
        )
        self.assertEqual(AppSetting.objects.count(), 15)

    def test_delete_setting_scope_project_user_params_user(self):
        self.assertEqual(AppSetting.objects.count(), 16)
        app_settings.delete_setting(
            EXAMPLE_APP_NAME,
            'project_user_string_setting',
            project=self.project,
            user=self.user,
        )
        self.assertEqual(AppSetting.objects.count(), 15)

    def test_delete_setting_scope_project_user_params_project(self):
        self.assertEqual(AppSetting.objects.count(), 16)
        app_settings.delete_setting(
            EXAMPLE_APP_NAME,
            'project_user_string_setting',
            project=self.project,
            user=self.user,
        )
        self.assertEqual(AppSetting.objects.count(), 15)

    def test_delete_setting_scope_project_user_params_user_project(self):
        self.assertEqual(AppSetting.objects.count(), 16)
        app_settings.delete_setting(
            EXAMPLE_APP_NAME,
            'project_user_string_setting',
            project=self.project,
            user=self.user,
        )
        self.assertEqual(AppSetting.objects.count(), 15)

    def test_delete_setting_scope_project_params_none(self):
        self.assertEqual(AppSetting.objects.count(), 16)
        app_settings.delete_setting(
            EXAMPLE_APP_NAME,
            'project_str_setting',
        )
        self.assertEqual(AppSetting.objects.count(), 15)

    def test_delete_setting_scope_project_params_user(self):
        with self.assertRaises(ValueError):
            app_settings.delete_setting(
                EXAMPLE_APP_NAME,
                'project_str_setting',
                user=self.user,
            )

    def test_delete_setting_scope_project_params_project(self):
        self.assertEqual(AppSetting.objects.count(), 16)
        app_settings.delete_setting(
            EXAMPLE_APP_NAME,
            'project_str_setting',
            project=self.project,
        )
        self.assertEqual(AppSetting.objects.count(), 15)

    def test_delete_setting_scope_project_params_user_project(self):
        with self.assertRaises(ValueError):
            app_settings.delete_setting(
                EXAMPLE_APP_NAME,
                'project_str_setting',
                project=self.project,
                user=self.user,
            )
