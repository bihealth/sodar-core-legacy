"""Backend API tests for the appalerts app"""

from django.forms.models import model_to_dict
from django.urls import reverse

from djangoplugins.models import Plugin
from test_plus.test import TestCase

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import get_backend_api
from projectroles.tests.test_models import ProjectMixin

from appalerts.models import AppAlert
from appalerts.tests.test_models import (
    AppAlertMixin,
    ALERT_NAME,
    ALERT_MSG,
    ALERT_LEVEL,
)


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


class TestAppAlertAPI(AppAlertMixin, ProjectMixin, TestCase):
    """Base class for appalerts backend API testing"""

    def setUp(self):
        # Create user
        self.user = self.make_user('user')
        self.project = self._make_project(
            title='TestProject', type=PROJECT_TYPE_PROJECT, parent=None
        )
        self.project_url = reverse(
            'projectroles:detail',
            kwargs={'project': str(self.project.sodar_uuid)},
        )
        # Get backend
        self.app_alerts = get_backend_api('appalerts_backend')

    def test_get_model(self):
        """Test get_model()"""
        self.assertEqual(self.app_alerts.get_model(), AppAlert)

    def test_add_alert(self):
        """Test alert addition with a plugin"""
        self.assertEqual(AppAlert.objects.count(), 0)
        alert = self.app_alerts.add_alert(
            app_name='filesfolders',
            alert_name=ALERT_NAME,
            user=self.user,
            message=ALERT_MSG,
            level=ALERT_LEVEL,
            url=self.project_url,
            project=self.project,
        )
        self.assertEqual(AppAlert.objects.count(), 1)
        expected = {
            'id': alert.pk,
            'app_plugin': Plugin.objects.get(name='filesfolders').pk,
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

    def test_add_alert_projectroles(self):
        """Test alert addition for projectroles"""
        self.assertEqual(AppAlert.objects.count(), 0)
        alert = self.app_alerts.add_alert(
            app_name='projectroles',
            alert_name=ALERT_NAME,
            user=self.user,
            message=ALERT_MSG,
            level=ALERT_LEVEL,
            url=self.project_url,
            project=self.project,
        )
        self.assertEqual(AppAlert.objects.count(), 1)
        self.assertIsNone(alert.app_plugin)

    def test_add_alert_invalid_plugin(self):
        """Test alert addition with an invalid plugin name"""
        with self.assertRaises(ValueError):
            self.app_alerts.add_alert(
                app_name='Not a valid plugin name',
                alert_name=ALERT_NAME,
                user=self.user,
                message=ALERT_MSG,
                level=ALERT_LEVEL,
                url=self.project_url,
                project=self.project,
            )

    def test_add_alert_invalid_level(self):
        """Test alert addition with an invalid level"""
        with self.assertRaises(ValueError):
            self.app_alerts.add_alert(
                app_name='filesfolders',
                alert_name=ALERT_NAME,
                user=self.user,
                message=ALERT_MSG,
                level='Not a valid level',
                url=self.project_url,
                project=self.project,
            )
