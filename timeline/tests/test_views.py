"""View tests for the timeline app"""

from django.urls import reverse

# Projectroles dependency
from projectroles.models import Role, SODAR_CONSTANTS
from projectroles.plugins import get_backend_api

from timeline.tests.test_models import (
    TestProjectEventBase,
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


class TestViewsBase(
    ProjectEventMixin, ProjectEventStatusMixin, TestProjectEventBase
):
    """Base class for timeline view testing"""

    def setUp(self):
        super().setUp()
        self.timeline = get_backend_api('timeline_backend')

        # Init roles
        self.role_owner = Role.objects.get_or_create(name=PROJECT_ROLE_OWNER)[0]
        self.role_delegate = Role.objects.get_or_create(
            name=PROJECT_ROLE_DELEGATE
        )[0]
        self.role_contributor = Role.objects.get_or_create(
            name=PROJECT_ROLE_CONTRIBUTOR
        )[0]
        self.role_guest = Role.objects.get_or_create(name=PROJECT_ROLE_GUEST)[0]

        # Init superuser
        self.user = self.make_user('superuser')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        # Init category and project
        self.category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.cat_owner_as = self._make_assignment(
            self.category, self.user, self.role_owner
        )
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        # Init default event
        self.event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.user,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
        )


class TestProjectEventListView(TestViewsBase):
    """Tests for the timeline project event list view"""

    def test_render(self):
        """Test rendering the list view for a project"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'timeline:list_project',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context['object_list']), 1)
            self.assertEqual(
                response.context['object_list'].first(), self.event
            )

    def test_render_category(self):
        """Test rendering the list view for a category"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'timeline:list_project',
                    kwargs={'project': self.category.sodar_uuid},
                )
            )
            self.assertEqual(response.status_code, 200)


class TestProjectObjectListView(TestViewsBase):
    """Tests for the timeline project object list view"""

    def setUp(self):
        super().setUp()

        # Add user as an object reference
        self.ref_obj = self.event.add_object(
            obj=self.user, label='user', name=self.user.username
        )

    def test_render(self):
        """Test to ensure the view renders correctly"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'timeline:list_object',
                    kwargs={
                        'project': self.project.sodar_uuid,
                        'object_model': self.ref_obj.object_model,
                        'object_uuid': self.ref_obj.object_uuid,
                    },
                )
            )
            self.assertEqual(response.status_code, 200)


class TestSiteEventListView(TestViewsBase):
    """Tests for the timeline site-wide event list view"""

    def setUp(self):
        super().setUp()
        self.event_site = self.timeline.add_event(
            project=None,
            app_name='projectroles',
            user=self.user,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
        )

    def test_render(self):
        """Test rendering the site-wide list view"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'timeline:list_site',
                )
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context['object_list']), 1)
            self.assertEqual(
                response.context['object_list'].first(), self.event_site
            )


class TestSiteObjectListView(TestViewsBase):
    """Tests for the timeline site-wide objectlist view"""

    def setUp(self):
        super().setUp()
        self.event_site = self.timeline.add_event(
            project=None,
            app_name='projectroles',
            user=self.user,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
        )
        # Add user as an object reference
        self.ref_obj = self.event_site.add_object(
            obj=self.user, label='user', name=self.user.username
        )

    def test_render(self):
        """Test rendering the site-wide list view"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'timeline:list_object_site',
                    kwargs={
                        'object_model': self.ref_obj.object_model,
                        'object_uuid': self.ref_obj.object_uuid,
                    },
                )
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context['object_list']), 1)
            self.assertEqual(
                response.context['object_list'].first(), self.event_site
            )
