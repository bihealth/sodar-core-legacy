"""Plugins for the appalerts app"""


# Projectroles dependency
from projectroles.plugins import SiteAppPluginPoint, BackendPluginPoint

from appalerts.api import AppAlertAPI


class SiteAppPlugin(SiteAppPluginPoint):
    """Site plugin for application alerts"""

    #: Name (slug-safe, used in URLs)
    name = 'appalerts'

    #: Title (used in templates)
    title = 'App Alerts'

    #: App URLs (will be included in settings by djangoplugins)
    urls = []

    #: Iconify icon
    icon = 'mdi:alert-octagram'

    #: Description string
    description = 'App-specific alerts for users'

    #: Entry point URL ID
    entry_point_url_id = 'appalerts:list'

    #: Required permission for displaying the app
    app_permission = 'appalerts.view_alerts'


class BackendPlugin(BackendPluginPoint):
    """Backend plugin for application alerts"""

    #: Name (slug-safe, used in URLs)
    name = 'appalerts_backend'

    #: Title (used in templates)
    title = 'App Alerts Backend'

    #: Iconify icon
    icon = 'mdi:alert-octagram-outline'

    #: Description string
    description = 'App Alerts backend for creating and accessing alerts'

    #: URL of optional javascript file to be included
    javascript_url = 'appalerts/js/appalerts.js'

    def get_api(self, **kwargs):
        """Return API entry point object."""
        return AppAlertAPI()
