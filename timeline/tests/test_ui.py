"""UI tests for the timeline app"""

from django.urls import reverse

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import get_backend_api
from projectroles.tests.test_ui import TestUIBase
from timeline.templatetags.timeline_tags import collect_extra_data

from timeline.tests.test_models import (
    ProjectEventMixin,
    ProjectEventStatusMixin,
)


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


class TestProjectListView(
    ProjectEventMixin, ProjectEventStatusMixin, TestUIBase
):
    """Tests for the timeline project list view UI"""

    def setUp(self):
        super().setUp()
        self.timeline = get_backend_api('timeline_backend')

        # Init default event
        self.event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.superuser,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            status_type='OK',
        )

        # Init classified event
        self.classified_event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.superuser,
            event_name='classified_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            classified=True,
        )

    def test_render(self):
        """Test visibility of events in project event list"""
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 2),
            (self.delegate_as.user, 2),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 1),
        ]
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')

    def test_render_no_user(self):
        """Test rendering with an event without user"""
        self.event.user = None
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 2),
            (self.delegate_as.user, 2),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 1),
        ]
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')

    def test_render_object(self):
        """Test visibility of object related events in project list"""
        # Add user as an object reference
        self.ref_obj = self.event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )
        self.classified_ref_obj = self.classified_event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 2),
            (self.delegate_as.user, 2),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 1),
        ]
        url = reverse(
            'timeline:list_object',
            kwargs={
                'project': self.project.sodar_uuid,
                'object_model': self.ref_obj.object_model,
                'object_uuid': self.ref_obj.object_uuid,
            },
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')

    def test_render_details(self):
        """Test visibility of events on the project details page"""
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 2),
            (self.delegate_as.user, 2),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 1),
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')


class TestExtraDataView(ProjectEventMixin, ProjectEventStatusMixin, TestUIBase):
    """Tests for the timeline list view UI extra data"""

    def setUp(self):
        super().setUp()
        self.timeline = get_backend_api('timeline_backend')

        # Init default event
        self.event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.superuser,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            status_type='OK',
        )

        # Init classified event
        self.extra_less_event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.superuser,
            event_name='classified_event',
            description='description',
            extra_data={},
        )

    def test_extra_data_badge(self):
        """Test visibility of extra data badges in project event list"""
        expected = [
            (self.superuser, 1),
            (self.owner_as.user, 1),
            (self.delegate_as.user, 1),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 1),
        ]
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(
            expected,
            url,
            'modal',
            attribute='data-toggle',
            path='//table[@id="sodar-tl-table"]/tbody/tr/td/',
        )

    def test_status_extra_data_only_badge(self):
        """Test visibility when event only has extra data in one of its states"""
        self.event_with_status = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.superuser,
            event_name='classified_event',
            description='description',
            extra_data={},
            status_extra_data={'acclerator': 'railgun'},
            status_type="OK",
        )
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 2),
            (self.delegate_as.user, 2),
            (self.contributor_as.user, 2),
            (self.guest_as.user, 2),
        ]
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(
            expected,
            url,
            'modal',
            attribute='data-toggle',
            path='//table/tbody/tr/td/',
        )

    def test_object_extra_data(self):
        """Test visibility of object related extra data in project list"""
        # Add user as an object reference
        self.ref_obj = self.event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )
        expected = [
            (self.superuser, 1),
            (self.owner_as.user, 1),
            (self.delegate_as.user, 1),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 1),
        ]
        url = reverse(
            'timeline:list_object',
            kwargs={
                'project': self.project.sodar_uuid,
                'object_model': self.ref_obj.object_model,
                'object_uuid': self.ref_obj.object_uuid,
            },
        )
        self.assert_element_count(
            expected,
            url,
            'modal',
            attribute='data-toggle',
            path='//table[@id="sodar-tl-table"]/tbody/tr/td/',
        )

    def test_event_extra_data_details(self):
        """Test visibility of events on the project details page"""
        expected = [
            (self.superuser, 0),
            (self.owner_as.user, 0),
            (self.delegate_as.user, 0),
            (self.contributor_as.user, 0),
            (self.guest_as.user, 0),
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(
            expected,
            url,
            'modal',
            attribute='data-toggle',
            path='//table/tbody/tr/td/',
        )

    def test_extra_data_content_existence(self):
        """Test existence of modal content"""
        expected = [
            (self.superuser, 1),
            (self.owner_as.user, 1),
            (self.delegate_as.user, 1),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 1),
        ]
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        data = collect_extra_data(self.event)[0]
        self.assert_element_count(
            expected, url, '{}-{}'.format(data[0], data[2].pk), attribute='id'
        )

    def test_status_extra_data_content_existence(self):
        """Test existence of modal content for status extra data"""
        self.event_with_status = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.superuser,
            event_name='classified_event',
            description='description',
            extra_data={},
            status_extra_data={'acclerator': 'railgun'},
            status_type='OK',
        )
        expected = [
            (self.superuser, 1),
            (self.owner_as.user, 1),
            (self.delegate_as.user, 1),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 1),
        ]
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        data = collect_extra_data(self.event_with_status)[0]
        self.assert_element_count(
            expected, url, '{}-{}'.format(data[0], data[2].pk), attribute='id'
        )


class TestSiteListView(ProjectEventMixin, ProjectEventStatusMixin, TestUIBase):
    """Tests for the timeline site-wide list view UI"""

    def setUp(self):
        super().setUp()
        self.timeline = get_backend_api('timeline_backend')

        # Init default event
        self.event = self.timeline.add_event(
            project=None,
            app_name='projectroles',
            user=self.superuser,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            status_type='OK',
        )

        # Init classified event
        self.classified_event = self.timeline.add_event(
            project=None,
            app_name='projectroles',
            user=self.superuser,
            event_name='classified_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            classified=True,
        )

    def test_render(self):
        """Test visibility of events in the site-wide event list"""
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 1),
            (self.delegate_as.user, 1),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 1),
        ]
        url = reverse('timeline:list_site')
        self.assert_element_count(expected, url, 'sodar-tl-list-event')

    def test_render_object(self):
        """Test visibility of object related events in site-wide event list"""
        # Add user as an object reference
        self.ref_obj = self.event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )
        self.classified_ref_obj = self.classified_event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 1),
            (self.delegate_as.user, 1),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 1),
        ]
        url = reverse(
            'timeline:list_object_site',
            kwargs={
                'object_model': self.ref_obj.object_model,
                'object_uuid': self.ref_obj.object_uuid,
            },
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')
