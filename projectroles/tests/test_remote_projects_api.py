"""Test for the remote projects API in the projectroles app"""
import uuid

from django.conf import settings
from django.contrib import auth
from django.test import override_settings

from test_plus.test import TestCase

from projectroles.models import Project, Role, RoleAssignment, \
    RemoteSite, RemoteProject, SODAR_CONSTANTS

from projectroles.remote_projects import RemoteProjectAPI
from projectroles.utils import build_secret
from projectroles.tests.test_models import ProjectMixin, RoleAssignmentMixin, \
    RemoteSiteMixin, RemoteProjectMixin, SodarUserMixin

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
REMOTE_LEVEL_VIEW_AVAIL = SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL']
REMOTE_LEVEL_READ_INFO = SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']

# Local constants
SOURCE_SITE_NAME = 'Test source site'
SOURCE_SITE_URL = 'https://sodar.bihealth.org'
SOURCE_SITE_DESC = 'Source description'
SOURCE_SITE_SECRET = build_secret()

SOURCE_USER_DOMAIN = 'TESTDOMAIN'
SOURCE_USER_USERNAME = 'source_user@' + SOURCE_USER_DOMAIN
SOURCE_USER_GROUP = SOURCE_USER_DOMAIN.lower()
SOURCE_USER_NAME = 'Firstname Lastname'
SOURCE_USER_FIRST_NAME = SOURCE_USER_NAME.split(' ')[0]
SOURCE_USER_LAST_NAME = SOURCE_USER_NAME.split(' ')[1]
SOURCE_USER_EMAIL = SOURCE_USER_USERNAME.split('@')[0] + '@example.com'
SOURCE_USER_UUID = uuid.uuid4()

SOURCE_CATEGORY_UUID = uuid.uuid4()
SOURCE_CATEGORY_TITLE = 'TestCategory'
SOURCE_PROJECT_UUID = uuid.uuid4()
SOURCE_PROJECT_TITLE = 'TestProject'
SOURCE_PROJECT_DESCRIPTION = 'Description'
SOURCE_PROJECT_README = 'Readme'


TARGET_SITE_NAME = 'Target name'
TARGET_SITE_URL = 'https://target.url'
TARGET_SITE_DESC = 'Target description'
TARGET_SITE_SECRET = build_secret()


class TestGetTargetData(
        TestCase, ProjectMixin, RoleAssignmentMixin, RemoteSiteMixin,
        RemoteProjectMixin, SodarUserMixin):
    """Tests for the get_target_data() API function"""

    def setUp(self):
        # Init roles
        self.role_owner = Role.objects.get_or_create(
            name=PROJECT_ROLE_OWNER)[0]
        self.role_delegate = Role.objects.get_or_create(
            name=PROJECT_ROLE_DELEGATE)[0]
        self.role_contributor = Role.objects.get_or_create(
            name=PROJECT_ROLE_CONTRIBUTOR)[0]
        self.role_guest = Role.objects.get_or_create(
            name=PROJECT_ROLE_GUEST)[0]

        # Init an LDAP user on the source site
        self.user_source = self._make_sodar_user(
            username=SOURCE_USER_USERNAME,
            name=SOURCE_USER_NAME,
            first_name=SOURCE_USER_FIRST_NAME,
            last_name=SOURCE_USER_LAST_NAME)

        # Init local category and project
        self.category = self._make_project(
            SOURCE_CATEGORY_TITLE, PROJECT_TYPE_CATEGORY, None)
        self.project = self._make_project(
            SOURCE_PROJECT_TITLE, PROJECT_TYPE_PROJECT, self.category)

        # Init role assignments
        self.category_owner_as = self._make_assignment(
            self.category, self.user_source, self.role_owner)
        self.project_owner_as = self._make_assignment(
            self.project, self.user_source, self.role_owner)

        # Init target site
        self.target_site = self._make_site(
            name=TARGET_SITE_NAME,
            url=TARGET_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=TARGET_SITE_DESC,
            secret=TARGET_SITE_SECRET)

        self.remote_api = RemoteProjectAPI()

    def test_view_avail(self):
        """Test get data with project level of VIEW_AVAIL (view availability)"""
        remote_project = self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=REMOTE_LEVEL_VIEW_AVAIL)

        sync_data = self.remote_api.get_target_data(self.target_site)

        expected = {
            'users': [],
            'categories': [],
            'projects': [{
                'sodar_uuid': self.project.sodar_uuid,
                'title': self.project.title,
                'type': PROJECT_TYPE_PROJECT,
                'level': REMOTE_LEVEL_VIEW_AVAIL,
                'available': True}]}

        self.assertEqual(sync_data, expected)

    def test_read_info(self):
        """Test get data with project level of READ_INFO (read information)"""
        remote_project = self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=REMOTE_LEVEL_READ_INFO)

        sync_data = self.remote_api.get_target_data(self.target_site)

        expected = {
            'users': [],
            'categories': [{
                'sodar_uuid': self.category.sodar_uuid,
                'title': self.category.title,
                'type': PROJECT_TYPE_CATEGORY,
                'parent': None,
                'description': self.category.description,
                'readme': self.category.readme.raw}],
            'projects': [{
                'sodar_uuid': self.project.sodar_uuid,
                'title': self.project.title,
                'type': PROJECT_TYPE_PROJECT,
                'level': REMOTE_LEVEL_READ_INFO,
                'description': self.project.description,
                'readme': self.project.readme.raw,
                'parent': self.category.sodar_uuid}]}

        self.assertEqual(sync_data, expected)

    def test_read_info_nested(self):
        """Test get data with project level of READ_INFO with nested categories"""
        sub_category = self._make_project(
            'SubCategory', PROJECT_TYPE_CATEGORY, parent=self.category)
        self._make_assignment(sub_category, self.user_source, self.role_owner)
        self.project.parent = sub_category
        self.project.save()

        remote_project = self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=REMOTE_LEVEL_READ_INFO)

        sync_data = self.remote_api.get_target_data(self.target_site)
        self.maxDiff = None  # DEBUG

        expected = {
            'users': [],
            'categories': [
                {
                    'sodar_uuid': self.category.sodar_uuid,
                    'title': self.category.title,
                    'type': PROJECT_TYPE_CATEGORY,
                    'parent': None,
                    'description': self.category.description,
                    'readme': self.category.readme.raw
                },
                {
                    'sodar_uuid': sub_category.sodar_uuid,
                    'title': sub_category.title,
                    'type': PROJECT_TYPE_CATEGORY,
                    'parent': self.category.sodar_uuid,
                    'description': sub_category.description,
                    'readme': sub_category.readme.raw
                }
            ],
            'projects': [{
                'sodar_uuid': self.project.sodar_uuid,
                'title': self.project.title,
                'type': PROJECT_TYPE_PROJECT,
                'level': REMOTE_LEVEL_READ_INFO,
                'description': self.project.description,
                'readme': self.project.readme.raw,
                'parent': sub_category.sodar_uuid}]}

        self.assertEqual(sync_data, expected)

    def test_read_roles(self):
        """Test get data with project level of READ_ROLES (read roles)"""
        remote_project = self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=REMOTE_LEVEL_READ_ROLES)

        sync_data = self.remote_api.get_target_data(self.target_site)

        expected = {
            'users': [{
                'sodar_uuid': self.user_source.sodar_uuid,
                'username': self.user_source.username,
                'name': self.user_source.name,
                'first_name': self.user_source.first_name,
                'last_name': self.user_source.last_name,
                'email': self.user_source.email,
                'groups': [SOURCE_USER_GROUP]}],
            'categories': [{
                'sodar_uuid': self.category.sodar_uuid,
                'title': self.category.title,
                'type': PROJECT_TYPE_CATEGORY,
                'parent': None,
                'description': self.category.description,
                'readme': self.category.readme.raw,
                'owner': self.user_source.username}],
            'projects': [{
                'sodar_uuid': self.project.sodar_uuid,
                'title': self.project.title,
                'type': PROJECT_TYPE_PROJECT,
                'level': REMOTE_LEVEL_READ_ROLES,
                'description': self.project.description,
                'readme': self.project.readme.raw,
                'parent': self.category.sodar_uuid,
                'roles': [{
                    'sodar_uuid': self.project_owner_as.sodar_uuid,
                    'user': self.project_owner_as.user.username,
                    'role': self.project_owner_as.role.name}]}]}

        self.assertEqual(sync_data, expected)

    def test_no_access(self):
        """Test get data with no project access set in the source site"""
        sync_data = self.remote_api.get_target_data(self.target_site)

        expected = {
            'users': [],
            'categories': [],
            'projects': []}

        self.assertEqual(sync_data, expected)


class TestSyncSourceData(
        TestCase, ProjectMixin, RoleAssignmentMixin, RemoteSiteMixin,
        RemoteProjectMixin, SodarUserMixin):
    """Tests for the sync_source_data() API function"""

    def setUp(self):
        # Init roles
        self.role_owner = Role.objects.get_or_create(
            name=PROJECT_ROLE_OWNER)[0]
        self.role_delegate = Role.objects.get_or_create(
            name=PROJECT_ROLE_DELEGATE)[0]
        self.role_contributor = Role.objects.get_or_create(
            name=PROJECT_ROLE_CONTRIBUTOR)[0]
        self.role_guest = Role.objects.get_or_create(
            name=PROJECT_ROLE_GUEST)[0]

        # Init source site
        self.source_site = self._make_site(
            name=SOURCE_SITE_NAME,
            url=SOURCE_SITE_URL,
            mode=SITE_MODE_SOURCE,
            description=SOURCE_SITE_DESC,
            secret=SOURCE_SITE_SECRET)

        self.remote_api = RemoteProjectAPI()

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_sync_create(self):
        """Test sync with non-existing project data and READ_ROLE access"""

        # Assert preconditions
        self.assertEqual(Project.objects.all().count(), 0)
        self.assertEqual(RoleAssignment.objects.all().count(), 0)
        self.assertEqual(User.objects.all().count(), 0)

        remote_data = {
            'users': [{
                'sodar_uuid': SOURCE_USER_UUID,
                'username': SOURCE_USER_USERNAME,
                'name': SOURCE_USER_NAME,
                'first_name': SOURCE_USER_FIRST_NAME,
                'last_name': SOURCE_USER_LAST_NAME,
                'email': SOURCE_USER_EMAIL,
                'groups': [SOURCE_USER_GROUP]}],
            'categories': [{
                'sodar_uuid': SOURCE_CATEGORY_UUID,
                'title': SOURCE_CATEGORY_TITLE,
                'type': PROJECT_TYPE_CATEGORY,
                'parent': None,
                'description': SOURCE_PROJECT_DESCRIPTION,
                'readme': SOURCE_PROJECT_README,
                'owner': SOURCE_USER_USERNAME}],
            'projects': [{
                'sodar_uuid': SOURCE_PROJECT_UUID,
                'title': SOURCE_PROJECT_TITLE,
                'type': PROJECT_TYPE_PROJECT,
                'level': REMOTE_LEVEL_READ_ROLES,
                'description': SOURCE_PROJECT_DESCRIPTION,
                'readme': SOURCE_PROJECT_README,
                'parent': SOURCE_CATEGORY_UUID,
                'roles': [{
                    'sodar_uuid': str(uuid.uuid4()),
                    'user': SOURCE_USER_USERNAME,
                    'role': self.role_owner.name}]}]}

        update_data = self.remote_api.sync_source_data(
            self.source_site, remote_data)

        # Assert database status
        self.assertEqual(Project.objects.all().count(), 2)
        # self.assertEqual(RoleAssignment.objects.all().count(), 2)  # TODO
        self.assertEqual(User.objects.all().count(), 1)

        # Assert update_data
        # TODO
