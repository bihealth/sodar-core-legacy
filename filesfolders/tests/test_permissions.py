"""Permission tests for the filesfolders app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_permissions import TestProjectPermissionBase

from filesfolders.tests.test_models import (
    FileMixin,
    FolderMixin,
    HyperLinkMixin,
)

# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
APP_NAME = 'filesfolders'
SECRET = '7dqq83clo2iyhg29hifbor56og6911r5'


# App settings API
app_settings = AppSettingAPI()


class TestListPermissions(TestProjectPermissionBase):
    """Tests for the file list view"""

    def test_list(self):
        """Test file list"""
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
        ]
        bad_users = [self.user_no_roles, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        # Test public project
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 200)
        self.assert_response(url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_list_anon(self):
        """Test file list with anonynomus access"""
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.project.set_public()
        self.assert_response(url, self.anonymous, 200)


class TestFolderPermissions(FolderMixin, TestProjectPermissionBase):
    """Tests for Folder views"""

    def setUp(self):
        super().setUp()

        self.folder = self._make_folder(
            name='folder',
            project=self.project,
            folder=None,
            owner=self.owner_as.user,  # Project owner is the owner of folder
            description='',
        )

    def test_folder_create(self):
        """Test folder creation"""
        url = reverse(
            'filesfolders:folder_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
        ]
        bad_users = [self.guest_as.user, self.user_no_roles, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        # Test public project
        self.project.set_public()
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_folder_create_anon(self):
        """Test folder creation with anonymous access"""
        url = reverse(
            'filesfolders:folder_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, self.anonymous, 302)

    def test_folder_create_category(self):
        """Test folder creation under category"""
        url = reverse(
            'filesfolders:folder_create',
            kwargs={'project': self.category.sodar_uuid},
        )
        bad_users = [
            self.anonymous,
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, bad_users, 302)

    def test_folder_update(self):
        """Test folder updating"""
        url = reverse(
            'filesfolders:folder_update',
            kwargs={'item': self.folder.sodar_uuid},
        )
        good_users = [self.superuser, self.owner_as.user, self.delegate_as.user]
        bad_users = [
            self.contributor_as.user,  # NOTE: not the owner of the folder
            self.anonymous,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        # Test public project
        self.project.set_public()
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_folder_update_anon(self):
        """Test folder updating with anonymous access"""
        url = reverse(
            'filesfolders:folder_update',
            kwargs={'item': self.folder.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, self.anonymous, 302)

    def test_folder_delete(self):
        """Test folder deletion"""
        url = reverse(
            'filesfolders:folder_delete',
            kwargs={'item': self.folder.sodar_uuid},
        )
        good_users = [self.superuser, self.owner_as.user, self.delegate_as.user]
        bad_users = [
            self.contributor_as.user,  # NOTE: not the owner of the folder
            self.anonymous,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        # Test public project
        self.project.set_public()
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_folder_delete_anon(self):
        """Test folder deletion with anonymous access"""
        url = reverse(
            'filesfolders:folder_delete',
            kwargs={'item': self.folder.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, self.anonymous, 302)


class TestFilePermissions(FileMixin, TestProjectPermissionBase):
    """Tests for File views"""

    def setUp(self):
        super().setUp()

        app_settings.set_app_setting(
            APP_NAME, 'allow_public_links', True, project=self.project
        )

        self.file_content = bytes('content'.encode('utf-8'))

        # Init file
        self.file = self._make_file(
            name='file.txt',
            file_name='file.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.owner_as.user,  # Project owner is the file owner
            description='',
            public_url=True,
            secret=SECRET,
        )

    def test_file_create(self):
        """Test file creation"""
        url = reverse(
            'filesfolders:file_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
        ]
        bad_users = [self.anonymous, self.guest_as.user, self.user_no_roles]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        # Test public project
        self.project.set_public()
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_file_create_anon(self):
        """Test file creation with anonymous access"""
        url = reverse(
            'filesfolders:file_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, self.anonymous, 302)

    def test_file_create_category(self):
        """Test file creation under category"""
        url = reverse(
            'filesfolders:file_create',
            kwargs={'project': self.category.sodar_uuid},
        )
        bad_users = [
            self.anonymous,
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, bad_users, 302)

    def test_file_update(self):
        """Test file updating"""
        url = reverse(
            'filesfolders:file_update', kwargs={'item': self.file.sodar_uuid}
        )
        good_users = [self.superuser, self.owner_as.user, self.delegate_as.user]
        bad_users = [
            self.contributor_as.user,  # NOTE: not the owner of the file
            self.anonymous,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        # Test public project
        self.project.set_public()
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_file_update_anon(self):
        """Test file updating with anonymous access"""
        url = reverse(
            'filesfolders:file_update', kwargs={'item': self.file.sodar_uuid}
        )
        self.project.set_public()
        self.assert_response(url, self.anonymous, 302)

    def test_file_delete(self):
        """Test file deletion"""
        url = reverse(
            'filesfolders:file_delete', kwargs={'item': self.file.sodar_uuid}
        )
        good_users = [self.superuser, self.owner_as.user, self.delegate_as.user]
        bad_users = [
            self.contributor_as.user,  # NOTE: not the owner of the file
            self.anonymous,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        # Test public project
        self.project.set_public()
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_file_delete_anon(self):
        """Test file deletion with anonymous access"""
        url = reverse(
            'filesfolders:file_delete', kwargs={'item': self.file.sodar_uuid}
        )
        self.project.set_public()
        self.assert_response(url, self.anonymous, 302)

    def test_file_public_link(self):
        """Test generation of a public URL to a file"""
        url = reverse(
            'filesfolders:file_public_link',
            kwargs={'file': self.file.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
        ]
        bad_users = [self.anonymous, self.guest_as.user, self.user_no_roles]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        # Test public project
        self.project.set_public()
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_file_public_link_anon(self):
        """Test generation of a public URL to a file with anonymous access"""
        url = reverse(
            'filesfolders:file_public_link',
            kwargs={'file': self.file.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, self.anonymous, 302)

    def test_file_serve(self):
        """Test file serving for authenticated users"""
        url = reverse(
            'filesfolders:file_serve',
            kwargs={'file': self.file.sodar_uuid, 'file_name': self.file.name},
        )
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
        ]
        bad_users = [self.anonymous, self.user_no_roles]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        # Test public project
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 200)
        self.assert_response(url, self.anonymous, 302)

    def test_file_serve_public(self):
        """Test public file serving"""
        url = reverse(
            'filesfolders:file_serve_public',
            kwargs={'secret': SECRET, 'file_name': self.file.name},
        )
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.anonymous,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)

    def test_file_serve_public_disabled(self):
        """Test public file serving if not allowed in project, should fail"""
        app_settings.set_app_setting(
            APP_NAME, 'allow_public_links', False, project=self.project
        )
        url = reverse(
            'filesfolders:file_serve_public',
            kwargs={'secret': SECRET, 'file_name': self.file.name},
        )
        bad_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]

        for user in bad_users:
            with self.login(user):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 400)

        # Anonymous
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)


class TestHyperLinkPermissions(HyperLinkMixin, TestProjectPermissionBase):
    """Tests for HyperLink views"""

    def setUp(self):
        super().setUp()

        # Init link
        self.hyperlink = self._make_hyperlink(
            name='Link',
            url='http://www.google.com/',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
        )

    def test_hyperlink_create(self):
        """Test hyperlink creation"""
        url = reverse(
            'filesfolders:hyperlink_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
        ]
        bad_users = [self.anonymous, self.guest_as.user, self.user_no_roles]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        # Test public project
        self.project.set_public()
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_hyperlink_create_anon(self):
        """Test hyperlink creation with anonymous access"""
        url = reverse(
            'filesfolders:hyperlink_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, self.anonymous, 302)

    def test_hyperlink_create_category(self):
        """Test hyperlink creation under category"""
        url = reverse(
            'filesfolders:hyperlink_create',
            kwargs={'project': self.category.sodar_uuid},
        )
        bad_users = [
            self.anonymous,
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, bad_users, 302)

    def test_hyperlink_update(self):
        """Test hyperlink updating"""
        url = reverse(
            'filesfolders:hyperlink_update',
            kwargs={'item': self.hyperlink.sodar_uuid},
        )
        good_users = [self.superuser, self.owner_as.user, self.delegate_as.user]
        bad_users = [
            self.contributor_as.user,  # NOTE: not the owner of the link
            self.anonymous,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        # Test public project
        self.project.set_public()
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_hyperlink_update_anon(self):
        """Test hyperlink updating with anonymous access"""
        url = reverse(
            'filesfolders:hyperlink_update',
            kwargs={'item': self.hyperlink.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, self.anonymous, 302)

    def test_hyperlink_delete(self):
        """Test hyperlink deletion"""
        url = reverse(
            'filesfolders:hyperlink_delete',
            kwargs={'item': self.hyperlink.sodar_uuid},
        )
        good_users = [self.superuser, self.owner_as.user, self.delegate_as.user]
        bad_users = [
            self.contributor_as.user,  # NOTE: not the owner of the link
            self.anonymous,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        # Test public project
        self.project.set_public()
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_hyperlink_delete_anon(self):
        """Test hyperlink deletion with anonymous access"""
        url = reverse(
            'filesfolders:hyperlink_delete',
            kwargs={'item': self.hyperlink.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, self.anonymous, 302)


class TestBatchPermissions(FolderMixin, TestProjectPermissionBase):
    """Tests for batch editing views"""

    def setUp(self):
        super().setUp()

        self.folder = self._make_folder(
            name='folder',
            project=self.project,
            folder=None,
            owner=self.owner_as.user,  # Project owner is the owner of folder
            description='',
        )

    def test_batch_edit(self):
        """Test access to batch editing confirmation"""
        url = reverse(
            'filesfolders:batch_edit',
            kwargs={'project': self.project.sodar_uuid},
        )

        # NOTE: Contributor is OK as checks for object perms happen after POST
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
        ]
        bad_users = [
            # self.anonymous,
            self.guest_as.user,
            self.user_no_roles,
        ]

        post_data = {
            'batch-action': 'delete',
            'user-confirmed': '0',
            'batch_item_Folder_{}'.format(self.folder.sodar_uuid): '1',
        }

        for user in good_users:
            with self.login(user):
                response = self.client.post(url, post_data)
                self.assertEqual(response.status_code, 200)

        for user in bad_users:
            with self.login(user):
                response = self.client.post(url, post_data)
                self.assertEqual(response.status_code, 302)

        # Test public project
        self.project.set_public()
        for user in bad_users:
            with self.login(user):
                response = self.client.post(url, post_data)
                self.assertEqual(response.status_code, 302)
