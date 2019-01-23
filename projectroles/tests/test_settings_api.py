"""Tests for the project settings API in the projectroles app"""

from test_plus.test import TestCase

from ..models import Role, ProjectSetting, SODAR_CONSTANTS
from ..plugins import get_app_plugin
from ..project_settings import get_project_setting, set_project_setting, \
    validate_project_setting
from .test_models import ProjectMixin, RoleAssignmentMixin, ProjectSettingMixin


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


# Local settings
EXISTING_SETTING = 'example_setting'
EXAMPLE_APP_NAME = 'example_project_app'


class TestProjectSettingAPI(
        ProjectMixin, RoleAssignmentMixin, ProjectSettingMixin, TestCase):
    """Tests for the ProjectSetting API"""
    # NOTE: This assumes an example app is available

    def setUp(self):
        # Init project
        self.project = self._make_project(
            title='TestProject',
            type=PROJECT_TYPE_PROJECT,
            parent=None)

        # Init role
        self.role_owner = Role.objects.get(
            name=PROJECT_ROLE_OWNER)

        # Init user & role
        self.user = self.make_user('owner')
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner)

        # Init test setting
        self.setting_str = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            project=self.project,
            name='str_setting',
            setting_type='STRING',
            value='test')

        # Init integer setting
        self.setting_int = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            project=self.project,
            name='int_setting',
            setting_type='INTEGER',
            value=170)

        # Init boolean setting
        self.setting_bool = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            project=self.project,
            name='bool_setting',
            setting_type='BOOLEAN',
            value=True)

    def test_get_project_setting(self):
        """Test get_project_setting()"""
        val = get_project_setting(
            project=self.project,
            app_name=EXAMPLE_APP_NAME,
            setting_name='str_setting')
        self.assertEqual(self.setting_str.value, val)

    def test_get_project_setting_default(self):
        """Test get_project_setting() with default value for existing setting"""
        app_plugin = get_app_plugin(EXAMPLE_APP_NAME)
        default_val = app_plugin.project_settings[EXISTING_SETTING]['default']

        val = get_project_setting(
            project=self.project,
            app_name=EXAMPLE_APP_NAME,
            setting_name=EXISTING_SETTING)

        self.assertEqual(val, default_val)

    def test_get_project_setting_nonexisting(self):
        """Test get_project_setting() with an non-existing setting"""
        with self.assertRaises(KeyError):
            get_project_setting(
                project=self.project,
                app_name=EXAMPLE_APP_NAME,
                setting_name='NON-EXISTING SETTING')

    def test_set_project_setting(self):
        """Test set_project_setting()"""

        # Assert postcondition
        val = get_project_setting(
            project=self.project,
            app_name=EXAMPLE_APP_NAME,
            setting_name='str_setting')
        self.assertEqual('test', val)

        ret = set_project_setting(
            project=self.project,
            app_name=EXAMPLE_APP_NAME,
            setting_name='str_setting',
            value='updated')

        self.assertEqual(ret, True)

        # Assert postcondition
        val = get_project_setting(
            project=self.project,
            app_name=EXAMPLE_APP_NAME,
            setting_name='str_setting')
        self.assertEqual('updated', val)

    def test_set_project_setting_unchanged(self):
        """Test set_project_setting() with an unchnaged value"""

        # Assert postcondition
        val = get_project_setting(
            project=self.project,
            app_name=EXAMPLE_APP_NAME,
            setting_name='str_setting')
        self.assertEqual('test', val)

        ret = set_project_setting(
            project=self.project,
            app_name=EXAMPLE_APP_NAME,
            setting_name='str_setting',
            value='test')

        self.assertEqual(ret, False)

        # Assert postcondition
        val = get_project_setting(
            project=self.project,
            app_name=EXAMPLE_APP_NAME,
            setting_name='str_setting')
        self.assertEqual('test', val)

    def test_set_project_setting_new(self):
        """Test set_project_setting() with a new but defined setting"""

        # Assert precondition
        with self.assertRaises(ProjectSetting.DoesNotExist):
            ProjectSetting.objects.get(
                app_plugin=get_app_plugin(EXAMPLE_APP_NAME).get_model(),
                project=self.project,
                name=EXISTING_SETTING)

        ret = set_project_setting(
            project=self.project,
            app_name=EXAMPLE_APP_NAME,
            setting_name=EXISTING_SETTING,
            value=True)

        # Asset postconditions
        self.assertEqual(ret, True)
        val = get_project_setting(
            project=self.project,
            app_name=EXAMPLE_APP_NAME,
            setting_name=EXISTING_SETTING)
        self.assertEqual(True, val)

        setting = ProjectSetting.objects.get(
            app_plugin=get_app_plugin(EXAMPLE_APP_NAME).get_model(),
            project=self.project,
            name=EXISTING_SETTING)
        self.assertIsInstance(setting, ProjectSetting)

    def test_set_project_setting_undefined(self):
        """Test set_project_setting() with an undefined setting (should fail)"""
        with self.assertRaises(KeyError):
            set_project_setting(
                project=self.project,
                app_name=EXAMPLE_APP_NAME,
                setting_name='new_setting',
                value='new')

    def test_validate_project_setting_bool(self):
        """Test validate_project_setting() with type BOOLEAN"""
        self.assertEqual(validate_project_setting('BOOLEAN', True), True)

        with self.assertRaises(ValueError):
            validate_project_setting('BOOLEAN', 'not a boolean')

    def test_validate_project_setting_int(self):
        """Test validate_project_setting() with type INTEGER"""
        self.assertEqual(validate_project_setting('INTEGER', 170), True)
        # NOTE: String is also OK if it corresponds to an int
        self.assertEqual(validate_project_setting('INTEGER', '170'), True)

        with self.assertRaises(ValueError):
            validate_project_setting('INTEGER', 'not an integer')

    def test_validate_project_setting_invalid(self):
        """Test validate_project_setting() with an invalid type"""
        with self.assertRaises(ValueError):
            validate_project_setting('INVALID_TYPE', 'value')
