"""Ajax API view tests for the timeline app"""

from django.urls import reverse
from django.utils.timezone import localtime

# Projectroles dependency
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleAssignmentMixin,
)
from projectroles.tests.test_views import (
    TestViewsBase,
    PROJECT_TYPE_CATEGORY,
    PROJECT_TYPE_PROJECT,
)

from timeline.models import DEFAULT_MESSAGES
from timeline.templatetags.timeline_tags import get_status_style
from timeline.tests.test_models import ProjectEventMixin


class TestEventDetailAjaxViewBase(
    ProjectMixin, RoleAssignmentMixin, ProjectEventMixin, TestViewsBase
):
    """Base class for timeline Ajax API view test"""

    @classmethod
    def _format_ts(cls, timestamp):
        """Format timestamp as an expected value from the Ajax API view"""
        return localtime(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    def setUp(self):
        super().setUp()
        self.category = self._make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as_cat = self._make_assignment(
            self.category, self.user, self.role_owner
        )
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )


class TestProjectEventDetailAjaxView(TestEventDetailAjaxViewBase):
    """Tests for ProjectEventDetailAjaxView"""

    def setUp(self):
        super().setUp()
        self.event = self._make_event(
            self.project, 'projectroles', self.user, 'project_create'
        )
        self.event_status_init = self.event.set_status(
            'INIT', DEFAULT_MESSAGES['INIT']
        )
        self.event_status_ok = self.event.set_status(
            'OK', DEFAULT_MESSAGES['OK']
        )

    def test_get(self):
        """Test project event detail retrieval"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'timeline:ajax_detail_project',
                    kwargs={'projectevent': self.event.sodar_uuid},
                ),
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            'app': self.event.app,
            'name': self.event.event_name,
            'user': self.user.username,
            'timestamp': self._format_ts(self.event.get_timestamp()),
            'status': [
                {
                    'type': 'OK',
                    'class': get_status_style(self.event_status_ok),
                    'description': DEFAULT_MESSAGES['OK'],
                    'timestamp': self._format_ts(
                        self.event_status_ok.timestamp
                    ),
                },
                {
                    'type': 'INIT',
                    'class': get_status_style(self.event_status_init),
                    'description': DEFAULT_MESSAGES['INIT'],
                    'timestamp': self._format_ts(
                        self.event_status_init.timestamp
                    ),
                },
            ],
        }
        self.assertEqual(response.data, expected)

    def test_get_no_user(self):
        """Test project event detail retrieval with no user for event"""
        self.event.user = None
        self.event.save()
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'timeline:ajax_detail_project',
                    kwargs={'projectevent': self.event.sodar_uuid},
                ),
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user'], 'N/A')


class TestsiteEventDetailAjaxView(TestEventDetailAjaxViewBase):
    """Tests for SiteEventDetailAjaxView"""

    def setUp(self):
        super().setUp()
        self.event = self._make_event(
            None, 'projectroles', self.user, 'test_event'
        )
        self.event_status_init = self.event.set_status(
            'INIT', DEFAULT_MESSAGES['INIT']
        )
        self.event_status_ok = self.event.set_status(
            'OK', DEFAULT_MESSAGES['OK']
        )

    def test_get(self):
        """Test site event detail retrieval"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'timeline:ajax_detail_site',
                    kwargs={'projectevent': self.event.sodar_uuid},
                ),
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            'app': self.event.app,
            'name': self.event.event_name,
            'user': self.user.username,
            'timestamp': self._format_ts(self.event.get_timestamp()),
            'status': [
                {
                    'type': 'OK',
                    'class': get_status_style(self.event_status_ok),
                    'description': DEFAULT_MESSAGES['OK'],
                    'timestamp': self._format_ts(
                        self.event_status_ok.timestamp
                    ),
                },
                {
                    'type': 'INIT',
                    'class': get_status_style(self.event_status_init),
                    'description': DEFAULT_MESSAGES['INIT'],
                    'timestamp': self._format_ts(
                        self.event_status_init.timestamp
                    ),
                },
            ],
        }
        self.assertEqual(response.data, expected)
