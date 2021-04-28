"""Taskflow API views for the projectroles app"""

import json

from django.conf import settings

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from projectroles.models import Project, RoleAssignment, Role
from projectroles.views import SUBMIT_STATUS_OK, User, app_settings


class TaskflowAPIAuthentication(BaseAuthentication):
    """Taskflow API authentication handling"""

    def authenticate(self, request):
        taskflow_secret = None

        if request.method == 'POST' and 'sodar_secret' in request.POST:
            taskflow_secret = request.POST['sodar_secret']

        elif request.method == 'GET':
            taskflow_secret = request.GET.get('sodar_secret', None)

        if (
            not hasattr(settings, 'TASKFLOW_SODAR_SECRET')
            or taskflow_secret != settings.TASKFLOW_SODAR_SECRET
        ):
            raise PermissionDenied('Not authorized')


class TaskflowAPIPermission(BasePermission):
    """Taskflow API permission handling"""

    def has_permission(self, request, view):
        # Only allow accessing Taskflow API views if Taskflow is used
        return True if 'taskflow' in settings.ENABLED_BACKEND_PLUGINS else False


class BaseTaskflowAPIView(APIView):
    """Base Taskflow API view"""

    authentication_classes = [TaskflowAPIAuthentication]
    permission_classes = [TaskflowAPIPermission]


class TaskflowProjectGetAPIView(BaseTaskflowAPIView):
    """Taskflow API view for getting a project"""

    def post(self, request):
        try:
            project = Project.objects.get(
                sodar_uuid=request.data['project_uuid'],
                submit_status=SUBMIT_STATUS_OK,
            )

        except Project.DoesNotExist as ex:
            return Response(str(ex), status=404)

        ret_data = {
            'project_uuid': str(project.sodar_uuid),
            'title': project.title,
            'description': project.description,
        }

        return Response(ret_data, status=200)


class TaskflowProjectUpdateAPIView(BaseTaskflowAPIView):
    """Taskflow API view for updating a project"""

    def post(self, request):
        try:
            project = Project.objects.get(
                sodar_uuid=request.data['project_uuid']
            )
            parent = (
                Project.objects.get(sodar_uuid=request.data['parent_uuid'])
                if request.data.get('parent_uuid')
                else None
            )
            project.parent = parent
            project.title = request.data['title']
            project.description = request.data.get('description') or ''
            project.readme.raw = request.data['readme']
            project.public_guest_access = (
                request.data.get('public_guest_access') or False
            )
            project.save()

        except Project.DoesNotExist as ex:
            return Response(str(ex), status=404)

        return Response('ok', status=200)


class TaskflowRoleAssignmentGetAPIView(BaseTaskflowAPIView):
    """Taskflow API view for getting a role assignment for user and project"""

    def post(self, request):
        try:
            project = Project.objects.get(
                sodar_uuid=request.data['project_uuid']
            )
            user = User.objects.get(sodar_uuid=request.data['user_uuid'])

        except (Project.DoesNotExist, User.DoesNotExist) as ex:
            return Response(str(ex), status=404)

        try:
            role_as = RoleAssignment.objects.get(project=project, user=user)
            ret_data = {
                'assignment_uuid': str(role_as.sodar_uuid),
                'project_uuid': str(role_as.project.sodar_uuid),
                'user_uuid': str(role_as.user.sodar_uuid),
                'role_pk': role_as.role.pk,
                'role_name': role_as.role.name,
            }
            return Response(ret_data, status=200)

        except RoleAssignment.DoesNotExist as ex:
            return Response(str(ex), status=404)


class TaskflowRoleAssignmentSetAPIView(BaseTaskflowAPIView):
    """Taskflow API view for creating or updating a role assignment"""

    def post(self, request):
        try:
            project = Project.objects.get(
                sodar_uuid=request.data['project_uuid']
            )
            user = User.objects.get(sodar_uuid=request.data['user_uuid'])
            role = Role.objects.get(pk=request.data['role_pk'])

        except (
            Project.DoesNotExist,
            User.DoesNotExist,
            Role.DoesNotExist,
        ) as ex:
            return Response(str(ex), status=404)

        try:
            role_as = RoleAssignment.objects.get(project=project, user=user)
            role_as.role = role
            role_as.save()

        except RoleAssignment.DoesNotExist:
            role_as = RoleAssignment(project=project, user=user, role=role)
            role_as.save()

        return Response('ok', status=200)


class TaskflowRoleAssignmentDeleteAPIView(BaseTaskflowAPIView):
    """Taskflow API view for deleting a role assignment"""

    def post(self, request):
        try:
            project = Project.objects.get(
                sodar_uuid=request.data['project_uuid']
            )
            user = User.objects.get(sodar_uuid=request.data['user_uuid'])

        except (Project.DoesNotExist, User.DoesNotExist) as ex:
            return Response(str(ex), status=404)

        try:
            role_as = RoleAssignment.objects.get(project=project, user=user)
            role_as.delete()

        except RoleAssignment.DoesNotExist as ex:
            return Response(str(ex), status=404)

        return Response('ok', status=200)


class TaskflowProjectSettingsGetAPIView(BaseTaskflowAPIView):
    """Taskflow API view for getting project settings"""

    def post(self, request):
        try:
            project = Project.objects.get(
                sodar_uuid=request.data['project_uuid']
            )

        except Project.DoesNotExist as ex:
            return Response(str(ex), status=404)

        project_settings = app_settings.get_all_settings(project)

        for k, v in project_settings.items():
            if isinstance(v, dict):
                project_settings[k] = json.dumps(v)

        ret_data = {
            'project_uuid': project.sodar_uuid,
            'settings': project_settings,
        }

        return Response(ret_data, status=200)


class TaskflowProjectSettingsSetAPIView(BaseTaskflowAPIView):
    """Taskflow API view for updating project settings"""

    def post(self, request):
        try:
            project = Project.objects.get(
                sodar_uuid=request.data['project_uuid']
            )

        except Project.DoesNotExist as ex:
            return Response(str(ex), status=404)

        for k, v in json.loads(request.data['settings']).items():
            app_settings.set_app_setting(
                k.split('.')[1], k.split('.')[2], v, project
            )

        return Response('ok', status=200)
