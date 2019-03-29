"""Plugins for the SodarProjectCache app"""

# Projectroles dependency
from projectroles.plugins import BackendPluginPoint

from .api import SodarProjectCacheAPI


class BackendPlugin(BackendPluginPoint):
    """Plugin for registering backend app with Projectroles"""

    #: Name (slug-safe, used in URLs)
    name = 'sodarprojectcache'

    #: Title (used in templates)
    title = 'Sodar Project Cache Backend'

    #: FontAwesome icon ID string
    icon = 'file-alt'

    #: Description string
    description = 'Sodar Project Cache backend for caching project data'

    def get_api(self):
        """Return API entry point object."""
        return SodarProjectCacheAPI()
