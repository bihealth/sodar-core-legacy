"""Tests for Ajax views in the adminalerts app"""

import json

from django.urls import reverse

from adminalerts.tests.test_views import TestViewsBase


class TestAdminAlertActiveToggleAjaxView(TestViewsBase):
    """Tests for the AdminAlert activation toggling Ajax view"""

    def test_deactivate_alert(self):
        """Test alert deactivation"""
        with self.login(self.superuser):
            self.assertTrue(self.alert.active)

            response = self.client.post(
                reverse(
                    'adminalerts:ajax_active_toggle',
                    kwargs={'adminalert': self.alert.sodar_uuid},
                ),
            )
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.content)
            self.alert.refresh_from_db()
            self.assertFalse(self.alert.active)
            self.assertFalse(data['is_active'])

    def test_activate_alert(self):
        """Test alert activation"""
        with self.login(self.superuser):
            self.alert.active = False
            self.alert.save()

            response = self.client.post(
                reverse(
                    'adminalerts:ajax_active_toggle',
                    kwargs={'adminalert': self.alert.sodar_uuid},
                ),
            )
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.content)
            self.alert.refresh_from_db()
            self.assertTrue(self.alert.active)
            self.assertTrue(data['is_active'])
