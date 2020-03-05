"""REST API view tests for the projectroles app with SODAR Taskflow enabled"""

from django.conf import settings
from django.contrib import auth
from django.core.exceptions import ImproperlyConfigured
from django.forms.models import model_to_dict
from django.test import tag
from django.urls import reverse

from rest_framework.test import APILiveServerTestCase

from unittest import skipIf

from projectroles.app_settings import AppSettingAPI
from projectroles.models import Project, Role, RoleAssignment, SODAR_CONSTANTS
from projectroles.plugins import get_backend_api, change_plugin_status
from projectroles.tests.taskflow_testcase import TestCase
from projectroles.tests.test_models import ProjectMixin, RoleAssignmentMixin
from projectroles.tests.test_views_api import SODARAPIViewTestMixin


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SUBMIT_STATUS_OK = SODAR_CONSTANTS['SUBMIT_STATUS_OK']
SUBMIT_STATUS_PENDING = SODAR_CONSTANTS['SUBMIT_STATUS_PENDING']
SUBMIT_STATUS_PENDING_TASKFLOW = SODAR_CONSTANTS[
    'SUBMIT_STATUS_PENDING_TASKFLOW'
]
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']

# Local constants
INVITE_EMAIL = 'test@example.com'
SECRET = 'rsd886hi8276nypuvw066sbvv0rb2a6x'
TASKFLOW_ENABLED = (
    True if 'taskflow' in settings.ENABLED_BACKEND_PLUGINS else False
)
TASKFLOW_SKIP_MSG = 'Taskflow not enabled in settings'
TASKFLOW_TEST_MODE = getattr(settings, 'TASKFLOW_TEST_MODE', False)
NEW_PROJECT_TITLE = 'New Project'
UPDATED_TITLE = 'Updated Title'
UPDATED_DESC = 'Updated description'
UPDATED_README = 'Updated readme'

# Access Django user model
User = auth.get_user_model()

# App settings API
app_settings = AppSettingAPI()


# Tests with Taskflow ----------------------------------------------------------


@tag('Taskflow')  # Run tests if iRODS and SODAR Taskflow are enabled
class TestTaskflowAPIBase(
    ProjectMixin,
    RoleAssignmentMixin,
    SODARAPIViewTestMixin,
    APILiveServerTestCase,
    TestCase,
):
    """Base class for testing API views with taskflow"""

    def _make_project_taskflow(
        self, title, type, parent, owner, description='', readme=''
    ):
        """Make Project with taskflow for UI view tests"""
        post_data = dict(self.request_data)
        post_data.update(
            {
                'title': title,
                'type': type,
                'parent': parent.sodar_uuid if parent else None,
                'owner': owner.sodar_uuid,
                'description': description,
                'readme': readme,
            }
        )
        response = self.request_knox(
            reverse('projectroles:api_project_create'),
            method='POST',
            data=post_data,
        )

        # Assert response and object status
        self.assertEqual(response.status_code, 201, msg=response.content)
        project = Project.objects.get(title=title)
        return project, project.get_owner()

    # TODO: Add version of _make_assignment_taskflow()

    def setUp(self):
        # Ensure TASKFLOW_TEST_MODE is True to avoid data loss
        if not TASKFLOW_TEST_MODE:
            raise ImproperlyConfigured(
                'TASKFLOW_TEST_MODE not True, '
                'testing with SODAR Taskflow disabled'
            )

        # Set up live server URL for requests
        self.request_data = {'sodar_url': self.live_server_url}

        # Get taskflow plugin (or None if taskflow not enabled)
        change_plugin_status(
            name='taskflow', status=0, plugin_type='backend'  # 0 = Enabled
        )
        self.taskflow = get_backend_api('taskflow', force=True)

        # Init roles
        self.role_owner = Role.objects.get_or_create(name=PROJECT_ROLE_OWNER)[0]
        self.role_delegate = Role.objects.get_or_create(
            name=PROJECT_ROLE_DELEGATE
        )[0]
        self.role_contributor = Role.objects.get_or_create(
            name=PROJECT_ROLE_CONTRIBUTOR
        )[0]
        self.role_guest = Role.objects.get_or_create(name=PROJECT_ROLE_GUEST)[0]

        # Init user
        self.user = self.make_user('superuser')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        # Create category locally (categories are not handled with taskflow)
        self.category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self._make_assignment(self.category, self.user, self.role_owner)

        # Get knox token for self.user
        self.knox_token = self.get_token(self.user)

    def tearDown(self):
        self.taskflow.cleanup()


@skipIf(not TASKFLOW_ENABLED, TASKFLOW_SKIP_MSG)
class TestProjectCreateAPIView(TestTaskflowAPIBase):
    """Tests for ProjectCreateAPIView with taskflow"""

    def test_create_project(self):
        """Test project creation"""

        # Assert precondition
        self.assertEqual(Project.objects.all().count(), 1)

        url = reverse('projectroles:api_project_create')
        self.request_data.update(
            {
                'title': NEW_PROJECT_TITLE,
                'type': PROJECT_TYPE_PROJECT,
                'parent': str(self.category.sodar_uuid),
                'description': 'description',
                'readme': 'readme',
                'owner': str(self.user.sodar_uuid),
            }
        )
        response = self.request_knox(url, method='POST', data=self.request_data)

        # Assert response and object status
        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(Project.objects.all().count(), 2)


@skipIf(not TASKFLOW_ENABLED, TASKFLOW_SKIP_MSG)
class TestProjectUpdateAPIView(TestTaskflowAPIBase):
    """Tests for ProjectUpdateAPIView with taskflow"""

    def setUp(self):
        super().setUp()

        # Make project with owner in Taskflow and Django
        self.project, self.owner_as = self._make_project_taskflow(
            title='TestProject',
            type=PROJECT_TYPE_PROJECT,
            parent=self.category,
            owner=self.user,
            description='description',
        )

    def test_put_category(self):
        """Test put() for category updating"""
        new_owner = self.make_user('new_owner')

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.category.sodar_uuid},
        )
        self.request_data.update(
            {
                'title': UPDATED_TITLE,
                'type': PROJECT_TYPE_CATEGORY,
                'parent': '',
                'description': UPDATED_DESC,
                'readme': UPDATED_README,
                'owner': str(new_owner.sodar_uuid),
            }
        )
        response = self.request_knox(url, method='PUT', data=self.request_data)

        # Assert response and project status
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(Project.objects.count(), 2)

        # Assert object content
        self.category.refresh_from_db()
        model_dict = model_to_dict(self.category)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': self.category.pk,
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'submit_status': SODAR_CONSTANTS['SUBMIT_STATUS_OK'],
            'sodar_uuid': self.category.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)

        # Assert role assignment
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.category).count(), 1
        )
        self.assertEqual(self.category.get_owner().user, new_owner)

    def test_put_project(self):
        """Test put() for project updating"""
        new_owner = self.make_user('new_owner')

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.request_data.update(
            {
                'title': UPDATED_TITLE,
                'type': PROJECT_TYPE_PROJECT,
                'parent': str(self.category.sodar_uuid),
                'description': UPDATED_DESC,
                'readme': UPDATED_README,
                'owner': str(new_owner.sodar_uuid),
            }
        )
        response = self.request_knox(url, method='PUT', data=self.request_data)

        # Assert response and project status
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(Project.objects.count(), 2)

        # Assert object content
        self.project.refresh_from_db()
        model_dict = model_to_dict(self.project)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': self.project.pk,
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': self.category.pk,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'submit_status': SODAR_CONSTANTS['SUBMIT_STATUS_OK'],
            'sodar_uuid': self.project.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)

        # Assert role assignment
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 1
        )
        self.assertEqual(self.project.get_owner().user, new_owner)

    def test_patch_category(self):
        """Test patch() for updating category metadata"""

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.category.sodar_uuid},
        )
        self.request_data.update(
            {
                'title': UPDATED_TITLE,
                'description': UPDATED_DESC,
                'readme': UPDATED_README,
            }
        )
        response = self.request_knox(
            url, method='PATCH', data=self.request_data
        )

        # Assert response and project status
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(Project.objects.count(), 2)

        # Assert object content
        self.category.refresh_from_db()
        model_dict = model_to_dict(self.category)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': self.category.pk,
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'submit_status': SODAR_CONSTANTS['SUBMIT_STATUS_OK'],
            'sodar_uuid': self.category.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)

        # Assert role assignment
        self.assertEqual(self.category.get_owner().user, self.user)

    def test_patch_project(self):
        """Test patch() for updating project metadata"""

        # Assert preconditions
        self.assertEqual(Project.objects.count(), 2)

        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.request_data.update(
            {
                'title': UPDATED_TITLE,
                'description': UPDATED_DESC,
                'readme': UPDATED_README,
            }
        )
        response = self.request_knox(
            url, method='PATCH', data=self.request_data
        )

        # Assert response and project status
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(Project.objects.count(), 2)

        # Assert object content
        self.project.refresh_from_db()
        model_dict = model_to_dict(self.project)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': self.project.pk,
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': self.category.pk,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'submit_status': SODAR_CONSTANTS['SUBMIT_STATUS_OK'],
            'sodar_uuid': self.project.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)

        # Assert role assignment
        self.assertEqual(self.project.get_owner().user, self.user)

    def test_patch_project_owner(self):
        """Test patch() for updating project owner"""
        new_owner = self.make_user('new_owner')

        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.request_data.update({'owner': str(new_owner.sodar_uuid)})
        response = self.request_knox(
            url, method='PATCH', data=self.request_data
        )

        # Assert response
        self.assertEqual(response.status_code, 200, msg=response.content)

        # Assert role assignment
        self.project.refresh_from_db()
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 1
        )
        self.assertEqual(self.project.get_owner().user, new_owner)

    def test_patch_project_move(self):
        """Test patch() for moving project under a different category"""

        new_category = self._make_project(
            'NewCategory', PROJECT_TYPE_CATEGORY, None
        )
        self._make_assignment(new_category, self.user, self.role_owner)
        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.request_data.update({'parent': str(new_category.sodar_uuid)})
        response = self.request_knox(
            url, method='PATCH', data=self.request_data
        )

        # Assert response
        self.assertEqual(response.status_code, 200, msg=response.content)

        # Assert object content
        self.project.refresh_from_db()
        model_dict = model_to_dict(self.project)
        self.assertEqual(model_dict['parent'], new_category.pk)

        # Assert role assignment
        self.assertEqual(self.project.get_owner().user, self.user)


@skipIf(not TASKFLOW_ENABLED, TASKFLOW_SKIP_MSG)
class TestRoleAssignmentCreateAPIView(TestTaskflowAPIBase):
    """Tests for RoleAssignmentCreateAPIView with taskflow"""

    def setUp(self):
        super().setUp()

        # Make project with owner in Taskflow and Django
        self.project, self.owner_as = self._make_project_taskflow(
            title='TestProject',
            type=PROJECT_TYPE_PROJECT,
            parent=self.category,
            owner=self.user,
            description='description',
        )

        # Create user for assignments
        self.assign_user = self.make_user('assign_user')

    def test_create_role(self):
        """Test role assignment creation"""

        # Assert precondition
        self.assertEqual(RoleAssignment.objects.all().count(), 2)

        url = reverse(
            'projectroles:api_role_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.request_data.update(
            {
                'role': PROJECT_ROLE_CONTRIBUTOR,
                'user': str(self.assign_user.sodar_uuid),
            }
        )
        response = self.request_knox(url, method='POST', data=self.request_data)

        # Assert response and object status
        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
