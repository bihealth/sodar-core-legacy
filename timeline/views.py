"""UI views for the timeline app"""

from django.conf import settings
from django.views.generic import ListView

# Projectroles dependency
from projectroles.models import Project
from projectroles.utils import get_display_name
from projectroles.views import (
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectContextMixin,
    ProjectPermissionMixin,
)

from timeline.models import ProjectEvent


# Local variables
DEFAULT_PAGINATION = 15


class EventTimelineMixin:
    """Mixin for common event timeline operations"""

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        project = None
        if self.kwargs.get('project'):
            project = Project.objects.filter(
                sodar_uuid=self.kwargs['project']
            ).first()
        if project:
            context['timeline_title'] = '{} Timeline'.format(
                get_display_name(project.type, title=True)
            )
            context['timeline_mode'] = 'project'
        else:
            context['timeline_title'] = 'Site-Wide Timeline Events'
            context['timeline_mode'] = 'site'
        return context

    def get_queryset(self):
        project_uuid = self.kwargs.get('project')
        set_kwargs = {'project__sodar_uuid': project_uuid}
        if (
            project_uuid
            and not self.request.user.has_perm(
                'timeline.view_classified_event', self.get_permission_object()
            )
        ) or (not project_uuid and not self.request.user.is_superuser):
            set_kwargs['classified'] = False
        return ProjectEvent.objects.filter(**set_kwargs).order_by('-pk')


class ProjectTimelineView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectContextMixin,
    ProjectPermissionMixin,
    EventTimelineMixin,
    ListView,
):
    """View for displaying timeline events for a project"""

    permission_required = 'timeline.view_timeline'
    template_name = 'timeline/timeline.html'
    model = ProjectEvent
    paginate_by = getattr(settings, 'TIMELINE_PAGINATION', DEFAULT_PAGINATION)


class SiteTimelineView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    EventTimelineMixin,
    ListView,
):
    """View for displaying timeline events for site-wide events"""

    permission_required = 'timeline.view_site_timeline'
    template_name = 'timeline/timeline_site.html'
    model = ProjectEvent
    paginate_by = getattr(settings, 'TIMELINE_PAGINATION', DEFAULT_PAGINATION)


class ObjectTimelineMixin:
    """Mixin for common object timeline operations"""

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['timeline_title'] = '{} Timeline'.format(
            self.kwargs['object_model']
        )
        context['timeline_mode'] = 'object'
        return context

    def get_queryset(self):
        project = None
        classified_perm = 'timeline.view_classified_site_event'
        if self.kwargs.get('project'):
            project = Project.objects.filter(
                sodar_uuid=self.kwargs['project']
            ).first()
            classified_perm = 'timeline.view_classified_event'
        queryset = ProjectEvent.objects.get_object_events(
            project=project,
            object_model=self.kwargs['object_model'],
            object_uuid=self.kwargs['object_uuid'],
        )
        if not self.request.user.has_perm(
            classified_perm, self.get_permission_object()
        ):
            queryset = queryset.filter(classified=False)
        return queryset


class ProjectObjectTimelineView(ObjectTimelineMixin, ProjectTimelineView):
    """View for displaying files and folders for a project"""


class SiteObjectTimelineView(ObjectTimelineMixin, SiteTimelineView):
    """View for displaying files and folders for a project"""
