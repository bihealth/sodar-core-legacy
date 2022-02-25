"""UI view tests for the projectroles app"""

import json
from urllib.parse import urlencode

from django.contrib import auth
from django.contrib.messages import get_messages
from django.core import mail
from django.forms import HiddenInput
from django.forms.models import model_to_dict
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from test_plus.test import TestCase

from projectroles.app_settings import AppSettingAPI
from projectroles.models import (
    Project,
    Role,
    RoleAssignment,
    ProjectInvite,
    RemoteSite,
    RemoteProject,
    SODAR_CONSTANTS,
)
from projectroles.plugins import (
    get_backend_api,
    get_active_plugins,
)
from projectroles.utils import (
    build_secret,
    get_display_name,
    get_user_display_name,
)
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    AppSettingMixin,
    RemoteTargetMixin,
)
from projectroles.views import (
    MSG_USER_PROFILE_LDAP,
    MSG_INVITE_LDAP_LOCAL_VIEW,
    MSG_INVITE_LOCAL_NOT_ALLOWED,
    MSG_INVITE_LOGGED_IN_ACCEPT,
    MSG_INVITE_USER_NOT_EQUAL,
    MSG_INVITE_USER_EXISTS,
)


app_settings = AppSettingAPI()
User = auth.get_user_model()


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
EXAMPLE_APP_NAME = 'example_project_app'
INVALID_UUID = '11111111-1111-1111-1111-111111111111'

PROJECTROLES_APP_SETTINGS_TEST_LOCAL = {
    'test_setting': {
        'scope': 'PROJECT',  # PROJECT/USER
        'type': 'BOOLEAN',  # STRING/INTEGER/BOOLEAN
        'default': False,
        'label': 'Test setting',  # Optional, defaults to name/key
        'description': 'Test setting',  # Optional
        'user_modifiable': True,  # Optional, show/hide in forms
        'local': False,
    },
    'test_setting_local': {
        'scope': 'PROJECT',  # PROJECT/USER
        'type': 'BOOLEAN',  # STRING/INTEGER/BOOLEAN
        'default': False,
        'label': 'Test setting',  # Optional, defaults to name/key
        'description': 'Test setting',  # Optional
        'user_modifiable': True,  # Optional, show/hide in forms
        'local': True,
    },
}


class TestViewsBase(TestCase):
    """Base class for view testing"""

    def setUp(self):
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
        """Test rendering the home view"""
        with self.login(self.user):
            response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        custom_cols = response.context['project_custom_cols']
        self.assertEqual(len(custom_cols), 2)
        self.assertEqual(custom_cols[0]['column_id'], 'links')
        self.assertEqual(response.context['project_col_count'], 4)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_render_anon(self):
        """Test rendering with anonymous access"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)


class TestProjectSearchView(ProjectMixin, RoleAssignmentMixin, TestViewsBase):
    """Tests for the project search results view"""

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
        """Test rendering project search view"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_terms'], ['test'])
        self.assertEqual(response.context['search_keywords'], {})
        self.assertEqual(response.context['search_type'], None)
        self.assertEqual(response.context['search_input'], 'test')
        self.assertEqual(
            len(response.context['app_search_data']),
            len([p for p in self.plugins if p.search_enable]),
        )

    def test_render_search_type(self):
        """Test rendering with search type"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search')
                + '?'
                + urlencode({'s': 'test type:file'})
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_terms'], ['test'])
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

    def test_render_non_text_input(self):
        """Test non-text input from standard search (should redirect)"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search') + '?s=+++'
            )
            self.assertRedirects(response, reverse('home'))

    def test_render_advanced(self):
        """Test input from advanced search"""
        new_project = self._make_project(
            'AnotherProject',
            PROJECT_TYPE_PROJECT,
            self.category,
            description='xxx',
        )
        self.cat_owner_as = self._make_assignment(
            new_project, self.user, self.role_owner
        )

        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search')
                + '?'
                + urlencode({'m': 'testproject\r\nxxx', 'k': ''})
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['search_terms'], ['testproject', 'xxx']
        )
        self.assertEqual(response.context['search_keywords'], {})
        self.assertEqual(response.context['search_type'], None)
        self.assertEqual(len(response.context['project_results']), 2)

    def test_render_advanced_short_input(self):
        """Test input from advanced search with a short term (< 3 characters)"""
        new_project = self._make_project(
            'AnotherProject',
            PROJECT_TYPE_PROJECT,
            self.category,
            description='xxx',
        )
        self.cat_owner_as = self._make_assignment(
            new_project, self.user, self.role_owner
        )

        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search')
                + '?'
                + urlencode({'m': 'testproject\r\nxx', 'k': ''})
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_terms'], ['testproject'])
        self.assertEqual(len(response.context['project_results']), 1)

    def test_render_advanced_empty_input(self):
        """Test input from advanced search with empty term (should be ignored)"""
        new_project = self._make_project(
            'AnotherProject',
            PROJECT_TYPE_PROJECT,
            self.category,
            description='xxx',
        )
        self.cat_owner_as = self._make_assignment(
            new_project, self.user, self.role_owner
        )

        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search')
                + '?'
                + urlencode({'m': 'testproject\r\n\r\nxxx', 'k': ''})
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['search_terms'], ['testproject', 'xxx']
        )
        self.assertEqual(len(response.context['project_results']), 2)

    def test_render_advanced_dupe(self):
        """Test input from advanced search with a duplicate term"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search')
                + '?'
                + urlencode({'m': 'xxx\r\nxxx', 'k': ''})
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_terms'], ['xxx'])

    @override_settings(PROJECTROLES_ENABLE_SEARCH=False)
    def test_disable_search(self):
        """Test redirecting the view due to search being disabled"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
            )
            self.assertRedirects(response, reverse('home'))


class TestProjectAdvancedSearchView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for the advanced search view"""

    def test_render(self):
        """Test to ensure the advanced search view renders correctly"""
        with self.login(self.user):
            response = self.client.get(reverse('projectroles:search_advanced'))
        self.assertEqual(response.status_code, 200)

    @override_settings(PROJECTROLES_ENABLE_SEARCH=False)
    def test_disable_search(self):
        """Test redirecting the view due to search being disabled"""
        with self.login(self.user):
            response = self.client.get(reverse('projectroles:search_advanced'))
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

    def test_render_not_found(self):
        """Test rendering of project detail view with invalid UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:detail',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)


class TestProjectCreateView(ProjectMixin, RoleAssignmentMixin, TestViewsBase):
    """Tests for Project creation view"""

    def setUp(self):
        super().setUp()
        app_alerts = get_backend_api('appalerts_backend')
        if app_alerts:
            self.app_alert_model = app_alerts.get_model()

    def test_render_top(self):
        """Test rendering top level category creation form"""
        with self.login(self.user):
            response = self.client.get(reverse('projectroles:create'))

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertEqual(form.initial['type'], PROJECT_TYPE_CATEGORY)
        self.assertIsInstance(form.fields['type'].widget, HiddenInput)
        self.assertIsInstance(form.fields['parent'].widget, HiddenInput)
        self.assertEqual(form.initial['owner'], self.user)

    def test_render_sub(self):
        """Test rendering if creating a subproject"""
        category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self._make_assignment(category, self.user, self.role_owner)
        # Create another user to enable checking for owner selection
        self.make_user('new_user')

        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:create',
                    kwargs={'project': category.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)

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
        self.assertEqual(form.initial['owner'], self.user)

    def test_render_sub_cat_member(self):
        """Test rendering under a category as a category non-owner"""
        category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self._make_assignment(category, self.user, self.role_owner)
        new_user = self.make_user('new_user')
        self._make_assignment(category, new_user, self.role_contributor)

        with self.login(new_user):
            response = self.client.get(
                reverse(
                    'projectroles:create',
                    kwargs={'project': category.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        # Current user should be the initial value for owner
        self.assertEqual(form.initial['owner'], new_user)

    def test_render_sub_project(self):
        """Test rendering if creating under a project (should fail)"""
        project = self._make_project('TestProject', PROJECT_TYPE_PROJECT, None)
        self._make_assignment(project, self.user, self.role_owner)
        # Create another user to enable checking for owner selection
        self.make_user('new_user')

        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:create',
                    kwargs={'project': project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 302)

    def test_render_sub_not_found(self):
        """Test rendering with invalid parent UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:create',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_render_parent_owner(self):
        """Test rendering with parent owner as initial value"""
        category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        user_new = self.make_user('new_user')
        self._make_assignment(category, user_new, self.role_owner)

        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:create',
                    kwargs={'project': category.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(form.initial['owner'], user_new)

    def test_create_top_level_category(self):
        """Test creation of top level category"""
        self.assertEqual(Project.objects.all().count(), 0)

        values = {
            'title': 'TestCategory',
            'type': PROJECT_TYPE_CATEGORY,
            'parent': '',
            'owner': self.user.sodar_uuid,
            'submit_status': SUBMIT_STATUS_OK,
            'description': 'description',
            'public_guest_access': False,
        }
        # Add settings values
        values.update(
            app_settings.get_all_defaults(
                APP_SETTING_SCOPE_PROJECT, post_safe=True
            )
        )
        with self.login(self.user):
            response = self.client.post(reverse('projectroles:create'), values)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Project.objects.all().count(), 1)
        project = Project.objects.first()
        self.assertIsNotNone(project)
        # Same user so no alerts or emails
        self.assertEqual(self.app_alert_model.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        expected = {
            'id': project.pk,
            'title': 'TestCategory',
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'submit_status': SUBMIT_STATUS_OK,
            'description': 'description',
            'public_guest_access': False,
            'full_title': 'TestCategory',
            'has_public_children': False,
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
        values = {
            'title': 'TestCategory',
            'type': PROJECT_TYPE_CATEGORY,
            'parent': '',
            'owner': self.user.sodar_uuid,
            'submit_status': SUBMIT_STATUS_OK,
            'description': 'description',
            'public_guest_access': False,
        }
        # Add settings values
        values.update(
            app_settings.get_all_defaults(
                APP_SETTING_SCOPE_PROJECT, post_safe=True
            )
        )

        with self.login(self.user):
            response = self.client.post(reverse('projectroles:create'), values)
        self.assertEqual(response.status_code, 302)
        category = Project.objects.first()
        self.assertIsNotNone(category)

        # Make project with owner in Django
        values = {
            'title': 'TestProject',
            'type': PROJECT_TYPE_PROJECT,
            'parent': category.sodar_uuid,
            'owner': self.user.sodar_uuid,
            'description': 'description',
            'public_guest_access': False,
        }
        # Add settings values
        values.update(
            app_settings.get_all_defaults(
                APP_SETTING_SCOPE_PROJECT, post_safe=True
            )
        )
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:create',
                    kwargs={'project': category.sodar_uuid},
                ),
                values,
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Project.objects.all().count(), 2)
        project = Project.objects.get(type=PROJECT_TYPE_PROJECT)
        # No alerts or emails should be sent as the same user triggered this
        self.assertEqual(self.app_alert_model.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        expected = {
            'id': project.pk,
            'title': 'TestProject',
            'type': PROJECT_TYPE_PROJECT,
            'parent': category.pk,
            'submit_status': SUBMIT_STATUS_OK,
            'description': 'description',
            'public_guest_access': False,
            'full_title': 'TestCategory / TestProject',
            'has_public_children': False,
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

    def test_create_project_cat_member(self):
        """Test Project creation as category member"""
        # Create category and add new user as member
        category = self._make_project(
            title='TestCategory', type=PROJECT_TYPE_CATEGORY, parent=None
        )
        self._make_assignment(category, self.user, self.role_owner)
        new_user = self.make_user('new_user')
        self._make_assignment(category, new_user, self.role_contributor)

        values = {
            'title': 'TestProject',
            'type': PROJECT_TYPE_PROJECT,
            'parent': category.sodar_uuid,
            'owner': new_user.sodar_uuid,
            'description': 'description',
            'public_guest_access': False,
        }
        values.update(
            app_settings.get_all_defaults(
                APP_SETTING_SCOPE_PROJECT, post_safe=True
            )
        )
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:create',
                    kwargs={'project': category.sodar_uuid},
                ),
                values,
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Project.objects.all().count(), 2)
        project = Project.objects.get(type=PROJECT_TYPE_PROJECT)
        self.assertEqual(project.get_owner().user, new_user)
        # Alert and email for parent owner should be created
        self.assertEqual(self.app_alert_model.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)


class TestProjectUpdateView(
    ProjectMixin, RoleAssignmentMixin, RemoteTargetMixin, TestViewsBase
):
    """Tests for Project updating view"""

    def setUp(self):
        super().setUp()
        self.category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as_cat = self._make_assignment(
            self.category, self.user, self.role_owner
        )
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )
        app_alerts = get_backend_api('appalerts_backend')
        if app_alerts:
            self.app_alert_model = app_alerts.get_model()

    def test_render_project(self):
        """Test rendering of Project updating form with an existing project"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:update',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsInstance(form.fields['type'].widget, HiddenInput)
        self.assertNotIsInstance(form.fields['parent'].widget, HiddenInput)
        self.assertIsInstance(form.fields['owner'].widget, HiddenInput)

    def test_render_parent(self):
        """Test current parent selectability without parent role"""
        # Create new user and project, make new user the owner
        user_new = self.make_user('new_user')
        self.owner_as.user = user_new
        self.owner_as.save()
        # Create another category with new user as owner
        category2 = self._make_project(
            'TestCategory2', PROJECT_TYPE_CATEGORY, None
        )
        self._make_assignment(category2, user_new, self.role_owner)

        with self.login(user_new):
            response = self.client.get(
                reverse(
                    'projectroles:update',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        # Ensure self.category (with no user_new rights) is initial
        self.assertEqual(form.initial['parent'], self.category.sodar_uuid)
        self.assertEqual(len(form.fields['parent'].choices), 2)

    def test_update_project(self):
        """Test Project updating"""
        timeline = get_backend_api('timeline_backend')
        new_category = self._make_project('NewCat', PROJECT_TYPE_CATEGORY, None)
        self._make_assignment(new_category, self.user, self.role_owner)

        self.assertEqual(Project.objects.all().count(), 3)

        values = model_to_dict(self.project)
        values['title'] = 'updated title'
        values['description'] = 'updated description'
        values['parent'] = new_category.sodar_uuid  # NOTE: Updated parent
        values['owner'] = self.user.sodar_uuid  # NOTE: Must add owner
        # Add settings values
        ps = app_settings.get_all_settings(project=self.project, post_safe=True)
        # Edit settings to non-default values
        ps['settings.example_project_app.project_int_setting'] = 1
        ps['settings.example_project_app.project_str_setting'] = 'test'
        ps['settings.example_project_app.project_bool_setting'] = True
        ps['settings.example_project_app.project_json_setting'] = '{}'
        ps['settings.projectroles.ip_restrict'] = True
        ps['settings.projectroles.ip_allowlist'] = '["192.168.1.1"]'
        values.update(ps)

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:update',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )

        self.assertEqual(Project.objects.all().count(), 3)
        self.project.refresh_from_db()
        self.assertIsNotNone(self.project)
        # No alert or mail, because the owner has not changed
        self.assertEqual(self.app_alert_model.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        expected = {
            'id': self.project.pk,
            'title': 'updated title',
            'type': PROJECT_TYPE_PROJECT,
            'parent': new_category.pk,
            'submit_status': SUBMIT_STATUS_OK,
            'description': 'updated description',
            'public_guest_access': False,
            'full_title': new_category.title + ' / ' + 'updated title',
            'has_public_children': False,
            'sodar_uuid': self.project.sodar_uuid,
        }
        model_dict = model_to_dict(self.project)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        # Assert settings
        for k, v in ps.items():
            v_json = None
            try:
                v_json = json.loads(v)
            except Exception:
                pass
            s = app_settings.get_app_setting(
                k.split('.')[1],
                k.split('.')[2],
                project=self.project,
                post_safe=True,
            )
            if isinstance(
                v_json,
                (
                    dict,
                    list,
                ),
            ):
                self.assertEqual(json.loads(s), v_json)
            else:
                self.assertEqual(s, v)

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:detail',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )

        # Assert timeline event
        tl_event = (
            timeline.get_project_events(self.project).order_by('-pk').first()
        )
        self.assertEqual(tl_event.event_name, 'project_update')
        self.assertIn('title', tl_event.extra_data)
        self.assertIn('description', tl_event.extra_data)
        self.assertIn('parent', tl_event.extra_data)

    def test_render_category(self):
        """Test rendering with existing category"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:update',
                    kwargs={'project': self.category.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsInstance(form.fields['type'].widget, HiddenInput)
        self.assertNotIsInstance(form.fields['parent'].widget, HiddenInput)
        self.assertIsInstance(form.fields['owner'].widget, HiddenInput)

    def test_update_category(self):
        """Test category updating"""
        self.assertEqual(Project.objects.all().count(), 2)

        values = model_to_dict(self.category)
        values['title'] = 'updated title'
        values['description'] = 'updated description'
        values['owner'] = self.user.sodar_uuid  # NOTE: Must add owner
        values['parent'] = ''
        # Add settings values
        values.update(
            app_settings.get_all_settings(project=self.category, post_safe=True)
        )
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:update',
                    kwargs={'project': self.category.sodar_uuid},
                ),
                values,
            )
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Project.objects.all().count(), 2)
        self.category.refresh_from_db()
        self.assertIsNotNone(self.category)
        # Ensure no alert or email (owner not updated)
        self.assertEqual(self.app_alert_model.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        expected = {
            'id': self.category.pk,
            'title': 'updated title',
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'submit_status': SUBMIT_STATUS_OK,
            'description': 'updated description',
            'public_guest_access': False,
            'full_title': 'updated title',
            'has_public_children': False,
            'sodar_uuid': self.category.sodar_uuid,
        }
        model_dict = model_to_dict(self.category)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        # TODO: Assert settings

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:detail',
                    kwargs={'project': self.category.sodar_uuid},
                ),
            )

    def test_update_category_parent(self):
        """Test category parent updating to ensure titles are changed"""
        new_category = self._make_project(
            'NewCategory', PROJECT_TYPE_CATEGORY, None
        )
        self._make_assignment(new_category, self.user, self.role_owner)

        self.assertEqual(
            self.category.full_title,
            self.category.title,
        )
        self.assertEqual(
            self.project.full_title,
            self.category.title + ' / ' + self.project.title,
        )

        values = model_to_dict(self.category)
        values['title'] = self.category.title
        values['description'] = self.category.description
        values['owner'] = self.user.sodar_uuid  # NOTE: Must add owner
        values['parent'] = new_category.sodar_uuid  # Updated category
        # Add settings values
        values.update(
            app_settings.get_all_settings(project=self.category, post_safe=True)
        )

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:update',
                    kwargs={'project': self.category.sodar_uuid},
                ),
                values,
            )

        self.assertEqual(response.status_code, 302)
        # Assert category state and project title after update
        self.category.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(self.category.parent, new_category)
        self.assertEqual(
            self.category.full_title,
            new_category.title + ' / ' + self.category.title,
        )
        self.assertEqual(
            self.project.full_title,
            new_category.title
            + ' / '
            + self.category.title
            + ' / '
            + self.project.title,
        )

    def test_update_public_access(self):
        """Test Project updating with public guest access"""
        self.assertEqual(self.project.public_guest_access, False)
        self.assertEqual(self.category.has_public_children, False)

        values = model_to_dict(self.project)
        values['public_guest_access'] = True
        values['parent'] = self.category.sodar_uuid  # NOTE: Must add parent
        values['owner'] = self.user.sodar_uuid  # NOTE: Must add owner
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

        self.assertEqual(response.status_code, 302)
        self.project.refresh_from_db()
        self.category.refresh_from_db()
        self.assertEqual(self.project.public_guest_access, True)
        # Assert the parent category has_public_children is set true
        self.assertEqual(self.category.has_public_children, True)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_render_remote(self):
        """Test rendering form for remote site as target"""
        self._set_up_as_target(projects=[self.category, self.project])

        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:update',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsInstance(form.fields['title'].widget, HiddenInput)
        self.assertIsInstance(form.fields['type'].widget, HiddenInput)
        self.assertIsInstance(form.fields['parent'].widget, HiddenInput)
        self.assertIsInstance(form.fields['description'].widget, HiddenInput)
        self.assertIsInstance(form.fields['readme'].widget, HiddenInput)
        self.assertNotIsInstance(
            form.fields[
                'settings.example_project_app.project_str_setting'
            ].widget,
            HiddenInput,
        )
        self.assertNotIsInstance(
            form.fields[
                'settings.example_project_app.project_int_setting'
            ].widget,
            HiddenInput,
        )
        self.assertNotIsInstance(
            form.fields[
                'settings.example_project_app.project_bool_setting'
            ].widget,
            HiddenInput,
        )
        self.assertTrue(
            form.fields['settings.projectroles.ip_restrict'].disabled
        )
        self.assertTrue(
            form.fields['settings.projectroles.ip_allowlist'].disabled
        )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_update_remote(self):
        """Test updating remote project as target"""
        self._set_up_as_target(projects=[self.category, self.project])

        values = model_to_dict(self.project)
        values['owner'] = self.user.sodar_uuid
        values['parent'] = self.category.sodar_uuid
        values['settings.example_project_app.project_int_setting'] = 0
        values['settings.example_project_app.project_int_setting_options'] = 0
        values['settings.example_project_app.project_str_setting'] = 'test'
        values[
            'settings.example_project_app.project_str_setting_options'
        ] = 'string1'
        values['settings.example_project_app.project_bool_setting'] = True
        values['settings.projectroles.ip_restrict'] = True
        values['settings.projectroles.ip_allowlist'] = '["192.168.1.1"]'

        self.assertEqual(Project.objects.all().count(), 2)

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:update',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Project.objects.all().count(), 2)

    def test_render_not_found(self):
        """Test rendering with invalid project UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:update',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)


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
        self.setting_str = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='project_str_setting',
            setting_type='STRING',
            value='',
            project=self.project,
        )

        # Init string setting with options
        self.setting_str_options = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='project_str_setting_options',
            setting_type='STRING',
            value='string1',
            project=self.project,
        )

        # Init integer setting
        self.setting_int = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='project_int_setting',
            setting_type='INTEGER',
            value=0,
            project=self.project,
        )

        # Init integer setting with options
        self.setting_int_options = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='project_int_setting_options',
            setting_type='INTEGER',
            value=0,
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

        # Init IP restrict setting
        self.setting_ip_restrict = self._make_setting(
            app_name='projectroles',
            name='ip_restrict',
            setting_type='BOOLEAN',
            value=False,
            project=self.project,
        )

        # Init IP allowlist setting
        self.setting_ip_allowlist = self._make_setting(
            app_name='projectroles',
            name='ip_allowlist',
            setting_type='JSON',
            value=None,
            value_json=[],
            project=self.project,
        )

    def test_get(self):
        """Test rendering settings values"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:update',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'])
        field = response.context['form'].fields.get(
            'settings.%s.project_str_setting' % EXAMPLE_APP_NAME
        )
        self.assertIsNotNone(field)
        self.assertEqual(field.widget.attrs['placeholder'], 'Example string')
        field = response.context['form'].fields.get(
            'settings.%s.project_int_setting' % EXAMPLE_APP_NAME
        )
        self.assertIsNotNone(field)
        self.assertEqual(field.widget.attrs['placeholder'], 0)
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.%s.project_str_setting_options' % EXAMPLE_APP_NAME
            )
        )
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.%s.project_int_setting_options' % EXAMPLE_APP_NAME
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
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.projectroles.ip_restrict'
            )
        )
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.projectroles.ip_allowlist'
            )
        )

    def test_post(self):
        """Test modifying settings values"""
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
                EXAMPLE_APP_NAME,
                'project_str_setting_options',
                project=self.project,
            ),
            'string1',
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME,
                'project_int_setting_options',
                project=self.project,
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
        self.assertEqual(
            app_settings.get_app_setting(
                'projectroles', 'ip_restrict', project=self.project
            ),
            False,
        )
        self.assertEqual(
            app_settings.get_app_setting(
                'projectroles', 'ip_allowlist', project=self.project
            ),
            [],
        )

        values = {
            'settings.%s.project_str_setting' % EXAMPLE_APP_NAME: 'updated',
            'settings.%s.project_int_setting' % EXAMPLE_APP_NAME: 170,
            'settings.%s.project_str_setting_options'
            % EXAMPLE_APP_NAME: 'string2',
            'settings.%s.project_int_setting_options' % EXAMPLE_APP_NAME: 1,
            'settings.%s.project_bool_setting' % EXAMPLE_APP_NAME: True,
            'settings.%s.project_json_setting'
            % EXAMPLE_APP_NAME: '{"Test": "Updated"}',
            'settings.projectroles.ip_restrict': True,
            'settings.projectroles.ip_allowlist': '["192.168.1.1"]',
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
                EXAMPLE_APP_NAME,
                'project_str_setting_options',
                project=self.project,
            ),
            'string2',
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME,
                'project_int_setting_options',
                project=self.project,
            ),
            1,
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
        self.assertEqual(
            app_settings.get_app_setting(
                'projectroles', 'ip_restrict', project=self.project
            ),
            True,
        )
        self.assertEqual(
            app_settings.get_app_setting(
                'projectroles', 'ip_allowlist', project=self.project
            ),
            ['192.168.1.1'],
        )


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
class TestProjectSettingsFormTarget(
    RemoteSiteMixin,
    RemoteProjectMixin,
    AppSettingMixin,
    TestViewsBase,
    ProjectMixin,
    RoleAssignmentMixin,
):
    """
    Tests for project settings in the project create/update view on target site
    """

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

        # Create site
        self.site = self._make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_SOURCE'],
            description='',
            secret=REMOTE_SITE_SECRET,
        )

        self.remote_project = self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )

        # Init string setting
        self.setting_str = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='project_str_setting',
            setting_type='STRING',
            value='',
            project=self.project,
        )

        # Init string setting with options
        self.setting_str_options = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='project_str_setting_options',
            setting_type='STRING',
            value='string1',
            project=self.project,
        )

        # Init integer setting
        self.setting_int = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='project_int_setting',
            setting_type='INTEGER',
            value='0',
            project=self.project,
        )

        # Init integer setting with options
        self.setting_int_options = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='project_int_setting_options',
            setting_type='INTEGER',
            value=0,
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
                'settings.%s.project_str_setting_options' % EXAMPLE_APP_NAME
            )
        )
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.%s.project_int_setting_options' % EXAMPLE_APP_NAME
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
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.projectroles.ip_restrict'
            )
        )
        self.assertTrue(
            response.context['form']
            .fields.get('settings.projectroles.ip_restrict')
            .disabled
        )
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.projectroles.ip_allowlist'
            )
        )
        self.assertTrue(
            response.context['form']
            .fields.get('settings.projectroles.ip_allowlist')
            .disabled
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
                EXAMPLE_APP_NAME,
                'project_str_setting_options',
                project=self.project,
            ),
            'string1',
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME,
                'project_int_setting_options',
                project=self.project,
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
            'settings.%s.project_str_setting_options'
            % EXAMPLE_APP_NAME: 'string2',
            'settings.%s.project_int_setting_options' % EXAMPLE_APP_NAME: 1,
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
                EXAMPLE_APP_NAME,
                'project_str_setting_options',
                project=self.project,
            ),
            'string2',
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME,
                'project_int_setting_options',
                project=self.project,
            ),
            1,
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


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
@override_settings(
    PROJECTROLES_APP_SETTINGS_TEST=PROJECTROLES_APP_SETTINGS_TEST_LOCAL
)
class TestProjectSettingsFormTargetLocal(
    RemoteSiteMixin,
    RemoteProjectMixin,
    AppSettingMixin,
    TestViewsBase,
    ProjectMixin,
    RoleAssignmentMixin,
):
    """
    Tests for project settings in the project create/update view on target site
    """

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

        # Create site
        self.site = self._make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_SOURCE'],
            description='',
            secret=REMOTE_SITE_SECRET,
        )

        self.remote_project = self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )

        # Init string setting
        self.setting_str = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='project_str_setting',
            setting_type='STRING',
            value='',
            project=self.project,
        )

        # Init string setting with options
        self.setting_str_options = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='project_str_setting_options',
            setting_type='STRING',
            value='string1',
            project=self.project,
        )

        # Init integer setting
        self.setting_int = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='project_int_setting',
            setting_type='INTEGER',
            value='0',
            project=self.project,
        )

        # Init integer setting with options
        self.setting_int_options = self._make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='project_int_setting_options',
            setting_type='INTEGER',
            value=0,
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
        """Test rendering settings values as target"""
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
                'settings.%s.project_str_setting_options' % EXAMPLE_APP_NAME
            )
        )
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.%s.project_int_setting_options' % EXAMPLE_APP_NAME
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
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.projectroles.test_setting_local'
            )
        )
        self.assertFalse(
            response.context['form']
            .fields.get('settings.projectroles.test_setting_local')
            .disabled
        )
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.projectroles.test_setting'
            )
        )
        self.assertTrue(
            response.context['form']
            .fields.get('settings.projectroles.test_setting')
            .disabled
        )

    def test_post(self):
        """Test modifying settings values as target"""
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
                EXAMPLE_APP_NAME,
                'project_str_setting_options',
                project=self.project,
            ),
            'string1',
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME,
                'project_int_setting_options',
                project=self.project,
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
        self.assertEqual(
            app_settings.get_app_setting(
                'projectroles', 'test_setting', project=self.project
            ),
            False,
        )

        values = {
            'settings.%s.project_str_setting' % EXAMPLE_APP_NAME: 'updated',
            'settings.%s.project_int_setting' % EXAMPLE_APP_NAME: 170,
            'settings.%s.project_str_setting_options'
            % EXAMPLE_APP_NAME: 'string2',
            'settings.%s.project_int_setting_options' % EXAMPLE_APP_NAME: 1,
            'settings.%s.project_bool_setting' % EXAMPLE_APP_NAME: True,
            'settings.%s.project_json_setting'
            % EXAMPLE_APP_NAME: '{"Test": "Updated"}',
            'settings.projectroles.test_setting_local': True,
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
                EXAMPLE_APP_NAME,
                'project_str_setting_options',
                project=self.project,
            ),
            'string2',
        )
        self.assertEqual(
            app_settings.get_app_setting(
                EXAMPLE_APP_NAME,
                'project_int_setting_options',
                project=self.project,
            ),
            1,
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
        self.assertEqual(
            app_settings.get_app_setting(
                'projectroles', 'test_setting_local', project=self.project
            ),
            True,
        )
        self.assertEqual(
            app_settings.get_app_setting(
                'projectroles', 'test_setting', project=self.project
            ),
            False,
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
        """Test rendering project roles view"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:roles',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project'].pk, self.project.pk)

        # Assert users
        expected = {
            'id': self.owner_as.pk,
            'project': self.project.pk,
            'role': self.role_owner.pk,
            'user': self.user.pk,
            'sodar_uuid': self.owner_as.sodar_uuid,
        }
        self.assertEqual(model_to_dict(response.context['owner']), expected)
        expected = {
            'id': self.delegate_as.pk,
            'project': self.project.pk,
            'role': self.role_delegate.pk,
            'user': self.user_delegate.pk,
            'sodar_uuid': self.delegate_as.sodar_uuid,
        }
        self.assertEqual(model_to_dict(response.context['delegate']), expected)
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

    def test_render_not_found(self):
        """Test rendering project roles view with invalid project UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:roles',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)


class TestRoleAssignmentCreateView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for RoleAssignment creation view"""

    def setUp(self):
        super().setUp()

        # Set up category and project
        self.category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.user_owner_cat = self.make_user('owner_cat')
        self.owner_as_cat = self._make_assignment(
            self.category, self.user_owner_cat, self.role_owner
        )
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.user_owner = self.make_user('owner')
        self.owner_as = self._make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        self.user_new = self.make_user('guest')

        app_alerts = get_backend_api('appalerts_backend')
        if app_alerts:
            self.app_alert_model = app_alerts.get_model()

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

    def test_render_not_found(self):
        """Test rendering with invalid project UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_create',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_create_assignment(self):
        """Test RoleAssignment creation"""
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_create'
            ).count(),
            0,
        )

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

        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        role_as = RoleAssignment.objects.get(
            project=self.project, user=self.user_new
        )
        expected = {
            'id': role_as.pk,
            'project': self.project.pk,
            'user': self.user_new.pk,
            'role': self.role_guest.pk,
            'sodar_uuid': role_as.sodar_uuid,
        }
        self.assertEqual(model_to_dict(role_as), expected)
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_create'
            ).count(),
            1,
        )

        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:roles',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )

    def test_create_delegate(self):
        """Test RoleAssignment creation with project delegate role"""
        self.assertEqual(RoleAssignment.objects.all().count(), 2)

        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_new.sodar_uuid,
            'role': self.role_delegate.pk,
        }
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:role_create',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        role_as = RoleAssignment.objects.get(
            project=self.project, user=self.user_new
        )
        expected = {
            'id': role_as.pk,
            'project': self.project.pk,
            'user': self.user_new.pk,
            'role': self.role_delegate.pk,
            'sodar_uuid': role_as.sodar_uuid,
        }
        self.assertEqual(model_to_dict(role_as), expected)

    def test_create_delegate_limit_reached(self):
        """Test RoleAssignment creation with exceeded delegate limit"""
        del_user = self.make_user('new_del_user')
        self._make_assignment(self.project, del_user, self.role_delegate)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)

        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_new.sodar_uuid,
            'role': self.role_delegate.pk,
        }
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:role_create',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertIsNone(
            RoleAssignment.objects.filter(
                project=self.project, user=self.user_new
            ).first()
        )

    @override_settings(PROJECTROLES_DELEGATE_LIMIT=2)
    def test_create_delegate_limit_increased(self):
        """Test RoleAssignment creation with delegate limit > 1"""
        del_user = self.make_user('new_del_user')
        self._make_assignment(self.project, del_user, self.role_delegate)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)

        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_new.sodar_uuid,
            'role': self.role_delegate.pk,
        }
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:role_create',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoleAssignment.objects.all().count(), 4)
        self.assertIsNotNone(
            RoleAssignment.objects.filter(
                project=self.project, user=self.user_new
            ).first()
        )

    def test_create_delegate_limit_inherited(self):
        """Test creation with existing delegate role for inherited owner"""
        self._make_assignment(
            self.project, self.user_owner_cat, self.role_delegate
        )
        self.assertEqual(RoleAssignment.objects.all().count(), 3)

        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_new.sodar_uuid,
            'role': self.role_delegate.pk,
        }
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:role_create',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )

        # NOTE: Limit should be reached, but inherited owner role is disregarded
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoleAssignment.objects.all().count(), 4)
        self.assertIsNotNone(
            RoleAssignment.objects.filter(
                project=self.project, user=self.user_new
            ).first()
        )

    def test_redirect_to_invite(self):
        """Test redirects for the ProjectInvite creation view"""
        values = {
            'project': self.project.sodar_uuid,
            'role': self.role_guest.pk,
            'text': 'test@example.com',
        }
        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:ajax_autocomplete_user_redirect'), values
            )
        self.assertEqual(response.status_code, 200)
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
        """Test if new options are being displayed by SODARUserRedirectWidget"""
        values = {
            'project': self.project.sodar_uuid,
            'role': self.role_guest.pk,
            'q': 'test@example.com',
        }
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:ajax_autocomplete_user_redirect'), values
            )
        self.assertEqual(response.status_code, 200)
        new_option = {
            'id': 'test@example.com',
            'text': 'Send an invite to "test@example.com"',
            'create_id': True,
        }
        data = json.loads(response.content)
        self.assertIn(new_option, data['results'])

    def test_dont_create_option(self):
        """Test for new options not displayed if not valid email addresses"""
        values = {
            'project': self.project.sodar_uuid,
            'role': self.role_guest.pk,
            'q': 'test@example',
        }
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:ajax_autocomplete_user_redirect'), values
            )
        self.assertEqual(response.status_code, 200)
        new_option = {
            'id': 'test@example.com',
            'text': 'Send an invite to "test@example"',
            'create_id': True,
        }
        data = json.loads(response.content)
        self.assertNotIn(new_option, data['results'])


class TestRoleAssignmentUpdateView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for RoleAssignment update view"""

    def setUp(self):
        super().setUp()

        # Set up category and project
        self.category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.user_owner_cat = self.make_user('owner_cat')
        self.owner_as_cat = self._make_assignment(
            self.category, self.user_owner_cat, self.role_owner
        )
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.user_owner = self.make_user('owner')
        self.owner_as = self._make_assignment(
            self.project, self.user_owner, self.role_owner
        )

        # Create guest user and role
        self.user_new = self.make_user('new_user')
        self.role_as = self._make_assignment(
            self.project, self.user_new, self.role_guest
        )

        app_alerts = get_backend_api('appalerts_backend')
        if app_alerts:
            self.app_alert_model = app_alerts.get_model()

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

    def test_render_not_found(self):
        """Test rendering with invalid assignment UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_update',
                    kwargs={'roleassignment': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_update_assignment(self):
        """Test RoleAssignment updating"""
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_update'
            ).count(),
            0,
        )

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

        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        role_as = RoleAssignment.objects.get(
            project=self.project, user=self.user_new
        )
        expected = {
            'id': role_as.pk,
            'project': self.project.pk,
            'user': self.user_new.pk,
            'role': self.role_contributor.pk,
            'sodar_uuid': role_as.sodar_uuid,
        }
        self.assertEqual(model_to_dict(role_as), expected)
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_update'
            ).count(),
            1,
        )
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:roles',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )

    def test_update_delegate(self):
        """Test RoleAssignment updating to delegate"""
        self.assertEqual(RoleAssignment.objects.all().count(), 3)

        values = {
            'project': self.role_as.project.sodar_uuid,
            'user': self.role_as.user.sodar_uuid,
            'role': self.role_delegate.pk,
        }
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:role_update',
                    kwargs={'roleassignment': self.role_as.sodar_uuid},
                ),
                values,
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        role_as = RoleAssignment.objects.get(
            project=self.project, user=self.user_new
        )
        expected = {
            'id': role_as.pk,
            'project': self.project.pk,
            'user': self.user_new.pk,
            'role': self.role_delegate.pk,
            'sodar_uuid': role_as.sodar_uuid,
        }
        self.assertEqual(model_to_dict(role_as), expected)

    def test_update_delegate_limit_reached(self):
        """Test RoleAssignment updating with exceeded delegate limit"""
        del_user = self.make_user('new_del_user')
        self._make_assignment(self.project, del_user, self.role_delegate)
        self.assertEqual(RoleAssignment.objects.all().count(), 4)

        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_new.sodar_uuid,
            'role': self.role_delegate.pk,
        }
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:role_update',
                    kwargs={'roleassignment': self.role_as.sodar_uuid},
                ),
                values,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(RoleAssignment.objects.all().count(), 4)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, user=self.user_new
            )
            .first()
            .role,
            self.role_guest,
        )

    @override_settings(PROJECTROLES_DELEGATE_LIMIT=2)
    def test_update_delegate_limit_increased(self):
        """Test RoleAssignment updating with delegate limit > 1"""
        del_user = self.make_user('new_del_user')
        self._make_assignment(self.project, del_user, self.role_delegate)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, role=self.role_delegate
            ).count(),
            1,
        )

        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_new.sodar_uuid,
            'role': self.role_delegate.pk,
        }
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:role_update',
                    kwargs={'roleassignment': self.role_as.sodar_uuid},
                ),
                values,
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, role=self.role_delegate
            ).count(),
            2,
        )

    def test_update_delegate_limit_inherited(self):
        """Test updating with existing delegate role for inherited owner"""
        self._make_assignment(
            self.project, self.user_owner_cat, self.role_delegate
        )
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, role=self.role_delegate
            ).count(),
            1,
        )

        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_new.sodar_uuid,
            'role': self.role_delegate.pk,
        }
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:role_update',
                    kwargs={'roleassignment': self.role_as.sodar_uuid},
                ),
                values,
            )

        # NOTE: Limit should be reached, but inherited owner role is disregarded
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, role=self.role_delegate
            ).count(),
            2,
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

        app_alerts = get_backend_api('appalerts_backend')
        if app_alerts:
            self.app_alert_model = app_alerts.get_model()

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

    def test_render_not_found(self):
        """Test rendering with invalid assignment UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_delete',
                    kwargs={'roleassignment': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_delete_assignment(self):
        """Test RoleAssignment deleting"""
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_delete'
            ).count(),
            0,
        )

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:role_delete',
                    kwargs={'roleassignment': self.role_as.sodar_uuid},
                )
            )

        self.assertEqual(RoleAssignment.objects.all().count(), 1)
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_delete'
            ).count(),
            1,
        )
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:roles',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )

    def test_delete_owner(self):
        """Test RoleAssignment owner deletion (should fail)"""
        owner_user = self.make_user('owner_user')
        self.owner_as.user = owner_user  # Not a superuser
        self.owner_as.save()
        self.assertEqual(RoleAssignment.objects.all().count(), 2)

        with self.login(owner_user):
            response = self.client.post(
                reverse(
                    'projectroles:role_delete',
                    kwargs={'roleassignment': self.owner_as.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)

    def test_delete_delegate(self):
        """Test RoleAssignment delegate deleting by contributor (should fail)"""
        contrib_user = self.make_user('contrib_user')
        self._make_assignment(self.project, contrib_user, self.role_contributor)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)

        with self.login(contrib_user):
            response = self.client.post(
                reverse(
                    'projectroles:role_delete',
                    kwargs={'roleassignment': self.role_as.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)


class TestRoleAssignmentOwnerTransferView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    def setUp(self):
        super().setUp()

        # Set up category and project
        self.category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.user_owner_cat = self.make_user('owner_cat')
        self.owner_as_cat = self._make_assignment(
            self.category, self.user_owner_cat, self.role_owner
        )
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.user_owner = self.make_user('owner')
        self.owner_as = self._make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        # Create guest user and role
        self.user_new = self.make_user('guest')
        self.role_as = self._make_assignment(
            self.project, self.user_new, self.role_guest
        )

        app_alerts = get_backend_api('appalerts_backend')
        if app_alerts:
            self.app_alert_model = app_alerts.get_model()

    def test_transfer_ownership(self):
        """Test ownership transfer"""
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:role_owner_transfer',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                data={
                    'project': self.project.sodar_uuid,
                    'old_owner_role': self.role_guest.pk,
                    'new_owner': self.user_new.sodar_uuid,
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.get_owner().user, self.user_new)
        self.assertEqual(
            RoleAssignment.objects.get(
                project=self.project, user=self.user_owner
            ).role,
            self.role_guest,
        )
        self.assertEqual(self.app_alert_model.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_transfer_as_old_owner(self):
        """Test ownership transfer as old owner (should only create one mail)"""
        with self.login(self.user_owner):
            response = self.client.post(
                reverse(
                    'projectroles:role_owner_transfer',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                data={
                    'project': self.project.sodar_uuid,
                    'old_owner_role': self.role_guest.pk,
                    'new_owner': self.user_new.sodar_uuid,
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.get_owner().user, self.user_new)
        self.assertEqual(
            RoleAssignment.objects.get(
                project=self.project, user=self.user_owner
            ).role,
            self.role_guest,
        )
        self.assertEqual(self.app_alert_model.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_transfer_ownership_inherited(self):
        """Test ownership transfer to an inherited owner"""
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:role_owner_transfer',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                data={
                    'project': self.project.sodar_uuid,
                    'old_owner_role': self.role_guest.pk,
                    'new_owner': self.user_owner_cat.sodar_uuid,
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.get_owner().user, self.user_owner_cat)
        self.assertEqual(
            RoleAssignment.objects.get(
                project=self.project, user=self.user_owner
            ).role,
            self.role_guest,
        )
        self.assertEqual(self.app_alert_model.objects.count(), 2)
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
        """Test rendering ProjectInvite creation form"""
        with self.login(self.owner_as.user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_create',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertIsNotNone(form)
        # Assert owner role is not selectable
        self.assertNotIn(
            [(self.role_owner.pk, self.role_owner.name)],
            form.fields['role'].choices,
        )

    def test_render_from_roleassignment(self):
        """Test rendering with forwarded values from RoleAssignment Form"""
        values = {
            'e': 'test@example.com',
            'r': self.role_contributor.pk,
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

        form = response.context['form']
        self.assertIsNotNone(form)
        # Assert owner role is not selectable
        self.assertNotIn(
            [(self.role_owner.pk, self.role_owner.name)],
            form.fields['role'].choices,
        )
        # Assert forwarded mail address and role have been set in the form
        self.assertEqual(
            form.fields['role'].initial, str(self.role_contributor.pk)
        )
        self.assertEqual(form.fields['email'].initial, 'test@example.com')

    def test_render_not_found(self):
        """Test rendering with invalid project UUID"""
        with self.login(self.owner_as.user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_create',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_create_invite(self):
        """Test ProjectInvite creation"""
        self.assertEqual(ProjectInvite.objects.all().count(), 0)

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

    @override_settings(AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE')
    @override_settings(ENABLE_LDAP=True)
    def test_accept_ldap(self):
        """Test accepting an LDAP invite"""
        invite = self._make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
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
                ),
                follow=True,
            )

        self.assertListEqual(
            response.redirect_chain,
            [
                (
                    reverse(
                        'projectroles:invite_process_ldap',
                        kwargs={'secret': invite.secret},
                    ),
                    302,
                ),
                (
                    reverse(
                        'projectroles:detail',
                        kwargs={'project': self.project.sodar_uuid},
                    ),
                    302,
                ),
            ],
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 0)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=self.new_user,
                role=self.role_contributor,
            ).count(),
            1,
        )

    @override_settings(AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE')
    @override_settings(ENABLE_LDAP=True)
    def test_accept_ldap_expired(self):
        """Test accepting an expired LDAP invite"""
        invite = self._make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
            date_expire=timezone.now(),
        )
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
                ),
                follow=True,
            )

        self.assertListEqual(
            response.redirect_chain,
            [
                (
                    reverse(
                        'projectroles:invite_process_ldap',
                        kwargs={'secret': invite.secret},
                    ),
                    302,
                ),
                (
                    reverse('home'),
                    302,
                ),
            ],
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 0)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=self.new_user,
                role=self.role_contributor,
            ).count(),
            0,
        )

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_accept_local(self):
        """Test accepting local invite (user doesn't exist and no user is logged in)"""
        # Init invite
        invite = self._make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)

        response = self.client.get(
            reverse(
                'projectroles:invite_accept',
                kwargs={'secret': invite.secret},
            ),
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'projectroles:invite_process_local',
                kwargs={'secret': invite.secret},
            ),
        )

        response = self.client.get(
            reverse(
                'projectroles:invite_process_local',
                kwargs={'secret': invite.secret},
            ),
        )
        email = response.context['form']['email'].value()
        username = response.context['form']['username'].value()
        self.assertEqual(email, invite.email)
        self.assertEqual(username, invite.email.split('@')[0])
        self.assertEqual(User.objects.count(), 2)

        response = self.client.post(
            reverse(
                'projectroles:invite_process_local',
                kwargs={'secret': invite.secret},
            ),
            data={
                'first_name': 'First',
                'last_name': 'Last',
                'username': username,
                'email': email,
                'password': 'asd',
                'password_confirm': 'asd',
            },
            follow=True,
        )
        self.assertListEqual(
            response.redirect_chain,
            [
                (
                    reverse(
                        'projectroles:detail',
                        kwargs={'project': self.project.sodar_uuid},
                    ),
                    302,
                ),
                (
                    reverse('login')
                    + '?next='
                    + reverse(
                        'projectroles:detail',
                        kwargs={'project': self.project.sodar_uuid},
                    ),
                    302,
                ),
            ],
        )
        user = User.objects.get(username=username)
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 0)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=user,
                role=self.role_contributor,
            ).count(),
            1,
        )

        with self.login(user, password='asd'):
            response = self.client.get(
                reverse(
                    'projectroles:detail',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )
        self.assertEqual(response.status_code, 200)

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_accept_expired_local(self):
        """Test user accepting an expired local invite"""
        invite = self._make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
            date_expire=timezone.now(),
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=self.new_user,
                role=self.role_contributor,
            ).count(),
            0,
        )

        response = self.client.get(
            reverse(
                'projectroles:invite_accept',
                kwargs={'secret': invite.secret},
            ),
            follow=True,
        )
        self.assertListEqual(
            response.redirect_chain,
            [
                (
                    reverse(
                        'projectroles:invite_process_local',
                        kwargs={'secret': invite.secret},
                    ),
                    302,
                ),
                (reverse('home'), 302),
                (
                    reverse('login') + '?next=/',
                    302,
                ),
            ],
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 0)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=self.new_user,
                role=self.role_contributor,
            ).count(),
            0,
        )

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    @override_settings(AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE')
    @override_settings(AUTH_LDAP_DOMAIN_PRINTABLE='EXAMPLE')
    @override_settings(ENABLE_LDAP=True)
    def test_accept_wrong_type_local(self):
        """Test accepting a local invite in the view processing LDAP invites"""
        invite = self._make_invite(
            email='test@different.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)

        response = self.client.get(
            reverse(
                'projectroles:invite_process_ldap',
                kwargs={'secret': invite.secret},
            ),
        )
        # LDAP expects user to be logged in
        self.assertRedirects(
            response,
            reverse('login')
            + '?next='
            + reverse(
                'projectroles:invite_process_ldap',
                kwargs={'secret': invite.secret},
            ),
        )

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    @override_settings(AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE')
    @override_settings(AUTH_LDAP_DOMAIN_PRINTABLE='EXAMPLE')
    @override_settings(ENABLE_LDAP=True)
    def test_accept_wrong_type_ldap(self):
        """Test accepting a LDAP invite in the view processing local invites"""
        invite = self._make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)

        response = self.client.get(
            reverse(
                'projectroles:invite_process_local',
                kwargs={'secret': invite.secret},
            ),
            follow=True,
        )
        self.assertRedirects(
            response, reverse('login') + '?next=' + reverse('home')
        )
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            MSG_INVITE_LDAP_LOCAL_VIEW,
        )

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=False)
    def test_accept_local_user_not_allowed(self):
        """Test accepting a local invite while local users are disabled"""
        invite = self._make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)

        response = self.client.get(
            reverse(
                'projectroles:invite_accept',
                kwargs={'secret': invite.secret},
            ),
            follow=True,
        )
        self.assertListEqual(
            response.redirect_chain,
            [
                (
                    reverse('home'),
                    302,
                ),
                (
                    reverse('login') + '?next=/',
                    302,
                ),
            ],
        )

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=False)
    def test_process_local_user_not_allowed(self):
        """Test processing local invite while local users are disabled"""
        invite = self._make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)

        response = self.client.get(
            reverse(
                'projectroles:invite_process_local',
                kwargs={'secret': invite.secret},
            ),
            follow=True,
        )
        self.assertRedirects(
            response, reverse('login') + '?next=' + reverse('home')
        )
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            MSG_INVITE_LOCAL_NOT_ALLOWED,
        )

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_accept_no_local_user_different_user_logged_in(self):
        """Test processing local invite while invited user doesn't exist and different user is logged in"""
        invite = self._make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)

        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_process_local',
                    kwargs={'secret': invite.secret},
                ),
                follow=True,
            )
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            MSG_INVITE_LOGGED_IN_ACCEPT,
        )

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_accept_local_user_exists_different_user_logged_in(self):
        """Test processing local invite while invited user exists but different user is logged in"""
        invited_user = self.make_user(INVITE_EMAIL.split('@')[0])
        invited_user.email = INVITE_EMAIL
        invited_user.save()
        invite = self._make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)

        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_process_local',
                    kwargs={'secret': invite.secret},
                ),
                follow=True,
            )
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            MSG_INVITE_USER_NOT_EQUAL,
        )

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_accept_local_user_exists_is_logged_in(self):
        """Test processing local invite while invited user exists and is logged in"""
        invited_user = self.make_user(INVITE_EMAIL.split('@')[0])
        invited_user.email = INVITE_EMAIL
        invited_user.save()
        invite = self._make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)

        with self.login(invited_user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_process_local',
                    kwargs={'secret': invite.secret},
                ),
                follow=True,
            )
        self.assertRedirects(
            response,
            reverse(
                'projectroles:detail',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            'Welcome to project "TestProject"! You have been assigned the '
            'role of project contributor.',
        )

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_accept_local_user_exists_not_logged_in(self):
        """Test processing local invite while invited user exists but not user is logged in"""
        invited_user = self.make_user(INVITE_EMAIL.split('@')[0])
        invited_user.email = INVITE_EMAIL
        invited_user.save()
        invite = self._make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)

        response = self.client.get(
            reverse(
                'projectroles:invite_process_local',
                kwargs={'secret': invite.secret},
            ),
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'login',
            )
            + '?next='
            + reverse(
                'projectroles:invite_process_local',
                kwargs={'secret': invite.secret},
            ),
        )
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            MSG_INVITE_USER_EXISTS,
        )

    def test_accept_role_exists(self):
        """Test accepting an invite for user with roles in project"""
        invited_user = self.make_user(INVITE_EMAIL.split('@')[0])
        invited_user.email = INVITE_EMAIL
        invited_user.save()
        invite = self._make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self._make_assignment(self.project, invited_user, self.role_guest)
        self.assertTrue(invite.active)

        with self.login(invited_user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_accept',
                    kwargs={'secret': invite.secret},
                ),
                follow=True,
            )
        self.assertRedirects(
            response,
            reverse('home'),
        )
        invite.refresh_from_db()
        self.assertFalse(invite.active)


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
        """Test rendering ProjectInvite list form"""
        with self.login(self.owner_as.user):
            response = self.client.get(
                reverse(
                    'projectroles:invites',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)

    def test_render_not_found(self):
        """Test rendering ProjectInvite list form with invalid project UUID"""
        with self.login(self.owner_as.user):
            response = self.client.get(
                reverse(
                    'projectroles:invites',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)


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
        """Test rendering ProjectInvite revocation form"""
        with self.login(self.owner_as.user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_revoke',
                    kwargs={'projectinvite': self.invite.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)

    def test_render_not_found(self):
        """Test rendering with invalid invite UUID"""
        with self.login(self.owner_as.user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_revoke',
                    kwargs={'projectinvite': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_revoke_invite(self):
        """Test invite revocation"""
        self.assertEqual(ProjectInvite.objects.all().count(), 1)
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)

        with self.login(self.user):
            self.client.post(
                reverse(
                    'projectroles:invite_revoke',
                    kwargs={'projectinvite': self.invite.sodar_uuid},
                )
            )
        self.assertEqual(ProjectInvite.objects.all().count(), 1)
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 0)

    def test_revoke_delegate(self):
        """Test invite revocation for a delegate role"""
        self.invite.role = self.role_delegate
        self.invite.save()
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)

        with self.login(self.user):
            self.client.post(
                reverse(
                    'projectroles:invite_revoke',
                    kwargs={'projectinvite': self.invite.sodar_uuid},
                )
            )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 0)

    def test_revoke_delegate_no_perms(self):
        """Test delegate revocation with insufficient perms (should fail)"""
        self.invite.role = self.role_delegate
        self.invite.save()
        delegate = self.make_user('delegate')
        self._make_assignment(self.project, delegate, self.role_delegate)
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)

        with self.login(delegate):
            self.client.post(
                reverse(
                    'projectroles:invite_revoke',
                    kwargs={'projectinvite': self.invite.sodar_uuid},
                )
            )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)


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
        """Test rendering remote site create view as source"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:remote_site_create')
            )
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsNotNone(form.fields['secret'].initial)
        self.assertEqual(form.fields['secret'].widget.attrs['readonly'], True)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_render_as_target(self):
        """Test rendering remote site create view as target"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:remote_site_create')
            )
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsNone(form.fields['secret'].initial)
        self.assertNotIn('readonly', form.fields['secret'].widget.attrs)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_render_as_target_existing(self):
        """Test rendering as target with existing source (should fail)"""
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
        with self.login(self.user):
            self.assertRedirects(response, reverse('projectroles:remote_sites'))

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_create_source(self):
        """Test creating a source site as target"""
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
        with self.login(self.user):
            self.assertRedirects(response, reverse('projectroles:remote_sites'))

    def test_create_target_existing_name(self):
        """Test creating a target site with an existing name"""
        self.target_site = self._make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )
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
        """Test rendering remote site update view as source"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:remote_site_update',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertEqual(form['name'].initial, REMOTE_SITE_NAME)
        self.assertEqual(form['url'].initial, REMOTE_SITE_URL)
        self.assertEqual(form['description'].initial, REMOTE_SITE_DESC)
        self.assertEqual(form['secret'].initial, REMOTE_SITE_SECRET)
        self.assertEqual(form.fields['secret'].widget.attrs['readonly'], True)
        self.assertEqual(form['user_display'].initial, REMOTE_SITE_USER_DISPLAY)

    def test_render_not_found(self):
        """Test rendering remote site update view with invalid site UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:remote_site_update',
                    kwargs={'remotesite': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_update(self):
        """Test updating target site as source"""
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
        with self.login(self.user):
            self.assertRedirects(response, reverse('projectroles:remote_sites'))

    def test_update_existing_name(self):
        """Test creating target site with an existing name as source (should fail)"""
        new_target_site = self._make_site(
            name=REMOTE_SITE_NEW_NAME,
            url=REMOTE_SITE_NEW_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_NEW_DESC,
            secret=REMOTE_SITE_NEW_SECRET,
        )
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

    def test_render_not_found(self):
        """Test rendering the remote site delete view with invalid site UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:remote_site_delete',
                    kwargs={'remotesite': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_delete(self):
        """Test deleting the remote site"""
        self.assertEqual(RemoteSite.objects.all().count(), 1)
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:remote_site_delete',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                )
            )
            self.assertRedirects(response, reverse('projectroles:remote_sites'))
        self.assertEqual(RemoteSite.objects.all().count(), 0)


class TestRemoteProjectBatchUpdateView(
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
        """Test rendering remote project update view in confirm mode"""
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
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['site'], self.target_site)
        self.assertIsNotNone(response.context['modifying_access'])

    def test_render_confirm_no_change(self):
        """Test rendering without changes (should redirect)"""
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
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:remote_projects',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                ),
            )

    def test_post_create(self):
        """Test updating remote project access by adding a new RemoteProject"""
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
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:remote_projects',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                ),
            )

        self.assertEqual(RemoteProject.objects.all().count(), 1)
        rp = RemoteProject.objects.first()
        self.assertEqual(rp.project_uuid, self.project.sodar_uuid)
        self.assertEqual(rp.level, SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO'])

    def test_post_update(self):
        """Test updating by modifying an existing RemoteProject"""
        rp = self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL'],
        )
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
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:remote_projects',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                ),
            )

        self.assertEqual(RemoteProject.objects.all().count(), 1)
        rp.refresh_from_db()
        self.assertEqual(rp.project_uuid, self.project.sodar_uuid)
        self.assertEqual(rp.level, SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO'])


class TestUserUpdateView(TestViewsBase):
    """Tests for the user update view"""

    # NOTE: This assumes an example app is available
    def setUp(self):
        # Init user & role
        self.user_local = self.make_user('local_user')
        self.user_ldap = self.make_user('ldap_user@EXAMPLE')

    def test_render_local_user(self):
        with self.login(self.user_local):
            response = self.client.get(reverse('projectroles:user_update'))
        self.assertEqual(response.status_code, 200)

    def test_render_ldap_user(self):
        with self.login(self.user_ldap):
            response = self.client.get(
                reverse('projectroles:user_update'), follow=True
            )
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            MSG_USER_PROFILE_LDAP,
        )

    def test_submit_local_user(self):
        self.assertEqual(User.objects.count(), 2)
        user = User.objects.get(id=self.user_local.id)
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')

        with self.login(self.user_local):
            response = self.client.post(
                reverse('projectroles:user_update'),
                {
                    'first_name': 'Local',
                    'last_name': 'User',
                    'username': self.user_local.username,
                    'email': self.user_local.email,
                    'password': 'fjf',
                    'password_confirm': 'fjf',
                },
                follow=True,
            )
        self.assertListEqual(
            response.redirect_chain,
            [
                (reverse('home'), 302),
                (
                    reverse('login') + '?next=' + reverse('home'),
                    302,
                ),
            ],
        )
        self.assertEqual(User.objects.count(), 2)
        user = User.objects.get(id=self.user_local.id)
        self.assertEqual(user.first_name, 'Local')
        self.assertEqual(user.last_name, 'User')
