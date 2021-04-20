"""Model tests for the appalerts app"""

from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.urls import reverse

from djangoplugins.models import Plugin
from test_plus.test import TestCase

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_models import ProjectMixin

from appalerts.models import AppAlert


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
ALERT_NAME = 'test_alert'
ALERT_MSG = 'Test alert message'
ALERT_LEVEL = 'INFO'


class AppAlertMixin:
    """Mixin for AppAlert test helpers"""

    @classmethod
    def _make_app_alert(
        cls,
        app_plugin=None,
        alert_name=ALERT_NAME,
        user=None,
        message=ALERT_MSG,
        level=ALERT_LEVEL,
        active=True,
        url=None,
        project=None,
    ):
        return AppAlert.objects.create(
            app_plugin=app_plugin,
            alert_name=alert_name,
            user=user,
            message=message,
            level=level,
            active=active,
            url=url,
            project=project,
        )


class TestAppAlert(AppAlertMixin, ProjectMixin, TestCase):
    """Tests for the AppAlert model"""

    def setUp(self):
        self.project = self._make_project(
            title='TestProject', type=PROJECT_TYPE_PROJECT, parent=None
        )
        self.project_url = reverse(
            'projectroles:detail',
            kwargs={'project': str(self.project.sodar_uuid)},
        )
        self.user = self.make_user()

    def test_initialization(self):
        """Test AppAlert initialization"""
        alert = self._make_app_alert(
            user=self.user,
            url=self.project_url,
            project=self.project,
        )
        expected = {
            'id': alert.pk,
            'app_plugin': None,
            'alert_name': ALERT_NAME,
            'user': self.user.pk,
            'message': ALERT_MSG,
            'level': ALERT_LEVEL,
            'active': True,
            'url': '/project/' + str(self.project.sodar_uuid),
            'project': self.project.pk,
            'sodar_uuid': alert.sodar_uuid,
        }
        model_dict = model_to_dict(alert)
        self.assertEqual(model_dict, expected)

    def test_initialization_plugin(self):
        """Test AppAlert initialization with app plugin"""
        app_plugin = Plugin.objects.get(name='filesfolders')
        alert = self._make_app_alert(
            app_plugin=app_plugin,
            user=self.user,
            url=self.project_url,
            project=self.project,
        )
        expected = {
            'id': alert.pk,
            'app_plugin': app_plugin.pk,
            'alert_name': ALERT_NAME,
            'user': self.user.pk,
            'message': ALERT_MSG,
            'level': ALERT_LEVEL,
            'active': True,
            'url': '/project/' + str(self.project.sodar_uuid),
            'project': self.project.pk,
            'sodar_uuid': alert.sodar_uuid,
        }
        model_dict = model_to_dict(alert)
        self.assertEqual(model_dict, expected)

    def test_str(self):
        """Test AppAlert __str__()"""
        alert = self._make_app_alert(
            user=self.user,
            url=self.project_url,
            project=self.project,
        )
        expected = 'projectroles / {} / {}'.format(
            ALERT_NAME, self.user.username
        )
        self.assertEqual(str(alert), expected)

    def test_str_plugin(self):
        """Test AppAlert __str__() with app plugin"""
        app_plugin = Plugin.objects.get(name='filesfolders')
        alert = self._make_app_alert(
            app_plugin=app_plugin,
            user=self.user,
            url=self.project_url,
            project=self.project,
        )
        expected = 'filesfolders / {} / {}'.format(
            ALERT_NAME, self.user.username
        )
        self.assertEqual(str(alert), expected)

    def test_repr(self):
        """Test AppAlert __repr__()"""
        alert = self._make_app_alert(
            user=self.user,
            url=self.project_url,
            project=self.project,
        )
        expected = "AppAlert('projectroles', '{}', '{}', '{}')".format(
            ALERT_NAME, self.user.username, self.project.title
        )
        self.assertEqual(repr(alert), expected)

    def test_repr_plugin(self):
        """Test AppAlert __repr__() with app plugin"""
        app_plugin = Plugin.objects.get(name='filesfolders')
        alert = self._make_app_alert(
            app_plugin=app_plugin,
            user=self.user,
            url=self.project_url,
            project=self.project,
        )
        expected = "AppAlert('filesfolders', '{}', '{}', '{}')".format(
            ALERT_NAME, self.user.username, self.project.title
        )
        self.assertEqual(repr(alert), expected)

    def test_validate_level(self):
        """Test level validation"""
        with self.assertRaises(ValidationError):
            self._make_app_alert(
                user=self.user,
                level='not a valid level',
                url=self.project_url,
                project=self.project,
            )
