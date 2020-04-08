"""Taskflow view tests for the timeline app"""

import uuid

from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from timeline.tests.test_views import TestViewsBase


class TestTaskflowSetStatusAPIView(TestViewsBase):
    """Tests for the taskflow status setting API view"""

    def setUp(self):
        super().setUp()

        # Init default event
        self.event_init = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.user,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            status_type='INIT',
        )

    @override_settings(ENABLED_BACKEND_PLUGINS=['taskflow'])
    def test_set_status(self):
        """Test setting the status of the event"""
        values = {
            'event_uuid': self.event_init.sodar_uuid,
            'status_type': 'OK',
            'status_desc': '',
            'sodar_secret': settings.TASKFLOW_SODAR_SECRET,
        }

        response = self.client.post(
            reverse('timeline:taskflow_status_set'), values
        )

        self.assertEqual(response.status_code, 200)

    @override_settings(ENABLED_BACKEND_PLUGINS=['taskflow'])
    def test_set_invalid_event(self):
        """Test setting the status of the event with an invalid event pk"""
        values = {
            'event_uuid': uuid.uuid4(),
            'status_type': 'OK',
            'status_desc': '',
            'sodar_secret': settings.TASKFLOW_SODAR_SECRET,
        }

        response = self.client.post(
            reverse('timeline:taskflow_status_set'), values
        )

        self.assertEqual(response.status_code, 404)

    @override_settings(ENABLED_BACKEND_PLUGINS=['taskflow'])
    def test_set_invalid_status(self):
        """Test setting the status of the event with an invalid status type"""
        values = {
            'event_uuid': self.event_init.sodar_uuid,
            'status_type': 'ahL4VeerAeth4ohh',
            'status_desc': '',
            'sodar_secret': settings.TASKFLOW_SODAR_SECRET,
        }

        response = self.client.post(
            reverse('timeline:taskflow_status_set'), values
        )

        self.assertEqual(response.status_code, 400)
