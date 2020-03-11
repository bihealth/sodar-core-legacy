"""API views for the sodarcache app"""

from rest_framework.response import Response
from rest_framework.views import APIView

# Projectroles dependency
from projectroles.plugins import get_backend_api
from projectroles.views_api import CoreAPIBaseProjectMixin

APP_NAME = 'sodarcache'


# TODO: Refactor views and URLs to match SODAR conventions in v0.9 (see #498)


class SodarCacheSetAPIView(CoreAPIBaseProjectMixin, APIView):
    """API View for creating or updating the value of a cache item"""

    permission_required = 'sodarcache.set_cache_value'

    def post(self, request, *args, **kwargs):
        cache_backend = get_backend_api('sodar_cache')
        project = self.get_project()

        try:
            cache_backend.set_cache_item(
                name=request.data['name'],
                app_name=APP_NAME,
                user=self.request.user,
                data=request.data['data'],
                data_type='json',
                project=project,
            )

        except Exception as ex:
            return Response({'message': str(ex)}, status=500)

        return Response({'message': 'ok'}, status=200)


class SodarCacheGetAPIView(CoreAPIBaseProjectMixin, APIView):
    """API View for retrieving the value of a cache item"""

    permission_required = 'sodarcache.get_cache_value'

    def get(self, request, *args, **kwargs):
        cache_backend = get_backend_api('sodar_cache')
        project = self.get_project()

        try:
            item = cache_backend.get_cache_item(
                app_name=request.GET.get('app_name'),
                name=request.GET.get('name'),
                project=project,
            )

            if not item:
                return Response({'message': 'Not found'}, status=404)

            ret_data = {
                'sodar_uuid': str(item.sodar_uuid),
                'project_uuid': str(item.project.sodar_uuid),
                'user_uuid': str(item.user.sodar_uuid) if item.user else None,
                'name': item.name,
                'data': item.data,
            }
            return Response(ret_data, status=200)

        except Exception as ex:
            return Response({'message': str(ex)}, status=500)


class SodarCacheGetDateAPIView(CoreAPIBaseProjectMixin, APIView):
    """API View for retrieving the update date of a cache item"""

    permission_required = 'sodarcache.get_cache_value'

    def get(self, request, *args, **kwargs):
        cache_backend = get_backend_api('sodar_cache')
        project = self.get_project()

        update_time = cache_backend.get_update_time(
            request.GET.get('app_name'),
            request.GET.get('name'),
            project=project,
        )

        if update_time:
            return Response({'update_time': update_time}, status=200)

        return Response({'message': 'Not found'}, status=404)
