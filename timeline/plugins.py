"""Plugins for the Timeline app"""

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import (
    ProjectAppPluginPoint,
    BackendPluginPoint,
    SiteAppPluginPoint,
)
from projectroles.utils import get_display_name

from timeline.api import TimelineAPI
from timeline.models import ProjectEvent
from timeline.urls import urlpatterns


class ProjectAppPlugin(ProjectAppPluginPoint):
    """Plugin for registering app with Projectroles"""

    # Properties required by django-plugins ------------------------------

    #: Name (slug-safe, used in URLs)
    name = 'timeline'

    #: Title (used in templates)
    title = 'Timeline'

    #: App URLs (will be included in settings by djangoplugins)
    urls = urlpatterns

    # Properties defined in ProjectAppPluginPoint -----------------------

    #: Iconify icon
    icon = 'mdi:clock-time-eight'

    #: Entry point URL ID (must take project sodar_uuid as "project" argument)
    entry_point_url_id = 'timeline:list_project'

    #: Description string
    description = 'Timeline of {} events'.format(
        get_display_name(SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'])
    )

    #: Required permission for accessing the app
    app_permission = 'timeline.view_timeline'

    #: Enable or disable general search from project title bar
    search_enable = False  # Not allowed for timeline

    #: App card template for the project details page
    details_template = 'timeline/_details_card.html'

    #: App card title for the project details page
    details_title = 'Timeline Overview'

    #: Position in plugin ordering
    plugin_ordering = 40

    #: Display application for categories in addition to projects
    category_enable = True

    #: Names of plugin specific Django settings to display in siteinfo
    info_settings = ['TIMELINE_PAGINATION']

    def get_statistics(self):
        return {
            'event_count': {
                'label': 'Events',
                'value': ProjectEvent.objects.all().count(),
            }
        }


class BackendPlugin(BackendPluginPoint):
    """Plugin for registering backend app with Projectroles"""

    #: Name (slug-safe, used in URLs)
    name = 'timeline_backend'

    #: Title (used in templates)
    title = 'Timeline Backend'

    #: Iconify icon
    icon = 'mdi:clock-time-eight-outline'

    #: Description string
    description = 'Timeline backend for modifying events'

    def get_api(self, **kwargs):
        """Return API entry point object."""
        return TimelineAPI()


class SiteAppPlugin(SiteAppPluginPoint):
    """Projectroles plugin for registering the app"""

    #: Name (slug-safe, used in URLs)
    name = 'timeline_site'

    #: Title (used in templates)
    title = 'Site-Wide Events'

    #: App URLs (will be included in settings by djangoplugins)
    urls = urlpatterns

    #: Iconify icon
    icon = 'mdi:clock-time-eight'

    #: Description string
    description = 'Timeline of Site-Wide Events'

    #: Entry point URL ID
    entry_point_url_id = 'timeline:list_site'

    #: Required permission for displaying the app
    app_permission = 'timeline.view_site_timeline'
