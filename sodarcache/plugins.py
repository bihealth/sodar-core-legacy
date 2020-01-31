"""Plugins for the sodarcache app"""

# Projectroles dependency
from projectroles.plugins import BackendPluginPoint

from .api import SodarCacheAPI


class BackendPlugin(BackendPluginPoint):
    """Plugin for registering backend app with Projectroles"""

    #: Name (slug-safe, used in URLs)
    name = 'sodar_cache'

    #: Title (used in templates)
    title = 'Sodar Cache Backend'

    #: FontAwesome icon ID string
    icon = 'shopping-basket'

    #: Description string
    description = (
        'Sodar Cache backend for caching and aggregating data from '
        'external databases'
    )

    def get_api(self, **kwargs):
        """Return API entry point object."""
        return SodarCacheAPI()
