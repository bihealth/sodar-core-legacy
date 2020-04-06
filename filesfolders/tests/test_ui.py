"""UI tests for the filesfolders app"""

from urllib.parse import urlencode

from django.urls import reverse

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.models import AppSetting, SODAR_CONSTANTS
from projectroles.tests.test_ui import TestUIBase
from projectroles.utils import build_secret

from .test_models import FolderMixin, FileMixin, HyperLinkMixin


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
APP_NAME = 'filesfolders'


# App settings API
app_settings = AppSettingAPI()


class TestListView(FolderMixin, FileMixin, HyperLinkMixin, TestUIBase):
    """Tests for filesfolders main file list view UI"""

    def setUp(self):
        super().setUp()

        app_settings.set_app_setting(
            APP_NAME, 'allow_public_links', True, project=self.project
        )

        self.file_content = bytes('content'.encode('utf-8'))
        self.secret_file_owner = build_secret()
        self.secret_file_contributor = build_secret()

        # Init folders

        # Folder created by project owner
        self.folder_owner = self._make_folder(
            name='folder_owner',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
        )

        # File created by project contributor
        self.folder_contributor = self._make_folder(
            name='folder_contributor',
            project=self.project,
            folder=None,
            owner=self.user_contributor,
            description='',
        )

        # Init files

        # File uploaded by project owner
        self.file_owner = self._make_file(
            name='file_owner.txt',
            file_name='file_owner.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
            public_url=True,  # NOTE: Public URL OK
            secret=self.secret_file_owner,
        )

        # File uploaded by project contributor
        self.file_contributor = self._make_file(
            name='file_contributor.txt',
            file_name='file_contributor.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user_contributor,
            description='',
            public_url=False,  # NOTE: No public URL
            secret=self.secret_file_contributor,
        )

        # Init hyperlinks

        # HyperLink added by project owner
        self.hyperlink_owner = self._make_hyperlink(
            name='Owner link',
            url='https://www.bihealth.org/',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
        )

        # HyperLink added by project contributor
        self.hyperlink_contrib = self._make_hyperlink(
            name='Contributor link',
            url='http://www.google.com/',
            project=self.project,
            folder=None,
            owner=self.user_contributor,
            description='',
        )

    def test_readme(self):
        """Test rendering readme if it has been uploaded to the folder"""

        # Init readme file
        self.readme_file = self._make_file(
            name='readme.txt',
            file_name='readme.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
            public_url=False,
            secret='xxxxxxxxx',
        )

        expected_true = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )

        self.assert_element_exists(
            expected_true, url, 'sodar-ff-readme-card', True
        )

    def test_buttons_list(self):
        """Test file/folder list-wide button visibility according to user
        permissions"""
        expected_true = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
        ]
        expected_false = [self.guest_as.user]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )

        self.assert_element_exists(
            expected_true, url, 'sodar-ff-buttons-list', True
        )

        self.assert_element_exists(
            expected_false, url, 'sodar-ff-buttons-list', False
        )

    def test_buttons_file(self):
        """Test file action buttons visibility according to user permissions"""
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 2),
            (self.delegate_as.user, 2),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-file-buttons')

    def test_buttons_folder(self):
        """Test folder action buttons visibility according to user
        permissions"""
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 2),
            (self.delegate_as.user, 2),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-folder-buttons')

    def test_buttons_hyperlink(self):
        """Test hyperlink action buttons visibility according to user
        permissions"""
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 2),
            (self.delegate_as.user, 2),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-hyperlink-buttons')

    def test_file_checkboxes(self):
        """Test batch file editing checkbox visibility according to user
        permissions"""
        expected = [
            (self.superuser, 6),
            (self.owner_as.user, 6),
            (self.delegate_as.user, 6),
            (self.contributor_as.user, 3),
            (self.guest_as.user, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-checkbox')

    def test_public_link(self):
        """Test public link visibility according to user
        permissions"""
        expected = [
            (self.superuser, 1),
            (self.owner_as.user, 1),
            (self.delegate_as.user, 1),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-link-public')

    def test_public_link_disable(self):
        """Test public link visibility if allow_public_links is set to False"""
        setting = AppSetting.objects.get(
            project=self.project.pk,
            app_plugin__name=APP_NAME,
            name='allow_public_links',
        )
        setting.value = 0
        setting.save()

        expected = [
            (self.superuser, 0),
            (self.owner_as.user, 0),
            (self.delegate_as.user, 0),
            (self.contributor_as.user, 0),
            (self.guest_as.user, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-link-public')

    def test_item_flags(self):
        """Test item flagging"""

        # Set up flags
        self.file_owner.flag = 'IMPORTANT'
        self.file_owner.save()
        self.folder_contributor.flag = 'FLAG'
        self.folder_contributor.save()
        self.hyperlink_contrib.flag = 'REVOKED'
        self.hyperlink_contrib.save()

        expected = [
            (self.superuser, 3),
            (self.owner_as.user, 3),
            (self.delegate_as.user, 3),
            (self.contributor_as.user, 3),
            (self.guest_as.user, 3),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-flag-icon', 'class')


class TestSearch(FolderMixin, FileMixin, HyperLinkMixin, TestUIBase):
    """Tests for the project search UI functionalities"""

    def setUp(self):
        super().setUp()

        self.file_content = bytes('content'.encode('utf-8'))
        self.secret_file_owner = build_secret()
        self.secret_file_contributor = build_secret()

        # Init folders

        # Folder created by project owner
        self.folder_owner = self._make_folder(
            name='folder_owner',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='description',
        )

        # File created by project contributor
        self.folder_contributor = self._make_folder(
            name='folder_contributor',
            project=self.project,
            folder=None,
            owner=self.user_contributor,
            description='description',
        )

        # Init files

        # File uploaded by project owner
        self.file_owner = self._make_file(
            name='file_owner.txt',
            file_name='file_owner.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='description',
            public_url=True,  # NOTE: Public URL OK
            secret=self.secret_file_owner,
        )

        # File uploaded by project contributor
        self.file_contributor = self._make_file(
            name='file_contributor.txt',
            file_name='file_contributor.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user_contributor,
            description='description',
            public_url=False,  # NOTE: No public URL
            secret=self.secret_file_contributor,
        )

        # Init hyperlinks

        # HyperLink added by project owner
        self.hyperlink_owner = self._make_hyperlink(
            name='Owner link',
            url='https://www.bihealth.org/',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='description',
        )

        # HyperLink added by project contributor
        self.hyperlink_contrib = self._make_hyperlink(
            name='Contributor link',
            url='http://www.google.com/',
            project=self.project,
            folder=None,
            owner=self.user_contributor,
            description='description',
        )

    def test_search_results(self):
        """Test search items visibility according to user permissions"""
        expected = [
            (self.superuser, 6),
            (self.owner_as.user, 6),
            (self.delegate_as.user, 6),
            (self.contributor_as.user, 6),
            (self.guest_as.user, 6),
            (self.user_no_roles, 0),
        ]
        url = (
            reverse('projectroles:search')
            + '?'
            + urlencode({'s': 'description'})
        )
        self.assert_element_count(expected, url, 'sodar-ff-search-item')

    def test_search_type_file(self):
        """Test search items visibility with 'file' type"""
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 2),
            (self.delegate_as.user, 2),
            (self.contributor_as.user, 2),
            (self.guest_as.user, 2),
            (self.user_no_roles, 0),
        ]
        url = (
            reverse('projectroles:search')
            + '?'
            + urlencode({'s': 'file type:file'})
        )
        self.assert_element_count(expected, url, 'sodar-ff-search-item')

    def test_search_type_folder(self):
        """Test search items visibility with 'folder' type"""
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 2),
            (self.delegate_as.user, 2),
            (self.contributor_as.user, 2),
            (self.guest_as.user, 2),
            (self.user_no_roles, 0),
        ]
        url = (
            reverse('projectroles:search')
            + '?'
            + urlencode({'s': 'folder type:folder'})
        )
        self.assert_element_count(expected, url, 'sodar-ff-search-item')

    def test_search_type_link(self):
        """Test search items visibility with 'link' as type"""
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 2),
            (self.delegate_as.user, 2),
            (self.contributor_as.user, 2),
            (self.guest_as.user, 2),
            (self.user_no_roles, 0),
        ]
        url = (
            reverse('projectroles:search')
            + '?'
            + urlencode({'s': 'link type:link'})
        )
        self.assert_element_count(expected, url, 'sodar-ff-search-item')

    def test_search_type_nonexisting(self):
        """Test search items visibility with a nonexisting type"""
        expected = [
            (self.superuser, 0),
            (self.owner_as.user, 0),
            (self.delegate_as.user, 0),
            (self.contributor_as.user, 0),
            (self.guest_as.user, 0),
            (self.user_no_roles, 0),
        ]
        url = (
            reverse('projectroles:search')
            + '?'
            + urlencode({'s': 'test type:Jaix1au'})
        )
        self.assert_element_count(expected, url, 'sodar-ff-search-item')


class TestHomeView(TestUIBase):
    """Tests for appearance of filesfolders specific data in the home view"""

    def test_project_list(self):
        """Test custom filesfolders project list column visibility"""

        users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        url = reverse('home')

        self.assert_element_exists(
            users, url, 'sodar-pr-project-list-header-filesfolders-files', True
        )
        self.assert_element_exists(
            users, url, 'sodar-pr-project-list-header-filesfolders-links', True
        )
