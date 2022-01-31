"""API tests for the timeline app"""

from django.contrib.auth.models import AnonymousUser
from django.forms.models import model_to_dict
from django.test import RequestFactory
from django.urls import reverse

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import get_backend_api
from projectroles.tests.test_models import (
    RemoteSiteMixin,
    REMOTE_SITE_NAME,
    REMOTE_SITE_URL,
)

# Filesfolders dependency
from filesfolders.tests.test_models import FolderMixin

from timeline.tests.test_models import (
    TestProjectEventBase,
    ProjectEventMixin,
    ProjectEventStatusMixin,
)
from timeline.models import (
    ProjectEvent,
    ProjectEventStatus,
    ProjectEventObjectRef,
    DEFAULT_MESSAGES,
)
from timeline.templatetags import timeline_tags as tags


# Global constants from settings
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


class TimelineAPIMixin:
    """Helpers for timeline API use"""

    @classmethod
    def get_request(cls, user, project):
        """Return mock request"""
        request = RequestFactory().get(
            'timeline:list', kwargs={'project': project}
        )
        request.user = user
        return request


class TestTimelineAPI(
    TimelineAPIMixin,
    ProjectEventMixin,
    ProjectEventStatusMixin,
    RemoteSiteMixin,
    FolderMixin,
    TestProjectEventBase,
):
    def setUp(self):
        super().setUp()
        self.timeline = get_backend_api('timeline_backend')
        self.superuser = self.make_user('superuser')
        self.superuser.is_superuser = True
        self.superuser.save()

    def test_add_event(self):
        """Test adding an event"""
        self.assertEqual(ProjectEvent.objects.all().count(), 0)
        self.assertEqual(ProjectEventStatus.objects.all().count(), 0)

        event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.user_owner,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
        )

        self.assertEqual(ProjectEvent.objects.all().count(), 1)
        self.assertEqual(ProjectEventStatus.objects.all().count(), 1)  # Init

        expected = {
            'id': event.pk,
            'project': self.project.pk,
            'app': 'projectroles',
            'user': self.user_owner.pk,
            'event_name': 'test_event',
            'description': 'description',
            'classified': False,
            'extra_data': {'test_key': 'test_val'},
            'sodar_uuid': event.sodar_uuid,
        }
        self.assertEqual(model_to_dict(event), expected)

        status = event.get_current_status()
        expected_status = {
            'id': status.pk,
            'event': event.pk,
            'status_type': 'INIT',
            'description': DEFAULT_MESSAGES['INIT'],
            'extra_data': {},
        }
        self.assertEqual(model_to_dict(status), expected_status)

    def test_add_event_with_status(self):
        """Test adding an event with status"""
        self.assertEqual(ProjectEvent.objects.all().count(), 0)
        self.assertEqual(ProjectEventStatus.objects.all().count(), 0)

        event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.user_owner,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            status_type='OK',
            status_desc='OK',
            status_extra_data={},
        )

        status = event.get_current_status()
        self.assertEqual(ProjectEvent.objects.all().count(), 1)
        self.assertEqual(ProjectEventStatus.objects.all().count(), 2)

        expected_event = {
            'id': event.pk,
            'project': self.project.pk,
            'app': 'projectroles',
            'user': self.user_owner.pk,
            'event_name': 'test_event',
            'description': 'description',
            'classified': False,
            'extra_data': {'test_key': 'test_val'},
            'sodar_uuid': event.sodar_uuid,
        }
        self.assertEqual(model_to_dict(event), expected_event)

        expected_status = {
            'id': status.pk,
            'event': event.pk,
            'status_type': 'OK',
            'description': 'OK',
            'extra_data': {},
        }
        self.assertEqual(model_to_dict(status), expected_status)

    def test_add_event_custom_init(self):
        """Test adding an event with custom INIT status"""
        custom_init_desc = 'Custom init'
        self.assertEqual(ProjectEvent.objects.all().count(), 0)
        self.assertEqual(ProjectEventStatus.objects.all().count(), 0)

        event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.user_owner,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            status_type='INIT',
            status_desc=custom_init_desc,
        )

        self.assertEqual(ProjectEvent.objects.all().count(), 1)
        self.assertEqual(ProjectEventStatus.objects.all().count(), 1)  # Init

        status = event.get_current_status()
        expected_status = {
            'id': status.pk,
            'event': event.pk,
            'status_type': 'INIT',
            'description': custom_init_desc,
            'extra_data': {},
        }
        self.assertEqual(model_to_dict(status), expected_status)

    def test_add_event_no_user(self):
        """Test adding an event with no user"""
        self.assertEqual(ProjectEvent.objects.all().count(), 0)
        self.assertEqual(ProjectEventStatus.objects.all().count(), 0)

        event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=None,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
        )

        self.assertEqual(ProjectEvent.objects.all().count(), 1)
        self.assertEqual(ProjectEventStatus.objects.all().count(), 1)

        expected = {
            'id': event.pk,
            'project': self.project.pk,
            'app': 'projectroles',
            'user': None,
            'event_name': 'test_event',
            'description': 'description',
            'classified': False,
            'extra_data': {'test_key': 'test_val'},
            'sodar_uuid': event.sodar_uuid,
        }
        self.assertEqual(model_to_dict(event), expected)

    def test_add_event_anon_user(self):
        """Test adding an event with AnonymousUser"""
        self.assertEqual(ProjectEvent.objects.all().count(), 0)
        self.assertEqual(ProjectEventStatus.objects.all().count(), 0)

        event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=AnonymousUser(),
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
        )

        self.assertEqual(ProjectEvent.objects.all().count(), 1)
        self.assertEqual(ProjectEventStatus.objects.all().count(), 1)
        self.assertIsNone(event.user)

    def test_add_event_invalid_app(self):
        """Test adding an event with an invalid app name (should fail)"""
        self.assertEqual(ProjectEvent.objects.all().count(), 0)
        self.assertEqual(ProjectEventStatus.objects.all().count(), 0)

        with self.assertRaises(ValueError):
            self.timeline.add_event(
                project=self.project,
                app_name='NON-EXISTING APP NAME',
                user=self.user_owner,
                event_name='test_event',
                description='description',
                extra_data={'test_key': 'test_val'},
            )

        self.assertEqual(ProjectEvent.objects.all().count(), 0)
        self.assertEqual(ProjectEventStatus.objects.all().count(), 0)

    def test_add_event_invalid_status(self):
        """Test adding an event with an invalid status type"""
        self.assertEqual(ProjectEvent.objects.all().count(), 0)
        self.assertEqual(ProjectEventStatus.objects.all().count(), 0)

        with self.assertRaises(ValueError):
            self.timeline.add_event(
                project=self.project,
                app_name='projectroles',
                user=self.user_owner,
                event_name='test_event',
                description='description',
                status_type='NON-EXISTING STATUS TYPE',
                extra_data={'test_key': 'test_val'},
            )

        self.assertEqual(ProjectEvent.objects.all().count(), 0)
        self.assertEqual(ProjectEventStatus.objects.all().count(), 0)

    def test_add_object(self):
        """Test adding an object to an event"""
        self.assertEqual(ProjectEventObjectRef.objects.all().count(), 0)

        event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.user_owner,
            event_name='test_event',
            description='event with {obj}',
            extra_data={'test_key': 'test_val'},
        )
        temp_obj = self.project.get_owner()
        ref = event.add_object(
            obj=temp_obj,
            label='obj',
            name='assignment',
            extra_data={'test_key': 'test_val'},
        )

        self.assertEqual(ProjectEventObjectRef.objects.all().count(), 1)
        expected = {
            'id': ref.pk,
            'event': event.pk,
            'label': 'obj',
            'name': 'assignment',
            'object_model': temp_obj.__class__.__name__,
            'object_uuid': temp_obj.sodar_uuid,
            'extra_data': {'test_key': 'test_val'},
        }
        self.assertEqual(model_to_dict(ref), expected)

    def test_get_project_events(self):
        """Test get_project_events()"""
        event_normal = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.user_owner,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
        )
        event_classified = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.user_owner,
            event_name='test_event',
            description='description',
            classified=True,
            extra_data={'test_key': 'test_val'},
        )

        events = self.timeline.get_project_events(
            self.project, classified=False
        )
        self.assertEqual(events.count(), 1)
        self.assertEqual(events[0], event_normal)

        # Test with classified
        events = self.timeline.get_project_events(self.project, classified=True)
        self.assertEqual(events.count(), 2)
        self.assertIn(event_classified, events)

    def test_get_object_url(self):
        """Test get_object_url()"""
        expected_url = reverse(
            'timeline:list_object',
            kwargs={
                'project': self.project.sodar_uuid,
                'object_model': self.user_owner.__class__.__name__,
                'object_uuid': self.user_owner.sodar_uuid,
            },
        )
        url = self.timeline.get_object_url(self.user_owner, self.project)
        self.assertEqual(expected_url, url)

    def test_get_object_url_no_project(self):
        """Test get_object_url() without project"""
        expected_url = reverse(
            'timeline:list_object_site',
            kwargs={
                'object_model': self.user_owner.__class__.__name__,
                'object_uuid': self.user_owner.sodar_uuid,
            },
        )
        url = self.timeline.get_object_url(self.user_owner, None)
        self.assertEqual(expected_url, url)

    def test_get_object_link(self):
        """Test get_object_link()"""
        expected_url = reverse(
            'timeline:list_object',
            kwargs={
                'project': self.project.sodar_uuid,
                'object_model': self.user_owner.__class__.__name__,
                'object_uuid': self.user_owner.sodar_uuid,
            },
        )
        link = self.timeline.get_object_link(self.user_owner, self.project)
        self.assertIn(expected_url, link)

    def test_get_object_link_no_project(self):
        """Test get_object_link() without project"""
        expected_url = reverse(
            'timeline:list_object_site',
            kwargs={
                'object_model': self.user_owner.__class__.__name__,
                'object_uuid': self.user_owner.sodar_uuid,
            },
        )
        link = self.timeline.get_object_link(self.user_owner, None)
        self.assertIn(expected_url, link)

    def test_get_event_description(self):
        """Test getting event description"""
        event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.user_owner,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
        )
        self.assertEqual(
            self.timeline.get_event_description(event), event.description
        )

    def test_get_event_description_user(self):
        """Test getting event description with User object"""
        event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.user_owner,
            event_name='test_event',
            description='event with {obj}',
        )
        event.add_object(
            obj=self.user_owner,
            label='obj',
            name=self.user_owner.username,
        )
        desc = self.timeline.get_event_description(event)
        self.assertIn(self.user_owner.username, desc)
        self.assertIn('sodar-tl-object-link', desc)

    def test_get_event_description_project(self):
        """Test getting event description with Project object"""
        event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.user_owner,
            event_name='test_event',
            description='event with {obj}',
        )
        event.add_object(
            obj=self.project,
            label='obj',
            name=self.project.title,
        )
        desc = self.timeline.get_event_description(
            event, request=self.get_request(self.user_owner, self.project)
        )
        self.assertIn(self.project.title, desc)
        self.assertIn('sodar-tl-project-link', desc)

    def test_get_event_description_remote_site(self):
        """Test getting event description with RemoteSite object"""
        event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.user_owner,
            event_name='test_event',
            description='event with {obj}',
        )
        site = self._make_site(name=REMOTE_SITE_NAME, url=REMOTE_SITE_URL)
        event.add_object(
            obj=site,
            label='obj',
            name=site.name,
        )
        desc = self.timeline.get_event_description(
            event, request=self.get_request(self.superuser, self.project)
        )
        self.assertIn(site.name, desc)
        self.assertIn('sodar-tl-object-link', desc)

    def test_get_event_description_plugin_app(self):
        """Test getting event description with app plugin"""
        event = self.timeline.add_event(
            project=self.project,
            app_name='filesfolders',
            user=self.user_owner,
            event_name='test_event',
            description='event with {obj}',
        )
        folder = self._make_folder(
            name='folder',
            project=self.project,
            folder=None,
            description='',
            owner=self.user_owner,
        )
        event.add_object(
            obj=folder,
            label='obj',
            name=folder.name,
        )
        desc = self.timeline.get_event_description(
            event, request=self.get_request(self.superuser, self.project)
        )
        self.assertIn(folder.name, desc)
        self.assertIn('sodar-tl-object-link', desc)

    def test_get_event_description_plugin_lookup(self):
        """Test getting event description with app plugin and lookup dict"""
        event = self.timeline.add_event(
            project=self.project,
            app_name='filesfolders',
            user=self.user_owner,
            event_name='test_event',
            description='event with {obj}',
        )
        folder = self._make_folder(
            name='folder',
            project=self.project,
            folder=None,
            description='',
            owner=self.user_owner,
        )
        event.add_object(
            obj=folder,
            label='obj',
            name=folder.name,
        )
        desc = self.timeline.get_event_description(
            event,
            plugin_lookup=tags.get_plugin_lookup(),
            request=self.get_request(self.superuser, self.project),
        )
        self.assertIn(folder.name, desc)
        self.assertIn('sodar-tl-object-link', desc)

    def test_get_event_description_invalid_app(self):
        """Test getting event description with non-existing app plugin"""
        event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.user_owner,
            event_name='test_event',
            description='event with {obj}',
        )
        event.app = 'NOT_AN_ACTUAL_APP'
        event.save()
        event.add_object(
            obj=self.project,
            label='obj',
            name=self.project.title,
        )
        desc = self.timeline.get_event_description(
            event, request=self.get_request(self.superuser, self.project)
        )
        self.assertNotIn(self.project.title, desc)
        self.assertIn('sodar-tl-plugin-error', desc)
