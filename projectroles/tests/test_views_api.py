"""REST API view tests for the projectroles app"""

import json

from django.urls import reverse

from projectroles.models import SODAR_CONSTANTS
from projectroles.remote_projects import RemoteProjectAPI
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
)
from projectroles.tests.test_views import (
    SODARAPIViewMixin,
    TestViewsBase,
    PROJECT_TYPE_CATEGORY,
    PROJECT_TYPE_PROJECT,
    REMOTE_SITE_NAME,
    REMOTE_SITE_URL,
    SITE_MODE_TARGET,
    REMOTE_SITE_DESC,
    REMOTE_SITE_SECRET,
)
from projectroles.utils import build_secret


CORE_API_MEDIA_TYPE_INVALID = 'application/vnd.bihealth.invalid'
CORE_API_VERSION_INVALID = '9.9.9'


class TestRemoteProjectGetAPIView(
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    SODARAPIViewMixin,
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
            HTTP_ACCEPT=self.get_accept_header(),
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
            HTTP_ACCEPT=self.get_accept_header(
                version=CORE_API_VERSION_INVALID
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
            HTTP_ACCEPT=self.get_accept_header(
                media_type=CORE_API_MEDIA_TYPE_INVALID
            ),
        )

        self.assertEqual(response.status_code, 406)
