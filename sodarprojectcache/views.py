"""Views for the sodarprojectcache app"""

from django.contrib.auth.mixins import LoginRequiredMixin

from rest_framework.response import Response
from rest_framework.views import APIView


# Projectroles dependency
from projectroles.plugins import get_backend_api
from projectroles.views import (
    ProjectPermissionMixin,
    APIPermissionMixin,
    BaseTaskflowAPIView,
)

from .models import JsonCacheItem
from projectroles.models import Project

APP_NAME = 'sodarprojectcache'


# or is this more like adding a new cache item?
class SodarProjectCacheSetAPIView(
    LoginRequiredMixin, ProjectPermissionMixin, APIPermissionMixin, APIView
):
    """API View for creating or updating the value of a cache item"""

    permission_required = 'sodarprojectcache.set_cache_value'

    def post(self, request, *args, **kwargs):
        project_cache = get_backend_api('sodarprojectcache')
        try:
            project = Project.objects.get(sodar_uuid=kwargs['project'])
        except (Project.DoesNotExist,) as ex:
            return Response(str(ex), status=404)
        try:
            project_cache.set_cache_item(
                name=request.data['name'],
                app_name=APP_NAME,
                user=self.request.user,
                data=request.data['data'],
                data_type='json',
                project=project,
            )
        except Exception as ex:
            return Response(str(ex), status=400)
        return Response('ok', status=200)


class SodarProjectCacheGetAPIView(
    LoginRequiredMixin, ProjectPermissionMixin, APIPermissionMixin, APIView
):
    """API View for retrieving the value of a cache item"""

    permission_required = 'sodarprojectcache.get_cache_value'

    def post(self, request, *args, **kwargs):
        try:
            project = Project.objects.get(sodar_uuid=kwargs['project'])
        except Project.DoesNotExist as ex:
            return Response(str(ex), status=404)

        try:
            item = JsonCacheItem.objects.get(
                name=request.data['name'], project=project
            )
            ret_data = {
                'sodar_uuid': str(item.sodar_uuid),
                'project_uuid': str(item.project.sodar_uuid),
                'user_uuid': str(item.user.sodar_uuid),
                'name': item.name,
                'data': item.data,
            }

            return Response(ret_data, status=200)
        except JsonCacheItem.DoesNotExist as ex:
            return Response(str(ex), status=404)


class SodarProjectCacheGetDateAPIView(
    LoginRequiredMixin, ProjectPermissionMixin, APIPermissionMixin, APIView
):
    """API View for retrieving the update date of a cache item"""

    permission_required = 'sodarprojectcache.get_cache_value'

    def post(self, request, *args, **kwargs):
        project_cache = get_backend_api('sodarprojectcache')

        project_uuid = request.POST.get('project')
        if project_uuid:
            try:
                project = Project.objects.get(sodar_uuid=project_uuid)
                update_time = project_cache.get_update_time(
                    request.data['name'], project=project
                )
            except Project.DoesNotExist or JsonCacheItem.DoesNotExist as ex:
                return Response(str(ex), status=404)
        else:
            try:
                update_time = project_cache.get_update_time(
                    request.data['name']
                )
                return Response(update_time, status=200)
            except JsonCacheItem.DoesNotExist as ex:
                return Response(str(ex), status=404)


class TaskflowCacheUpdateAPIView(BaseTaskflowAPIView):
    """Taskflow API view for updating a cache item"""

    def post(self, request):
        project_uuid = request.POST.get('project')
        if project_uuid:
            try:
                project = Project.objects.get(sodar_uuid=project_uuid)
                item = JsonCacheItem.objects.get(
                    name=request.data['name'], project=project
                )
                item.project = project
            except Project.DoesNotExist or JsonCacheItem.DoesNotExist as ex:
                return Response(str(ex), status=404)
        else:
            try:
                item = JsonCacheItem.objects.get(name=request.data['name'])
                item.app_name = 'taskflow'
                item.data = request.data['data']
                item.user = self.request.user
            except JsonCacheItem.DoesNotExist:
                item = JsonCacheItem(
                    name=request.data['name'],
                    app_name='taskflow',
                    user=self.request.user,
                    data=request.data['data'],
                    data_type='json',
                )

        item.save()

        return Response('ok', status=200)
