# Projectroles dependency
from projectroles.plugins import BackendPluginPoint

from .api import TaskflowAPI


class BackendPlugin(BackendPluginPoint):
    """Plugin for registering backend app with Projectroles"""

    #: Name (slug-safe, used in URLs)
    name = 'taskflow'

    #: Title (used in templates)
    title = 'Taskflow'

    #: Iconify icon
    icon = 'mdi:database'

    #: Description string
    description = 'SODAR Taskflow backend for data transactions'

    def get_api(self):
        """Return API entry point object."""
        return TaskflowAPI()
