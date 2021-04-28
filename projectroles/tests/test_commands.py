"""Tests for management commands in the projectroles Django app"""

import os
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.test import override_settings
from djangoplugins.models import Plugin

from test_plus.test import TestCase

from projectroles.management.commands.cleanappsettings import START_MSG, END_MSG
from projectroles.management.commands.batchupdateroles import (
    Command as BatchUpdateRolesCommand,
)
from projectroles.models import (
    Role,
    RoleAssignment,
    ProjectInvite,
    AppSetting,
    SODAR_CONSTANTS,
)
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
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
CLEAN_LOG_PREFIX = 'INFO:projectroles.management.commands.cleanappsettings:'


class BatchUpdateRolesMixin:
    """Helpers for batchupdateroles testing"""

    file = None

    def _write_file(self, data):
        """Write data to temporary CSV file"""
        if not isinstance(data[0], list):
            data = [data]
        self.file.write(
            bytes('\n'.join([';'.join(r) for r in data]), encoding='utf-8')
        )
        self.file.close()


class TestBatchUpdateRoles(
    ProjectMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
    BatchUpdateRolesMixin,
    TestCase,
):
    """Tests for batchupdateroles command"""

    def setUp(self):
        super().setUp()

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
        self.user_owner_cat = self.make_user('owner_cat')
        self.user_owner_cat.email = 'cat_owner_user@example.com'
        self.user_owner_cat.save()

        # Init projects
        self.category = self._make_project(
            'top_category', PROJECT_TYPE_CATEGORY, None
        )
        self.cat_owner_as = self._make_assignment(
            self.category, self.user_owner_cat, self.role_owner
        )

        self.project = self._make_project(
            'sub_project', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self._make_assignment(
            self.project, self.user_owner, self.role_owner
        )

        # Init command class
        self.command = BatchUpdateRolesCommand()

        # Init file
        self.file = NamedTemporaryFile(delete=False)

    def tearDown(self):
        if self.file:
            os.remove(self.file.name)
        super().tearDown()

    def test_invite(self):
        """Test inviting a single user via email to project"""
        p_uuid = str(self.project.sodar_uuid)
        email = 'new@example.com'

        # Assert preconditions
        self.assertEqual(ProjectInvite.objects.count(), 0)

        self._write_file([p_uuid, email, PROJECT_ROLE_GUEST])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        # Assert postconditions
        self.assertEqual(ProjectInvite.objects.count(), 1)
        invite = ProjectInvite.objects.first()
        self.assertEqual(invite.email, email)
        self.assertEqual(invite.project, self.project)
        self.assertEqual(invite.role, self.role_guest)
        self.assertEqual(invite.issuer, self.user_owner)
        self.assertEqual(len(mail.outbox), 1)

    def test_invite_existing(self):
        """Test inviting a user when they already have an active invite"""
        p_uuid = str(self.project.sodar_uuid)
        email = 'new@example.com'
        self._make_invite(email, self.project, self.role_guest, self.user_owner)

        # Assert preconditions
        self.assertEqual(ProjectInvite.objects.count(), 1)

        self._write_file([p_uuid, email, PROJECT_ROLE_GUEST])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        # Assert postconditions
        self.assertEqual(ProjectInvite.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_invite_multi_user(self):
        """Test inviting multiple users"""
        p_uuid = str(self.project.sodar_uuid)
        email = 'new@example.com'
        email2 = 'new2@example.com'

        # Assert preconditions
        self.assertEqual(ProjectInvite.objects.count(), 0)

        fd = [
            [p_uuid, email, PROJECT_ROLE_GUEST],
            [p_uuid, email2, PROJECT_ROLE_GUEST],
        ]
        self._write_file(fd)
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        # Assert postconditions
        self.assertEqual(ProjectInvite.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_invite_multi_project(self):
        """Test inviting user to multiple projects"""
        c_uuid = str(self.category.sodar_uuid)
        p_uuid = str(self.project.sodar_uuid)
        email = 'new@example.com'

        # Assert preconditions
        self.assertEqual(ProjectInvite.objects.count(), 0)

        fd = [
            [c_uuid, email, PROJECT_ROLE_GUEST],
            [p_uuid, email, PROJECT_ROLE_GUEST],
        ]
        self._write_file(fd)
        # NOTE: Using user_owner_cat as they have perms for both projects
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner_cat.username}
        )

        # Assert postconditions
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.category).count(), 1
        )
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 1
        )
        self.assertEqual(len(mail.outbox), 2)

    def test_invite_owner(self):
        """Test inviting an owner (should fail)"""
        p_uuid = str(self.project.sodar_uuid)
        email = 'new@example.com'
        self._write_file([p_uuid, email, PROJECT_ROLE_OWNER])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        # Assert postconditions
        self.assertEqual(ProjectInvite.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_invite_delegate(self):
        """Test inviting a delegate"""
        p_uuid = str(self.project.sodar_uuid)
        email = 'new@example.com'
        self._write_file([p_uuid, email, PROJECT_ROLE_DELEGATE])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        # Assert postconditions
        self.assertEqual(ProjectInvite.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(PROJECTROLES_DELEGATE_LIMIT=2)
    def test_invite_delegate_no_perms(self):
        """Test inviting a delegate without perms (should fail)"""
        p_uuid = str(self.project.sodar_uuid)
        email = 'new@example.com'
        user_delegate = self.make_user('delegate')
        self._make_assignment(self.project, user_delegate, self.role_delegate)
        self._write_file([p_uuid, email, PROJECT_ROLE_DELEGATE])
        self.command.handle(
            **{'file': self.file.name, 'issuer': user_delegate.username}
        )

        # Assert postconditions
        self.assertEqual(ProjectInvite.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_invite_delegate_limit(self):
        """Test inviting a delegate with limit reached (should fail)"""
        p_uuid = str(self.project.sodar_uuid)
        email = 'new@example.com'
        user_delegate = self.make_user('delegate')
        self._make_assignment(self.project, user_delegate, self.role_delegate)

        self._write_file([p_uuid, email, PROJECT_ROLE_DELEGATE])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        # Assert postconditions
        self.assertEqual(ProjectInvite.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_role_add(self):
        """Test adding role to user already in system"""
        p_uuid = str(self.project.sodar_uuid)
        email = 'new@example.com'
        user_new = self.make_user('user_new')
        user_new.email = email
        user_new.save()

        # Assert preconditions
        self.assertEqual(ProjectInvite.objects.count(), 0)

        self._write_file([p_uuid, email, PROJECT_ROLE_GUEST])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        # Assert postconditions
        self.assertEqual(ProjectInvite.objects.count(), 0)
        role_as = RoleAssignment.objects.get(
            project=self.project, user=user_new
        )
        self.assertEqual(role_as.role, self.role_guest)
        self.assertEqual(len(mail.outbox), 1)

    def test_role_update(self):
        """Test updating an existing role for user"""
        p_uuid = str(self.project.sodar_uuid)
        email = 'new@example.com'
        user_new = self.make_user('user_new')
        user_new.email = email
        user_new.save()
        role_as = self._make_assignment(self.project, user_new, self.role_guest)

        # Assert preconditions
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, user=user_new
            ).count(),
            1,
        )

        self._write_file([p_uuid, email, PROJECT_ROLE_CONTRIBUTOR])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        # Assert postconditions
        self.assertEqual(ProjectInvite.objects.count(), 0)
        role_as.refresh_from_db()
        self.assertEqual(role_as.role, self.role_contributor)
        self.assertEqual(len(mail.outbox), 1)

    def test_role_update_owner(self):
        """Test updating the role of current owner (should fail)"""
        p_uuid = str(self.project.sodar_uuid)
        email = 'owner@example.com'
        self.user_owner.email = email
        self.user_owner.save()

        self._write_file([p_uuid, email, PROJECT_ROLE_CONTRIBUTOR])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        # Assert postconditions
        self.assertEqual(ProjectInvite.objects.count(), 0)
        self.owner_as.refresh_from_db()
        self.assertEqual(self.owner_as.role, self.role_owner)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, user=self.user_owner
            ).count(),
            1,
        )
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(PROJECTROLES_DELEGATE_LIMIT=2)
    def test_role_update_delegate_no_perms(self):
        """Test updating a delegate role without perms (should fail)"""
        p_uuid = str(self.project.sodar_uuid)
        email = 'new@example.com'
        user_new = self.make_user('user_new')
        user_new.email = email
        user_new.save()
        role_as = self._make_assignment(self.project, user_new, self.role_guest)
        user_delegate = self.make_user('delegate')
        self._make_assignment(self.project, user_delegate, self.role_delegate)

        self._write_file([p_uuid, email, PROJECT_ROLE_DELEGATE])
        self.command.handle(
            **{'file': self.file.name, 'issuer': user_delegate.username}
        )

        # Assert postconditions
        self.assertEqual(ProjectInvite.objects.count(), 0)
        role_as.refresh_from_db()
        self.assertEqual(role_as.role, self.role_guest)
        self.assertEqual(len(mail.outbox), 0)

    def test_role_update_delegate_limit(self):
        """Test updating a delegate role with limit reached (should fail)"""
        p_uuid = str(self.project.sodar_uuid)
        email = 'new@example.com'
        user_new = self.make_user('user_new')
        user_new.email = email
        user_new.save()
        role_as = self._make_assignment(self.project, user_new, self.role_guest)
        user_delegate = self.make_user('delegate')
        self._make_assignment(self.project, user_delegate, self.role_delegate)

        self._write_file([p_uuid, email, PROJECT_ROLE_DELEGATE])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        # Assert postconditions
        self.assertEqual(ProjectInvite.objects.count(), 0)
        role_as.refresh_from_db()
        self.assertEqual(role_as.role, self.role_guest)
        self.assertEqual(len(mail.outbox), 0)

    def test_role_add_inherited_owner(self):
        """Test adding a role of an inherited owner (should fail)"""
        p_uuid = str(self.project.sodar_uuid)
        email = self.user_owner_cat.email

        self._write_file([p_uuid, email, PROJECT_ROLE_CONTRIBUTOR])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        # Assert postconditions
        self.assertEqual(ProjectInvite.objects.count(), 0)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, user=self.user_owner_cat
            ).count(),
            0,
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_invite_and_update(self):
        """Test inviting and updating in one command"""
        p_uuid = str(self.project.sodar_uuid)
        email = 'new@example.com'
        user_new = self.make_user('user_new')
        user_new.email = email
        user_new.save()
        email2 = 'new2@example.com'

        # Assert preconditions
        self.assertEqual(ProjectInvite.objects.count(), 0)

        fd = [
            [p_uuid, email, PROJECT_ROLE_GUEST],
            [p_uuid, email2, PROJECT_ROLE_GUEST],
        ]
        self._write_file(fd)
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        # Assert postconditions
        self.assertEqual(ProjectInvite.objects.count(), 1)
        self.assertIsNotNone(
            RoleAssignment.objects.filter(
                project=self.project, user=user_new
            ).count(),
            1,
        )
        self.assertEqual(len(mail.outbox), 2)

    def test_command_no_issuer(self):
        """Test invite without issuer (should go under admin)"""
        admin = self.make_user(settings.PROJECTROLES_DEFAULT_ADMIN)
        admin.is_superuser = True
        admin.save()
        p_uuid = str(self.project.sodar_uuid)
        email = 'new@example.com'

        self._write_file([p_uuid, email, PROJECT_ROLE_GUEST])
        self.command.handle(**{'file': self.file.name, 'issuer': None})

        # Assert postconditions
        invite = ProjectInvite.objects.first()
        self.assertEqual(invite.issuer, admin)

    def test_command_no_perms(self):
        """Test invite with issuer who lacks permissions for a project"""
        issuer = self.make_user('issuer')
        p_uuid = str(self.project.sodar_uuid)
        email = 'new@example.com'

        self._write_file([p_uuid, email, PROJECT_ROLE_GUEST])
        self.command.handle(
            **{'file': self.file.name, 'issuer': issuer.username}
        )

        # Assert postconditions
        self.assertEqual(ProjectInvite.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)


class TestCleanAppSettings(
    ProjectMixin, RoleAssignmentMixin, AppSettingMixin, TestCase
):
    """Tests for cleanappsettings command and associated functions"""

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

    def test_command_cleanappsettings(self):
        """Test the cleanappsetting commmand"""
        self._make_undefined_setting()
        self.assertEqual(AppSetting.objects.count(), 6)

        with self.assertLogs(
            'projectroles.management.commands.cleanappsettings', level='INFO'
        ) as cm:
            call_command('cleanappsettings')
            self.assertEqual(
                cm.output,
                [
                    CLEAN_LOG_PREFIX + START_MSG,
                    (
                        CLEAN_LOG_PREFIX
                        + 'Deleting "settings.example_project_app.ghost" '
                        'from project "{}"'.format(self.project.title)
                    ),
                    CLEAN_LOG_PREFIX + END_MSG,
                ],
            )
        self.assertEqual(AppSetting.objects.count(), 5)
