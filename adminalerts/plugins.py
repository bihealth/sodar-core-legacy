from django.urls import reverse
from django.utils import timezone

# Projectroles dependency
from projectroles.plugins import SiteAppPluginPoint

from adminalerts.models import AdminAlert
from adminalerts.urls import urlpatterns


class SiteAppPlugin(SiteAppPluginPoint):
    """Projectroles plugin for registering the app"""

    #: Name (slug-safe, used in URLs)
    name = 'adminalerts'

    #: Title (used in templates)
    title = 'Admin Alerts'

    #: App URLs (will be included in settings by djangoplugins)
    urls = urlpatterns

    #: Iconify icon
    icon = 'mdi:alert'

    #: Description string
    description = 'Administrator alerts to be shown for users'

    #: Entry point URL ID
    entry_point_url_id = 'adminalerts:list'

    #: Required permission for displaying the app
    app_permission = 'adminalerts.create_alert'

    #: Names of plugin specific Django settings to display in siteinfo
    info_settings = ['ADMINALERTS_PAGINATION']

    def get_statistics(self):
        return {
            'alert_count': {
                'label': 'Alerts',
                'value': AdminAlert.objects.all().count(),
            }
        }

    def get_messages(self, user=None):
        """
        Return a list of messages to be shown to users.
        :param user: User object (optional)
        :return: List of dicts or empty list if no messages
        """
        messages = []
        alerts = AdminAlert.objects.filter(
            active=True, date_expire__gte=timezone.now()
        ).order_by('-pk')

        for a in alerts:
            content = (
                '<i class="iconify" data-icon="mdi:alert"></i> ' + a.message
            )

            if a.description.raw and user and user.is_authenticated:
                content += (
                    '<span class="pull-right"><a href="{}" class="text-info">'
                    '<i class="iconify" data-icon="mdi:arrow-right-circle">'
                    '</i> Details</a>'.format(
                        reverse(
                            'adminalerts:detail',
                            kwargs={'adminalert': a.sodar_uuid},
                        )
                    )
                )

            messages.append(
                {
                    'content': content,
                    'color': 'info',
                    'dismissable': False,
                    'require_auth': a.require_auth,
                }
            )

        return messages
