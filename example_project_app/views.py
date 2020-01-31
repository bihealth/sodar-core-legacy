from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

# Projectroles dependency
from projectroles.plugins import get_backend_api
from projectroles.views import (
    LoggedInPermissionMixin,
    ProjectContextMixin,
    ProjectPermissionMixin,
)


class ExampleView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    TemplateView,
):
    """Example project app view"""

    # Projectroles dependency
    permission_required = 'example_project_app.view_data'
    template_name = 'example_project_app/example.html'

    def get_context_data(self, *args, **kwargs):
        """Override get_context_data() to demonstrate using a backend app"""
        context = super().get_context_data(*args, **kwargs)

        # Get API and data from backend into context
        example_api = get_backend_api(
            'example_backend_app', **{'hello': 'world'}
        )
        print('example_api={}'.format(example_api))
        context['backend_data'] = example_api.hello() if example_api else ''

        return context
