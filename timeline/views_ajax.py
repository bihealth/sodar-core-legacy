"""Ajax API views for the timeline app"""

from django.utils.timezone import localtime

from rest_framework.response import Response

# Projectroles dependency
from projectroles.views_ajax import (
    SODARBaseProjectAjaxView,
    SODARBasePermissionAjaxView,
)

from timeline.models import ProjectEvent
from timeline.templatetags.timeline_tags import get_status_style


class EventDetailMixin:
    """Mixin for event detail retrieval helpers"""

    def get_event_details(self, event):
        """
        Return event details.

        :param event: ProjectEvent object
        :return: Dict
        """
        ret = {
            'app': event.app,
            'name': event.event_name,
            'user': event.user.username if event.user else 'N/A',
            'timestamp': localtime(event.get_timestamp()).strftime(
                '%Y-%m-%d %H:%M:%S'
            ),
            'status': [],
        }
        status_changes = event.get_status_changes(reverse=True)
        for s in status_changes:
            ret['status'].append(
                {
                    'timestamp': localtime(s.timestamp).strftime(
                        '%Y-%m-%d %H:%M:%S'
                    ),
                    'description': s.description,
                    'type': s.status_type,
                    'class': get_status_style(s),
                }
            )
        return ret


class ProjectEventDetailAjaxView(EventDetailMixin, SODARBaseProjectAjaxView):
    """Ajax view for retrieving event details for projects"""

    permission_required = 'timeline.view_timeline'
    allow_anonymous = True

    def get(self, request, *args, **kwargs):
        event = ProjectEvent.objects.filter(
            sodar_uuid=self.kwargs['projectevent']
        ).first()
        if event.classified and not request.user.has_perm(
            'timeline.view_classified_event', event.project
        ):
            return Response(status=403)
        return Response(self.get_event_details(event), status=200)


class SiteEventDetailAjaxView(EventDetailMixin, SODARBasePermissionAjaxView):
    """Ajax view for retrieving event details for site-wide events"""

    permission_required = 'timeline.view_site_timeline'
    allow_anonymous = True

    def get(self, request, *args, **kwargs):
        event = ProjectEvent.objects.filter(
            sodar_uuid=self.kwargs['projectevent']
        ).first()
        if event.classified and not request.user.has_perm(
            'timeline.view_classified_site_event'
        ):
            return Response(status=403)
        return Response(self.get_event_details(event), status=200)
