"""Tests for the remote projects API in the projectroles app"""

from copy import deepcopy
import uuid

from django.conf import settings
from django.contrib import auth
from django.forms.models import model_to_dict
from django.test import override_settings

from test_plus.test import TestCase

from projectroles.models import (
    Project,
    Role,
    RoleAssignment,
    RemoteProject,
    RemoteSite,
    SODAR_CONSTANTS,
    AppSetting,
)

from projectroles.remote_projects import RemoteProjectAPI
from projectroles.utils import build_secret
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    SodarUserMixin,
    AppSettingMixin,
)


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
SITE_MODE_PEER = SODAR_CONSTANTS['SITE_MODE_PEER']
REMOTE_LEVEL_VIEW_AVAIL = SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL']
REMOTE_LEVEL_READ_INFO = SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']
REMOTE_LEVEL_REVOKED = SODAR_CONSTANTS['REMOTE_LEVEL_REVOKED']

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
SOURCE_USER_UUID = str(uuid.uuid4())

SOURCE_USER2_DOMAIN = SOURCE_USER_DOMAIN
SOURCE_USER2_USERNAME = 'source_user2@' + SOURCE_USER_DOMAIN
SOURCE_USER2_GROUP = SOURCE_USER_DOMAIN.lower()
SOURCE_USER2_NAME = 'Firstname2 Lastname2'
SOURCE_USER2_FIRST_NAME = SOURCE_USER2_NAME.split(' ')[0]
SOURCE_USER2_LAST_NAME = SOURCE_USER2_NAME.split(' ')[1]
SOURCE_USER2_EMAIL = SOURCE_USER2_USERNAME.split('@')[0] + '@example.com'
SOURCE_USER2_UUID = str(uuid.uuid4())

SOURCE_USER3_DOMAIN = SOURCE_USER_DOMAIN
SOURCE_USER3_USERNAME = 'source_user3@' + SOURCE_USER_DOMAIN
SOURCE_USER3_GROUP = SOURCE_USER_DOMAIN.lower()
SOURCE_USER3_NAME = 'Firstname3 Lastname3'
SOURCE_USER3_FIRST_NAME = SOURCE_USER3_NAME.split(' ')[0]
SOURCE_USER3_LAST_NAME = SOURCE_USER3_NAME.split(' ')[1]
SOURCE_USER3_EMAIL = SOURCE_USER3_USERNAME.split('@')[0] + '@example.com'
SOURCE_USER3_UUID = str(uuid.uuid4())

SOURCE_USER4_DOMAIN = SOURCE_USER_DOMAIN
SOURCE_USER4_USERNAME = 'source_user4@' + SOURCE_USER_DOMAIN
SOURCE_USER4_GROUP = SOURCE_USER_DOMAIN.lower()
SOURCE_USER4_NAME = 'Firstname4 Lastname4'
SOURCE_USER4_FIRST_NAME = SOURCE_USER4_NAME.split(' ')[0]
SOURCE_USER4_LAST_NAME = SOURCE_USER4_NAME.split(' ')[1]
SOURCE_USER4_EMAIL = SOURCE_USER4_USERNAME.split('@')[0] + '@example.com'
SOURCE_USER4_UUID = str(uuid.uuid4())

SOURCE_CATEGORY_UUID = str(uuid.uuid4())
SOURCE_CATEGORY_TITLE = 'TestCategory'
SOURCE_PROJECT_UUID = str(uuid.uuid4())
SOURCE_PROJECT_TITLE = 'TestProject'
SOURCE_PROJECT_DESCRIPTION = 'Description'
SOURCE_PROJECT_README = 'Readme'
SOURCE_PROJECT_FULL_TITLE = SOURCE_CATEGORY_TITLE + ' / ' + SOURCE_PROJECT_TITLE
SOURCE_CATEGORY_ROLE_UUID = str(uuid.uuid4())
SOURCE_CATEGORY_ROLE2_UUID = str(uuid.uuid4())
SOURCE_CATEGORY_ROLE3_UUID = str(uuid.uuid4())
SOURCE_CATEGORY_ROLE4_UUID = str(uuid.uuid4())
SOURCE_PROJECT_ROLE_UUID = str(uuid.uuid4())
SOURCE_PROJECT_ROLE2_UUID = str(uuid.uuid4())
SOURCE_PROJECT_ROLE3_UUID = str(uuid.uuid4())
SOURCE_PROJECT_ROLE4_UUID = str(uuid.uuid4())

TARGET_SITE_NAME = 'Target name'
TARGET_SITE_URL = 'https://target.url'
TARGET_SITE_DESC = 'Target description'
TARGET_SITE_SECRET = build_secret()

PEER_SITE_UUID = str(uuid.uuid4())
PEER_SITE_NAME = 'Peer name'
PEER_SITE_URL = 'https://peer.url'
PEER_SITE_DESC = 'peer description'
PEER_SITE_SECRET = build_secret()
PEER_SITE_USER_DISPLAY = True

NEW_PEER_NAME = PEER_SITE_NAME + ' new'
NEW_PEER_DESC = PEER_SITE_DESC + ' new'
NEW_PEER_USER_DISPLAY = not PEER_SITE_USER_DISPLAY

PR_IP_RESTRICT_UUID = str(uuid.uuid4())
PR_IP_ALLOWLIST_UUID = str(uuid.uuid4())


class TestGetSourceData(
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    SodarUserMixin,
    TestCase,
):
    """Tests for the get_source_data() API function"""

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

        # Init an LDAP user on the source site
        self.user_source = self._make_sodar_user(
            username=SOURCE_USER_USERNAME,
            name=SOURCE_USER_NAME,
            first_name=SOURCE_USER_FIRST_NAME,
            last_name=SOURCE_USER_LAST_NAME,
            email=SOURCE_USER_EMAIL,
        )

        # Init local category and project
        self.category = self._make_project(
            SOURCE_CATEGORY_TITLE, PROJECT_TYPE_CATEGORY, None
        )
        self.project = self._make_project(
            SOURCE_PROJECT_TITLE, PROJECT_TYPE_PROJECT, self.category
        )

        # Init role assignments
        self.category_owner_as = self._make_assignment(
            self.category, self.user_source, self.role_owner
        )
        self.project_owner_as = self._make_assignment(
            self.project, self.user_source, self.role_owner
        )

        # Init target site
        self.target_site = self._make_site(
            name=TARGET_SITE_NAME,
            url=TARGET_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=TARGET_SITE_DESC,
            secret=TARGET_SITE_SECRET,
        )

        # Init peer site
        self.peer_site = self._make_site(
            name=PEER_SITE_NAME,
            url=PEER_SITE_URL,
            mode=SITE_MODE_PEER,
            description=PEER_SITE_DESC,
            secret=PEER_SITE_SECRET,
        )

        self.remote_api = RemoteProjectAPI()

    def test_view_avail(self):
        """Test get data with project level of VIEW_AVAIL (view availability)"""
        self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=REMOTE_LEVEL_VIEW_AVAIL,
        )
        self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.peer_site,
            level=REMOTE_LEVEL_VIEW_AVAIL,
        )
        sync_data = self.remote_api.get_source_data(self.target_site)
        expected = {
            'users': {},
            'projects': {
                str(self.project.sodar_uuid): {
                    'title': self.project.title,
                    'type': PROJECT_TYPE_PROJECT,
                    'level': REMOTE_LEVEL_VIEW_AVAIL,
                    'available': True,
                    'remote_sites': [],
                }
            },
            'peer_sites': {},
            'app_settings': {},
        }
        self.assertEqual(sync_data, expected)

    def test_read_info(self):
        """Test get data with project level of READ_INFO (read information)"""
        self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=REMOTE_LEVEL_READ_INFO,
        )
        self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.peer_site,
            level=REMOTE_LEVEL_READ_INFO,
        )
        sync_data = self.remote_api.get_source_data(self.target_site)
        expected = {
            'users': {},
            'projects': {
                str(self.category.sodar_uuid): {
                    'title': self.category.title,
                    'type': PROJECT_TYPE_CATEGORY,
                    'level': REMOTE_LEVEL_READ_INFO,
                    'parent_uuid': None,
                    'description': self.category.description,
                    'readme': self.category.readme.raw,
                },
                str(self.project.sodar_uuid): {
                    'title': self.project.title,
                    'type': PROJECT_TYPE_PROJECT,
                    'level': REMOTE_LEVEL_READ_INFO,
                    'description': self.project.description,
                    'readme': self.project.readme.raw,
                    'parent_uuid': str(self.category.sodar_uuid),
                    'remote_sites': [str(self.peer_site.sodar_uuid)],
                },
            },
            'peer_sites': {
                str(self.peer_site.sodar_uuid): {
                    'name': self.peer_site.name,
                    'url': self.peer_site.url,
                    'description': self.peer_site.description,
                    'user_display': self.peer_site.user_display,
                }
            },
            'app_settings': {},
        }
        self.assertEqual(sync_data, expected)

    def test_read_info_nested(self):
        """Test get data with READ_INFO and nested categories"""
        sub_category = self._make_project(
            'SubCategory', PROJECT_TYPE_CATEGORY, parent=self.category
        )
        self._make_assignment(sub_category, self.user_source, self.role_owner)
        self.project.parent = sub_category
        self.project.save()
        self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=REMOTE_LEVEL_READ_INFO,
        )
        sync_data = self.remote_api.get_source_data(self.target_site)
        expected = {
            'users': {},
            'projects': {
                str(self.category.sodar_uuid): {
                    'title': self.category.title,
                    'type': PROJECT_TYPE_CATEGORY,
                    'level': REMOTE_LEVEL_READ_INFO,
                    'parent_uuid': None,
                    'description': self.category.description,
                    'readme': self.category.readme.raw,
                },
                str(sub_category.sodar_uuid): {
                    'title': sub_category.title,
                    'type': PROJECT_TYPE_CATEGORY,
                    'level': REMOTE_LEVEL_READ_INFO,
                    'parent_uuid': str(self.category.sodar_uuid),
                    'description': sub_category.description,
                    'readme': sub_category.readme.raw,
                },
                str(self.project.sodar_uuid): {
                    'title': self.project.title,
                    'type': PROJECT_TYPE_PROJECT,
                    'level': REMOTE_LEVEL_READ_INFO,
                    'description': self.project.description,
                    'readme': self.project.readme.raw,
                    'parent_uuid': str(sub_category.sodar_uuid),
                    'remote_sites': [],
                },
            },
            'peer_sites': {},
            'app_settings': {},
        }
        self.assertEqual(sync_data, expected)

    def test_read_roles(self):
        """Test get data with project level of READ_ROLES (read roles)"""
        self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=REMOTE_LEVEL_READ_ROLES,
        )
        self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.peer_site,
            level=REMOTE_LEVEL_READ_ROLES,
        )
        sync_data = self.remote_api.get_source_data(self.target_site)
        expected = {
            'users': {
                str(self.user_source.sodar_uuid): {
                    'username': self.user_source.username,
                    'name': self.user_source.name,
                    'first_name': self.user_source.first_name,
                    'last_name': self.user_source.last_name,
                    'email': self.user_source.email,
                    'groups': [SOURCE_USER_GROUP],
                }
            },
            'projects': {
                str(self.category.sodar_uuid): {
                    'title': self.category.title,
                    'type': PROJECT_TYPE_CATEGORY,
                    'level': REMOTE_LEVEL_READ_ROLES,
                    'parent_uuid': None,
                    'description': self.category.description,
                    'readme': self.category.readme.raw,
                    'roles': {
                        str(self.category_owner_as.sodar_uuid): {
                            'user': self.category_owner_as.user.username,
                            'role': self.category_owner_as.role.name,
                        }
                    },
                },
                str(self.project.sodar_uuid): {
                    'title': self.project.title,
                    'type': PROJECT_TYPE_PROJECT,
                    'level': REMOTE_LEVEL_READ_ROLES,
                    'description': self.project.description,
                    'readme': self.project.readme.raw,
                    'parent_uuid': str(self.category.sodar_uuid),
                    'roles': {
                        str(self.project_owner_as.sodar_uuid): {
                            'user': self.project_owner_as.user.username,
                            'role': self.project_owner_as.role.name,
                        }
                    },
                    'remote_sites': [str(self.peer_site.sodar_uuid)],
                },
            },
            'peer_sites': {
                str(self.peer_site.sodar_uuid): {
                    'name': self.peer_site.name,
                    'url': self.peer_site.url,
                    'description': self.peer_site.description,
                    'user_display': self.peer_site.user_display,
                }
            },
            'app_settings': {},
        }
        self.assertEqual(sync_data, expected)

    def test_revoked(self):
        """Test get data with project level of REVOKED"""
        user_source_new = self.make_user('new_source_user')
        self._make_assignment(self.project, user_source_new, self.role_guest)
        self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=REMOTE_LEVEL_REVOKED,
        )
        self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.peer_site,
            level=REMOTE_LEVEL_REVOKED,
        )
        sync_data = self.remote_api.get_source_data(self.target_site)
        expected = {
            'users': {
                str(self.user_source.sodar_uuid): {
                    'username': self.user_source.username,
                    'name': self.user_source.name,
                    'first_name': self.user_source.first_name,
                    'last_name': self.user_source.last_name,
                    'email': self.user_source.email,
                    'groups': [SOURCE_USER_GROUP],
                }
            },
            'projects': {
                str(self.category.sodar_uuid): {
                    'title': self.category.title,
                    'type': PROJECT_TYPE_CATEGORY,
                    'level': REMOTE_LEVEL_READ_INFO,
                    'parent_uuid': None,
                    'description': self.category.description,
                    'readme': self.category.readme.raw,
                },
                str(self.project.sodar_uuid): {
                    'title': self.project.title,
                    'type': PROJECT_TYPE_PROJECT,
                    'level': REMOTE_LEVEL_REVOKED,
                    'description': self.project.description,
                    'readme': self.project.readme.raw,
                    'parent_uuid': str(self.category.sodar_uuid),
                    'roles': {
                        str(self.project_owner_as.sodar_uuid): {
                            'user': self.project_owner_as.user.username,
                            'role': self.project_owner_as.role.name,
                        }  # NOTE: Another user should not be synced
                    },
                    'remote_sites': [],
                },
            },
            'peer_sites': {},
            'app_settings': {},
        }
        self.assertEqual(sync_data, expected)

    def test_no_access(self):
        """Test get data with no project access set in the source site"""
        sync_data = self.remote_api.get_source_data(self.target_site)
        expected = {
            'users': {},
            'projects': {},
            'peer_sites': {},
            'app_settings': {},
        }
        self.assertEqual(sync_data, expected)


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
class TestSyncRemoteDataBase(
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    SodarUserMixin,
    AppSettingMixin,
    TestCase,
):
    """Base class for tests for the sync_remote_data() API function"""

    def setUp(self):
        # Init users
        self.admin_user = self.make_user(settings.PROJECTROLES_DEFAULT_ADMIN)
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.maxDiff = None

        # Init roles
        self.role_owner = Role.objects.get_or_create(name=PROJECT_ROLE_OWNER)[0]
        self.role_delegate = Role.objects.get_or_create(
            name=PROJECT_ROLE_DELEGATE
        )[0]
        self.role_contributor = Role.objects.get_or_create(
            name=PROJECT_ROLE_CONTRIBUTOR
        )[0]
        self.role_guest = Role.objects.get_or_create(name=PROJECT_ROLE_GUEST)[0]

        # Init source site
        self.source_site = self._make_site(
            name=SOURCE_SITE_NAME,
            url=SOURCE_SITE_URL,
            mode=SITE_MODE_SOURCE,
            description=SOURCE_SITE_DESC,
            secret=SOURCE_SITE_SECRET,
        )

        self.remote_api = RemoteProjectAPI()

        # Default data to receive from source when testing site in target mode
        self.default_data = {
            'users': {
                SOURCE_USER_UUID: {
                    'sodar_uuid': SOURCE_USER_UUID,
                    'username': SOURCE_USER_USERNAME,
                    'name': SOURCE_USER_NAME,
                    'first_name': SOURCE_USER_FIRST_NAME,
                    'last_name': SOURCE_USER_LAST_NAME,
                    'email': SOURCE_USER_EMAIL,
                    'groups': [SOURCE_USER_GROUP],
                },
            },
            'projects': {
                SOURCE_CATEGORY_UUID: {
                    'title': SOURCE_CATEGORY_TITLE,
                    'type': PROJECT_TYPE_CATEGORY,
                    'level': REMOTE_LEVEL_READ_ROLES,
                    'parent_uuid': None,
                    'description': SOURCE_PROJECT_DESCRIPTION,
                    'readme': SOURCE_PROJECT_README,
                    'roles': {
                        SOURCE_CATEGORY_ROLE_UUID: {
                            'user': SOURCE_USER_USERNAME,
                            'role': self.role_owner.name,
                        },
                    },
                },
                SOURCE_PROJECT_UUID: {
                    'title': SOURCE_PROJECT_TITLE,
                    'type': PROJECT_TYPE_PROJECT,
                    'level': REMOTE_LEVEL_READ_ROLES,
                    'description': SOURCE_PROJECT_DESCRIPTION,
                    'readme': SOURCE_PROJECT_README,
                    'parent_uuid': SOURCE_CATEGORY_UUID,
                    'roles': {
                        SOURCE_PROJECT_ROLE_UUID: {
                            'user': SOURCE_USER_USERNAME,
                            'role': self.role_owner.name,
                        },
                    },
                    'remote_sites': [PEER_SITE_UUID],
                },
            },
            'peer_sites': {
                PEER_SITE_UUID: {
                    'name': PEER_SITE_NAME,
                    'url': PEER_SITE_URL,
                    'description': PEER_SITE_DESC,
                    'user_display': PEER_SITE_USER_DISPLAY,
                }
            },
            'app_settings': {
                PR_IP_RESTRICT_UUID: {
                    'name': 'ip_restrict',
                    'type': 'BOOLEAN',
                    'value': False,
                    'value_json': {},
                    'app_plugin': None,  # None is for 'projectroles' app
                    'project_uuid': SOURCE_PROJECT_UUID,
                    'user_uuid': None,
                    'local': False,
                },
                PR_IP_ALLOWLIST_UUID: {
                    'name': 'ip_allowlist',
                    'type': 'JSON',
                    'value': '',
                    'value_json': [],
                    'app_plugin': None,  # None is for 'projectroles' app
                    'project_uuid': SOURCE_PROJECT_UUID,
                    'user_uuid': None,
                    'local': False,
                },
            },
        }


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
class TestSyncRemoteDataCreate(TestSyncRemoteDataBase):
    """Creation tests for the sync_remote_data() API function"""

    def test_create(self):
        """Test sync with non-existing project data and READ_ROLE access"""
        self.assertEqual(Project.objects.all().count(), 0)
        self.assertEqual(RoleAssignment.objects.all().count(), 0)
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(RemoteProject.objects.all().count(), 0)
        self.assertEqual(RemoteSite.objects.all().count(), 1)

        self.default_data['users'].update(
            {
                SOURCE_USER2_UUID: {
                    'sodar_uuid': SOURCE_USER2_UUID,
                    'username': SOURCE_USER2_USERNAME,
                    'name': SOURCE_USER2_NAME,
                    'first_name': SOURCE_USER2_FIRST_NAME,
                    'last_name': SOURCE_USER2_LAST_NAME,
                    'email': SOURCE_USER2_EMAIL,
                    'groups': [SOURCE_USER2_GROUP],
                },
                SOURCE_USER3_UUID: {
                    'sodar_uuid': SOURCE_USER3_UUID,
                    'username': SOURCE_USER3_USERNAME,
                    'name': SOURCE_USER3_NAME,
                    'first_name': SOURCE_USER3_FIRST_NAME,
                    'last_name': SOURCE_USER3_LAST_NAME,
                    'email': SOURCE_USER3_EMAIL,
                    'groups': [SOURCE_USER3_GROUP],
                },
                SOURCE_USER4_UUID: {
                    'sodar_uuid': SOURCE_USER4_UUID,
                    'username': SOURCE_USER4_USERNAME,
                    'name': SOURCE_USER4_NAME,
                    'first_name': SOURCE_USER4_FIRST_NAME,
                    'last_name': SOURCE_USER4_LAST_NAME,
                    'email': SOURCE_USER4_EMAIL,
                    'groups': [SOURCE_USER4_GROUP],
                },
            }
        )
        self.default_data['projects'][SOURCE_CATEGORY_UUID]['roles'].update(
            {
                SOURCE_CATEGORY_ROLE2_UUID: {
                    'user': SOURCE_USER2_USERNAME,
                    'role': self.role_delegate.name,
                },
                SOURCE_CATEGORY_ROLE3_UUID: {
                    'user': SOURCE_USER3_USERNAME,
                    'role': self.role_contributor.name,
                },
                SOURCE_CATEGORY_ROLE4_UUID: {
                    'user': SOURCE_USER4_USERNAME,
                    'role': self.role_guest.name,
                },
            }
        )
        self.default_data['projects'][SOURCE_PROJECT_UUID]['roles'].update(
            {
                SOURCE_PROJECT_ROLE2_UUID: {
                    'user': SOURCE_USER2_USERNAME,
                    'role': self.role_delegate.name,
                },
                SOURCE_PROJECT_ROLE3_UUID: {
                    'user': SOURCE_USER3_USERNAME,
                    'role': self.role_contributor.name,
                },
                SOURCE_PROJECT_ROLE4_UUID: {
                    'user': SOURCE_USER4_USERNAME,
                    'role': self.role_guest.name,
                },
            }
        )
        original_data = deepcopy(self.default_data)

        # Do sync
        self.remote_api.sync_remote_data(self.source_site, self.default_data)

        # Assert database status
        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 8)
        self.assertEqual(User.objects.all().count(), 5)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)
        self.assertEqual(AppSetting.objects.count(), 2)

        new_user = User.objects.get(username=SOURCE_USER_USERNAME)
        new_user2 = User.objects.get(username=SOURCE_USER2_USERNAME)
        new_user3 = User.objects.get(username=SOURCE_USER3_USERNAME)
        new_user4 = User.objects.get(username=SOURCE_USER4_USERNAME)

        category_obj = Project.objects.get(sodar_uuid=SOURCE_CATEGORY_UUID)
        expected = {
            'id': category_obj.pk,
            'title': SOURCE_CATEGORY_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'description': SOURCE_PROJECT_DESCRIPTION,
            'parent': None,
            'public_guest_access': False,
            'submit_status': SUBMIT_STATUS_OK,
            'full_title': SOURCE_CATEGORY_TITLE,
            'has_public_children': False,
            'sodar_uuid': uuid.UUID(SOURCE_CATEGORY_UUID),
        }
        model_dict = model_to_dict(category_obj)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        c_owner_obj = RoleAssignment.objects.get(
            sodar_uuid=SOURCE_CATEGORY_ROLE_UUID
        )
        c_delegate_obj = RoleAssignment.objects.get(
            sodar_uuid=SOURCE_CATEGORY_ROLE2_UUID
        )
        c_contributor_obj = RoleAssignment.objects.get(
            sodar_uuid=SOURCE_CATEGORY_ROLE3_UUID
        )
        c_guest_obj = RoleAssignment.objects.get(
            sodar_uuid=SOURCE_CATEGORY_ROLE4_UUID
        )

        expected = {
            'id': c_owner_obj.pk,
            'project': category_obj.pk,
            'user': new_user.pk,
            'role': self.role_owner.pk,
            'sodar_uuid': uuid.UUID(SOURCE_CATEGORY_ROLE_UUID),
        }
        self.assertEqual(model_to_dict(c_owner_obj), expected)
        expected = {
            'id': c_delegate_obj.pk,
            'project': category_obj.pk,
            'user': new_user2.pk,
            'role': self.role_delegate.pk,
            'sodar_uuid': uuid.UUID(SOURCE_CATEGORY_ROLE2_UUID),
        }
        self.assertEqual(model_to_dict(c_delegate_obj), expected)
        expected = {
            'id': c_contributor_obj.pk,
            'project': category_obj.pk,
            'user': new_user3.pk,
            'role': self.role_contributor.pk,
            'sodar_uuid': uuid.UUID(SOURCE_CATEGORY_ROLE3_UUID),
        }
        self.assertEqual(model_to_dict(c_contributor_obj), expected)
        expected = {
            'id': c_guest_obj.pk,
            'project': category_obj.pk,
            'user': new_user4.pk,
            'role': self.role_guest.pk,
            'sodar_uuid': uuid.UUID(SOURCE_CATEGORY_ROLE4_UUID),
        }
        self.assertEqual(model_to_dict(c_guest_obj), expected)

        project_obj = Project.objects.get(sodar_uuid=SOURCE_PROJECT_UUID)
        expected = {
            'id': project_obj.pk,
            'title': SOURCE_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'description': SOURCE_PROJECT_DESCRIPTION,
            'parent': category_obj.pk,
            'public_guest_access': False,
            'submit_status': SUBMIT_STATUS_OK,
            'full_title': SOURCE_PROJECT_FULL_TITLE,
            'has_public_children': False,
            'sodar_uuid': uuid.UUID(SOURCE_PROJECT_UUID),
        }
        model_dict = model_to_dict(project_obj)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        p_owner_obj = RoleAssignment.objects.get(
            sodar_uuid=SOURCE_PROJECT_ROLE_UUID
        )
        p_delegate_obj = RoleAssignment.objects.get(
            sodar_uuid=SOURCE_PROJECT_ROLE2_UUID
        )
        p_contributor_obj = RoleAssignment.objects.get(
            sodar_uuid=SOURCE_PROJECT_ROLE3_UUID
        )
        p_guest_obj = RoleAssignment.objects.get(
            sodar_uuid=SOURCE_PROJECT_ROLE4_UUID
        )

        expected = {
            'id': p_owner_obj.pk,
            'project': project_obj.pk,
            'user': new_user.pk,
            'role': self.role_owner.pk,
            'sodar_uuid': uuid.UUID(SOURCE_PROJECT_ROLE_UUID),
        }
        self.assertEqual(model_to_dict(p_owner_obj), expected)
        expected = {
            'id': p_delegate_obj.pk,
            'project': project_obj.pk,
            'user': new_user2.pk,
            'role': self.role_delegate.pk,
            'sodar_uuid': uuid.UUID(SOURCE_PROJECT_ROLE2_UUID),
        }
        self.assertEqual(model_to_dict(p_delegate_obj), expected)
        expected = {
            'id': p_contributor_obj.pk,
            'project': project_obj.pk,
            'user': new_user3.pk,
            'role': self.role_contributor.pk,
            'sodar_uuid': uuid.UUID(SOURCE_PROJECT_ROLE3_UUID),
        }
        self.assertEqual(model_to_dict(p_contributor_obj), expected)
        expected = {
            'id': p_guest_obj.pk,
            'project': project_obj.pk,
            'user': new_user4.pk,
            'role': self.role_guest.pk,
            'sodar_uuid': uuid.UUID(SOURCE_PROJECT_ROLE4_UUID),
        }
        self.assertEqual(model_to_dict(p_guest_obj), expected)

        remote_cat_obj = RemoteProject.objects.get(
            site=self.source_site, project_uuid=category_obj.sodar_uuid
        )
        expected = {
            'id': remote_cat_obj.pk,
            'site': self.source_site.pk,
            'project_uuid': category_obj.sodar_uuid,
            'project': category_obj.pk,
            'level': REMOTE_LEVEL_READ_ROLES,
            'date_access': remote_cat_obj.date_access,
            'sodar_uuid': remote_cat_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(remote_cat_obj), expected)

        remote_project_obj = RemoteProject.objects.get(
            site=self.source_site, project_uuid=project_obj.sodar_uuid
        )
        expected = {
            'id': remote_project_obj.pk,
            'site': self.source_site.pk,
            'project_uuid': project_obj.sodar_uuid,
            'project': project_obj.pk,
            'level': REMOTE_LEVEL_READ_ROLES,
            'date_access': remote_project_obj.date_access,
            'sodar_uuid': remote_project_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(remote_project_obj), expected)

        peer_site_obj = RemoteSite.objects.get(
            sodar_uuid=PEER_SITE_UUID, mode=SITE_MODE_PEER
        )
        expected = {
            'name': PEER_SITE_NAME,
            'url': PEER_SITE_URL,
            'mode': SITE_MODE_PEER,
            'description': PEER_SITE_DESC,
            'secret': None,
            'sodar_uuid': uuid.UUID(PEER_SITE_UUID),
            'user_display': PEER_SITE_USER_DISPLAY,
        }
        peer_site_dict = model_to_dict(peer_site_obj)
        peer_site_dict.pop('id')
        self.assertEqual(peer_site_dict, expected)

        peer_project_obj = RemoteProject.objects.get(site=peer_site_obj)
        expected = {
            'site': peer_site_obj.pk,
            'project_uuid': project_obj.sodar_uuid,
            'project': project_obj.pk,
        }
        peer_project_dict = model_to_dict(peer_project_obj)
        peer_project_dict.pop('id')
        peer_project_dict.pop('sodar_uuid')
        peer_project_dict.pop('level')
        peer_project_dict.pop('date_access')
        self.assertEqual(peer_project_dict, expected)

        app_setting_ip_restrict_obj = AppSetting.objects.get(
            sodar_uuid=PR_IP_RESTRICT_UUID,
        )
        app_setting_ip_allowlist_obj = AppSetting.objects.get(
            sodar_uuid=PR_IP_ALLOWLIST_UUID,
        )

        expected_ip_restrict = {
            'name': 'ip_restrict',
            'type': 'BOOLEAN',
            'value': '0',
            'value_json': {},
            'sodar_uuid': uuid.UUID(PR_IP_RESTRICT_UUID),
            'project': project_obj.id,
            'app_plugin': None,
            'user': None,
            'user_modifiable': True,
        }
        expected_ip_allowlist = {
            'name': 'ip_allowlist',
            'type': 'JSON',
            'value': '',
            'value_json': [],
            'sodar_uuid': uuid.UUID(PR_IP_ALLOWLIST_UUID),
            'project': project_obj.id,
            'app_plugin': None,
            'user': None,
            'user_modifiable': True,
        }
        app_setting_ip_restrict_dict = model_to_dict(
            app_setting_ip_restrict_obj
        )
        app_setting_ip_allowlist_dict = model_to_dict(
            app_setting_ip_allowlist_obj
        )
        app_setting_ip_restrict_dict.pop('id')
        app_setting_ip_allowlist_dict.pop('id')

        self.assertEqual(app_setting_ip_allowlist_dict, expected_ip_allowlist)
        self.assertEqual(app_setting_ip_restrict_dict, expected_ip_restrict)

        # Assert remote_data changes
        expected = original_data
        expected['users'][SOURCE_USER_UUID]['status'] = 'created'
        expected['users'][SOURCE_USER2_UUID]['status'] = 'created'
        expected['users'][SOURCE_USER3_UUID]['status'] = 'created'
        expected['users'][SOURCE_USER4_UUID]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['roles'][
            SOURCE_CATEGORY_ROLE_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['roles'][
            SOURCE_CATEGORY_ROLE2_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['roles'][
            SOURCE_CATEGORY_ROLE3_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['roles'][
            SOURCE_CATEGORY_ROLE4_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['roles'][
            SOURCE_PROJECT_ROLE_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['roles'][
            SOURCE_PROJECT_ROLE2_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['roles'][
            SOURCE_PROJECT_ROLE3_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['roles'][
            SOURCE_PROJECT_ROLE4_UUID
        ]['status'] = 'created'
        expected['app_settings'][PR_IP_RESTRICT_UUID]['status'] = 'created'
        expected['app_settings'][PR_IP_ALLOWLIST_UUID]['status'] = 'created'
        self.assertEqual(self.default_data, expected)

    def test_create_app_setting_local(self):
        """Test creating a local app setting"""
        remote_data = self.default_data
        remote_data['app_settings'][PR_IP_RESTRICT_UUID]['local'] = True
        remote_data['app_settings'][PR_IP_ALLOWLIST_UUID]['local'] = True
        original_data = deepcopy(remote_data)

        self.remote_api.sync_remote_data(self.source_site, remote_data)

        expected = original_data
        expected['users'][SOURCE_USER_UUID]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['roles'][
            SOURCE_CATEGORY_ROLE_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['roles'][
            SOURCE_PROJECT_ROLE_UUID
        ]['status'] = 'created'
        expected['app_settings'][PR_IP_RESTRICT_UUID]['status'] = 'created'
        expected['app_settings'][PR_IP_ALLOWLIST_UUID]['status'] = 'created'
        self.assertEqual(remote_data, expected)

    def test_create_multiple(self):
        """Test sync with non-existing project data and multiple projects"""
        self.assertEqual(Project.objects.all().count(), 0)
        self.assertEqual(RoleAssignment.objects.all().count(), 0)
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(RemoteProject.objects.all().count(), 0)
        self.assertEqual(RemoteSite.objects.all().count(), 1)

        remote_data = self.default_data
        new_project_uuid = str(uuid.uuid4())
        new_project_title = 'New Project Title'
        new_role_uuid = str(uuid.uuid4())
        remote_data['projects'][new_project_uuid] = {
            'title': new_project_title,
            'type': PROJECT_TYPE_PROJECT,
            'level': REMOTE_LEVEL_READ_ROLES,
            'description': SOURCE_PROJECT_DESCRIPTION,
            'readme': SOURCE_PROJECT_README,
            'parent_uuid': SOURCE_CATEGORY_UUID,
            'roles': {
                new_role_uuid: {
                    'user': SOURCE_USER_USERNAME,
                    'role': self.role_owner.name,
                }
            },
        }
        original_data = deepcopy(remote_data)

        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 3)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(User.objects.all().count(), 2)
        self.assertEqual(RemoteProject.objects.all().count(), 4)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

        new_user = User.objects.get(username=SOURCE_USER_USERNAME)
        category_obj = Project.objects.get(sodar_uuid=SOURCE_CATEGORY_UUID)
        new_project_obj = Project.objects.get(sodar_uuid=new_project_uuid)
        expected = {
            'id': new_project_obj.pk,
            'title': new_project_title,
            'type': PROJECT_TYPE_PROJECT,
            'description': SOURCE_PROJECT_DESCRIPTION,
            'parent': category_obj.pk,
            'public_guest_access': False,
            'submit_status': SUBMIT_STATUS_OK,
            'full_title': SOURCE_CATEGORY_TITLE + ' / ' + new_project_title,
            'has_public_children': False,
            'sodar_uuid': uuid.UUID(new_project_uuid),
        }
        model_dict = model_to_dict(new_project_obj)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        p_new_owner_obj = RoleAssignment.objects.get(sodar_uuid=new_role_uuid)
        expected = {
            'id': p_new_owner_obj.pk,
            'project': new_project_obj.pk,
            'user': new_user.pk,
            'role': self.role_owner.pk,
            'sodar_uuid': uuid.UUID(new_role_uuid),
        }
        self.assertEqual(model_to_dict(p_new_owner_obj), expected)

        expected = original_data
        expected['users'][SOURCE_USER_UUID]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['roles'][
            SOURCE_CATEGORY_ROLE_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['roles'][
            SOURCE_PROJECT_ROLE_UUID
        ]['status'] = 'created'
        expected['projects'][new_project_uuid]['status'] = 'created'
        expected['projects'][new_project_uuid]['roles'][new_role_uuid][
            'status'
        ] = 'created'
        expected['app_settings'][PR_IP_RESTRICT_UUID]['status'] = 'created'
        expected['app_settings'][PR_IP_ALLOWLIST_UUID]['status'] = 'created'
        self.assertEqual(remote_data, expected)

    def test_create_local_owner(self):
        """Test sync with non-existing project data and a local owner"""
        self.assertEqual(Project.objects.all().count(), 0)
        self.assertEqual(RoleAssignment.objects.all().count(), 0)
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(RemoteProject.objects.all().count(), 0)
        self.assertEqual(RemoteSite.objects.all().count(), 1)

        remote_data = self.default_data
        remote_data['users'][SOURCE_USER_UUID]['username'] = 'source_admin'
        remote_data['projects'][SOURCE_CATEGORY_UUID]['roles'][
            SOURCE_CATEGORY_ROLE_UUID
        ]['user'] = 'source_admin'
        remote_data['projects'][SOURCE_PROJECT_UUID]['roles'][
            SOURCE_PROJECT_ROLE_UUID
        ]['user'] = 'source_admin'

        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)
        category_obj = Project.objects.get(sodar_uuid=SOURCE_CATEGORY_UUID)
        self.assertEqual(category_obj.get_owner().user, self.admin_user)
        project_obj = Project.objects.get(sodar_uuid=SOURCE_PROJECT_UUID)
        self.assertEqual(project_obj.get_owner().user, self.admin_user)

    def test_create_category_conflict(self):
        """Test sync with conflict in local categories (should fail)"""
        self._make_project(
            title=SOURCE_CATEGORY_TITLE,
            type=PROJECT_TYPE_CATEGORY,
            parent=None,
        )
        self.assertEqual(Project.objects.all().count(), 1)
        self.assertEqual(RoleAssignment.objects.all().count(), 0)
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(RemoteProject.objects.all().count(), 0)
        self.assertEqual(RemoteSite.objects.all().count(), 1)
        remote_data = self.default_data

        # Do sync, assert an exception is raised
        with self.assertRaises(ValueError):
            self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 1)
        self.assertEqual(RoleAssignment.objects.all().count(), 0)
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(RemoteProject.objects.all().count(), 0)
        self.assertEqual(RemoteSite.objects.all().count(), 1)

    def test_create_no_access(self):
        """Test sync with no READ_ROLE access set"""
        remote_data = self.default_data
        remote_data['projects'][SOURCE_CATEGORY_UUID][
            'level'
        ] = REMOTE_LEVEL_READ_INFO
        remote_data['projects'][SOURCE_PROJECT_UUID][
            'level'
        ] = REMOTE_LEVEL_READ_INFO
        original_data = deepcopy(remote_data)

        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 0)
        self.assertEqual(RoleAssignment.objects.all().count(), 0)
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(RemoteProject.objects.all().count(), 0)
        self.assertEqual(RemoteSite.objects.all().count(), 1)
        # Assert no changes between update_data and remote_data
        self.assertEqual(original_data, remote_data)

    def test_create_local_user(self):
        """Test sync with a local non-owner user"""
        local_user_username = 'localusername'
        local_user_uuid = str(uuid.uuid4())
        role_uuid = str(uuid.uuid4())
        remote_data = self.default_data
        remote_data['users'][local_user_uuid] = {
            'sodar_uuid': local_user_uuid,
            'username': local_user_username,
            'name': SOURCE_USER_NAME,
            'first_name': SOURCE_USER_FIRST_NAME,
            'last_name': SOURCE_USER_LAST_NAME,
            'email': SOURCE_USER_EMAIL,
            'groups': ['system'],
        }
        remote_data['projects'][SOURCE_PROJECT_UUID]['roles'][role_uuid] = {
            'user': local_user_username,
            'role': self.role_contributor.name,
        }

        self.remote_api.sync_remote_data(self.source_site, remote_data)

        # Assert database status (the new user and role should not be created)
        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 2)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_create_local_user_allow(self):
        """Test sync with a local user with local users allowed"""
        local_user_username = 'localusername'
        local_user_uuid = str(uuid.uuid4())
        role_uuid = str(uuid.uuid4())
        remote_data = self.default_data
        # Create the user on the target site
        self.make_user(local_user_username)
        remote_data['users'][local_user_uuid] = {
            'sodar_uuid': local_user_uuid,
            'username': local_user_username,
            'name': SOURCE_USER_NAME,
            'first_name': SOURCE_USER_FIRST_NAME,
            'last_name': SOURCE_USER_LAST_NAME,
            'email': SOURCE_USER_EMAIL,
            'groups': ['system'],
        }
        remote_data['projects'][SOURCE_PROJECT_UUID]['roles'][role_uuid] = {
            'user': local_user_username,
            'role': self.role_contributor.name,
        }

        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(User.objects.all().count(), 3)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_create_local_user_allow_unavailable(self):
        """Test sync with a non-existent local user with local users allowed"""
        local_user_username = 'localusername'
        local_user_uuid = str(uuid.uuid4())
        role_uuid = str(uuid.uuid4())
        remote_data = self.default_data
        remote_data['users'][local_user_uuid] = {
            'sodar_uuid': local_user_uuid,
            'username': local_user_username,
            'name': SOURCE_USER_NAME,
            'first_name': SOURCE_USER_FIRST_NAME,
            'last_name': SOURCE_USER_LAST_NAME,
            'email': SOURCE_USER_EMAIL,
            'groups': ['system'],
        }
        remote_data['projects'][SOURCE_PROJECT_UUID]['roles'][role_uuid] = {
            'user': local_user_username,
            'role': self.role_contributor.name,
        }

        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 2)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_create_local_owner_allow(self):
        """Test sync with a local owner with local users allowed"""
        local_user_username = 'localusername'
        local_user_uuid = str(uuid.uuid4())
        role_uuid = str(uuid.uuid4())
        remote_data = self.default_data
        # Create the user on the target site
        new_user = self.make_user(local_user_username)
        remote_data['users'][local_user_uuid] = {
            'sodar_uuid': local_user_uuid,
            'username': local_user_username,
            'name': SOURCE_USER_NAME,
            'first_name': SOURCE_USER_FIRST_NAME,
            'last_name': SOURCE_USER_LAST_NAME,
            'email': SOURCE_USER_EMAIL,
            'groups': ['system'],
        }
        remote_data['projects'][SOURCE_PROJECT_UUID]['roles'] = {
            role_uuid: {
                'user': local_user_username,
                'role': self.role_owner.name,
            }
        }

        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 3)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)
        # Assert owner role
        new_project = Project.objects.get(sodar_uuid=SOURCE_PROJECT_UUID)
        self.assertEqual(new_project.get_owner().user, new_user)

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_create_local_owner_allow_unavailable(self):
        """Test sync with an unavailable local owner"""
        local_user_username = 'localusername'
        local_user_uuid = str(uuid.uuid4())
        role_uuid = str(uuid.uuid4())
        remote_data = self.default_data
        # Create the user on the target site
        remote_data['users'][local_user_uuid] = {
            'sodar_uuid': local_user_uuid,
            'username': local_user_username,
            'name': SOURCE_USER_NAME,
            'first_name': SOURCE_USER_FIRST_NAME,
            'last_name': SOURCE_USER_LAST_NAME,
            'email': SOURCE_USER_EMAIL,
            'groups': ['system'],
        }

        remote_data['projects'][SOURCE_PROJECT_UUID]['roles'] = {
            role_uuid: {
                'user': local_user_username,
                'role': self.role_owner.name,
            }
        }

        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 2)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)
        # Assert owner role
        new_project = Project.objects.get(sodar_uuid=SOURCE_PROJECT_UUID)
        self.assertEqual(new_project.get_owner().user, self.admin_user)


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
class TestSyncRemoteDataUpdate(TestSyncRemoteDataBase):
    """Updating tests for the sync_remote_data() API function"""

    def setUp(self):
        super().setUp()

        # Set up target category and project
        self.category_obj = self._make_project(
            title='NewCategoryTitle',
            type=PROJECT_TYPE_CATEGORY,
            parent=None,
            description='New description',
            readme='New readme',
            sodar_uuid=SOURCE_CATEGORY_UUID,
        )
        self.project_obj = self._make_project(
            title='NewProjectTitle',
            type=PROJECT_TYPE_PROJECT,
            parent=self.category_obj,
            description='New description',
            readme='New readme',
            sodar_uuid=SOURCE_PROJECT_UUID,
        )

        # Set up user and roles
        self.target_user = self._make_sodar_user(
            username=SOURCE_USER_USERNAME,
            name='NewFirstName NewLastName',
            first_name='NewFirstName',
            last_name='NewLastName',
            email='newemail@example.com',
        )
        self.c_owner_obj = self._make_assignment(
            self.category_obj, self.target_user, self.role_owner
        )
        self.p_owner_obj = self._make_assignment(
            self.project_obj, self.target_user, self.role_owner
        )

        # Set up RemoteProject objects
        self._make_remote_project(
            project_uuid=self.category_obj.sodar_uuid,
            project=self.category_obj,
            site=self.source_site,
            level=REMOTE_LEVEL_READ_ROLES,
        )
        self._make_remote_project(
            project_uuid=self.project_obj.sodar_uuid,
            project=self.project_obj,
            site=self.source_site,
            level=REMOTE_LEVEL_READ_ROLES,
        )

        # Set up Peer Objects
        self.peer_site = RemoteSite.objects.create(
            **{
                'name': PEER_SITE_NAME,
                'url': PEER_SITE_URL,
                'mode': SITE_MODE_PEER,
                'description': PEER_SITE_DESC,
                'secret': None,
                'sodar_uuid': PEER_SITE_UUID,
                'user_display': PEER_SITE_USER_DISPLAY,
            }
        )

        self._make_remote_project(
            project_uuid=self.project_obj.sodar_uuid,
            project=self.project_obj,
            site=self.peer_site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_NONE'],
        )

        # Init IP restrict setting
        self._make_setting(
            app_name='projectroles',
            name='ip_restrict',
            setting_type='BOOLEAN',
            value=False,
            project=self.project_obj,
            sodar_uuid=PR_IP_RESTRICT_UUID,
        )
        # Init IP allowlist setting
        self._make_setting(
            app_name='projectroles',
            name='ip_allowlist',
            setting_type='JSON',
            value=None,
            value_json=[],
            project=self.project_obj,
            sodar_uuid=PR_IP_ALLOWLIST_UUID,
        )

        # Update default data
        self.default_data['projects'][SOURCE_CATEGORY_UUID][
            'status'
        ] = 'updated'
        self.default_data['projects'][SOURCE_PROJECT_UUID]['status'] = 'updated'
        self.default_data['users'][SOURCE_USER_UUID]['status'] = 'updated'

    def test_update(self):
        """Test sync with existing project data and READ_ROLE access"""
        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 2)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)
        self.assertEqual(AppSetting.objects.count(), 2)

        remote_data = self.default_data
        # Add new user and contributor role to source project
        new_user_username = 'newuser@' + SOURCE_USER_DOMAIN
        new_user_uuid = str(uuid.uuid4())
        new_role_uuid = str(uuid.uuid4())
        remote_data['users'][str(new_user_uuid)] = {
            'sodar_uuid': new_user_uuid,
            'username': new_user_username,
            'name': 'Some Name',
            'first_name': 'Some',
            'last_name': 'Name',
            'groups': [SOURCE_USER_GROUP],
        }
        remote_data['projects'][SOURCE_PROJECT_UUID]['roles'][new_role_uuid] = {
            'user': new_user_username,
            'role': PROJECT_ROLE_CONTRIBUTOR,
        }

        # Change Peer Site data
        remote_data['peer_sites'][PEER_SITE_UUID]['name'] = NEW_PEER_NAME
        remote_data['peer_sites'][PEER_SITE_UUID]['description'] = NEW_PEER_DESC
        remote_data['peer_sites'][PEER_SITE_UUID][
            'user_display'
        ] = NEW_PEER_USER_DISPLAY
        original_data = deepcopy(remote_data)
        # Change projectroles app settings
        remote_data['app_settings'][PR_IP_RESTRICT_UUID]['value'] = True
        remote_data['app_settings'][PR_IP_ALLOWLIST_UUID]['value_json'] = [
            '192.168.1.1'
        ]

        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(User.objects.all().count(), 3)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)
        self.assertEqual(AppSetting.objects.count(), 2)

        new_user = User.objects.get(username=new_user_username)

        self.category_obj.refresh_from_db()
        expected = {
            'id': self.category_obj.pk,
            'title': SOURCE_CATEGORY_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'description': SOURCE_PROJECT_DESCRIPTION,
            'parent': None,
            'public_guest_access': False,
            'submit_status': SUBMIT_STATUS_OK,
            'full_title': SOURCE_CATEGORY_TITLE,
            'has_public_children': False,
            'sodar_uuid': uuid.UUID(SOURCE_CATEGORY_UUID),
        }
        model_dict = model_to_dict(self.category_obj)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        self.c_owner_obj.refresh_from_db()
        expected = {
            'id': self.c_owner_obj.pk,
            'project': self.category_obj.pk,
            'user': self.target_user.pk,
            'role': self.role_owner.pk,
            'sodar_uuid': self.c_owner_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.c_owner_obj), expected)

        self.project_obj.refresh_from_db()
        expected = {
            'id': self.project_obj.pk,
            'title': SOURCE_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'description': SOURCE_PROJECT_DESCRIPTION,
            'parent': self.category_obj.pk,
            'public_guest_access': False,
            'submit_status': SUBMIT_STATUS_OK,
            'full_title': SOURCE_PROJECT_FULL_TITLE,
            'has_public_children': False,
            'sodar_uuid': uuid.UUID(SOURCE_PROJECT_UUID),
        }
        model_dict = model_to_dict(self.project_obj)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        self.p_owner_obj.refresh_from_db()
        expected = {
            'id': self.p_owner_obj.pk,
            'project': self.project_obj.pk,
            'user': self.target_user.pk,
            'role': self.role_owner.pk,
            'sodar_uuid': self.p_owner_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.p_owner_obj), expected)

        p_contrib_obj = RoleAssignment.objects.get(
            project__sodar_uuid=SOURCE_PROJECT_UUID,
            role__name=PROJECT_ROLE_CONTRIBUTOR,
        )
        expected = {
            'id': p_contrib_obj.pk,
            'project': self.project_obj.pk,
            'user': new_user.pk,
            'role': self.role_contributor.pk,
            'sodar_uuid': p_contrib_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(p_contrib_obj), expected)

        remote_cat_obj = RemoteProject.objects.get(
            site=self.source_site, project_uuid=self.category_obj.sodar_uuid
        )
        expected = {
            'id': remote_cat_obj.pk,
            'site': self.source_site.pk,
            'project_uuid': self.category_obj.sodar_uuid,
            'project': self.category_obj.pk,
            'level': REMOTE_LEVEL_READ_ROLES,
            'date_access': remote_cat_obj.date_access,
            'sodar_uuid': remote_cat_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(remote_cat_obj), expected)

        remote_project_obj = RemoteProject.objects.get(
            site=self.source_site, project_uuid=self.project_obj.sodar_uuid
        )
        expected = {
            'id': remote_project_obj.pk,
            'site': self.source_site.pk,
            'project_uuid': self.project_obj.sodar_uuid,
            'project': self.project_obj.pk,
            'level': REMOTE_LEVEL_READ_ROLES,
            'date_access': remote_project_obj.date_access,
            'sodar_uuid': remote_project_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(remote_project_obj), expected)

        peer_site_obj = RemoteSite.objects.get(
            sodar_uuid=PEER_SITE_UUID, mode=SITE_MODE_PEER
        )
        expected = {
            'name': NEW_PEER_NAME,
            'url': PEER_SITE_URL,
            'mode': SITE_MODE_PEER,
            'description': NEW_PEER_DESC,
            'secret': None,
            'user_display': NEW_PEER_USER_DISPLAY,
        }
        peer_site_dict = model_to_dict(peer_site_obj)
        peer_site_dict.pop('id')
        peer_site_dict.pop('sodar_uuid')
        self.assertEqual(peer_site_dict, expected)

        peer_project_obj = RemoteProject.objects.get(site=peer_site_obj)
        expected = {
            'site': peer_site_obj.pk,
            'project_uuid': self.project_obj.sodar_uuid,
            'project': self.project_obj.pk,
        }
        peer_project_dict = model_to_dict(peer_project_obj)
        peer_project_dict.pop('id')
        peer_project_dict.pop('sodar_uuid')
        peer_project_dict.pop('level')
        peer_project_dict.pop('date_access')
        self.assertEqual(peer_project_dict, expected)

        app_setting_ip_restrict_obj = AppSetting.objects.get(
            sodar_uuid=PR_IP_RESTRICT_UUID,
        )
        app_setting_ip_allowlist_obj = AppSetting.objects.get(
            sodar_uuid=PR_IP_ALLOWLIST_UUID,
        )
        expected_ip_restrict = {
            'name': 'ip_restrict',
            'type': 'BOOLEAN',
            'value': '1',
            'value_json': {},
            'sodar_uuid': uuid.UUID(PR_IP_RESTRICT_UUID),
            'project': self.project_obj.id,
            'app_plugin': None,
            'user': None,
            'user_modifiable': True,
        }
        expected_ip_allowlist = {
            'name': 'ip_allowlist',
            'type': 'JSON',
            'value': '',
            'value_json': ['192.168.1.1'],
            'sodar_uuid': uuid.UUID(PR_IP_ALLOWLIST_UUID),
            'project': self.project_obj.id,
            'app_plugin': None,
            'user': None,
            'user_modifiable': True,
        }
        app_setting_ip_restrict_dict = model_to_dict(
            app_setting_ip_restrict_obj
        )
        app_setting_ip_allowlist_dict = model_to_dict(
            app_setting_ip_allowlist_obj
        )
        app_setting_ip_restrict_dict.pop('id')
        app_setting_ip_allowlist_dict.pop('id')

        self.assertEqual(app_setting_ip_allowlist_dict, expected_ip_allowlist)
        self.assertEqual(app_setting_ip_restrict_dict, expected_ip_restrict)

        # Assert update_data changes
        expected = original_data
        expected['users'][SOURCE_USER_UUID]['status'] = 'updated'
        expected['users'][new_user_uuid]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['status'] = 'updated'
        expected['projects'][SOURCE_PROJECT_UUID]['status'] = 'updated'
        expected['projects'][SOURCE_PROJECT_UUID]['roles'][new_role_uuid][
            'status'
        ] = 'created'
        expected['app_settings'][PR_IP_RESTRICT_UUID]['value'] = True
        expected['app_settings'][PR_IP_ALLOWLIST_UUID]['value_json'] = [
            '192.168.1.1'
        ]
        expected['app_settings'][PR_IP_RESTRICT_UUID]['status'] = 'updated'
        expected['app_settings'][PR_IP_ALLOWLIST_UUID]['status'] = 'updated'
        self.assertEqual(remote_data, expected)

    def test_update_app_setting_local(self):
        """Test update with a local app setting"""
        remote_data = self.default_data
        # Change projectroles app settings
        remote_data['app_settings'][PR_IP_RESTRICT_UUID]['local'] = True
        remote_data['app_settings'][PR_IP_ALLOWLIST_UUID]['local'] = True
        remote_data['app_settings'][PR_IP_RESTRICT_UUID]['value'] = True
        remote_data['app_settings'][PR_IP_ALLOWLIST_UUID]['value_json'] = [
            '192.168.1.1'
        ]
        original_data = deepcopy(remote_data)

        self.remote_api.sync_remote_data(self.source_site, remote_data)

        app_setting_ip_restrict_obj = AppSetting.objects.get(
            sodar_uuid=PR_IP_RESTRICT_UUID,
        )
        app_setting_ip_allowlist_obj = AppSetting.objects.get(
            sodar_uuid=PR_IP_ALLOWLIST_UUID,
        )
        expected_ip_restrict = {
            'name': 'ip_restrict',
            'type': 'BOOLEAN',
            'value': '0',
            'value_json': {},
            'sodar_uuid': uuid.UUID(PR_IP_RESTRICT_UUID),
            'project': self.project_obj.id,
            'app_plugin': None,
            'user': None,
            'user_modifiable': True,
        }
        expected_ip_allowlist = {
            'name': 'ip_allowlist',
            'type': 'JSON',
            'value': None,
            'value_json': [],
            'sodar_uuid': uuid.UUID(PR_IP_ALLOWLIST_UUID),
            'project': self.project_obj.id,
            'app_plugin': None,
            'user': None,
            'user_modifiable': True,
        }
        app_setting_ip_restrict_dict = model_to_dict(
            app_setting_ip_restrict_obj
        )
        app_setting_ip_allowlist_dict = model_to_dict(
            app_setting_ip_allowlist_obj
        )
        app_setting_ip_restrict_dict.pop('id')
        app_setting_ip_allowlist_dict.pop('id')

        self.assertEqual(app_setting_ip_allowlist_dict, expected_ip_allowlist)
        self.assertEqual(app_setting_ip_restrict_dict, expected_ip_restrict)

        # Assert update_data changes
        expected = original_data
        expected['users'][SOURCE_USER_UUID]['status'] = 'updated'
        expected['projects'][SOURCE_CATEGORY_UUID]['status'] = 'updated'
        expected['projects'][SOURCE_PROJECT_UUID]['status'] = 'updated'
        self.assertEqual(remote_data, expected)

    def test_update_app_setting_no_app(self):
        """Test update with app setting for app not present on target site"""
        self.assertEqual(AppSetting.objects.count(), 2)

        remote_data = self.default_data
        setting_uuid = str(uuid.uuid4())
        setting_name = 'NOT_A_VALID_SETTING'
        # Change projectroles app settings
        remote_data['app_settings'][setting_uuid] = {
            'name': setting_name,
            'type': 'BOOLEAN',
            'value': False,
            'value_json': {},
            'app_plugin': 'NOT_A_VALID_APP',
            'project_uuid': SOURCE_PROJECT_UUID,
            'user_uuid': None,
            'local': False,
        }

        self.remote_api.sync_remote_data(self.source_site, remote_data)

        # Make sure setting was not set
        self.assertIsNone(AppSetting.objects.filter(name=setting_name).first())

    def test_update_revoke(self):
        """Test sync with existing project data and REVOKED access"""
        new_user_username = 'newuser@' + SOURCE_USER_DOMAIN
        target_user2 = self._make_sodar_user(
            username=new_user_username,
            name='Some OtherName',
            first_name='Some',
            last_name='OtherName',
            email='othername@example.com',
        )
        self._make_assignment(
            self.project_obj, target_user2, self.role_contributor
        )
        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(User.objects.all().count(), 3)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

        remote_data = self.default_data
        # Revoke access to project
        remote_data['projects'][SOURCE_PROJECT_UUID][
            'level'
        ] = REMOTE_LEVEL_REVOKED
        remote_data['projects'][SOURCE_PROJECT_UUID]['remote_sites'] = []

        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 3)
        self.assertEqual(RemoteProject.objects.all().count(), 2)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

        new_user = User.objects.get(username=new_user_username)

        # Assert removal of role assignment
        with self.assertRaises(RoleAssignment.DoesNotExist):
            RoleAssignment.objects.get(
                project__sodar_uuid=SOURCE_PROJECT_UUID,
                user=new_user,
                role__name=PROJECT_ROLE_CONTRIBUTOR,
            )
        # Assert update_data changes
        self.assertEqual(
            remote_data['projects'][SOURCE_PROJECT_UUID]['level'],
            REMOTE_LEVEL_REVOKED,
        )
        self.assertNotIn(str(new_user.sodar_uuid), remote_data['users'].keys())

    def test_delete_role(self):
        """Test sync with existing project data and a removed role"""
        # Add new user and contributor role in target site
        new_user_username = 'newuser@' + SOURCE_USER_DOMAIN
        new_user = self.make_user(new_user_username)
        new_role_obj = self._make_assignment(
            self.project_obj, new_user, self.role_contributor
        )
        new_role_uuid = str(new_role_obj.sodar_uuid)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(User.objects.all().count(), 3)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

        remote_data = self.default_data
        original_data = deepcopy(remote_data)

        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 3)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)
        with self.assertRaises(RoleAssignment.DoesNotExist):
            RoleAssignment.objects.get(
                project__sodar_uuid=SOURCE_PROJECT_UUID,
                role__name=PROJECT_ROLE_CONTRIBUTOR,
            )

        expected = original_data
        expected['projects'][SOURCE_PROJECT_UUID]['roles'][new_role_uuid] = {
            'user': new_user_username,
            'role': PROJECT_ROLE_CONTRIBUTOR,
            'status': 'deleted',
        }
        expected['app_settings'][PR_IP_RESTRICT_UUID]['status'] = 'updated'
        expected['app_settings'][PR_IP_ALLOWLIST_UUID]['status'] = 'updated'
        self.assertEqual(remote_data, expected)

    def test_update_no_changes(self):
        """Test sync with existing project data and no changes"""
        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 2)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

        remote_data = self.default_data
        original_data = deepcopy(remote_data)

        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 2)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

        self.category_obj.refresh_from_db()
        expected = {
            'id': self.category_obj.pk,
            'title': SOURCE_CATEGORY_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'description': SOURCE_PROJECT_DESCRIPTION,
            'parent': None,
            'public_guest_access': False,
            'submit_status': SUBMIT_STATUS_OK,
            'full_title': SOURCE_CATEGORY_TITLE,
            'has_public_children': False,
            'sodar_uuid': uuid.UUID(SOURCE_CATEGORY_UUID),
        }
        model_dict = model_to_dict(self.category_obj)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        self.c_owner_obj.refresh_from_db()
        expected = {
            'id': self.c_owner_obj.pk,
            'project': self.category_obj.pk,
            'user': self.target_user.pk,
            'role': self.role_owner.pk,
            'sodar_uuid': self.c_owner_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.c_owner_obj), expected)

        self.project_obj.refresh_from_db()
        expected = {
            'id': self.project_obj.pk,
            'title': SOURCE_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'description': SOURCE_PROJECT_DESCRIPTION,
            'parent': self.category_obj.pk,
            'public_guest_access': False,
            'submit_status': SUBMIT_STATUS_OK,
            'full_title': SOURCE_PROJECT_FULL_TITLE,
            'has_public_children': False,
            'sodar_uuid': uuid.UUID(SOURCE_PROJECT_UUID),
        }
        model_dict = model_to_dict(self.project_obj)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        self.p_owner_obj.refresh_from_db()
        expected = {
            'id': self.p_owner_obj.pk,
            'project': self.project_obj.pk,
            'user': self.target_user.pk,
            'role': self.role_owner.pk,
            'sodar_uuid': self.p_owner_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.p_owner_obj), expected)

        remote_cat_obj = RemoteProject.objects.get(
            site=self.source_site, project_uuid=self.category_obj.sodar_uuid
        )
        expected = {
            'id': remote_cat_obj.pk,
            'site': self.source_site.pk,
            'project_uuid': self.category_obj.sodar_uuid,
            'project': self.category_obj.pk,
            'level': REMOTE_LEVEL_READ_ROLES,
            'date_access': remote_cat_obj.date_access,
            'sodar_uuid': remote_cat_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(remote_cat_obj), expected)

        remote_project_obj = RemoteProject.objects.get(
            site=self.source_site, project_uuid=self.project_obj.sodar_uuid
        )
        expected = {
            'id': remote_project_obj.pk,
            'site': self.source_site.pk,
            'project_uuid': self.project_obj.sodar_uuid,
            'project': self.project_obj.pk,
            'level': REMOTE_LEVEL_READ_ROLES,
            'date_access': remote_project_obj.date_access,
            'sodar_uuid': remote_project_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(remote_project_obj), expected)

        peer_site_obj = RemoteSite.objects.get(
            sodar_uuid=PEER_SITE_UUID, mode=SITE_MODE_PEER
        )
        expected = {
            'name': PEER_SITE_NAME,
            'url': PEER_SITE_URL,
            'mode': SITE_MODE_PEER,
            'description': PEER_SITE_DESC,
            'secret': None,
            'sodar_uuid': uuid.UUID(PEER_SITE_UUID),
            'user_display': PEER_SITE_USER_DISPLAY,
        }
        peer_site_dict = model_to_dict(peer_site_obj)
        peer_site_dict.pop('id')
        self.assertEqual(peer_site_dict, expected)

        peer_project_obj = RemoteProject.objects.get(site=peer_site_obj)
        expected = {
            'site': peer_site_obj.pk,
            'project_uuid': self.project_obj.sodar_uuid,
            'project': self.project_obj.pk,
        }
        peer_project_dict = model_to_dict(peer_project_obj)
        peer_project_dict.pop('id')
        peer_project_dict.pop('sodar_uuid')
        peer_project_dict.pop('level')
        peer_project_dict.pop('date_access')
        self.assertEqual(peer_project_dict, expected)

        # Assert no changes between update_data and remote_data
        # Except global app settings, they are always updated.
        original_data['app_settings'][PR_IP_RESTRICT_UUID]['status'] = 'updated'
        original_data['app_settings'][PR_IP_ALLOWLIST_UUID][
            'status'
        ] = 'updated'
        self.assertEqual(original_data, remote_data)
