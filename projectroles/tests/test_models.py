"""Tests for models in the projectroles Django app"""

import uuid

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.urls import reverse
from django.utils import timezone
from django.test import override_settings

from test_plus.test import TestCase

from projectroles.models import (
    Project,
    Role,
    RoleAssignment,
    ProjectInvite,
    AppSetting,
    ProjectUserTag,
    RemoteSite,
    RemoteProject,
    SODAR_CONSTANTS,
    PROJECT_TAG_STARRED,
)
from projectroles.plugins import get_app_plugin
from projectroles.utils import build_secret


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
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']


# Settings
INVITE_EXPIRY_DAYS = settings.PROJECTROLES_INVITE_EXPIRY_DAYS


# Local constants
SECRET = 'rsd886hi8276nypuvw066sbvv0rb2a6x'
EXAMPLE_APP_NAME = 'example_project_app'
REMOTE_SITE_NAME = 'Test site'
REMOTE_SITE_URL = 'https://sodar.example.org'
REMOTE_SITE_SECRET = build_secret()
REMOTE_SITE_USER_DISPLAY = True


class ProjectMixin:
    """Helper mixin for Project creation"""

    @classmethod
    def _make_project(
        cls,
        title,
        type,
        parent,
        description='',
        submit_status=SUBMIT_STATUS_OK,
        readme=None,
        public_guest_access=False,
        sodar_uuid=None,
    ):
        """Make and save a Project"""
        values = {
            'title': title,
            'type': type,
            'parent': parent,
            'submit_status': submit_status,
            'description': description,
            'readme': readme,
            'public_guest_access': public_guest_access,
        }
        if sodar_uuid:
            values['sodar_uuid'] = sodar_uuid
        project = Project(**values)
        project.save()
        return project


class ProjectInviteMixin:
    """Helper mixin for ProjectInvite creation"""

    @classmethod
    def _make_invite(
        cls,
        email,
        project,
        role,
        issuer,
        message='',
        date_expire=None,
        secret=None,
    ):
        """Make and save a ProjectInvite"""
        values = {
            'email': email,
            'project': project,
            'role': role,
            'issuer': issuer,
            'message': message,
            'date_expire': date_expire
            if date_expire
            else (timezone.now() + timezone.timedelta(days=INVITE_EXPIRY_DAYS)),
            'secret': secret or SECRET,
            'active': True,
        }
        invite = ProjectInvite(**values)
        invite.save()
        return invite


class AppSettingMixin:
    """Helper mixin for AppSetting creation"""

    @classmethod
    def _make_setting(
        cls,
        app_name,
        name,
        setting_type,
        value,
        value_json={},
        user_modifiable=True,
        project=None,
        user=None,
        sodar_uuid=None,
    ):
        """Make and save a AppSetting"""
        values = {
            'app_plugin': None
            if app_name == 'projectroles'
            else get_app_plugin(app_name).get_model(),
            'project': project,
            'name': name,
            'type': setting_type,
            'value': value,
            'value_json': value_json,
            'user_modifiable': user_modifiable,
            'user': user,
        }
        if sodar_uuid:
            values['sodar_uuid'] = sodar_uuid
        setting = AppSetting(**values)
        setting.save()
        return setting


class ProjectUserTagMixin:
    """Helper mixin for ProjectUserTag creation"""

    @classmethod
    def _make_tag(cls, project, user, name):
        """Make and save a ProjectUserTag"""
        values = {'project': project, 'user': user, 'name': name}
        tag = ProjectUserTag(**values)
        tag.save()
        return tag


class RemoteSiteMixin:
    """Helper mixin for RemoteSite creation"""

    @classmethod
    def _make_site(
        cls,
        name,
        url,
        user_display=REMOTE_SITE_USER_DISPLAY,
        mode=SODAR_CONSTANTS['SITE_MODE_TARGET'],
        description='',
        secret=build_secret(),
    ):
        """Make and save a RemoteSite"""
        values = {
            'name': name,
            'url': url,
            'mode': mode,
            'description': description,
            'secret': secret,
            'user_display': user_display,
        }
        site = RemoteSite(**values)
        site.save()
        return site


class RemoteProjectMixin:
    """Helper mixin for RemoteProject creation"""

    @classmethod
    def _make_remote_project(
        cls, project_uuid, site, level, date_access=None, project=None
    ):
        """Make and save a RemoteProject"""
        if isinstance(project_uuid, str):
            project_uuid = uuid.UUID(project_uuid)

        values = {
            'project_uuid': project_uuid,
            'site': site,
            'level': level,
            'date_access': date_access,
            'project': project
            if project
            else Project.objects.filter(sodar_uuid=project_uuid).first(),
        }
        remote_project = RemoteProject(**values)
        remote_project.save()
        return remote_project


class RemoteTargetMixin(RemoteSiteMixin, RemoteProjectMixin):
    """Helper mixin for setting up the site as TARGET for testing"""

    @classmethod
    def _set_up_as_target(cls, projects):
        """Set up current site as a target site"""
        source_site = cls._make_site(
            name='Test Source',
            url='http://0.0.0.0',
            mode=SITE_MODE_SOURCE,
            description='',
            secret=build_secret(),
        )

        remote_projects = []

        for project in projects:
            remote_projects.append(
                cls._make_remote_project(
                    project_uuid=project.sodar_uuid,
                    project=project,
                    site=source_site,
                    level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
                )
            )

        return source_site, remote_projects


class SodarUserMixin:
    """Helper mixin for LDAP SodarUser creation"""

    def _make_sodar_user(
        self,
        username,
        name,
        first_name,
        last_name,
        email=None,
        sodar_uuid=None,
        password='password',
    ):
        user = self.make_user(username, password)
        user.name = name
        user.first_name = first_name
        user.last_name = last_name

        if email:
            user.email = email

        if sodar_uuid:
            user.sodar_uuid = sodar_uuid

        user.save()
        return user


class TestProject(ProjectMixin, TestCase):
    """Tests for model.Project"""

    def setUp(self):
        # Top level category
        self.category_top = self._make_project(
            title='TestCategoryTop', type=PROJECT_TYPE_CATEGORY, parent=None
        )
        # Subproject under category_top
        self.project_sub = self._make_project(
            title='TestProjectSub',
            type=PROJECT_TYPE_PROJECT,
            parent=self.category_top,
        )
        # Top level project
        self.project_top = self._make_project(
            title='TestProjectTop', type=PROJECT_TYPE_PROJECT, parent=None
        )

    def test_initialization(self):
        """Test Project initialization"""
        expected = {
            'id': self.project_sub.pk,
            'title': 'TestProjectSub',
            'type': PROJECT_TYPE_PROJECT,
            'parent': self.category_top.pk,
            'submit_status': SUBMIT_STATUS_OK,
            'full_title': 'TestCategoryTop / TestProjectSub',
            'sodar_uuid': self.project_sub.sodar_uuid,
            'description': '',
            'public_guest_access': False,
            'has_public_children': False,
        }
        model_dict = model_to_dict(self.project_sub)
        # HACK: Can't compare markupfields like this. Better solution?
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

    def test__str__(self):
        """Test Project __str__()"""
        expected = 'TestCategoryTop / TestProjectSub'
        self.assertEqual(str(self.project_sub), expected)

    def test__repr__(self):
        """Test Project __repr__()"""
        expected = "Project('TestProjectSub', 'PROJECT', " "'TestCategoryTop')"
        self.assertEqual(repr(self.project_sub), expected)

    def test_validate_parent(self):
        """Test parent ForeignKey validation: project can't be its own
        parent"""
        with self.assertRaises(ValidationError):
            project_tmp = self.project_top
            project_tmp.parent = project_tmp
            project_tmp.save()

    def test_validate_title(self):
        """Test title validation: title can't be equal between subproject and
        parent"""
        with self.assertRaises(ValidationError):
            self._make_project(
                title='TestCategoryTop',
                type=PROJECT_TYPE_PROJECT,
                parent=self.category_top,
            )

    def test_validate_parent_type(self):
        """Test parent type validation"""
        with self.assertRaises(ValidationError):
            self._make_project(
                title='FailProject',
                type=PROJECT_TYPE_PROJECT,
                parent=self.project_top,
            )

    def test_get_absolute_url(self):
        """Test get_absolute_url()"""
        expected_url = reverse(
            'projectroles:detail',
            kwargs={'project': self.project_sub.sodar_uuid},
        )
        self.assertEqual(self.project_sub.get_absolute_url(), expected_url)

    def test_get_children_top(self):
        """Test children getting function for top category"""
        children = self.category_top.get_children()
        self.assertEqual(children[0], self.project_sub)

    def test_get_children_sub(self):
        """Test children getting function for sub project"""
        children = self.project_sub.get_children()
        self.assertEqual(children.count(), 0)

    def test_get_depth_top(self):
        """Test project depth getting function for top category"""
        self.assertEqual(self.category_top.get_depth(), 0)

    def test_get_depth_sub(self):
        """Test children getting function for sub project"""
        self.assertEqual(self.project_sub.get_depth(), 1)

    def test_get_parents_top(self):
        """Test get parents function for top category"""
        self.assertEqual(self.category_top.get_parents(), [])

    def test_get_parents_sub(self):
        """Test get parents function for sub project"""
        self.assertEqual(
            list(self.project_sub.get_parents()), [self.category_top]
        )

    def test_is_remote(self):
        """Test Project.is_remote() without remote projects"""
        self.assertEqual(self.project_sub.is_remote(), False)

    def test_is_revoked(self):
        """Test Project.is_revoked() without remote projects"""
        self.assertEqual(self.project_sub.is_revoked(), False)

    def test_set_public(self):
        """Test Project.set_public()"""
        self.assertFalse(self.project_sub.public_guest_access)
        self.project_sub.set_public()  # Default = true
        self.assertTrue(self.project_sub.public_guest_access)
        self.project_sub.set_public(False)
        self.assertFalse(self.project_sub.public_guest_access)
        self.project_sub.set_public(True)
        self.assertTrue(self.project_sub.public_guest_access)


class TestRole(TestCase):
    def setUp(self):
        self.role = Role.objects.get(name=PROJECT_ROLE_OWNER)

    def test_initialization(self):
        """Test Role initialization"""
        expected = {
            'id': self.role.pk,
            'name': PROJECT_ROLE_OWNER,
            'description': self.role.description,
        }
        self.assertEqual(model_to_dict(self.role), expected)

    def test__str__(self):
        """Test Role __str__()"""
        expected = PROJECT_ROLE_OWNER
        self.assertEqual(str(self.role), expected)

    def test__repr__(self):
        """Test Role __repr__()"""
        expected = "Role('{}')".format(PROJECT_ROLE_OWNER)
        self.assertEqual(repr(self.role), expected)


class RoleAssignmentMixin:
    """Helper mixin for RoleAssignment creation"""

    @classmethod
    def _make_assignment(cls, project, user, role):
        """Make and save a RoleAssignment"""
        values = {'project': project, 'user': user, 'role': role}
        result = RoleAssignment(**values)
        result.save()
        return result


class TestRoleAssignment(ProjectMixin, RoleAssignmentMixin, TestCase):
    """Tests for model.RoleAssignment"""

    def setUp(self):
        # Init projects/categories
        # Top level category
        self.category_top = self._make_project(
            title='TestCategoryTop', type=PROJECT_TYPE_CATEGORY, parent=None
        )
        # Subproject under category_top
        self.project_sub = self._make_project(
            title='TestProjectSub',
            type=PROJECT_TYPE_PROJECT,
            parent=self.category_top,
        )
        # Top level project
        self.project_top = self._make_project(
            title='TestProjectTop', type=PROJECT_TYPE_PROJECT, parent=None
        )

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
        self.user_alice = self.make_user('alice')
        self.user_bob = self.make_user('bob')
        self.user_carol = self.make_user('carol')
        self.user_dan = self.make_user('dan')
        self.user_erin = self.make_user('erin')
        self.user_frank = self.make_user('frank')

        # Init assignment
        self.assignment_owner = self._make_assignment(
            self.category_top, self.user_alice, self.role_owner
        )

        self.expected_default = {
            'id': self.assignment_owner.pk,
            'project': self.category_top.pk,
            'user': self.user_alice.pk,
            'role': self.role_owner.pk,
            'sodar_uuid': self.assignment_owner.sodar_uuid,
        }

    def test_initialization(self):
        """Test RoleAssignment initialization"""
        self.assertEqual(
            model_to_dict(self.assignment_owner), self.expected_default
        )

    def test__str__(self):
        """Test RoleAssignment __str__()"""
        expected = 'TestCategoryTop: {}: alice'.format(PROJECT_ROLE_OWNER)
        self.assertEqual(str(self.assignment_owner), expected)

    def test__repr__(self):
        """Test RoleAssignment __repr__()"""
        expected = "RoleAssignment('TestCategoryTop', 'alice', '{}')".format(
            PROJECT_ROLE_OWNER
        )
        self.assertEqual(repr(self.assignment_owner), expected)

    def test_validate_user(self):
        """Test user role uniqueness validation: can't add more than one
        role for user in project at once"""
        with self.assertRaises(ValidationError):
            self._make_assignment(
                self.category_top, self.user_alice, self.role_contributor
            )

    def test_validate_owner(self):
        """Test owner uniqueness validation: can't add owner for project if
        one already exists"""
        with self.assertRaises(ValidationError):
            self._make_assignment(
                self.category_top, self.user_bob, self.role_owner
            )

    @override_settings(PROJECTROLES_DELEGATE_LIMIT=1)
    def test_validate_one_delegate(self):
        """Test delegate validation: can't add delegate for project if limit (1)
        of delegates is reached"""
        self._make_assignment(
            self.project_sub, self.user_bob, self.role_delegate
        )

        with self.assertRaises(ValidationError):
            self._make_assignment(
                self.project_sub, self.user_carol, self.role_delegate
            )

    @override_settings(PROJECTROLES_DELEGATE_LIMIT=0)
    def test_validate_several_delegates(self):
        """Test delegate validation: can add delegate for project if no limit
        of delegates is set"""
        self._make_assignment(
            self.project_sub, self.user_bob, self.role_delegate
        )

        try:
            self._make_assignment(
                self.project_sub, self.user_carol, self.role_delegate
            )
        except ValidationError as e:
            self.fail(e)

    # Tests for RoleAssignmentManager

    def test_get_assignment(self):
        """Test get_assignment() results"""
        self.assertEqual(
            model_to_dict(
                RoleAssignment.objects.get_assignment(
                    self.user_alice, self.category_top
                )
            ),
            self.expected_default,
        )

    def test_get_assignment_anon(self):
        """Test get_assignment() results with an anonymous user"""
        anon_user = AnonymousUser()
        self.assertIsNone(
            RoleAssignment.objects.get_assignment(anon_user, self.category_top)
        )

    def test_get_project_owner(self):
        """Test get_project_owner() results"""
        self.assertEqual(self.category_top.get_owner().user, self.user_alice)

    def test_get_project_owners(self):
        """Test project.get_owners() results"""

        # Set bob as project owner
        self._make_assignment(self.project_sub, self.user_bob, self.role_owner)

        self.assertEqual(len(self.project_sub.get_owners()), 2)
        self.assertEqual(
            len(self.project_sub.get_owners(inherited_only=True)), 1
        )

    def test_is_project_owner(self):
        """Test project.is_owner() reuslts"""

        # Set bob as project owner
        self._make_assignment(self.project_sub, self.user_bob, self.role_owner)

        self.assertTrue(self.project_sub.is_owner(self.user_bob))
        self.assertTrue(self.project_sub.is_owner(self.user_alice))
        self.assertFalse(self.project_sub.is_owner(self.user_carol))

    def test_get_project_delegates(self):
        """Test get_project_delegates() results"""
        assignment_d0 = self._make_assignment(
            self.project_top, self.user_carol, self.role_delegate
        )

        expected = [
            {
                'id': assignment_d0.pk,
                'project': self.project_top.pk,
                'user': self.user_carol.pk,
                'role': self.role_delegate.pk,
                'sodar_uuid': assignment_d0.sodar_uuid,
            }
        ]

        if getattr(settings, 'PROJECTROLES_DELEGATE_LIMIT', 1) != 1:
            assignment_d1 = self._make_assignment(
                self.project_top, self.user_dan, self.role_delegate
            )
            expected.append(
                {
                    'id': assignment_d1.pk,
                    'project': self.project_top.pk,
                    'user': self.user_dan.pk,
                    'role': self.role_delegate.pk,
                    'sodar_uuid': assignment_d1.sodar_uuid,
                }
            )

        delegates = self.project_top.get_delegates()

        for i in range(0, delegates.count()):
            self.assertEqual(model_to_dict(delegates[i]), expected[i])

    def test_get_project_members(self):
        """Test project.get_members() results"""
        assignment_c0 = self._make_assignment(
            self.project_top, self.user_erin, self.role_contributor
        )
        assignment_c1 = self._make_assignment(
            self.project_top, self.user_frank, self.role_contributor
        )

        expected = [
            {
                'id': assignment_c0.pk,
                'project': self.project_top.pk,
                'user': self.user_erin.pk,
                'role': self.role_contributor.pk,
                'sodar_uuid': assignment_c0.sodar_uuid,
            },
            {
                'id': assignment_c1.pk,
                'project': self.project_top.pk,
                'user': self.user_frank.pk,
                'role': self.role_contributor.pk,
                'sodar_uuid': assignment_c1.sodar_uuid,
            },
        ]

        members = self.project_top.get_members()

        for i in range(0, members.count()):
            self.assertEqual(model_to_dict(members[i]), expected[i])

    def test_get_all_project_roles(self):
        """Test project.get_all_roles() results"""

        # Set bob as project owner
        self._make_assignment(self.project_sub, self.user_bob, self.role_owner)
        self.assertEqual(len(self.project_sub.get_all_roles()), 2)

    def test_has_role(self):
        """Test the has_role() function for an existing role"""
        self.assertEqual(self.category_top.has_role(self.user_alice), True)
        self.assertEqual(self.project_sub.has_role(self.user_alice), True)

    def test_has_role_norole(self):
        """Test the has_role() function for a non-existing role without
        recursion"""
        self._make_assignment(
            self.project_sub, self.user_bob, self.role_contributor
        )
        self.assertEqual(self.category_top.has_role(self.user_bob), False)

    def test_has_role_norole_children(self):
        """Test the has_role() function for a non-existing role with
        recursion using include_children"""
        self._make_assignment(
            self.project_sub, self.user_bob, self.role_contributor
        )
        self.assertEqual(
            self.category_top.has_role(self.user_bob, include_children=True),
            True,
        )


class TestProjectInvite(
    ProjectMixin, RoleAssignmentMixin, ProjectInviteMixin, TestCase
):
    """Tests for model.ProjectInvite"""

    def setUp(self):
        # Init project
        self.project = self._make_project(
            title='TestProject', type=PROJECT_TYPE_PROJECT, parent=None
        )

        # Init roles
        self.role_owner = Role.objects.get(name=PROJECT_ROLE_OWNER)
        self.role_delegate = Role.objects.get(name=PROJECT_ROLE_DELEGATE)
        self.role_contributor = Role.objects.get(name=PROJECT_ROLE_CONTRIBUTOR)

        # Init user & role
        self.user = self.make_user('owner')
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        # Init invite
        self.invite = self._make_invite(
            email='test@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )

    def test_initialization(self):
        """Test ProjectInvite initialization"""
        expected = {
            'id': self.invite.pk,
            'email': 'test@example.com',
            'project': self.project.pk,
            'role': self.role_contributor.pk,
            'issuer': self.user.pk,
            'date_expire': self.invite.date_expire,
            'message': '',
            'secret': SECRET,
            'sodar_uuid': self.invite.sodar_uuid,
            'active': True,
        }
        self.assertEqual(model_to_dict(self.invite), expected)

    def test__str__(self):
        """Test ProjectInvite __str__()"""
        expected = (
            'TestProject: test@example.com (project contributor) ' '[ACTIVE]'
        )
        self.assertEqual(str(self.invite), expected)

    def test__repr__(self):
        """Test ProjectInvite __repr__()"""
        expected = (
            "ProjectInvite('TestProject', 'test@example.com', "
            "'project contributor', True)"
        )
        self.assertEqual(repr(self.invite), expected)


class TestProjectManager(ProjectMixin, RoleAssignmentMixin, TestCase):
    """Tests for ProjectManager"""

    def setUp(self):
        # Init projects/categories
        # Top level category
        self.category_top = self._make_project(
            title='TestCategoryTop',
            type=PROJECT_TYPE_CATEGORY,
            parent=None,
            description='XXX',
        )
        # Subproject under category_top
        self.project_sub = self._make_project(
            title='TestProjectSub',
            type=PROJECT_TYPE_PROJECT,
            parent=self.category_top,
            description='YYY',
        )

    def test_find_all(self):
        """Test find() with any project type"""
        result = Project.objects.find(['test'], project_type=None)
        self.assertEqual(len(result), 2)
        result = Project.objects.find(['ThisFails'], project_type=None)
        self.assertEqual(len(result), 0)

    def test_find_project(self):
        """Test find() with project_type=PROJECT"""
        result = Project.objects.find(
            ['test'], project_type=PROJECT_TYPE_PROJECT
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.project_sub)

    def test_find_category(self):
        """Test find() with project_type=CATEGORY"""
        result = Project.objects.find(
            ['test'], project_type=PROJECT_TYPE_CATEGORY
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.category_top)

    def test_find_multi_one(self):
        """Test find() with one valid multi-term"""
        result = Project.objects.find(['sub', 'ThisFails'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.project_sub)

    def test_find_multi_two(self):
        """Test find() with two valid multi-terms"""
        result = Project.objects.find(['top', 'sub'])
        self.assertEqual(len(result), 2)

    def test_find_description(self):
        """Test find() with search term for description"""
        result = Project.objects.find(['xxx'], project_type=None)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.category_top)

    def test_find_description_multi_one(self):
        """Test find() with one valid multi-search term for description"""
        result = Project.objects.find(['xxx', 'ThisFails'], project_type=None)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.category_top)

    def test_find_description_multi_two(self):
        """Test find() with two valid multi-search terms for description"""
        result = Project.objects.find(['xxx', 'yyy'], project_type=None)
        self.assertEqual(len(result), 2)

    def test_find_multi_fields(self):
        """Test find() with multiple terms for different fields"""
        result = Project.objects.find(['sub', 'xxx'])
        self.assertEqual(len(result), 2)


class TestProjectSetting(
    ProjectMixin, RoleAssignmentMixin, AppSettingMixin, TestCase
):
    """Tests for model.AppSetting with ``user == None``"""

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
        self.setting_str = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='str_setting',
            setting_type='STRING',
            value='test',
            project=self.project,
        )

        # Init integer setting
        self.setting_int = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='int_setting',
            setting_type='INTEGER',
            value=170,
            project=self.project,
        )

        # Init boolean setting
        self.setting_bool = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='bool_setting',
            setting_type='BOOLEAN',
            value=True,
            project=self.project,
        )

        # Init JSON setting
        self.setting_json = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='json_setting',
            setting_type='JSON',
            value=None,
            value_json={'Testing': 'good'},
            project=self.project,
        )

    def test_initialization(self):
        """Test AppSetting initialization"""
        expected = {
            'id': self.setting_str.pk,
            'app_plugin': get_app_plugin(EXAMPLE_APP_NAME).get_model().pk,
            'project': self.project.pk,
            'name': 'str_setting',
            'type': 'STRING',
            'user': None,
            'value': 'test',
            'value_json': {},
            'user_modifiable': True,
            'sodar_uuid': self.setting_str.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.setting_str), expected)

    def test_initialization_integer(self):
        """Test initialization with integer value"""
        expected = {
            'id': self.setting_int.pk,
            'app_plugin': get_app_plugin(EXAMPLE_APP_NAME).get_model().pk,
            'project': self.project.pk,
            'name': 'int_setting',
            'type': 'INTEGER',
            'user': None,
            'value': '170',
            'value_json': {},
            'user_modifiable': True,
            'sodar_uuid': self.setting_int.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.setting_int), expected)

    def test_initialization_json(self):
        """Test initialization with JSON value"""
        expected = {
            'id': self.setting_json.pk,
            'app_plugin': get_app_plugin(EXAMPLE_APP_NAME).get_model().pk,
            'project': self.project.pk,
            'name': 'json_setting',
            'type': 'JSON',
            'user': None,
            'value': None,
            'value_json': {'Testing': 'good'},
            'user_modifiable': True,
            'sodar_uuid': self.setting_json.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.setting_json), expected)

    def test__str__(self):
        """Test AppSetting __str__()"""
        expected = 'TestProject: {} / str_setting'.format(EXAMPLE_APP_NAME)
        self.assertEqual(str(self.setting_str), expected)

    def test__repr__(self):
        """Test AppSetting __repr__()"""
        expected = (
            "AppSetting('TestProject', None, '{}', 'str_setting')".format(
                EXAMPLE_APP_NAME
            )
        )
        self.assertEqual(repr(self.setting_str), expected)

    def test_get_value_str(self):
        """Test get_value() with type STRING"""
        val = self.setting_str.get_value()
        self.assertIsInstance(val, str)
        self.assertEqual(val, 'test')

    def test_get_value_int(self):
        """Test get_value() with type INTEGER"""
        val = self.setting_int.get_value()
        self.assertIsInstance(val, int)
        self.assertEqual(val, 170)

    def test_get_value_bool(self):
        """Test get_value() with type BOOLEAN"""
        val = self.setting_bool.get_value()
        self.assertIsInstance(val, bool)
        self.assertEqual(val, True)

    def test_get_value_json(self):
        """Test get_value() with type JSON"""
        val = self.setting_json.get_value()
        self.assertEqual(val, {'Testing': 'good'})


class TestUserSetting(
    ProjectMixin, RoleAssignmentMixin, AppSettingMixin, TestCase
):
    """Tests for model.AppSetting with ``project == None``"""

    # NOTE: This assumes an example app is available
    def setUp(self):
        # Init user & role
        self.user = self.make_user('owner')

        # Init test setting
        self.setting_str = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='str_setting',
            setting_type='STRING',
            value='test',
            user=self.user,
        )

        # Init integer setting
        self.setting_int = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='int_setting',
            setting_type='INTEGER',
            value=170,
            user=self.user,
        )

        # Init boolean setting
        self.setting_bool = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='bool_setting',
            setting_type='BOOLEAN',
            value=True,
            user=self.user,
        )

        # Init json setting
        self.setting_json = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='json_setting',
            setting_type='JSON',
            value=None,
            value_json={'Testing': 'good'},
            user=self.user,
        )

    def test_initialization(self):
        """Test AppSetting initialization"""
        expected = {
            'id': self.setting_str.pk,
            'app_plugin': get_app_plugin(EXAMPLE_APP_NAME).get_model().pk,
            'project': None,
            'name': 'str_setting',
            'type': 'STRING',
            'user': self.user.pk,
            'value': 'test',
            'value_json': {},
            'user_modifiable': True,
            'sodar_uuid': self.setting_str.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.setting_str), expected)

    def test_initialization_integer(self):
        """Test initialization with integer value"""
        expected = {
            'id': self.setting_int.pk,
            'app_plugin': get_app_plugin(EXAMPLE_APP_NAME).get_model().pk,
            'project': None,
            'name': 'int_setting',
            'type': 'INTEGER',
            'user': self.user.pk,
            'value': '170',
            'value_json': {},
            'user_modifiable': True,
            'sodar_uuid': self.setting_int.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.setting_int), expected)

    def test_initialization_json(self):
        """Test initialization with integer value"""
        expected = {
            'id': self.setting_json.pk,
            'app_plugin': get_app_plugin(EXAMPLE_APP_NAME).get_model().pk,
            'project': None,
            'name': 'json_setting',
            'type': 'JSON',
            'user': self.user.pk,
            'value': None,
            'value_json': {'Testing': 'good'},
            'user_modifiable': True,
            'sodar_uuid': self.setting_json.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.setting_json), expected)

    def test__str__(self):
        """Test AppSetting __str__()"""
        expected = 'owner: {} / str_setting'.format(EXAMPLE_APP_NAME)
        self.assertEqual(str(self.setting_str), expected)

    def test__repr__(self):
        """Test AppSetting __repr__()"""
        expected = "AppSetting(None, 'owner', '{}', 'str_setting')".format(
            EXAMPLE_APP_NAME
        )
        self.assertEqual(repr(self.setting_str), expected)

    def test_get_value_str(self):
        """Test get_value() with type STRING"""
        val = self.setting_str.get_value()
        self.assertIsInstance(val, str)
        self.assertEqual(val, 'test')

    def test_get_value_int(self):
        """Test get_value() with type INTEGER"""
        val = self.setting_int.get_value()
        self.assertIsInstance(val, int)
        self.assertEqual(val, 170)

    def test_get_value_bool(self):
        """Test get_value() with type BOOLEAN"""
        val = self.setting_bool.get_value()
        self.assertIsInstance(val, bool)
        self.assertEqual(val, True)

    def test_get_value_json(self):
        """Test get_value() with type BOOLEAN"""
        val = self.setting_json.get_value()
        self.assertEqual(val, {'Testing': 'good'})


# TODO: Test manager


class TestProjectUserTag(
    ProjectMixin, RoleAssignmentMixin, ProjectUserTagMixin, TestCase
):
    """Tests for model.ProjectUserTag"""

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

        # Init tag
        self.tag = self._make_tag(self.project, self.user, PROJECT_TAG_STARRED)

    def test_initialization(self):
        """Test ProjectUserTag initialization"""
        expected = {
            'id': self.tag.pk,
            'project': self.project.pk,
            'user': self.user.pk,
            'name': PROJECT_TAG_STARRED,
            'sodar_uuid': self.tag.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.tag), expected)

    def test__str__(self):
        """Test ProjectUserTag __str__()"""
        expected = 'TestProject: owner: STARRED'
        self.assertEqual(str(self.tag), expected)

    def test__repr__(self):
        """Test ProjectUserTag __repr__()"""
        expected = "ProjectUserTag('TestProject', 'owner', 'STARRED')"
        self.assertEqual(repr(self.tag), expected)


class TestRemoteSite(
    ProjectMixin, RoleAssignmentMixin, RemoteSiteMixin, TestCase
):
    """Tests for model.RemoteSite"""

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

        # Init remote site
        self.site = self._make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_TARGET'],
            description='',
            secret=REMOTE_SITE_SECRET,
            user_display=REMOTE_SITE_USER_DISPLAY,
        )

    def test_initialization(self):
        """Test RemoteSite initialization"""
        expected = {
            'id': self.site.pk,
            'name': REMOTE_SITE_NAME,
            'url': REMOTE_SITE_URL,
            'mode': SODAR_CONSTANTS['SITE_MODE_TARGET'],
            'description': '',
            'secret': REMOTE_SITE_SECRET,
            'sodar_uuid': self.site.sodar_uuid,
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }
        self.assertEqual(model_to_dict(self.site), expected)

    def test__str__(self):
        """Test RemoteSite __str__()"""
        expected = '{} ({})'.format(
            REMOTE_SITE_NAME, SODAR_CONSTANTS['SITE_MODE_TARGET']
        )
        self.assertEqual(str(self.site), expected)

    def test__repr__(self):
        """Test RemoteSite __repr__()"""
        expected = "RemoteSite('{}', '{}', '{}')".format(
            REMOTE_SITE_NAME,
            SODAR_CONSTANTS['SITE_MODE_TARGET'],
            REMOTE_SITE_URL,
        )
        self.assertEqual(repr(self.site), expected)

    def test_validate_mode(self):
        """Test _validate_mode() with an invalid mode (should fail)"""

        with self.assertRaises(ValidationError):
            self._make_site(
                name='New site',
                url='http://example.com',
                mode='uGaj9eicQueib1th',
            )


class TestRemoteProject(
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    TestCase,
):
    """Tests for model.RemoteProject"""

    def setUp(self):
        # Init project
        self.project = self._make_project(
            title='TestProject', type=PROJECT_TYPE_PROJECT, parent=None
        )

        # Init role
        self.role_owner = Role.objects.get(name=PROJECT_ROLE_OWNER)
        self.role_delegate = Role.objects.get_or_create(
            name=PROJECT_ROLE_DELEGATE
        )[0]

        # Init user & role
        self.user = self.make_user('owner')
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )
        self.user_alice = self.make_user('alice')
        self.user_bob = self.make_user('bob')

        # Init remote site
        self.site = self._make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description='',
            secret=REMOTE_SITE_SECRET,
        )

        self.remote_project = self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL'],
            project=self.project,
        )

    def test_initialization(self):
        """Test RemoteProject initialization"""
        expected = {
            'id': self.remote_project.pk,
            'project_uuid': self.project.sodar_uuid,
            'project': self.project.pk,
            'site': self.site.pk,
            'level': SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL'],
            'date_access': None,
            'sodar_uuid': self.remote_project.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.remote_project), expected)

    def test__str__(self):
        """Test RemoteProject __str__()"""
        expected = '{}: {} ({})'.format(
            REMOTE_SITE_NAME, str(self.project.sodar_uuid), SITE_MODE_TARGET
        )
        self.assertEqual(str(self.remote_project), expected)

    def test__repr__(self):
        """Test RemoteProject __repr__()"""
        expected = "RemoteProject('{}', '{}', '{}')".format(
            REMOTE_SITE_NAME, str(self.project.sodar_uuid), SITE_MODE_TARGET
        )
        self.assertEqual(repr(self.remote_project), expected)

    def test_is_remote_source(self):
        """Test Project.is_remote() as source"""
        self.assertEqual(self.project.is_remote(), False)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_is_remote_target(self):
        """Test Project.is_remote() as target"""
        self.site.mode = SITE_MODE_SOURCE
        self.site.save()
        self.assertEqual(self.project.is_remote(), True)

    def test_get_source_site(self):
        """Test Project.get_source_site() as source"""
        self.assertEqual(self.project.get_source_site(), None)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_get_source_site_target(self):
        """Test Project.get_source_site() as target"""
        self.site.mode = SITE_MODE_SOURCE
        self.site.save()
        self.assertEqual(self.project.get_source_site(), self.site)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_is_revoked_target(self):
        """Test Project.is_revoked() as target"""
        self.site.mode = SITE_MODE_SOURCE
        self.site.save()
        self.assertEqual(self.project.is_revoked(), False)
        self.remote_project.level = SODAR_CONSTANTS['REMOTE_LEVEL_REVOKED']
        self.remote_project.save()
        self.assertEqual(self.project.is_revoked(), True)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    @override_settings(PROJECTROLES_DELEGATE_LIMIT=1)
    def test_validate_remote_delegates(self):
        """Test delegate validation: can add delegate for remote project even if
        there is a limit"""
        self.site.mode = SITE_MODE_SOURCE
        self.site.save()

        self._make_assignment(self.project, self.user_bob, self.role_delegate)

        try:
            self._make_assignment(
                self.project, self.user_alice, self.role_delegate
            )
        except ValidationError as e:
            self.fail(e)

    def test_get_project(self):
        """Test get_project() with project and project_uuid"""
        self.assertEqual(self.remote_project.get_project(), self.project)

    def test_get_project_no_foreignkey(self):
        """Test get_project() with no project foreign key"""
        self.remote_project.project = None
        self.remote_project.save()
        self.assertEqual(self.remote_project.get_project(), self.project)
