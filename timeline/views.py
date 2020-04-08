"""UI views for the timeline Django app"""

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

# Projectroles dependency
from projectroles.models import Project
from projectroles.utils import get_display_name
from projectroles.views import (
    LoggedInPermissionMixin,
    ProjectContextMixin,
    ProjectPermissionMixin,
)

from timeline.models import ProjectEvent


# Local variables
DEFAULT_PAGINATION = 15


class ProjectTimelineView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectContextMixin,
    ProjectPermissionMixin,
    ListView,
):
    """View for displaying files and folders for a project"""

    permission_required = 'timeline.view_timeline'
    template_name = 'timeline/timeline.html'
    model = ProjectEvent
    paginate_by = getattr(settings, 'TIMELINE_PAGINATION', DEFAULT_PAGINATION)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['timeline_title'] = '{} Timeline'.format(
            get_display_name(context['project'].type, title=True)
        )
        context['timeline_mode'] = 'project'
        return context

    def get_queryset(self):
        set_kwargs = {'project__sodar_uuid': self.kwargs['project']}

        if not self.request.user.has_perm(
            'timeline.view_classified_event', self.get_permission_object()
        ):
            set_kwargs['classified'] = False

        return ProjectEvent.objects.filter(**set_kwargs).order_by('-pk')


class ObjectTimelineView(ProjectTimelineView):
    """View for displaying files and folders for a project"""

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context['timeline_title'] = '{} Timeline'.format(
            self.kwargs['object_model']
        )
        context['timeline_mode'] = 'object'

        return context

    def get_queryset(self):
        project = Project.objects.get(sodar_uuid=self.kwargs['project'])

        queryset = ProjectEvent.objects.get_object_events(
            project=project,
            object_model=self.kwargs['object_model'],
            object_uuid=self.kwargs['object_uuid'],
        )

        if not self.request.user.has_perm(
            'timeline.view_classified_event', self.get_permission_object()
        ):
            queryset = queryset.filter(classified=False)

        return queryset
