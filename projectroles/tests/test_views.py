"""Tests for views in the projectroles Django app"""

import base64
import json
from urllib.parse import urlencode

from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.forms import HiddenInput
from django.forms.models import model_to_dict
from django.test import RequestFactory, override_settings
from django.utils import timezone

from test_plus.test import TestCase

from projectroles.app_settings import AppSettingAPI
from .. import views
from ..models import (
    Project,
    Role,
    RoleAssignment,
    ProjectInvite,
    ProjectUserTag,
    RemoteSite,
    RemoteProject,
    SODAR_CONSTANTS,
    PROJECT_TAG_STARRED,
)
from ..plugins import change_plugin_status, get_backend_api, get_active_plugins
from ..remote_projects import RemoteProjectAPI
from ..utils import build_secret, get_display_name
from .test_models import (
    ProjectMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
    ProjectUserTagMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    AppSettingMixin,
)
from projectroles.utils import get_user_display_name


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
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']

# Local constants
INVITE_EMAIL = 'test@example.com'
SECRET = 'rsd886hi8276nypuvw066sbvv0rb2a6x'
TASKFLOW_SECRET_INVALID = 'Not a valid secret'
REMOTE_SITE_NAME = 'Test site'
REMOTE_SITE_URL = 'https://sodar.bihealth.org'
REMOTE_SITE_DESC = 'description'
REMOTE_SITE_SECRET = build_secret()
REMOTE_SITE_USER_DISPLAY = True

REMOTE_SITE_NEW_NAME = 'New name'
REMOTE_SITE_NEW_URL = 'https://new.url'
REMOTE_SITE_NEW_DESC = 'New description'
REMOTE_SITE_NEW_SECRET = build_secret()

SODAR_API_MEDIA_TYPE = 'application/vnd.bihealth.sodar-core+json'
SODAR_API_MEDIA_TYPE_INVALID = 'application/vnd.bihealth.invalid'
SODAR_API_VERSION = '0.1'
SODAR_API_VERSION_INVALID = '9.9'

EXAMPLE_APP_NAME = 'example_project_app'

# App settings API
app_settings = AppSettingAPI()


class KnoxAuthMixin:
    """Helper mixin for API views with Knox token authorization"""

    # Copied from Knox tests
    @classmethod
    def _get_basic_auth_header(cls, username, password):
        return (
            'Basic %s'
            % base64.b64encode(
                ('%s:%s' % (username, password)).encode('ascii')
            ).decode()
        )

    @classmethod
    def get_token_header(cls, token):
        """
        Return auth header based on token
        :param token: Token string
        :return: Dict
        """
        return {'HTTP_AUTHORIZATION': 'token {}'.format(token)}

    @classmethod
    def get_accept_header(cls, version=settings.SODAR_API_DEFAULT_VERSION):
        """
        Return version accept header based on version string
        :param version: String
        :return: Dict
        """
        return {
            'HTTP_ACCEPT': '{}; version={}'.format(
                settings.SODAR_API_MEDIA_TYPE, version
            )
        }

    def knox_login(self, user, password):
        """
        Login with Knox
        :param user: User object
        :param password: Password (string)
        :return: Token returned by Knox on successful login
        """
        response = self.client.post(
            reverse('knox_login'),
            HTTP_AUTHORIZATION=self._get_basic_auth_header(
                user.username, password
            ),
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        return response.data['token']

    def knox_get(self, url, token, version=settings.SODAR_API_DEFAULT_VERSION):
        """
        Perform a HTTP GET request with Knox token auth
        :param url: URL for getting
        :param token: String
        :param version: String
        :return: Response object
        """
        return self.client.get(
            url,
            **self.get_accept_header(version),
            **self.get_token_header(token)
        )


class TestViewsBase(TestCase):
    """Base class for view testing"""

    def setUp(self):
        self.req_factory = RequestFactory()

        # Force disabling of taskflow plugin if it's available
        if get_backend_api('taskflow'):
            change_plugin_status(
                name='taskflow', status=1, plugin_type='backend'  # 0 = Disabled
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

        # Init superuser
        self.user = self.make_user('superuser')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()


# General view tests -----------------------------------------------------------


class TestHomeView(ProjectMixin, RoleAssignmentMixin, TestViewsBase):
    """Tests for the home view"""

    def setUp(self):
        super().setUp()
        self.category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

    def test_render(self):
        """Test to ensure the home view renders correctly"""
        with self.login(self.user):
            response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

        # Assert the project list is provided by context processors
        self.assertIsNotNone(response.context['project_list'])
        self.assertEqual(
            response.context['project_list'][1].pk, self.project.pk
        )


class TestProjectSearchView(ProjectMixin, RoleAssignmentMixin, TestViewsBase):
    """Tests for the project search view"""

    def setUp(self):
        super().setUp()
        self.category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        self.plugins = get_active_plugins(plugin_type='project_app')

    def test_render(self):
        """Test to ensure the project search view renders correctly"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
            )
        self.assertEqual(response.status_code, 200)

        # Assert the search parameters are provided
        self.assertEqual(response.context['search_term'], 'test')
        self.assertEqual(response.context['search_keywords'], {})
        self.assertEqual(response.context['search_type'], None)
        self.assertEqual(response.context['search_input'], 'test')
        self.assertEqual(
            len(response.context['app_search_data']),
            len([p for p in self.plugins if p.search_enable]),
        )

    def test_render_search_type(self):
        """Test to ensure the project search view renders correctly with a search type"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search')
                + '?'
                + urlencode({'s': 'test type:file'})
            )
        self.assertEqual(response.status_code, 200)

        # Assert the search parameters are provided
        self.assertEqual(response.context['search_term'], 'test')
        self.assertEqual(response.context['search_keywords'], {})
        self.assertEqual(response.context['search_type'], 'file')
        self.assertEqual(response.context['search_input'], 'test type:file')
        self.assertEqual(
            len(response.context['app_search_data']),
            len(
                [
                    p
                    for p in self.plugins
                    if (
                        p.search_enable
                        and response.context['search_type'] in p.search_types
                    )
                ]
            ),
        )

    def test_redirect_invalid_input(self):
        """Test to ensure the project search view redirects if input is not valid"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search')
                + '?'
                + urlencode({'s': 'test\'"%,'})
            )
            self.assertRedirects(response, reverse('home'))

    @override_settings(PROJECTROLES_ENABLE_SEARCH=False)
    def test_disable_search(self):
        """Test redirecting the view due to search being disabled"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
            )
            self.assertRedirects(response, reverse('home'))


class TestProjectDetailView(ProjectMixin, RoleAssignmentMixin, TestViewsBase):
    """Tests for Project detail view"""

    def setUp(self):
        super().setUp()
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

    def test_render(self):
        """Test rendering of project detail view"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:detail',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'].pk, self.project.pk)


class TestProjectCreateView(ProjectMixin, RoleAssignmentMixin, TestViewsBase):
    """Tests for Project creation view"""

    def test_render_top(self):
        """Test rendering of top level category creation form"""
        with self.login(self.user):
            response = self.client.get(reverse('projectroles:create'))

        self.assertEqual(response.status_code, 200)

        # Assert form field values
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertEqual(form.initial['type'], PROJECT_TYPE_CATEGORY)
        self.assertIsInstance(form.fields['type'].widget, HiddenInput)
        self.assertIsInstance(form.fields['parent'].widget, HiddenInput)

    def test_render_sub(self):
        """Test rendering of Project creation form if creating a subproject"""
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        # Create another user to enable checking for owner selection
        self.user_new = self.make_user('newuser')

        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:create',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )

        self.assertEqual(response.status_code, 200)

        # Assert form field values
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertEqual(
            form.fields['type'].choices,
            [
                (
                    PROJECT_TYPE_CATEGORY,
                    get_display_name(PROJECT_TYPE_CATEGORY, title=True),
                ),
                (
                    PROJECT_TYPE_PROJECT,
                    get_display_name(PROJECT_TYPE_PROJECT, title=True),
                ),
            ],
        )
        self.assertIsInstance(form.fields['parent'].widget, HiddenInput)

    def test_render_sub_project(self):
        """Test rendering of Project creation form if creating a subproject under a project (should fail with redirect)"""
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        # Create another user to enable checking for owner selection
        self.user_new = self.make_user('newuser')

        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:create',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )

        self.assertEqual(response.status_code, 302)

    def test_create_top_level_category(self):
        """Test creation of top level category"""

        # Assert precondition
        self.assertEqual(Project.objects.all().count(), 0)

        # Issue POST request
        values = {
            'title': 'TestProject',
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'owner': self.user.sodar_uuid,
            'submit_status': SUBMIT_STATUS_OK,
            'description': 'description',
        }

        # Add settings values
        values.update(
            app_settings.get_all_defaults(
                APP_SETTING_SCOPE_PROJECT, post_safe=True
            )
        )

        with self.login(self.user):
            response = self.client.post(reverse('projectroles:create'), values)

        # Assert Project state after creation
        self.assertEqual(Project.objects.all().count(), 1)
        project = Project.objects.all()[0]
        self.assertIsNotNone(project)
        self.assertEqual(len(mail.outbox), 1)

        expected = {
            'id': project.pk,
            'title': 'TestProject',
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'submit_status': SUBMIT_STATUS_OK,
            'description': 'description',
            'sodar_uuid': project.sodar_uuid,
        }

        model_dict = model_to_dict(project)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        # TODO: Assert settings

        # Assert owner role assignment
        owner_as = RoleAssignment.objects.get(
            project=project, role=self.role_owner
        )

        expected = {
            'id': owner_as.pk,
            'project': project.pk,
            'role': self.role_owner.pk,
            'user': self.user.pk,
            'sodar_uuid': owner_as.sodar_uuid,
        }

        self.assertEqual(model_to_dict(owner_as), expected)

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:detail',
                    kwargs={'project': project.sodar_uuid},
                ),
            )

    def test_create_project(self):
        """Test Project creation"""
        # Create category
        # Issue POST request
        values = {
            'title': 'TestCategory',
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'owner': self.user.sodar_uuid,
            'submit_status': SUBMIT_STATUS_OK,
            'description': 'description',
        }

        # Add settings values
        values.update(
            app_settings.get_all_defaults(
                APP_SETTING_SCOPE_PROJECT, post_safe=True
            )
        )

        with self.login(self.user):
            self.client.post(reverse('projectroles:create'), values)

        category = Project.objects.all()[0]

        # Make project with owner in Django
        values = {
            'title': 'TestProject',
            'type': PROJECT_TYPE_PROJECT,
            'parent': category.pk,
            'owner': self.user.sodar_uuid,
            'description': 'description',
        }

        # Add settings values
        values.update(
            app_settings.get_all_defaults(
                APP_SETTING_SCOPE_PROJECT, post_safe=True
            )
        )

        with self.login(self.user):
            self.client.post(
                reverse(
                    'projectroles:create',
                    kwargs={'project': category.sodar_uuid},
                ),
                values,
            )

        # Assert Project state after creation
        self.assertEqual(Project.objects.all().count(), 2)
        project = Project.objects.get(type=PROJECT_TYPE_PROJECT)
        self.assertIsNotNone(project)
        # 2 mails should be send, for the project and for the category
        self.assertEqual(len(mail.outbox), 2)

        expected = {
            'id': project.pk,
            'title': 'TestProject',
            'type': PROJECT_TYPE_PROJECT,
            'parent': category.pk,
            'submit_status': SUBMIT_STATUS_OK,
            'description': 'description',
            'sodar_uuid': project.sodar_uuid,
        }

        model_dict = model_to_dict(project)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        # Assert owner role assignment
        owner_as = RoleAssignment.objects.get(
            project=project, role=self.role_owner
        )

        expected = {
            'id': owner_as.pk,
            'project': project.pk,
            'role': self.role_owner.pk,
            'user': self.user.pk,
            'sodar_uuid': owner_as.sodar_uuid,
        }

        self.assertEqual(model_to_dict(owner_as), expected)


class TestProjectUpdateView(ProjectMixin, RoleAssignmentMixin, TestViewsBase):
    """Tests for Project updating view"""

    def setUp(self):
        super().setUp()
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

    def test_render(self):
        """Test rendering of Project updating form"""

        # Create another user to enable checking for owner selection
        self.user_new = self.make_user('newuser')

        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:update',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )

        self.assertEqual(response.status_code, 200)

        # Assert form field values
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsInstance(form.fields['type'].widget, HiddenInput)
        self.assertIsInstance(form.fields['parent'].widget, HiddenInput)

    def test_update_project(self):
        """Test Project updating"""

        # Assert precondition
        self.assertEqual(Project.objects.all().count(), 1)

        values = model_to_dict(self.project)
        values['title'] = 'updated title'
        values['description'] = 'updated description'
        values['owner'] = self.user.sodar_uuid  # NOTE: Must add owner

        # Add settings values
        values.update(
            app_settings.get_all_settings(project=self.project, post_safe=True)
        )

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:update',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )

        # Assert Project state after update
        self.assertEqual(Project.objects.all().count(), 1)
        project = Project.objects.all()[0]
        self.assertIsNotNone(project)
        # no mail should be send, cause the owner has not changed
        self.assertEqual(len(mail.outbox), 0)

        expected = {
            'id': project.pk,
            'title': 'updated title',
            'type': PROJECT_TYPE_PROJECT,
            'parent': None,
            'submit_status': SUBMIT_STATUS_OK,
            'description': 'updated description',
            'sodar_uuid': project.sodar_uuid,
        }

        model_dict = model_to_dict(project)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        # TODO: Assert settings

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:detail',
                    kwargs={'project': project.sodar_uuid},
                ),
            )

    def test_update_project_owner(self):
        """Test email sending on project owner update"""
        new_owner = self.make_user('New Owner')

        values = model_to_dict(self.project)
        values['owner'] = new_owner.sodar_uuid  # NOTE: Must add owner

        # Add settings values
        values.update(
            app_settings.get_all_settings(project=self.project, post_safe=True)
        )

        with self.login(self.user):
            self.client.post(
                reverse(
                    'projectroles:update',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )

        # mail should be send, cause the owner has changed
        self.assertEqual(len(mail.outbox), 1)
        new_owner_ra = RoleAssignment.objects.get_assignment(
            new_owner, self.project
        )
        self.assertEqual(new_owner_ra.role, self.role_owner)


class TestProjectSettingsForm(
    AppSettingMixin, TestViewsBase, ProjectMixin, RoleAssignmentMixin
):
    """Tests for project settings in the project create/update view"""

    # NOTE: This assumes an example app is available
    def setUp(self):
        super().setUp()
        # Init user & role
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        # Init string setting
        self.setting_bool = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='project_str_setting',
            setting_type='STRING',
            value='',
            project=self.project,
        )

        # Init integer setting
        self.setting_bool = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='project_int_setting',
            setting_type='INTEGER',
            value='0',
            project=self.project,
        )

        # Init boolean setting
        self.setting_bool = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='project_bool_setting',
            setting_type='BOOLEAN',
            value=False,
            project=self.project,
        )

        # Init json setting
        self.setting_json = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='project_json_setting',
            setting_type='JSON',
            value=None,
            value_json={
                'Example': 'Value',
                'list': [1, 2, 3, 4, 5],
                'level_6': False,
            },
            project=self.project,
        )

    def test_get(self):
        """Test rendering the settings values"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:update',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'])
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.%s.project_str_setting' % EXAMPLE_APP_NAME
            )
        )
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.%s.project_int_setting' % EXAMPLE_APP_NAME
            )
        )
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.%s.project_bool_setting' % EXAMPLE_APP_NAME
            )
        )
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.%s.project_json_setting' % EXAMPLE_APP_NAME
            )
        )

    def test_post(self):
        """Test modifying the settings values"""
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME, 'project_str_setting', project=self.project
            ),
            '',
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME, 'project_int_setting', project=self.project
            ),
            0,
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME, 'project_bool_setting', project=self.project
            ),
            False,
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME, 'project_json_setting', project=self.project
            ),
            {'Example': 'Value', 'list': [1, 2, 3, 4, 5], 'level_6': False},
        )

        values = {
            'settings.%s.project_str_setting' % EXAMPLE_APP_NAME: 'updated',
            'settings.%s.project_int_setting' % EXAMPLE_APP_NAME: 170,
            'settings.%s.project_bool_setting' % EXAMPLE_APP_NAME: True,
            'settings.%s.project_json_setting'
            % EXAMPLE_APP_NAME: '{"Test": "Updated"}',
            'owner': self.user.sodar_uuid,
            'title': 'TestProject',
            'type': PROJECT_TYPE_PROJECT,
        }

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:update',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:detail',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )

        # Assert settings state after update
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME, 'project_str_setting', project=self.project
            ),
            'updated',
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME, 'project_int_setting', project=self.project
            ),
            170,
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME, 'project_bool_setting', project=self.project
            ),
            True,
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME, 'project_json_setting', project=self.project
            ),
            {'Test': 'Updated'},
        )


class TestProjectRoleView(ProjectMixin, RoleAssignmentMixin, TestViewsBase):
    """Tests for project roles view"""

    def setUp(self):
        super().setUp()
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )

        # Set superuser as owner
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        # Set new user as delegate
        self.user_delegate = self.make_user('delegate')
        self.delegate_as = self._make_assignment(
            self.project, self.user_delegate, self.role_delegate
        )

        # Set another new user as guest (= one of the member roles)
        self.user_new = self.make_user('guest')
        self.guest_as = self._make_assignment(
            self.project, self.user_new, self.role_guest
        )

    def test_render(self):
        """Test rendering of project roles view"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:roles',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )

        # Assert page
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project'].pk, self.project.pk)

        # Assert owner
        expected = {
            'id': self.owner_as.pk,
            'project': self.project.pk,
            'role': self.role_owner.pk,
            'user': self.user.pk,
            'sodar_uuid': self.owner_as.sodar_uuid,
        }

        self.assertEqual(model_to_dict(response.context['owner']), expected)

        # Assert delegate
        expected = {
            'id': self.delegate_as.pk,
            'project': self.project.pk,
            'role': self.role_delegate.pk,
            'user': self.user_delegate.pk,
            'sodar_uuid': self.delegate_as.sodar_uuid,
        }

        self.assertEqual(model_to_dict(response.context['delegate']), expected)

        # Assert member
        expected = {
            'id': self.guest_as.pk,
            'project': self.project.pk,
            'role': self.role_guest.pk,
            'user': self.user_new.pk,
            'sodar_uuid': self.guest_as.sodar_uuid,
        }

        self.assertEqual(
            model_to_dict(response.context['members'][0]), expected
        )


class TestRoleAssignmentCreateView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for RoleAssignment creation view"""

    def setUp(self):
        super().setUp()

        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        self.user_new = self.make_user('guest')

    def test_render(self):
        """Test rendering of RoleAssignment creation form"""

        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_create',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )

        self.assertEqual(response.status_code, 200)

        # Assert form field values
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsInstance(form.fields['project'].widget, HiddenInput)
        self.assertEqual(form.initial['project'], self.project.sodar_uuid)
        # Assert user with previously added role in project is not selectable
        self.assertNotIn(
            [
                (
                    self.owner_as.user.sodar_uuid,
                    get_user_display_name(self.owner_as.user, True),
                )
            ],
            form.fields['user'].choices,
        )
        # Assert owner role is not selectable
        self.assertNotIn(
            [(self.role_owner.pk, self.role_owner.name)],
            form.fields['role'].choices,
        )
        # Assert delegate role is selectable
        self.assertIn(
            (self.role_delegate.pk, self.role_delegate.name),
            form.fields['role'].choices,
        )

    def test_create_assignment(self):
        """Test RoleAssignment creation"""
        # Assert precondition
        self.assertEqual(RoleAssignment.objects.all().count(), 1)

        # Issue POST request
        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_new.sodar_uuid,
            'role': self.role_guest.pk,
        }

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:role_create',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )

        # Assert RoleAssignment state after creation
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        role_as = RoleAssignment.objects.get(
            project=self.project, user=self.user_new
        )
        self.assertIsNotNone(role_as)

        expected = {
            'id': role_as.pk,
            'project': self.project.pk,
            'user': self.user_new.pk,
            'role': self.role_guest.pk,
            'sodar_uuid': role_as.sodar_uuid,
        }

        self.assertEqual(model_to_dict(role_as), expected)

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:roles',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )

    def test_redirect_to_invite(self):
        """Test RedirectWidget redirects to the ProjectInvite creation view"""
        # Issue POST request
        values = {
            'project': self.project.sodar_uuid,
            'role': self.role_guest.pk,
            'text': 'test@example.com',
        }

        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:autocomplete_user_redirect'), values
            )

        self.assertEqual(response.status_code, 200)

        # Assert correct redirect url
        with self.login(self.user):
            data = json.loads(response.content)
            self.assertEqual(data['success'], True)
            self.assertEqual(
                data['redirect_url'],
                reverse(
                    'projectroles:invite_create',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )

    def test_create_option(self):
        """Test if new options are being displayedby the RedirectWidget"""
        values = {
            'project': self.project.sodar_uuid,
            'role': self.role_guest.pk,
            'q': 'test@example.com',
        }

        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:autocomplete_user_redirect'), values
            )

        new_option = {
            'id': 'test@example.com',
            'text': 'Send an invite to "test@example.com"',
            'create_id': True,
        }

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn(new_option, data['results'])

    def test_dont_create_option(self):
        """Test if new options are not being displayed by the RedirectWidget if
        they are nor valid email addresses """
        values = {
            'project': self.project.sodar_uuid,
            'role': self.role_guest.pk,
            'q': 'test@example',
        }

        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:autocomplete_user_redirect'), values
            )

        new_option = {
            'id': 'test@example.com',
            'text': 'Send an invite to "test@example"',
            'create_id': True,
        }

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertNotIn(new_option, data['results'])


class TestRoleAssignmentUpdateView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for RoleAssignment update view"""

    def setUp(self):
        super().setUp()

        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        # Create guest user and role
        self.user_new = self.make_user('newuser')
        self.role_as = self._make_assignment(
            self.project, self.user_new, self.role_guest
        )

    def test_render(self):
        """Test rendering of RoleAssignment updating form"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_update',
                    kwargs={'roleassignment': self.role_as.sodar_uuid},
                )
            )

        self.assertEqual(response.status_code, 200)

        # Assert form field values
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsInstance(form.fields['project'].widget, HiddenInput)
        self.assertEqual(form.initial['project'], self.project.sodar_uuid)
        self.assertIsInstance(form.fields['user'].widget, HiddenInput)
        self.assertEqual(form.initial['user'], self.role_as.user.sodar_uuid)

        # Assert owner role is not sectable
        self.assertNotIn(
            [(self.role_owner.pk, self.role_owner.name)],
            form.fields['role'].choices,
        )
        # Assert delegate role is selectable
        self.assertIn(
            (self.role_delegate.pk, self.role_delegate.name),
            form.fields['role'].choices,
        )

    def test_update_assignment(self):
        """Test RoleAssignment updating"""

        # Assert precondition
        self.assertEqual(RoleAssignment.objects.all().count(), 2)

        values = {
            'project': self.role_as.project.sodar_uuid,
            'user': self.role_as.user.sodar_uuid,
            'role': self.role_contributor.pk,
        }

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:role_update',
                    kwargs={'roleassignment': self.role_as.sodar_uuid},
                ),
                values,
            )

        # Assert RoleAssignment state after update
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        role_as = RoleAssignment.objects.get(
            project=self.project, user=self.user_new
        )
        self.assertIsNotNone(role_as)

        expected = {
            'id': role_as.pk,
            'project': self.project.pk,
            'user': self.user_new.pk,
            'role': self.role_contributor.pk,
            'sodar_uuid': role_as.sodar_uuid,
        }

        self.assertEqual(model_to_dict(role_as), expected)

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:roles',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )


class TestRoleAssignmentDeleteView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for RoleAssignment delete view"""

    def setUp(self):
        super().setUp()

        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        # Create guest user and role
        self.user_new = self.make_user('guest')
        self.role_as = self._make_assignment(
            self.project, self.user_new, self.role_guest
        )

    def test_render(self):
        """Test rendering of the RoleAssignment deletion confirmation form"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_delete',
                    kwargs={'roleassignment': self.role_as.sodar_uuid},
                )
            )

        self.assertEqual(response.status_code, 200)

    def test_delete_assignment(self):
        """Test RoleAssignment deleting"""

        # Assert precondition
        self.assertEqual(RoleAssignment.objects.all().count(), 2)

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:role_delete',
                    kwargs={'roleassignment': self.role_as.sodar_uuid},
                )
            )

        # Assert RoleAssignment state after update
        self.assertEqual(RoleAssignment.objects.all().count(), 1)

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:roles',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )


class TestRoleAssignmentTransferOwnershipView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    def setUp(self):
        super().setUp()

        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        # Create guest user and role
        self.user_new = self.make_user('guest')
        self.role_as = self._make_assignment(
            self.project, self.user_new, self.role_guest
        )

    def test_transfer_ownership(self):
        """Test RoleAssignment deleting"""

        # Assert precondition
        self.assertEqual(RoleAssignment.objects.all().count(), 2)

        with self.login(self.user):
            self.client.post(
                reverse(
                    'projectroles:role_transfer_owner',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                data={
                    'project': self.project.sodar_uuid,
                    'owners_new_role': self.role_guest.pk,
                    'new_owner': self.user_new.sodar_uuid,
                },
            )
        self.role_as.refresh_from_db()
        self.owner_as.refresh_from_db()

        self.assertEqual(self.role_as.role, self.role_owner)
        self.assertEqual(self.owner_as.role, self.role_guest)
        self.assertEqual(len(mail.outbox), 2)


class TestProjectInviteCreateView(
    ProjectMixin, RoleAssignmentMixin, ProjectInviteMixin, TestViewsBase
):
    """Tests for ProjectInvite creation view"""

    def setUp(self):
        super().setUp()

        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        self.new_user = self.make_user('new_user')

    def test_render(self):
        """Test rendering of ProjectInvite creation form"""

        with self.login(self.owner_as.user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_create',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )

        self.assertEqual(response.status_code, 200)

        # Assert form field values
        form = response.context['form']
        self.assertIsNotNone(form)

        # Assert owner role is not selectable
        self.assertNotIn(
            [(self.role_owner.pk, self.role_owner.name)],
            form.fields['role'].choices,
        )

    def test_render_from_roleassignment(self):
        """Test rendering of ProjectInvite creation form with forwarded values
        from the RoleAssignment Form"""

        values = {
            'forwarded-email': 'test@example.com',
            'forwarded-role': self.role_contributor.pk,
        }

        with self.login(self.owner_as.user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_create',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )

        self.assertEqual(response.status_code, 200)

        # Assert form field values
        form = response.context['form']
        self.assertIsNotNone(form)

        # Assert owner role is not selectable
        self.assertNotIn(
            [(self.role_owner.pk, self.role_owner.name)],
            form.fields['role'].choices,
        )

        # Assert that forwarded mail address and role have been set in the form
        self.assertEqual(
            form.fields['role'].initial, str(self.role_contributor.pk)
        )
        self.assertEqual(form.fields['email'].initial, 'test@example.com')

    def test_create_invite(self):
        """Test ProjectInvite creation"""

        # Assert precondition
        self.assertEqual(ProjectInvite.objects.all().count(), 0)

        # Issue POST request
        values = {
            'email': INVITE_EMAIL,
            'project': self.project.pk,
            'role': self.role_contributor.pk,
        }

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:invite_create',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )

        # Assert ProjectInvite state after creation
        self.assertEqual(ProjectInvite.objects.all().count(), 1)

        invite = ProjectInvite.objects.get(
            project=self.project, email=INVITE_EMAIL, active=True
        )
        self.assertIsNotNone(invite)

        expected = {
            'id': invite.pk,
            'project': self.project.pk,
            'email': INVITE_EMAIL,
            'role': self.role_contributor.pk,
            'issuer': self.user.pk,
            'message': '',
            'date_expire': invite.date_expire,
            'secret': invite.secret,
            'active': True,
            'sodar_uuid': invite.sodar_uuid,
        }

        self.assertEqual(model_to_dict(invite), expected)

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:invites',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )

    def test_accept_invite(self):
        """Test user accepting an invite"""

        # Init invite
        invite = self._make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )

        # Assert preconditions
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)

        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=self.new_user,
                role=self.role_contributor,
            ).count(),
            0,
        )

        with self.login(self.new_user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_accept',
                    kwargs={'secret': invite.secret},
                )
            )

            self.assertRedirects(
                response,
                reverse(
                    'projectroles:detail',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )

            # Assert postconditions
            self.assertEqual(
                ProjectInvite.objects.filter(active=True).count(), 0
            )

            self.assertEqual(
                RoleAssignment.objects.filter(
                    project=self.project,
                    user=self.new_user,
                    role=self.role_contributor,
                ).count(),
                1,
            )

    def test_accept_invite_expired(self):
        """Test user accepting an expired invite"""

        # Init invite
        invite = self._make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
            date_expire=timezone.now(),
        )

        # Assert preconditions
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)

        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=self.new_user,
                role=self.role_contributor,
            ).count(),
            0,
        )

        with self.login(self.new_user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_accept',
                    kwargs={'secret': invite.secret},
                )
            )

            self.assertRedirects(response, reverse('home'))

            # Assert postconditions
            self.assertEqual(
                ProjectInvite.objects.filter(active=True).count(), 0
            )

            self.assertEqual(
                RoleAssignment.objects.filter(
                    project=self.project,
                    user=self.new_user,
                    role=self.role_contributor,
                ).count(),
                0,
            )


class TestProjectInviteListView(
    ProjectMixin, RoleAssignmentMixin, ProjectInviteMixin, TestViewsBase
):
    """Tests for ProjectInvite list view"""

    def setUp(self):
        super().setUp()

        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        self.invite = self._make_invite(
            email='test@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )

    def test_render(self):
        """Test rendering of ProjectInvite list form"""

        with self.login(self.owner_as.user):
            response = self.client.get(
                reverse(
                    'projectroles:invites',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )

        self.assertEqual(response.status_code, 200)


class TestProjectInviteRevokeView(
    ProjectMixin, RoleAssignmentMixin, ProjectInviteMixin, TestViewsBase
):
    """Tests for ProjectInvite revocation view"""

    def setUp(self):
        super().setUp()

        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        self.invite = self._make_invite(
            email='test@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )

    def test_render(self):
        """Test rendering of ProjectInvite revocation form"""

        with self.login(self.owner_as.user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_revoke',
                    kwargs={'projectinvite': self.invite.sodar_uuid},
                )
            )

        self.assertEqual(response.status_code, 200)

    def test_revoke_invite(self):
        """Test invite revocation"""

        # Assert precondition
        self.assertEqual(ProjectInvite.objects.all().count(), 1)
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)

        # Issue POST request
        with self.login(self.user):
            self.client.post(
                reverse(
                    'projectroles:invite_revoke',
                    kwargs={'projectinvite': self.invite.sodar_uuid},
                )
            )

        # Assert ProjectInvite state after creation
        self.assertEqual(ProjectInvite.objects.all().count(), 1)
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 0)


class TestProjectStarringAPIView(
    ProjectMixin, RoleAssignmentMixin, ProjectUserTagMixin, TestViewsBase
):
    """Tests for project starring API view"""

    def setUp(self):
        super().setUp()

        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

    def test_star_project(self):
        """Test project starring"""

        # Assert precondition
        self.assertEqual(ProjectUserTag.objects.all().count(), 0)

        # Issue request
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:star',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )

        # Assert ProjectUserTag state after creation
        self.assertEqual(ProjectUserTag.objects.all().count(), 1)

        tag = ProjectUserTag.objects.get(
            project=self.project, user=self.user, name=PROJECT_TAG_STARRED
        )
        self.assertIsNotNone(tag)

        expected = {
            'id': tag.pk,
            'project': self.project.pk,
            'user': self.user.pk,
            'name': PROJECT_TAG_STARRED,
            'sodar_uuid': tag.sodar_uuid,
        }

        self.assertEqual(model_to_dict(tag), expected)

        # Assert redirect
        self.assertEqual(response.status_code, 200)

    def test_unstar_project(self):
        """Test project unstarring"""
        self._make_tag(self.project, self.user, name=PROJECT_TAG_STARRED)

        # Assert precondition
        self.assertEqual(ProjectUserTag.objects.all().count(), 1)

        # Issue request
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:star',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )

        # Assert ProjectUserTag state after creation
        self.assertEqual(ProjectUserTag.objects.all().count(), 0)

        # Assert status code
        self.assertEqual(response.status_code, 200)


# Taskflow API view tests ------------------------------------------------------


@override_settings(ENABLED_BACKEND_PLUGINS=['taskflow'])
class TestProjectGetAPIView(ProjectMixin, RoleAssignmentMixin, TestViewsBase):
    """Tests for the project retrieve API view"""

    def setUp(self):
        super().setUp()

        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

    def test_post(self):
        """Test POST request for getting a project"""
        request = self.req_factory.post(
            reverse('projectroles:taskflow_project_get'),
            data={
                'project_uuid': str(self.project.sodar_uuid),
                'sodar_secret': settings.TASKFLOW_SODAR_SECRET,
            },
        )
        response = views.TaskflowProjectGetAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        expected = {
            'project_uuid': str(self.project.sodar_uuid),
            'title': self.project.title,
            'description': self.project.description,
        }

        self.assertEqual(response.data, expected)

    @override_settings(ENABLED_BACKEND_PLUGINS=['taskflow'])
    def test_get_pending(self):
        """Test POST request to get a pending project"""
        pd_project = self._make_project(
            title='TestProject2',
            type=PROJECT_TYPE_PROJECT,
            parent=None,
            submit_status=SUBMIT_STATUS_PENDING_TASKFLOW,
        )

        request = self.req_factory.post(
            reverse('projectroles:taskflow_project_get'),
            data={
                'project_uuid': str(pd_project.sodar_uuid),
                'sodar_secret': settings.TASKFLOW_SODAR_SECRET,
            },
        )
        response = views.TaskflowProjectGetAPIView.as_view()(request)
        self.assertEqual(response.status_code, 404)


@override_settings(ENABLED_BACKEND_PLUGINS=['taskflow'])
class TestProjectUpdateAPIView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for the project updating API view"""

    def setUp(self):
        super().setUp()

        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

    def test_post(self):
        """Test POST request for updating a project"""

        # NOTE: Duplicate titles not checked here, not allowed in the form
        title = 'New title'
        desc = 'New desc'
        readme = 'New readme'

        request = self.req_factory.post(
            reverse('projectroles:taskflow_project_update'),
            data={
                'project_uuid': str(self.project.sodar_uuid),
                'title': title,
                'description': desc,
                'readme': readme,
                'sodar_secret': settings.TASKFLOW_SODAR_SECRET,
            },
        )
        response = views.TaskflowProjectUpdateAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        self.project.refresh_from_db()
        self.assertEqual(self.project.title, title)
        self.assertEqual(self.project.description, desc)
        self.assertEqual(self.project.readme.raw, readme)

    def test_post_no_description(self):
        """Test POST request without a description field"""

        # NOTE: Duplicate titles not checked here, not allowed in the form
        title = 'New title'
        readme = 'New readme'

        request = self.req_factory.post(
            reverse('projectroles:taskflow_project_update'),
            data={
                'project_uuid': str(self.project.sodar_uuid),
                'title': title,
                'readme': readme,
                'sodar_secret': settings.TASKFLOW_SODAR_SECRET,
            },
        )
        response = views.TaskflowProjectUpdateAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        self.project.refresh_from_db()
        self.assertEqual(self.project.title, title)
        self.assertEqual(self.project.description, '')
        self.assertEqual(self.project.readme.raw, readme)


@override_settings(ENABLED_BACKEND_PLUGINS=['taskflow'])
class TestRoleAssignmentGetAPIView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for the role assignment getting API view"""

    def setUp(self):
        super().setUp()

        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

    def test_post(self):
        """Test POST request for getting a role assignment"""
        request = self.req_factory.post(
            reverse('projectroles:taskflow_role_get'),
            data={
                'project_uuid': str(self.project.sodar_uuid),
                'user_uuid': str(self.user.sodar_uuid),
                'sodar_secret': settings.TASKFLOW_SODAR_SECRET,
            },
        )
        response = views.TaskflowRoleAssignmentGetAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        expected = {
            'assignment_uuid': str(self.owner_as.sodar_uuid),
            'project_uuid': str(self.project.sodar_uuid),
            'user_uuid': str(self.user.sodar_uuid),
            'role_pk': self.role_owner.pk,
            'role_name': self.role_owner.name,
        }
        self.assertEqual(response.data, expected)


@override_settings(ENABLED_BACKEND_PLUGINS=['taskflow'])
class TestRoleAssignmentSetAPIView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for the role assignment setting API view"""

    def setUp(self):
        super().setUp()

        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

    def test_post_new(self):
        """Test POST request for assigning a new role"""
        new_user = self.make_user('new_user')

        # Assert precondition
        self.assertEqual(RoleAssignment.objects.all().count(), 1)

        request = self.req_factory.post(
            reverse('projectroles:taskflow_role_set'),
            data={
                'project_uuid': str(self.project.sodar_uuid),
                'user_uuid': str(new_user.sodar_uuid),
                'role_pk': self.role_contributor.pk,
                'sodar_secret': settings.TASKFLOW_SODAR_SECRET,
            },
        )

        response = views.TaskflowRoleAssignmentSetAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)

        new_as = RoleAssignment.objects.get(project=self.project, user=new_user)
        self.assertEqual(new_as.role.pk, self.role_contributor.pk)

    def test_post_existing(self):
        """Test POST request for updating an existing role"""
        new_user = self.make_user('new_user')
        self._make_assignment(self.project, new_user, self.role_guest)

        # Assert precondition
        self.assertEqual(RoleAssignment.objects.all().count(), 2)

        request = self.req_factory.post(
            reverse('projectroles:taskflow_role_set'),
            data={
                'project_uuid': str(self.project.sodar_uuid),
                'user_uuid': str(new_user.sodar_uuid),
                'role_pk': self.role_contributor.pk,
                'sodar_secret': settings.TASKFLOW_SODAR_SECRET,
            },
        )

        response = views.TaskflowRoleAssignmentSetAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)

        new_as = RoleAssignment.objects.get(project=self.project, user=new_user)
        self.assertEqual(new_as.role.pk, self.role_contributor.pk)


@override_settings(ENABLED_BACKEND_PLUGINS=['taskflow'])
class TestRoleAssignmentDeleteAPIView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for the role assignment deletion API view"""

    def setUp(self):
        super().setUp()

        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

    def test_post(self):
        """Test POST request for removing a role assignment"""
        new_user = self.make_user('new_user')
        self._make_assignment(self.project, new_user, self.role_guest)

        # Assert precondition
        self.assertEqual(RoleAssignment.objects.all().count(), 2)

        request = self.req_factory.post(
            reverse('projectroles:taskflow_role_delete'),
            data={
                'project_uuid': str(self.project.sodar_uuid),
                'user_uuid': str(new_user.sodar_uuid),
                'sodar_secret': settings.TASKFLOW_SODAR_SECRET,
            },
        )

        response = views.TaskflowRoleAssignmentDeleteAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RoleAssignment.objects.all().count(), 1)

    def test_post_not_found(self):
        """Test POST request for removing a non-existing role assignment"""
        new_user = self.make_user('new_user')

        # Assert precondition
        self.assertEqual(RoleAssignment.objects.all().count(), 1)

        request = self.req_factory.post(
            reverse('projectroles:taskflow_role_delete'),
            data={
                'project_uuid': str(self.project.sodar_uuid),
                'user_uuid': str(new_user.sodar_uuid),
                'sodar_secret': settings.TASKFLOW_SODAR_SECRET,
            },
        )

        response = views.TaskflowRoleAssignmentDeleteAPIView.as_view()(request)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(RoleAssignment.objects.all().count(), 1)


class TestTaskflowAPIViewAccess(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for taskflow API view access"""

    def setUp(self):
        super().setUp()
        self.category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

    @override_settings(ENABLED_BACKEND_PLUGINS=['taskflow'])
    def test_access_invalid_token(self):
        """Test access with an invalid token"""
        urls = [
            reverse('projectroles:taskflow_project_get'),
            reverse('projectroles:taskflow_project_update'),
            reverse('projectroles:taskflow_role_get'),
            reverse('projectroles:taskflow_role_set'),
            reverse('projectroles:taskflow_role_delete'),
            reverse('projectroles:taskflow_settings_get'),
            reverse('projectroles:taskflow_settings_set'),
        ]

        for url in urls:
            request = self.req_factory.post(
                url, data={'sodar_secret': TASKFLOW_SECRET_INVALID}
            )
            response = views.TaskflowProjectGetAPIView.as_view()(request)
            self.assertEqual(response.status_code, 403)

    @override_settings(ENABLED_BACKEND_PLUGINS=['taskflow'])
    def test_access_no_token(self):
        """Test access with no token"""
        urls = [
            reverse('projectroles:taskflow_project_get'),
            reverse('projectroles:taskflow_project_update'),
            reverse('projectroles:taskflow_role_get'),
            reverse('projectroles:taskflow_role_set'),
            reverse('projectroles:taskflow_role_delete'),
            reverse('projectroles:taskflow_settings_get'),
            reverse('projectroles:taskflow_settings_set'),
        ]

        for url in urls:
            request = self.req_factory.post(url)
            response = views.TaskflowProjectGetAPIView.as_view()(request)
            self.assertEqual(response.status_code, 403)

    @override_settings(ENABLED_BACKEND_PLUGINS=[])
    def test_disable_api_views(self):
        """Test to make sure API views are disabled without taskflow"""
        urls = [
            reverse('projectroles:taskflow_project_get'),
            reverse('projectroles:taskflow_project_update'),
            reverse('projectroles:taskflow_role_get'),
            reverse('projectroles:taskflow_role_set'),
            reverse('projectroles:taskflow_role_delete'),
            reverse('projectroles:taskflow_settings_get'),
            reverse('projectroles:taskflow_settings_set'),
        ]

        for url in urls:
            request = self.req_factory.post(
                url, data={'sodar_secret': settings.TASKFLOW_SODAR_SECRET}
            )
            response = views.TaskflowProjectGetAPIView.as_view()(request)
            self.assertEqual(response.status_code, 403)


# Remote view tests ------------------------------------------------------------


class TestRemoteSiteListView(RemoteSiteMixin, TestViewsBase):
    """Tests for remote site list view"""

    def setUp(self):
        super().setUp()

        # Create target site
        self.target_site = self._make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )

    def test_render_as_source(self):
        """Test rendering the remote site list view as source"""

        with self.login(self.user):
            response = self.client.get(reverse('projectroles:remote_sites'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sites'].count(), 1)  # 1 target site

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_render_as_target(self):
        """Test rendering the remote site list view as target"""

        with self.login(self.user):
            response = self.client.get(reverse('projectroles:remote_sites'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sites'].count(), 0)  # 1 source sites

    # TODO: Remove this once #76 is done
    @override_settings(PROJECTROLES_DISABLE_CATEGORIES=True)
    def test_render_disable_categories(self):
        """Test rendering the remote site list view with categories disabled"""

        with self.login(self.user):
            response = self.client.get(reverse('projectroles:remote_sites'))
            self.assertRedirects(response, reverse('home'))


class TestRemoteSiteCreateView(RemoteSiteMixin, TestViewsBase):
    """Tests for remote site create view"""

    def setUp(self):
        super().setUp()

    def test_render_as_source(self):
        """Test rendering the remote site create view as source"""

        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:remote_site_create')
            )

        self.assertEqual(response.status_code, 200)

        # Assert form field values
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsNotNone(form.fields['secret'].initial)
        self.assertEqual(form.fields['secret'].widget.attrs['readonly'], True)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_render_as_target(self):
        """Test rendering the remote site create view as target"""

        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:remote_site_create')
            )

        self.assertEqual(response.status_code, 200)

        # Assert form field values
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsNone(form.fields['secret'].initial)
        self.assertNotIn('readonly', form.fields['secret'].widget.attrs)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_render_as_target_existing(self):
        """Test rendering the remote site create view as target with an existing source (should fail)"""

        # Create source site
        self.source_site = self._make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_SOURCE,
            description='',
            secret=REMOTE_SITE_SECRET,
        )

        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:remote_site_create')
            )
            self.assertRedirects(response, reverse('projectroles:remote_sites'))

    def test_create_target(self):
        """Test creating a target site"""

        # Assert precondition
        self.assertEqual(RemoteSite.objects.all().count(), 0)

        values = {
            'name': REMOTE_SITE_NAME,
            'url': REMOTE_SITE_URL,
            'description': REMOTE_SITE_DESC,
            'secret': REMOTE_SITE_SECRET,
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }

        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:remote_site_create'), values
            )

        # Assert site state after creation
        self.assertEqual(RemoteSite.objects.all().count(), 1)
        site = RemoteSite.objects.first()

        expected = {
            'id': site.pk,
            'name': REMOTE_SITE_NAME,
            'url': REMOTE_SITE_URL,
            'mode': SITE_MODE_TARGET,
            'description': REMOTE_SITE_DESC,
            'secret': REMOTE_SITE_SECRET,
            'sodar_uuid': site.sodar_uuid,
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }

        model_dict = model_to_dict(site)
        self.assertEqual(model_dict, expected)

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(response, reverse('projectroles:remote_sites'))

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_create_source(self):
        """Test creating a source site as target"""

        # Assert precondition
        self.assertEqual(RemoteSite.objects.all().count(), 0)

        values = {
            'name': REMOTE_SITE_NAME,
            'url': REMOTE_SITE_URL,
            'description': REMOTE_SITE_DESC,
            'secret': REMOTE_SITE_SECRET,
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }

        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:remote_site_create'), values
            )

        # Assert site state after creation
        self.assertEqual(RemoteSite.objects.all().count(), 1)
        site = RemoteSite.objects.first()

        expected = {
            'id': site.pk,
            'name': REMOTE_SITE_NAME,
            'url': REMOTE_SITE_URL,
            'mode': SITE_MODE_SOURCE,
            'description': REMOTE_SITE_DESC,
            'secret': REMOTE_SITE_SECRET,
            'sodar_uuid': site.sodar_uuid,
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }

        model_dict = model_to_dict(site)
        self.assertEqual(model_dict, expected)

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(response, reverse('projectroles:remote_sites'))

    def test_create_target_existing_name(self):
        """Test creating a target site with an existing name"""

        # Set up existing site
        self.target_site = self._make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )

        # Assert precondition
        self.assertEqual(RemoteSite.objects.all().count(), 1)

        values = {
            'name': REMOTE_SITE_NAME,  # Old name
            'url': REMOTE_SITE_NEW_URL,
            'description': REMOTE_SITE_NEW_DESC,
            'secret': build_secret(),
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }

        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:remote_site_create'), values
            )

        # Assert postconditions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RemoteSite.objects.all().count(), 1)


class TestRemoteSiteUpdateView(RemoteSiteMixin, TestViewsBase):
    """Tests for remote site update view"""

    def setUp(self):
        super().setUp()

        # Set up target site
        self.target_site = self._make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )

    def test_render(self):
        """Test rendering the remote site create view as source"""

        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:remote_site_update',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                )
            )

        self.assertEqual(response.status_code, 200)

        # Assert form field values
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertEqual(form['name'].initial, REMOTE_SITE_NAME)
        self.assertEqual(form['url'].initial, REMOTE_SITE_URL)
        self.assertEqual(form['description'].initial, REMOTE_SITE_DESC)
        self.assertEqual(form['secret'].initial, REMOTE_SITE_SECRET)
        self.assertEqual(form.fields['secret'].widget.attrs['readonly'], True)
        self.assertEqual(form['user_display'].initial, REMOTE_SITE_USER_DISPLAY)

    def test_update(self):
        """Test creating a target site as source"""

        # Assert precondition
        self.assertEqual(RemoteSite.objects.all().count(), 1)

        values = {
            'name': REMOTE_SITE_NEW_NAME,
            'url': REMOTE_SITE_NEW_URL,
            'description': REMOTE_SITE_NEW_DESC,
            'secret': REMOTE_SITE_SECRET,
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:remote_site_update',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                ),
                values,
            )

        # Assert site state after creation
        self.assertEqual(RemoteSite.objects.all().count(), 1)
        site = RemoteSite.objects.first()

        expected = {
            'id': site.pk,
            'name': REMOTE_SITE_NEW_NAME,
            'url': REMOTE_SITE_NEW_URL,
            'mode': SITE_MODE_TARGET,
            'description': REMOTE_SITE_NEW_DESC,
            'secret': REMOTE_SITE_SECRET,
            'sodar_uuid': site.sodar_uuid,
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }

        model_dict = model_to_dict(site)
        self.assertEqual(model_dict, expected)

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(response, reverse('projectroles:remote_sites'))

    def test_update_existing_name(self):
        """Test creating a target site with an existing name as source (should fail)"""

        # Create new site
        new_target_site = self._make_site(
            name=REMOTE_SITE_NEW_NAME,
            url=REMOTE_SITE_NEW_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_NEW_DESC,
            secret=REMOTE_SITE_NEW_SECRET,
        )

        # Assert precondition
        self.assertEqual(RemoteSite.objects.all().count(), 2)

        values = {
            'name': REMOTE_SITE_NAME,  # Old name
            'url': REMOTE_SITE_NEW_URL,
            'description': REMOTE_SITE_NEW_DESC,
            'secret': REMOTE_SITE_SECRET,
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:remote_site_update',
                    kwargs={'remotesite': new_target_site.sodar_uuid},
                ),
                values,
            )

        # Assert postconditions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RemoteSite.objects.all().count(), 2)


class TestRemoteSiteDeleteView(RemoteSiteMixin, TestViewsBase):
    """Tests for remote site delete view"""

    def setUp(self):
        super().setUp()

        # Set up target site
        self.target_site = self._make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )

    def test_render(self):
        """Test rendering the remote site delete view"""

        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:remote_site_delete',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                )
            )

        self.assertEqual(response.status_code, 200)

    def test_delete(self):
        """Test deleting the remote site"""

        # Assert precondition
        self.assertEqual(RemoteSite.objects.all().count(), 1)

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:remote_site_delete',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                )
            )
            self.assertRedirects(response, reverse('projectroles:remote_sites'))

        # Assert site status
        self.assertEqual(RemoteSite.objects.all().count(), 0)


class TestRemoteProjectsBatchUpdateView(
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    TestViewsBase,
):
    """Tests for remote project batch update view"""

    def setUp(self):
        super().setUp()

        # Set up project
        self.category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        # Set up target site
        self.target_site = self._make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )

    def test_render_confirm(self):
        """Test rendering the remote project update view in confirm mode"""

        access_field = 'remote_access_{}'.format(self.project.sodar_uuid)
        values = {access_field: SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO']}

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:remote_projects_update',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                ),
                values,
            )

            # Assert postconditions
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['site'], self.target_site)
            self.assertIsNotNone(response.context['modifying_access'])

    def test_render_confirm_no_change(self):
        """Test rendering the remote project update view without changes (should redirect)"""

        access_field = 'remote_access_{}'.format(self.project.sodar_uuid)
        values = {access_field: SODAR_CONSTANTS['REMOTE_LEVEL_NONE']}

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:remote_projects_update',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                ),
                values,
            )

            # Assert postconditions
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:remote_projects',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                ),
            )

    def test_post_create(self):
        """Test updating remote project access by adding a new RemoteProject"""

        # Assert precondition
        self.assertEqual(RemoteProject.objects.all().count(), 0)

        access_field = 'remote_access_{}'.format(self.project.sodar_uuid)
        values = {
            access_field: SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO'],
            'update-confirmed': 1,
        }

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:remote_projects_update',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                ),
                values,
            )

            # Assert postconditions
            self.assertEqual(RemoteProject.objects.all().count(), 1)
            rp = RemoteProject.objects.first()
            self.assertEqual(rp.project_uuid, self.project.sodar_uuid)
            self.assertEqual(
                rp.level, SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO']
            )

            self.assertRedirects(
                response,
                reverse(
                    'projectroles:remote_projects',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                ),
            )

    def test_post_update(self):
        """Test updating remote project access by modifying an existing RemoteProject"""

        rp = self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL'],
        )

        # Assert precondition
        self.assertEqual(RemoteProject.objects.all().count(), 1)

        access_field = 'remote_access_{}'.format(self.project.sodar_uuid)
        values = {
            access_field: SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO'],
            'update-confirmed': 1,
        }

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:remote_projects_update',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                ),
                values,
            )

            # Assert postconditions
            self.assertEqual(RemoteProject.objects.all().count(), 1)
            rp.refresh_from_db()
            self.assertEqual(rp.project_uuid, self.project.sodar_uuid)
            self.assertEqual(
                rp.level, SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO']
            )

            self.assertRedirects(
                response,
                reverse(
                    'projectroles:remote_projects',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                ),
            )


class TestRemoteProjectGetAPIView(
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    TestViewsBase,
):
    """Tests for remote project getting API view"""

    def setUp(self):
        super().setUp()

        # Set up projects
        self.category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.cat_owner_as = self._make_assignment(
            self.category, self.user, self.role_owner
        )
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.project_owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        # Create target site
        self.target_site = self._make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )

        # Create remote project
        self.remote_project = self._make_remote_project(
            site=self.target_site,
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO'],
        )

        self.remote_api = RemoteProjectAPI()

    def test_get(self):
        """Test retrieving project data to the target site"""

        response = self.client.get(
            reverse(
                'projectroles:api_remote_get',
                kwargs={'secret': REMOTE_SITE_SECRET},
            )
        )

        self.assertEqual(response.status_code, 200)

        expected = self.remote_api.get_target_data(self.target_site)
        response_dict = json.loads(response.content.decode('utf-8'))

        self.assertEqual(response_dict, expected)

    def test_get_invalid_secret(self):
        """Test retrieving project data with an invalid secret (should fail)"""

        response = self.client.get(
            reverse(
                'projectroles:api_remote_get', kwargs={'secret': build_secret()}
            )
        )

        self.assertEqual(response.status_code, 401)

    def test_api_versioning(self):
        """Test SODAR API Access with correct version headers"""
        # TODO: Test with a more simple SODAR API view once implemented

        response = self.client.get(
            reverse(
                'projectroles:api_remote_get',
                kwargs={'secret': REMOTE_SITE_SECRET},
            ),
            HTTP_ACCEPT='{};version={}'.format(
                SODAR_API_MEDIA_TYPE, SODAR_API_VERSION
            ),
        )

        self.assertEqual(response.status_code, 200)

    def test_api_versioning_invalid_version(self):
        """Test SODAR API Access with unsupported version (should fail)"""
        # TODO: Test with a more simple SODAR API view once implemented

        response = self.client.get(
            reverse(
                'projectroles:api_remote_get',
                kwargs={'secret': REMOTE_SITE_SECRET},
            ),
            HTTP_ACCEPT='{};version={}'.format(
                SODAR_API_MEDIA_TYPE, SODAR_API_VERSION_INVALID
            ),
        )

        self.assertEqual(response.status_code, 406)

    def test_api_versioning_invalid_media_type(self):
        """Test SODAR API Access with unsupported media type (should fail)"""
        # TODO: Test with a more simple SODAR API view once implemented

        response = self.client.get(
            reverse(
                'projectroles:api_remote_get',
                kwargs={'secret': REMOTE_SITE_SECRET},
            ),
            HTTP_ACCEPT='{};version={}'.format(
                SODAR_API_MEDIA_TYPE_INVALID, SODAR_API_VERSION
            ),
        )

        self.assertEqual(response.status_code, 406)
