"""Ajax API view tests for the projectroles app"""

from django.forms import model_to_dict
from django.urls import reverse

from projectroles.models import ProjectUserTag, PROJECT_TAG_STARRED
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleAssignmentMixin,
    ProjectUserTagMixin,
)
from projectroles.tests.test_views import TestViewsBase, PROJECT_TYPE_PROJECT


class TestProjectStarringAjaxView(
    ProjectMixin, RoleAssignmentMixin, ProjectUserTagMixin, TestViewsBase
):
    """Tests for the project starring Ajax view"""

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
                    'projectroles:ajax_star',
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
                    'projectroles:ajax_star',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )

        # Assert ProjectUserTag state after creation
        self.assertEqual(ProjectUserTag.objects.all().count(), 0)

        # Assert status code
        self.assertEqual(response.status_code, 200)
