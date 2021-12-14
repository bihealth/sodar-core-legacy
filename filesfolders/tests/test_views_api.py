"""REST API view tests for the filesfolders app"""

import json

from django.urls import reverse
from test_plus.test import APITestCase

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_views_api import SODARAPIViewTestMixin
from projectroles.views_api import (
    CORE_API_MEDIA_TYPE,
    CORE_API_DEFAULT_VERSION,
    INVALID_PROJECT_TYPE_MSG,
)

from filesfolders.tests.test_views import ZIP_PATH_NO_FILES, TestViewsBaseMixin
from filesfolders.models import Folder, File, HyperLink


# SODAR constants
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']

# Local constants
INVALID_UUID = '11111111-1111-1111-1111-111111111111'


class TestFilesfoldersAPIViewsBase(
    TestViewsBaseMixin, SODARAPIViewTestMixin, APITestCase
):
    """Base class for filesfolders API tests"""

    media_type = CORE_API_MEDIA_TYPE
    api_version = CORE_API_DEFAULT_VERSION

    def setUp(self):
        super().setUp()
        # Get knox token for self.user
        self.knox_token = self.get_token(self.user)


class TestFolderListCreateAPIView(TestFilesfoldersAPIViewsBase):
    """Tests for the FolderListCreateAPIView class"""

    def setUp(self):
        super().setUp()
        self.folder_data = {
            'name': 'New Folder',
            'flag': 'IMPORTANT',
            'description': 'Folder\'s description',
        }

    def test_list_superuser(self):
        """Test GET request listing folders"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_folder_list_create',
                kwargs={'project': self.project.sodar_uuid},
            )
        )
        self.assertEqual(response.status_code, 200, msg=response.data)
        expected = [
            {
                'name': self.folder.name,
                'folder': None,
                'owner': self.get_serialized_user(self.folder.owner),
                'project': str(self.folder.project.sodar_uuid),
                'flag': self.folder.flag,
                'description': self.folder.description,
                'date_modified': self.get_drf_datetime(
                    self.folder.date_modified
                ),
                'sodar_uuid': str(self.folder.sodar_uuid),
            }
        ]
        self.assertEqual(json.loads(response.content), expected)

    def test_create_in_root(self):
        """Test creation of new folder in root"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_folder_list_create',
                kwargs={'project': self.project.sodar_uuid},
            ),
            method='POST',
            data=self.folder_data,
        )

        self.assertEqual(response.status_code, 201, msg=response.data)
        new_folder = Folder.objects.filter(
            sodar_uuid=response.data['sodar_uuid']
        ).first()
        self.assertIsNotNone(new_folder)

        expected = {
            **self.folder_data,
            'folder': None,
            'owner': self.get_serialized_user(self.user),
            'project': str(self.project.sodar_uuid),
            'date_modified': self.get_drf_datetime(new_folder.date_modified),
            'sodar_uuid': str(new_folder.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_create_in_folder(self):
        """Test creation of new folder below other"""
        folder_data = {
            **self.folder_data,
            'folder': str(self.folder.sodar_uuid),
        }
        response = self.request_knox(
            reverse(
                'filesfolders:api_folder_list_create',
                kwargs={'project': self.project.sodar_uuid},
            ),
            method='POST',
            data=folder_data,
        )

        self.assertEqual(response.status_code, 201, msg=response.data)
        new_folder = Folder.objects.filter(
            sodar_uuid=response.data['sodar_uuid']
        ).first()
        self.assertIsNotNone(new_folder)

        expected = {
            **folder_data,
            'owner': self.get_serialized_user(self.user),
            'project': str(self.project.sodar_uuid),
            'date_modified': self.get_drf_datetime(new_folder.date_modified),
            'sodar_uuid': str(new_folder.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_create_in_category(self):
        """Test creation of new folder in a category (should fail)"""
        category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self._make_assignment(category, self.user, self.role_owner)
        response = self.request_knox(
            reverse(
                'filesfolders:api_folder_list_create',
                kwargs={'project': category.sodar_uuid},
            ),
            method='POST',
            data=self.folder_data,
        )
        self.assertEqual(response.status_code, 403, msg=response.data)
        self.assertEqual(
            str(response.data['detail']),
            INVALID_PROJECT_TYPE_MSG.format(project_type=PROJECT_TYPE_CATEGORY),
        )


class TestFolderRetrieveUpdateDestroyAPIView(TestFilesfoldersAPIViewsBase):
    """Tests for the FolderRetrieveUpdateDestroyAPIView class"""

    def test_retrieve(self):
        """Test retrieval of Folder model through API"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_folder_retrieve_update_destroy',
                kwargs={'folder': self.folder.sodar_uuid},
            )
        )

        self.assertEqual(response.status_code, 200, msg=response.data)
        expected = {
            'name': self.folder.name,
            'folder': None,
            'owner': self.get_serialized_user(self.folder.owner),
            'project': str(self.folder.project.sodar_uuid),
            'flag': self.folder.flag,
            'description': self.folder.description,
            'date_modified': self.get_drf_datetime(self.folder.date_modified),
            'sodar_uuid': str(self.folder.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_retrieve_not_found(self):
        """Test retrieval of Folder with invalid UUID"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_folder_retrieve_update_destroy',
                kwargs={'folder': INVALID_UUID},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_update(self):
        """Test update of Folder model through API"""

        folder_data = {
            'name': 'UPDATED Folder',
            'flag': 'FLAG',
            'description': 'UPDATED Description',
        }
        response = self.request_knox(
            reverse(
                'filesfolders:api_folder_retrieve_update_destroy',
                kwargs={'folder': self.folder.sodar_uuid},
            ),
            method='PUT',
            data=folder_data,
        )

        self.assertEqual(response.status_code, 200, msg=response.data)

        self.folder.refresh_from_db()
        expected = {
            **folder_data,
            'folder': None,
            'owner': self.get_serialized_user(self.folder.owner),
            'project': str(self.folder.project.sodar_uuid),
            'date_modified': self.get_drf_datetime(self.folder.date_modified),
            'sodar_uuid': str(self.folder.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_destroy(self):
        """Test destruction of Folder model through API"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_folder_retrieve_update_destroy',
                kwargs={'folder': self.folder.sodar_uuid},
            ),
            method='DELETE',
        )

        self.assertEqual(response.status_code, 204, msg=response.data)
        self.assertIsNone(response.data)

        with self.assertRaises(Folder.DoesNotExist):
            Folder.objects.get(
                project=self.project, sodar_uuid=self.folder.sodar_uuid
            )


class TestFileListCreateAPIView(TestFilesfoldersAPIViewsBase):
    """Tests for the FileListCreateAPIView class"""

    def setUp(self):
        super().setUp()
        self.file_data = {
            'name': 'New File',
            'flag': 'IMPORTANT',
            'description': 'File\'s description',
            'secret': 'foo',
            'public_url': True,
            'file': open(ZIP_PATH_NO_FILES, 'rb'),
        }

    def tearDown(self):
        self.file_data['file'].close()
        super().tearDown()

    def test_list_superuser(self):
        """Test GET request listing files"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_file_list_create',
                kwargs={'project': self.project.sodar_uuid},
            )
        )

        self.assertEqual(response.status_code, 200, msg=response.data)

        expected = [
            {
                'name': self.file.name,
                'folder': None,
                'owner': self.get_serialized_user(self.file.owner),
                'project': str(self.file.project.sodar_uuid),
                'flag': self.file.flag,
                'description': self.file.description,
                'secret': self.file.secret,
                'public_url': self.file.public_url,
                'date_modified': self.get_drf_datetime(self.file.date_modified),
                'sodar_uuid': str(self.file.sodar_uuid),
            }
        ]
        self.assertEqual(json.loads(response.content), expected)

    def test_create_in_root(self):
        """Test creation of new file in root"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_file_list_create',
                kwargs={'project': self.project.sodar_uuid},
            ),
            method='POST',
            format='multipart',
            data=self.file_data,
        )

        self.assertEqual(response.status_code, 201, msg=response.data)
        new_file = File.objects.filter(
            sodar_uuid=response.data['sodar_uuid']
        ).first()
        self.assertIsNotNone(new_file)
        self.assertNotEqual(new_file.file.file.size, 0)

        expected = {
            **self.file_data,
            'folder': None,
            'owner': self.get_serialized_user(self.user),
            'project': str(self.project.sodar_uuid),
            'secret': new_file.secret,
            'public_url': new_file.public_url,
            'date_modified': self.get_drf_datetime(new_file.date_modified),
            'sodar_uuid': str(new_file.sodar_uuid),
        }
        expected.pop('file')
        self.assertEqual(json.loads(response.content), expected)

    def test_create_in_folder(self):
        """Test creation of a file inside a folder"""
        file_data = {**self.file_data, 'folder': str(self.folder.sodar_uuid)}

        response = self.request_knox(
            reverse(
                'filesfolders:api_file_list_create',
                kwargs={'project': self.project.sodar_uuid},
            ),
            method='POST',
            format='multipart',
            data=file_data,
        )

        self.assertEqual(response.status_code, 201, msg=response.data)
        new_file = File.objects.filter(
            sodar_uuid=response.data['sodar_uuid']
        ).first()
        self.assertIsNotNone(new_file)
        self.assertNotEqual(new_file.file.file.size, 0)

        expected = {
            **file_data,
            'owner': self.get_serialized_user(self.user),
            'project': str(self.project.sodar_uuid),
            'public_url': self.file_data['public_url'],
            'secret': new_file.secret,
            'date_modified': self.get_drf_datetime(new_file.date_modified),
            'sodar_uuid': str(new_file.sodar_uuid),
        }
        expected.pop('file')
        self.assertEqual(json.loads(response.content), expected)

    def test_create_in_category(self):
        """Test creation of new file in a category (should fail)"""
        category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self._make_assignment(category, self.user, self.role_owner)
        response = self.request_knox(
            reverse(
                'filesfolders:api_file_list_create',
                kwargs={'project': category.sodar_uuid},
            ),
            method='POST',
            format='multipart',
            data=self.file_data,
        )
        self.assertEqual(response.status_code, 403, msg=response.data)
        self.assertEqual(
            str(response.data['detail']),
            INVALID_PROJECT_TYPE_MSG.format(project_type=PROJECT_TYPE_CATEGORY),
        )


class TestFileRetrieveUpdateDestroyAPIView(TestFilesfoldersAPIViewsBase):
    """Tests for the FileRetrieveUpdateDestroyAPIView class"""

    def setUp(self):
        super().setUp()
        self.file_data = {
            'name': 'UPDATED File',
            'flag': 'FLAG',
            'description': 'UPDATED description',
            'secret': 'foo',
            'public_url': False,
            'file': open(ZIP_PATH_NO_FILES, 'rb'),
        }

    def tearDown(self):
        self.file_data['file'].close()
        super().tearDown()

    def test_retrieve(self):
        """Test retrieval of File model through API"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_file_retrieve_update_destroy',
                kwargs={'file': self.file.sodar_uuid},
            )
        )

        self.assertEqual(response.status_code, 200, msg=response.data)

        expected = {
            'name': self.file.name,
            'folder': None,
            'owner': self.get_serialized_user(self.file.owner),
            'project': str(self.file.project.sodar_uuid),
            'flag': self.file.flag,
            'description': self.file.description,
            'public_url': self.file.public_url,
            'secret': self.file.secret,
            'date_modified': self.get_drf_datetime(self.file.date_modified),
            'sodar_uuid': str(self.file.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_retrieve_not_found(self):
        """Test retrieval of File with invalid UUID"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_file_retrieve_update_destroy',
                kwargs={'file': INVALID_UUID},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_update(self):
        """Test update of File model through API"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_file_retrieve_update_destroy',
                kwargs={'file': self.file.sodar_uuid},
            ),
            method='PUT',
            format='multipart',
            data=self.file_data,
        )

        self.assertEqual(response.status_code, 200, msg=response.data)
        old_secret = self.file.secret
        self.file.refresh_from_db()
        self.assertEqual(self.file.name, self.file_data['name'])
        self.assertEqual(self.file.flag, self.file_data['flag'])
        self.assertEqual(self.file.description, self.file_data['description'])
        self.assertNotEqual(
            self.file.secret,
            old_secret,
            msg='Secret should change when public_url flag changes',
        )

        expected = {
            **self.file_data,
            'folder': None,
            'owner': self.get_serialized_user(self.file.owner),
            'project': str(self.file.project.sodar_uuid),
            'public_url': self.file_data['public_url'],
            'secret': self.file.secret,
            'date_modified': self.get_drf_datetime(self.file.date_modified),
            'sodar_uuid': str(self.file.sodar_uuid),
        }
        expected.pop('file')
        self.assertEqual(json.loads(response.content), expected)

    def test_destroy(self):
        """Test destruction of File model through API"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_file_retrieve_update_destroy',
                kwargs={'file': self.file.sodar_uuid},
            ),
            method='DELETE',
        )

        self.assertEqual(response.status_code, 204, msg=response.data)
        self.assertIsNone(response.data)

        with self.assertRaises(File.DoesNotExist):
            File.objects.get(
                project=self.project, sodar_uuid=self.file.sodar_uuid
            )


class TestFileServeAPIView(TestFilesfoldersAPIViewsBase):
    """Tests for the FileServeAPIView class"""

    def test_get(self):
        """Test download of file content"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_file_serve',
                kwargs={'file': self.file.sodar_uuid},
            )
        )
        expected = b'content'
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(response.content, expected)

    def test_get_not_found(self):
        """Test download with invalid UUID"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_file_serve',
                kwargs={'file': INVALID_UUID},
            )
        )
        self.assertEqual(response.status_code, 404)


class TestHyperLinkListCreateAPIView(TestFilesfoldersAPIViewsBase):
    """Tests for the HyperLinkListCreateAPIView class"""

    def setUp(self):
        super().setUp()
        self.hyperlink_data = {
            'name': 'New HyperLink',
            'flag': 'IMPORTANT',
            'description': 'HyperLink\'s description',
            'url': 'http://www.cubi.bihealth.org',
        }

    def test_list_superuser(self):
        """Test GET request listing hyperlinks"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_hyperlink_list_create',
                kwargs={'project': self.project.sodar_uuid},
            )
        )

        self.assertEqual(response.status_code, 200, msg=response.data)

        expected = [
            {
                'name': self.hyperlink.name,
                'folder': None,
                'owner': self.get_serialized_user(self.hyperlink.owner),
                'project': str(self.hyperlink.project.sodar_uuid),
                'flag': self.hyperlink.flag,
                'description': self.hyperlink.description,
                'url': self.hyperlink.url,
                'date_modified': self.get_drf_datetime(
                    self.hyperlink.date_modified
                ),
                'sodar_uuid': str(self.hyperlink.sodar_uuid),
            }
        ]
        self.assertEqual(json.loads(response.content), expected)

    def test_create_in_root(self):
        """Test creation of new hyperlink in root"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_hyperlink_list_create',
                kwargs={'project': self.project.sodar_uuid},
            ),
            method='POST',
            data=self.hyperlink_data,
        )

        self.assertEqual(response.status_code, 201, msg=response.data)
        new_link = HyperLink.objects.filter(
            sodar_uuid=response.data['sodar_uuid']
        ).first()
        self.assertIsNotNone(new_link)

        expected = {
            **self.hyperlink_data,
            'folder': None,
            'owner': self.get_serialized_user(self.user),
            'project': str(self.project.sodar_uuid),
            'date_modified': self.get_drf_datetime(new_link.date_modified),
            'sodar_uuid': str(new_link.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_create_in_folder(self):
        """Test creation of new hyperlink below another"""
        hyperlink_data = {
            **self.hyperlink_data,
            'folder': str(self.folder.sodar_uuid),
        }

        response = self.request_knox(
            reverse(
                'filesfolders:api_hyperlink_list_create',
                kwargs={'project': self.project.sodar_uuid},
            ),
            method='POST',
            data=hyperlink_data,
        )

        self.assertEqual(response.status_code, 201, msg=response.data)
        new_link = HyperLink.objects.filter(
            sodar_uuid=response.data['sodar_uuid']
        ).first()
        self.assertIsNotNone(new_link)

        expected = {
            **hyperlink_data,
            'owner': self.get_serialized_user(self.user),
            'project': str(self.project.sodar_uuid),
            'date_modified': self.get_drf_datetime(new_link.date_modified),
            'sodar_uuid': str(new_link.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_create_in_category(self):
        """Test creation of new hyperlink in a category (should fail)"""
        category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self._make_assignment(category, self.user, self.role_owner)
        response = self.request_knox(
            reverse(
                'filesfolders:api_hyperlink_list_create',
                kwargs={'project': category.sodar_uuid},
            ),
            method='POST',
            data=self.hyperlink_data,
        )
        self.assertEqual(response.status_code, 403, msg=response.data)
        self.assertEqual(
            str(response.data['detail']),
            INVALID_PROJECT_TYPE_MSG.format(project_type=PROJECT_TYPE_CATEGORY),
        )


class TestHyperLinkRetrieveUpdateDestroyAPIView(TestFilesfoldersAPIViewsBase):
    """Tests for the HyperLinkRetrieveUpdateDestroyAPIView class"""

    def test_retrieve(self):
        """Test retrieval of HyperLink model through API"""

        response = self.request_knox(
            reverse(
                'filesfolders:api_hyperlink_retrieve_update_destroy',
                kwargs={'hyperlink': self.hyperlink.sodar_uuid},
            )
        )

        self.assertEqual(response.status_code, 200, msg=response.data)

        expected = {
            'name': self.hyperlink.name,
            'folder': None,
            'owner': self.get_serialized_user(self.hyperlink.owner),
            'project': str(self.hyperlink.project.sodar_uuid),
            'flag': self.hyperlink.flag,
            'description': self.hyperlink.description,
            'url': self.hyperlink.url,
            'date_modified': self.get_drf_datetime(
                self.hyperlink.date_modified
            ),
            'sodar_uuid': str(self.hyperlink.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_retrieve_not_found(self):
        """Test retrieval of HyperLink with invalid UUID"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_hyperlink_retrieve_update_destroy',
                kwargs={'hyperlink': INVALID_UUID},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_update(self):
        """Test update of HyperLink model through API"""
        hyperlink_data = {
            'name': 'UPDATED HyperLink',
            'flag': 'FLAG',
            'description': 'UPDATED Description',
            'url': 'http://www.bihealth.org',
        }

        response = self.request_knox(
            reverse(
                'filesfolders:api_hyperlink_retrieve_update_destroy',
                kwargs={'hyperlink': self.hyperlink.sodar_uuid},
            ),
            method='PUT',
            data=hyperlink_data,
        )

        self.assertEqual(response.status_code, 200, msg=response.data)
        self.hyperlink.refresh_from_db()
        self.assertEqual(self.hyperlink.name, hyperlink_data['name'])
        self.assertEqual(self.hyperlink.flag, hyperlink_data['flag'])
        self.assertEqual(
            self.hyperlink.description, hyperlink_data['description']
        )

        expected = {
            **hyperlink_data,
            'folder': None,
            'owner': self.get_serialized_user(self.hyperlink.owner),
            'project': str(self.hyperlink.project.sodar_uuid),
            'date_modified': self.get_drf_datetime(
                self.hyperlink.date_modified
            ),
            'sodar_uuid': str(self.hyperlink.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_destroy(self):
        """Test destruction of HyperLink model through API"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_hyperlink_retrieve_update_destroy',
                kwargs={'hyperlink': self.hyperlink.sodar_uuid},
            ),
            method='DELETE',
        )

        self.assertEqual(response.status_code, 204, msg=response.data)
        self.assertIsNone(response.data)
