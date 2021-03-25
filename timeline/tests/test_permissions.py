"""Permission tests for the timeline app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import TestProjectPermissionBase


class TestTimelinePermissions(TestProjectPermissionBase):
    """Tests for timeline views"""

    def test_project_list(self):
        """Test project event list"""
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
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
    def test_project_list_anon(self):
        """Test project event list with anonynomus access"""
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        self.project.set_public()
        self.assert_response(url, self.anonymous, 200)

    def test_object_list(self):
        """Test object event list"""
        url = reverse(
            'timeline:list_object',
            kwargs={
                'project': self.project.sodar_uuid,
                'object_model': 'User',
                'object_uuid': self.user_owner.sodar_uuid,
            },
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
    def test_object_list_anon(self):
        """Test object event list with anonynomus access"""
        url = reverse(
            'timeline:list_object',
            kwargs={
                'project': self.project.sodar_uuid,
                'object_model': 'User',
                'object_uuid': self.user_owner.sodar_uuid,
            },
        )
        self.project.set_public()
        self.assert_response(url, self.anonymous, 200)
