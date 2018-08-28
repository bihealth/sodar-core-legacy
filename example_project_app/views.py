from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

# Projectroles dependency
from projectroles.views import LoggedInPermissionMixin, \
    ProjectContextMixin, ProjectPermissionMixin


class ExampleView(
        LoginRequiredMixin, LoggedInPermissionMixin, ProjectPermissionMixin,
        ProjectContextMixin, TemplateView):
    """Example project app view"""

    # Projectroles dependency
    permission_required = 'example_project_app.view_data'
    template_name = 'example_project_app/example.html'
