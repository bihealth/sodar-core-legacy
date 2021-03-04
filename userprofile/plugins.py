# Projectroles dependency
from projectroles.plugins import SiteAppPluginPoint

from .urls import urlpatterns


class SiteAppPlugin(SiteAppPluginPoint):
    """Projectroles plugin for registering the app"""

    #: Name (slug-safe, used in URLs)
    name = 'userprofile'

    #: Title (used in templates)
    title = 'User Profile'

    #: App URLs (will be included in settings by djangoplugins)
    urls = urlpatterns

    #: Iconify icon
    icon = 'mdi:account-details'

    #: Description string
    description = 'Project User Profile'

    #: Entry point URL ID
    entry_point_url_id = 'userprofile:detail'

    #: Required permission for displaying the app
    app_permission = 'userprofile.view_detail'

    app_settings = {
        'enable_project_uuid_copy': {
            'scope': 'USER',
            'type': 'BOOLEAN',
            'label': 'Display project UUID copying link',
            'default': False,
            'user_modifiable': True,
        }
    }

    def get_messages(self, user=None):
        """
        Return a list of messages to be shown to users.
        :param user: User object (optional)
        :return: List of dicts or and empty list if no messages
        """
        messages = []
        return messages
