"""Example REST API views for SODAR Core"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# Projectroles dependency
from projectroles.views_api import (
    SODARAPIGenericProjectMixin,
)


class HelloExampleProjectAPIView(SODARAPIGenericProjectMixin, APIView):
    """
    Example API view with a project scope.

    This view can be used to e.g. retrieve assay UUIDs for landing zone
    operations.

    **URL:** ``api/hello/{Project.sodar_uuid}``

    **Methods:** ``GET``

    **Returns:**

    - ``detail``: Hello message (string)
    """

    http_method_names = ['get']
    permission_required = 'example_project_app.view_data'

    def get(self, request, *args, **kwargs):
        project = self.get_project()
        return Response(
            {'detail': 'Hello world from project: {}'.format(project.title)},
            status=status.HTTP_200_OK,
        )
