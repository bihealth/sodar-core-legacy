"""Test for the remote projects API in the projectroles app"""

import base64
from urllib.parse import urlencode

from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms.models import model_to_dict
from django.test import RequestFactory, override_settings
from django.utils import timezone

from test_plus.test import TestCase

from projectroles import views
from projectroles.models import Project, Role, RoleAssignment, ProjectInvite, \
    ProjectUserTag, RemoteSite, RemoteProject, SODAR_CONSTANTS, \
    PROJECT_TAG_STARRED
from projectroles.plugins import change_plugin_status, get_backend_api, \
    get_active_plugins, ProjectAppPluginPoint
from projectroles.remote_projects import RemoteProjectAPI
from projectroles.utils import build_secret
from projectroles.tests.test_models import ProjectMixin, RoleAssignmentMixin, \
    RemoteSiteMixin, RemoteProjectMixin, SodarUserMixin


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
CATEGORY_NAME = 'TestCategory'
PROJECT_NAME = 'ProjectName'
ADMIN_USER_NAME = settings.PROJECTROLES_ADMIN_OWNER

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

        # Init superuser on the source site
        self.user_admin = self.make_user(ADMIN_USER_NAME)
        self.user_admin.is_staff = True
        self.user_admin.is_superuser = True
        self.user_admin.save()

        # Init an LDAP user on the source site
        self.user_source = self._make_sodar_user(
            username=SOURCE_USER_USERNAME,
            name=SOURCE_USER_NAME,
            first_name=SOURCE_USER_FIRST_NAME,
            last_name=SOURCE_USER_LAST_NAME)

        # Init local category and project
        self.category = self._make_project(
            CATEGORY_NAME, PROJECT_TYPE_CATEGORY, None)
        self.project = self._make_project(
            PROJECT_NAME, PROJECT_TYPE_PROJECT, self.category)

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
                'parent': None,
                'description': self.category.description,
                'readme': self.category.readme.raw}],
            'projects': [{
                'sodar_uuid': self.project.sodar_uuid,
                'title': self.project.title,
                'level': REMOTE_LEVEL_READ_INFO,
                'description': self.project.description,
                'readme': self.project.readme.raw,
                'parent': self.category.sodar_uuid}]}

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
                'parent': None,
                'description': self.category.description,
                'readme': self.category.readme.raw,
                'owner': self.user_source.username}],
            'projects': [{
                'sodar_uuid': self.project.sodar_uuid,
                'title': self.project.title,
                'level': REMOTE_LEVEL_READ_ROLES,
                'description': self.project.description,
                'readme': self.project.readme.raw,
                'parent': self.category.sodar_uuid,
                'roles': [{
                    'sodar_uuid': self.project_owner_as.sodar_uuid,
                    'user': self.project_owner_as.user.username,
                    'role': self.project_owner_as.role.name}]}]}

        self.assertEqual(sync_data, expected)
