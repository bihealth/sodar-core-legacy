from django.views.generic import TemplateView

# Projectroles dependency
from projectroles.views import LoggedInPermissionMixin


# Listing/details views --------------------------------------------------------


class ExampleView(LoggedInPermissionMixin, TemplateView):
    """Site app example view"""

    permission_required = 'example_site_app.view_data'
    template_name = 'example_site_app/example.html'
