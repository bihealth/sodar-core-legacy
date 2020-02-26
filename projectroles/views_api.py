"""REST API views for the samplesheets app"""

import re

from django.conf import settings
from django.contrib import auth
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import (
    BasePermission,
    DjangoModelPermissions,
    AllowAny,
    IsAuthenticated,
)
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.versioning import AcceptHeaderVersioning
from rest_framework.views import APIView

from projectroles import __version__ as core_version
from projectroles.models import (
    Project,
    RoleAssignment,
    RemoteSite,
    SODAR_CONSTANTS,
)
from projectroles.remote_projects import RemoteProjectAPI
from projectroles.serializers import ProjectSerializer, SODARUserSerializer
from projectroles.views import ProjectAccessMixin, SITE_MODE_TARGET


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']


# API constants for external SODAR Core sites
SODAR_API_MEDIA_TYPE = getattr(
    settings, 'SODAR_API_MEDIA_TYPE', 'application/UNDEFINED+json'
)
SODAR_API_DEFAULT_VERSION = getattr(
    settings, 'SODAR_API_DEFAULT_VERSION', '0.1'
)
SODAR_API_ALLOWED_VERSIONS = getattr(
    settings, 'SODAR_API_ALLOWED_VERSIONS', [SODAR_API_DEFAULT_VERSION]
)
CORE_API_MEDIA_TYPE = 'application/vnd.bihealth.sodar-core+json'
CORE_API_DEFAULT_VERSION = re.match(
    r'^([0-9.]+)(?:[+|\-][\S]+)?$', core_version
)[1]
CORE_API_ALLOWED_VERSIONS = ['0.8.0']


# Access Django user model
User = auth.get_user_model()


# Permission / Versioning / Renderer Classes -----------------------------------


class SODARAPIProjectPermission(ProjectAccessMixin, BasePermission):
    """
    Mixin for providing a basic project permission checking for API views
    with a single permission_required attribute. Also works with Knox token
    based views.

    This must be used in the permission_classes attribute in order for token
    authentication to work.

    NOTE: Requires implementing either permission_required or
          get_permission_required() in the view
    """

    def has_permission(self, request, view):
        """
        Override has_permission() for checking auth and  project permission
        """
        if not request.user or not request.user.is_authenticated:
            return False

        if not hasattr(view, 'permission_required') and (
            not hasattr(view, 'get_permission_required')
            or not callable(getattr(view, 'get_permission_required', None))
        ):
            raise ImproperlyConfigured(
                '{0} is missing the permission_required attribute. '
                'Define {0}.permission_required, or override '
                '{0}.get_permission_required().'.format(view.__class__.__name__)
            )

        elif hasattr(view, 'permission_required'):
            perm = view.permission_required

        else:
            perm = view.get_permission_required()

        # This may return an iterable, but we are only interested in one perm
        if isinstance(perm, (list, tuple)) and len(perm) > 0:
            # TODO: TBD: Raise exception / log warning if given multiple perms?
            perm = perm[0]

        return request.user.has_perm(
            perm, self.get_project(request=request, kwargs=view.kwargs)
        )


class SODARAPIObjectInProjectPermissions(
    ProjectAccessMixin, DjangoModelPermissions
):
    """
    DRF ``Permissions`` implementation for objects in SODAR
    ``projectroles.models.Project``s.

    Permissions can only be checked on models having a ``project`` attribute or
    a get_project() function. Access control is based on the convention action
    names (``${app_label}.${action}_${model_name}``) but based on roles on the
    containing ``Project``.
    """

    def __init__(self, *args, **kwargs):
        """Override to patch ``self.perms_map`` to set required permissions on
        ``GET`` et al."""
        super().__init__(*args, **kwargs)
        patch = {
            'GET': ['%(app_label)s.view_%(model_name)s'],
            'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
            'HEAD': ['%(app_label)s.view_%(model_name)s'],
        }
        self.perms_map = {**self.perms_map, **patch}

    def has_permission(self, request, view):
        """Override to base permission check on project only"""
        if getattr(view, '_ignore_model_permissions', False):
            return True

        if not request.user or (
            not request.user.is_authenticated and self.authenticated_users_only
        ):
            return False

        queryset = self._queryset(view)
        perms = self.get_required_permissions(request.method, queryset.model)

        return request.user.has_perms(perms, self.get_project())


class SODARAPIVersioning(AcceptHeaderVersioning):
    allowed_versions = SODAR_API_ALLOWED_VERSIONS
    default_version = SODAR_API_DEFAULT_VERSION
    version_param = 'version'


class SODARAPIRenderer(JSONRenderer):
    media_type = SODAR_API_MEDIA_TYPE


# Base API Mixins and Views ----------------------------------------------------


# TODO: Combine with SODARAPIBaseProjectMixin? Is this needed on its own?
class SODARAPIBaseMixin:
    """Base SODAR API mixin to be used by external SODAR Core based sites"""

    renderer_classes = [SODARAPIRenderer]
    versioning_class = SODARAPIVersioning


class SODARAPIBaseProjectMixin(SODARAPIBaseMixin):
    """
    API view mixin for the base DRF APIView class with project permission
    checking, but without serializers and other generic view functionality.
    """

    permission_classes = [SODARAPIProjectPermission]


class SODARAPIGenericViewProjectMixin(
    ProjectAccessMixin, SODARAPIBaseProjectMixin
):
    """
    API view mixin for generic DRF API views with serializers, SODAR
    project context and permission checkin.

    NOTE: Unless overriding permission_classes with their own implementation,
          the user MUST supply a permission_required attribute.

    NOTE: Replace lookup_url_kwarg with your view's url kwarg (SODAR project
          compatible model name in lowercase)

    NOTE: If the lookup is done via the project object, change lookup_field into
          "sodar_uuid"
    """

    lookup_field = 'project__sodar_uuid'
    lookup_url_kwarg = 'project'  # Replace with relevant model

    def get_serializer_context(self, *args, **kwargs):
        result = super().get_serializer_context(*args, **kwargs)
        result['project'] = self.get_project(request=result['request'])
        return result

    def get_queryset(self):
        return self.__class__.serializer_class.Meta.model.objects.filter(
            project=self.get_project()
        )


class SheetSubmitBaseAPIView(SODARAPIBaseProjectMixin, APIView):
    """
    Base API view for initiating sample sheet operations via SODAR Taskflow.
    NOTE: Not tied to serializer or generic views, as the actual object will not
          be updated here.
    """

    http_method_names = ['post']


class ProjectQuerysetMixin:
    """
    Mixin for overriding the default queryset with one which allows us to lookup
    a Project object directly.
    """

    def get_queryset(self):
        return Project.objects.all()


# SODAR Core Base Views and Mixins ---------------------------------------------


class SODARCoreAPIVersioning(AcceptHeaderVersioning):
    allowed_versions = CORE_API_ALLOWED_VERSIONS
    default_version = CORE_API_DEFAULT_VERSION
    version_param = 'version'


class SODARCoreAPIRenderer(JSONRenderer):
    media_type = CORE_API_MEDIA_TYPE


class SODARCoreAPIBaseMixin:
    """
    SODAR Core API view mixin, which overrides versioning and renderer classes
    with ones intended for use with internal SODAR Core API views.
    """

    permission_classes = [SODARAPIProjectPermission]
    renderer_classes = [SODARCoreAPIRenderer]
    versioning_class = SODARCoreAPIVersioning


class SODARCoreGenericViewProjectMixin(SODARAPIGenericViewProjectMixin):
    """Generic API view mixin for internal SODAR Core API views"""

    renderer_classes = [SODARCoreAPIRenderer]
    versioning_class = SODARCoreAPIVersioning


# API Views --------------------------------------------------------------------


class ProjectListAPIView(ListAPIView):
    """
    API view for listing projects for which the user has access.

    NOTE: Not using base mixins as there is no project context
    """

    permission_classes = [IsAuthenticated]
    renderer_classes = [SODARCoreAPIRenderer]
    serializer_class = ProjectSerializer
    versioning_class = SODARCoreAPIVersioning

    def get_queryset(self):
        """
        Override get_queryset() to return projects of type PROJECT for which the
        requesting user has access.
        """
        qs = Project.objects.filter(submit_status='OK').order_by('pk')

        if self.request.user.is_superuser:
            return qs

        return qs.filter(
            roles__in=RoleAssignment.objects.filter(user=self.request.user)
        )


class ProjectRetrieveAPIView(
    ProjectQuerysetMixin, SODARCoreGenericViewProjectMixin, RetrieveAPIView
):
    """API view for retrieving a project by UUID."""

    lookup_field = 'sodar_uuid'
    lookup_url_kwarg = 'project'
    permission_required = 'projectroles.view_project'
    serializer_class = ProjectSerializer


class UserListAPIView(ListAPIView):
    """
    API view for listing users in the system.

    NOTE: Not using base mixins as there is no project context
    """

    permission_classes = [IsAuthenticated]
    renderer_classes = [SODARCoreAPIRenderer]
    serializer_class = SODARUserSerializer
    versioning_class = SODARCoreAPIVersioning

    def get_queryset(self):
        """
        Override get_queryset() to return users according to requesting user
        access.
        """
        qs = User.objects.all().order_by('pk')

        if self.request.user.is_superuser:
            return qs

        return qs.exclude(groups__name=SODAR_CONSTANTS['SYSTEM_USER_GROUP'])


# TODO: Update this for new API base classes
class RemoteProjectGetAPIView(SODARCoreAPIBaseMixin, APIView):
    """API view for retrieving remote projects from a source site"""

    permission_classes = (AllowAny,)  # We check the secret in get()/post()

    def get(self, request, *args, **kwargs):
        remote_api = RemoteProjectAPI()
        secret = kwargs['secret']

        try:
            target_site = RemoteSite.objects.get(
                mode=SITE_MODE_TARGET, secret=secret
            )

        except RemoteSite.DoesNotExist:
            return Response('Remote site not found, unauthorized', status=401)

        sync_data = remote_api.get_target_data(target_site)

        # Update access date for target site remote projects
        target_site.projects.all().update(date_access=timezone.now())

        return Response(sync_data, status=200)
