"""REST API views for the projectroles app"""

import re
from ipaddress import ip_address, ip_network

from django.conf import settings
from django.contrib import auth
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import (
    APIException,
    NotFound,
    PermissionDenied,
)
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
    DestroyAPIView,
)
from rest_framework.permissions import (
    BasePermission,
    AllowAny,
    IsAuthenticated,
)
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.versioning import AcceptHeaderVersioning
from rest_framework.views import APIView

from projectroles import __version__ as core_version
from projectroles.app_settings import AppSettingAPI
from projectroles.models import (
    Project,
    Role,
    RoleAssignment,
    ProjectInvite,
    RemoteSite,
    SODAR_CONSTANTS,
)
from projectroles.remote_projects import RemoteProjectAPI
from projectroles.serializers import (
    ProjectSerializer,
    RoleAssignmentSerializer,
    ProjectInviteSerializer,
    SODARUserSerializer,
    REMOTE_MODIFY_MSG,
)
from projectroles.views import (
    ProjectAccessMixin,
    RoleAssignmentDeleteMixin,
    RoleAssignmentOwnerTransferMixin,
    ProjectInviteMixin,
    SITE_MODE_TARGET,
)


User = auth.get_user_model()
app_settings = AppSettingAPI()


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']

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
CORE_API_ALLOWED_VERSIONS = [
    '0.7.2',
    '0.8.0',
    '0.8.1',
    '0.8.2',
    '0.8.3',
    '0.8.4',
    '0.9.0',
    '0.9.1',
    '0.10.0',
    '0.10.1',
    '0.10.2',
    '0.10.3',
    '0.10.4',
    '0.10.5',
    '0.10.6',
    '0.10.7',
    '0.10.8',
    '0.10.9',
]

# Local constants
INVALID_PROJECT_TYPE_MSG = (
    'Project type "{project_type}" not allowed for this API view'
)


# Permission / Versioning / Renderer Classes -----------------------------------


class SODARAPIProjectPermission(ProjectAccessMixin, BasePermission):
    """
    Mixin for providing a basic project permission checking for API views
    with a single permission_required attribute. Also works with Knox token
    based views.

    This must be used in the permission_classes attribute in order for token
    authentication to work.

    Requires implementing either permission_required or
    get_permission_required() in the view.

    Project type can be restricted to PROJECT_TYPE_CATEGORY or
    PROJECT_TYPE_PROJECT by setting the project_type attribute in the view.
    """

    def has_permission(self, request, view):
        """
        Override has_permission() for checking auth and project permission
        """
        if (not request.user or request.user.is_anonymous) and not getattr(
            settings, 'PROJECTROLES_ALLOW_ANONYMOUS', False
        ):
            return False

        project = self.get_project(request=request, kwargs=view.kwargs)
        if not project:
            raise NotFound()

        # Restrict project type
        project_type = getattr(view, 'project_type', None)
        p_types = [PROJECT_TYPE_CATEGORY, PROJECT_TYPE_PROJECT]
        if project_type and project_type not in p_types:
            raise ImproperlyConfigured(
                'Invalid value "{}" for project_type, accepted values: '
                '{}'.format(project_type, ', '.join(p_types))
            )
        elif project_type and project_type != project.type:
            raise PermissionDenied(
                INVALID_PROJECT_TYPE_MSG.format(project_type=project.type)
            )

        owner_or_delegate = project.is_owner_or_delegate(request.user)

        if not (
            request.user.is_superuser or owner_or_delegate
        ) and app_settings.get_app_setting(
            'projectroles', 'ip_restrict', project
        ):
            for k in (
                'HTTP_X_FORWARDED_FOR',
                'X_FORWARDED_FOR',
                'FORWARDED',
                'REMOTE_ADDR',
            ):
                v = request.META.get(k)
                if v:
                    client_address = ip_address(v.split(',')[0])
                    break
            else:  # Can't fetch client ip address
                return False

            for record in app_settings.get_app_setting(
                'projectroles', 'ip_allowlist', project
            ):
                if '/' in record:
                    if client_address in ip_network(record):
                        break
                else:
                    if client_address == ip_address(record):
                        break
            else:
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

        return request.user.has_perm(perm, project)


class SODARAPIVersioning(AcceptHeaderVersioning):
    """Accept header versioning class for SODAR API views"""

    allowed_versions = SODAR_API_ALLOWED_VERSIONS
    default_version = SODAR_API_DEFAULT_VERSION
    version_param = 'version'


class SODARAPIRenderer(JSONRenderer):
    """
    SODAR API JSON renderer with a site-specific media type retrieved from
    Django settings
    """

    media_type = SODAR_API_MEDIA_TYPE


# Base API View Mixins ---------------------------------------------------------


class SODARAPIBaseMixin:
    """Base SODAR API mixin to be used by external SODAR Core based sites"""

    renderer_classes = [SODARAPIRenderer]
    versioning_class = SODARAPIVersioning


class SODARAPIBaseProjectMixin(ProjectAccessMixin, SODARAPIBaseMixin):
    """
    API view mixin for the base DRF APIView class with project permission
    checking, but without serializers and other generic view functionality.

    Project type can be restricted to PROJECT_TYPE_CATEGORY or
    PROJECT_TYPE_PROJECT by setting the project_type attribute in the view.
    """

    permission_classes = [SODARAPIProjectPermission]
    project_type = None


class APIProjectContextMixin(ProjectAccessMixin):
    """
    Mixin to provide project context and queryset for generic API views. Can
    be used both in SODAR and SODAR Core API base views.
    """

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        context['project'] = self.get_project(request=context['request'])
        return context

    def get_queryset(self):
        return self.__class__.serializer_class.Meta.model.objects.filter(
            project=self.get_project()
        )


class SODARAPIGenericProjectMixin(
    APIProjectContextMixin, SODARAPIBaseProjectMixin
):
    """
    API view mixin for generic DRF API views with serializers, SODAR
    project context and permission checkin.

    Unless overriding permission_classes with their own implementation,
    the user MUST supply a permission_required attribute.

    Replace lookup_url_kwarg with your view's url kwarg (SODAR project
    compatible model name in lowercase)

    If the lookup is done via the project object, change lookup_field into
    "sodar_uuid"
    """

    lookup_field = 'sodar_uuid'  # Use project__sodar_uuid for lists
    lookup_url_kwarg = 'project'  # Replace with relevant model


class ProjectQuerysetMixin:
    """
    Mixin for overriding the default queryset with one which allows us to lookup
    a Project object directly.
    """

    def get_queryset(self):
        return Project.objects.all()


# SODAR Core Base Views and Mixins ---------------------------------------------


class CoreAPIVersioning(AcceptHeaderVersioning):
    allowed_versions = CORE_API_ALLOWED_VERSIONS
    default_version = CORE_API_DEFAULT_VERSION
    version_param = 'version'


class CoreAPIRenderer(JSONRenderer):
    media_type = CORE_API_MEDIA_TYPE


class CoreAPIBaseMixin:
    """
    SODAR Core API view mixin, which overrides versioning and renderer classes
    with ones intended for use with internal SODAR Core API views.
    """

    renderer_classes = [CoreAPIRenderer]
    versioning_class = CoreAPIVersioning


class CoreAPIBaseProjectMixin(ProjectAccessMixin, CoreAPIBaseMixin):
    """
    SODAR Core API view mixin for the base DRF APIView class with project
    permission checking, but without serializers and other generic view
    functionality.
    """

    permission_classes = [SODARAPIProjectPermission]


class CoreAPIGenericProjectMixin(
    APIProjectContextMixin, CoreAPIBaseProjectMixin
):
    """Generic API view mixin for internal SODAR Core API views"""

    lookup_field = 'sodar_uuid'  # Use project__sodar_uuid for lists
    lookup_url_kwarg = 'project'  # Replace with relevant model


# Projectroles Specific Base Views and Mixins ----------------------------------


class ProjectCreatePermission(ProjectAccessMixin, BasePermission):
    """Permission class specific to Project creation"""

    def has_permission(self, request, view):
        """Override has_permission() to check for project creation permission"""
        parent_uuid = request.data.get('parent')
        parent = (
            Project.objects.filter(sodar_uuid=parent_uuid).first()
            if parent_uuid
            else None
        )

        if (
            parent
            and settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET
            and (not settings.PROJECTROLES_TARGET_CREATE or parent.is_remote())
        ):
            return False

        if not parent and not request.user.is_superuser:
            return False

        return request.user.has_perm('projectroles.create_project', parent)


# API Views --------------------------------------------------------------------


class ProjectListAPIView(ListAPIView):
    """
    List all projects and categories for which the requesting user has access.

    **URL:** ``/project/api/list``

    **Methods:** ``GET``

    **Returns:** List of project details (see ``ProjectRetrieveAPIView``)
    """

    permission_classes = [IsAuthenticated]
    renderer_classes = [CoreAPIRenderer]
    serializer_class = ProjectSerializer
    versioning_class = CoreAPIVersioning

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
    ProjectQuerysetMixin, CoreAPIGenericProjectMixin, RetrieveAPIView
):
    """
    Retrieve a project or category by its UUID.

    **URL:** ``/project/api/retrieve/{Project.sodar_uuid}``

    **Methods:** ``GET``

    **Returns:**

    - ``description``: Project description (string)
    - ``parent``: Parent category UUID (string or null)
    - ``readme``: Project readme (string, supports markdown)
    - ``public_guest_access``: Guest access for all users (boolean)
    - ``roles``: Project role assignments (dict, assignment UUID as key)
    - ``sodar_uuid``: Project UUID (string)
    - ``submit_status``: Project creation status (string)
    - ``title``: Project title (string)
    - ``type``: Project type (string, options: ``PROJECT`` or ``CATEGORY``)
    """

    permission_required = 'projectroles.view_project'
    serializer_class = ProjectSerializer


class ProjectCreateAPIView(ProjectAccessMixin, CreateAPIView):
    """
    Create a project or a category.

    **URL:** ``/project/api/create``

    **Methods:** ``POST``

    **Parameters:**

    - ``title``: Project title (string)
    - ``type``: Project type (string, options: ``PROJECT`` or ``CATEGORY``)
    - ``parent``: Parent category UUID (string)
    - ``description``: Projcet description (string, optional)
    - ``readme``: Project readme (string, optional, supports markdown)
    - ``public_guest_access``: Guest access for all users (boolean)
    - ``owner``: User UUID of the project owner (string)
    """

    permission_classes = [ProjectCreatePermission]
    renderer_classes = [CoreAPIRenderer]
    serializer_class = ProjectSerializer
    versioning_class = CoreAPIVersioning


class ProjectUpdateAPIView(
    ProjectQuerysetMixin, CoreAPIGenericProjectMixin, UpdateAPIView
):
    """
    Update the metadata of a project or a category.

    Note that the project owner can not be updated here. Instead, use the
    dedicated API view ``RoleAssignmentOwnerTransferAPIView``.

    The project type can not be updated once a project has been created. The
    parameter is still required for non-partial updates via the ``PUT`` method.

    **URL:** ``/project/api/update/{Project.sodar_uuid}``

    **Methods:** ``PUT``, ``PATCH``

    **Parameters:**

    - ``title``: Project title (string)
    - ``type``: Project type (string, can not be modified)
    - ``parent``: Parent category UUID (string)
    - ``description``: Projcet description (string, optional)
    - ``readme``: Project readme (string, optional, supports markdown)
    - ``public_guest_access``: Guest access for all users (boolean)
    - ``owner``: User UUID of the project owner (string)
    """

    permission_required = 'projectroles.update_project'
    serializer_class = ProjectSerializer

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        project = self.get_project(request=context['request'])
        context['parent'] = (
            str(project.parent.sodar_uuid) if project.parent else None
        )
        return context


class RoleAssignmentCreateAPIView(CoreAPIGenericProjectMixin, CreateAPIView):
    """
    Create a role assignment in a project.

    **URL:** ``/project/api/roles/create/{Project.sodar_uuid}``

    **Methods:** ``POST``

    **Parameters:**

    - ``role``: Desired role for user (string, e.g. "project contributor")
    - ``user``: User UUID (string)
    """

    permission_required = 'projectroles.update_project_members'
    serializer_class = RoleAssignmentSerializer


class RoleAssignmentUpdateAPIView(CoreAPIGenericProjectMixin, UpdateAPIView):
    """
    Update the role assignment for a user in a project.

    The user can not be changed in this API view.

    **URL:** ``/project/api/roles/update/{RoleAssignment.sodar_uuid}``

    **Methods:** ``PUT``, ``PATCH``

    **Parameters:**

    - ``role``: Desired role for user (string, e.g. "project contributor")
    - ``user``: User UUID (string)
    """

    lookup_url_kwarg = 'roleassignment'
    permission_required = 'projectroles.update_project_members'
    serializer_class = RoleAssignmentSerializer


class RoleAssignmentDestroyAPIView(
    RoleAssignmentDeleteMixin, CoreAPIGenericProjectMixin, DestroyAPIView
):
    """
    Destroy a role assignment.

    The owner role can not be destroyed using this view.

    **URL:** ``/project/api/roles/destroy/{RoleAssignment.sodar_uuid}``

    **Methods:** ``DELETE``
    """

    lookup_url_kwarg = 'roleassignment'
    permission_required = 'projectroles.update_project_members'
    serializer_class = RoleAssignmentSerializer

    def perform_destroy(self, instance):
        """
        Override perform_destroy() to handle RoleAssignment deletion with or
        without SODAR Taskflow.
        """
        project = self.get_project()

        # Validation for remote sites and projects
        if project.is_remote():
            raise serializers.ValidationError(REMOTE_MODIFY_MSG)

        # Do not allow editing owner here
        if instance.role.name == PROJECT_ROLE_OWNER:
            raise serializers.ValidationError(
                'Use project updating API to update owner'
            )

        # Check delegate perms
        if (
            instance.role.name == PROJECT_ROLE_DELEGATE
            and not self.request.user.has_perm(
                'projectroles.update_project_delegate', project
            )
        ):
            raise PermissionDenied('User lacks permission to assign delegates')

        self.delete_assignment(request=self.request, instance=instance)


class RoleAssignmentOwnerTransferAPIView(
    RoleAssignmentOwnerTransferMixin, CoreAPIBaseProjectMixin, APIView
):
    """
    Trensfer project ownership to another user with a role in
    the project. Reassign a different role to the previous owner.

    The new owner must already have a role assigned in the project.

    **URL:** ``/project/api/roles/owner-transfer/{Project.sodar_uuid}``

    **Methods:** ``POST``

    **Parameters:**

    - ``new_owner``: User name of new owner (string)
    - ``old_owner_role``: Role for old owner (string. e.g. "project delegate")
    """

    permission_required = 'projectroles.update_project_owner'

    def post(self, request, *args, **kwargs):
        """Handle ownership transfer in a POST request"""
        project = self.get_project()

        # Validation for remote sites and projects
        if project.is_remote():
            raise serializers.ValidationError(REMOTE_MODIFY_MSG)

        new_owner = User.objects.filter(
            username=request.data.get('new_owner')
        ).first()
        old_owner_role = Role.objects.filter(
            name=request.data.get('old_owner_role')
        ).first()
        old_owner_as = project.get_owner()

        # Validate input
        if not new_owner or not old_owner_role:
            raise serializers.ValidationError(
                'Fields "new_owner" and "old_owner_role" must be present'
            )

        if not old_owner_role:
            raise serializers.ValidationError(
                'Unknown role "{}"'.format(request.data.get('old_owner_role'))
            )

        if not old_owner_as:
            raise serializers.ValidationError('Existing owner role not found')

        if not new_owner:
            raise serializers.ValidationError(
                'User "{}" not found'.format(request.data.get('new_owner'))
            )

        if new_owner == old_owner_as.user:
            raise serializers.ValidationError('Owner role already set for user')

        if not project.has_role(new_owner):
            raise serializers.ValidationError(
                'User {} is not a member of the project'.format(
                    new_owner.username
                )
            )

        # All OK, transfer owner
        try:
            self.transfer_owner(
                project, new_owner, old_owner_as, old_owner_role
            )

        except Exception as ex:
            raise APIException('Unable to transfer owner: {}'.format(ex))

        return Response(
            {
                'detail': 'Ownership transferred from {} to {} in '
                'project "{}"'.format(
                    old_owner_as.user.username,
                    new_owner.username,
                    project.title,
                )
            },
            status=200,
        )


class ProjectInviteAPIMixin:
    """Validation helpers for project invite modification via API"""

    def _validate(self, invite, request, **kwargs):
        if not invite:
            raise NotFound(
                'Invite not found (uuid={})'.format(kwargs['projectinvite'])
            )
        if (
            invite.role.name == PROJECT_ROLE_DELEGATE
            and not request.user.has_perm(
                'projectroles.update_project_delegate', invite.project
            )
        ):
            raise PermissionDenied(
                'User lacks permission to modify delegate invites'
            )
        if not invite.active:
            raise serializers.ValidationError('Invite is not active')


class ProjectInviteListAPIView(CoreAPIBaseProjectMixin, ListAPIView):
    """
    List user invites for a project.

    **URL:** ``/project/api/invites/list/{Project.sodar_uuid}``

    **Methods:** ``GET``

    **Returns:** List of project invite details
    """

    # lookup_field = 'project__sodar_uuid'
    # lookup_url_kwarg = 'projectinvite'
    permission_required = 'projectroles.invite_users'
    serializer_class = ProjectInviteSerializer

    def get_queryset(self):
        return ProjectInvite.objects.filter(
            project=self.get_project(), active=True
        ).order_by('pk')


class ProjectInviteCreateAPIView(CoreAPIGenericProjectMixin, CreateAPIView):
    """
    Create a project invite.

    **URL:** ``/project/api/invites/create/{Project.sodar_uuid}``

    **Methods:** ``POST``

    **Parameters:**

    - ``email``: User email (string)
    - ``role``: Desired role for user (string, e.g. "project contributor")
    """

    permission_required = 'projectroles.invite_users'
    serializer_class = ProjectInviteSerializer


class ProjectInviteRevokeAPIView(
    ProjectInviteMixin, ProjectInviteAPIMixin, CoreAPIBaseProjectMixin, APIView
):
    """
    Revoke a project invite.

    **URL:** ``/project/api/invites/revoke/{ProjectInvite.sodar_uuid}``

    **Methods:** ``POST``
    """

    permission_required = 'projectroles.invite_users'

    def post(self, request, *args, **kwargs):
        """Handle invite revoking in a POST request"""
        invite = ProjectInvite.objects.filter(
            sodar_uuid=kwargs['projectinvite']
        ).first()
        self._validate(invite, request, **kwargs)
        invite = self.revoke_invite(invite, invite.project, request)
        return Response(
            {
                'detail': 'Invite revoked from email {} in project "{}"'.format(
                    invite.email,
                    invite.project.title,
                )
            },
            status=200,
        )


class ProjectInviteResendAPIView(
    ProjectInviteMixin, ProjectInviteAPIMixin, CoreAPIBaseProjectMixin, APIView
):
    """
    Resend email for a project invite.

    **URL:** ``/project/api/invites/resend/{ProjectInvite.sodar_uuid}``

    **Methods:** ``POST``
    """

    permission_required = 'projectroles.invite_users'

    def post(self, request, *args, **kwargs):
        """Handle invite resending in a POST request"""
        invite = ProjectInvite.objects.filter(
            sodar_uuid=kwargs['projectinvite']
        ).first()
        self._validate(invite, request, **kwargs)
        self.handle_invite(invite, request, resend=True, add_message=False)
        return Response(
            {
                'detail': 'Invite resent from email {} in project "{}"'.format(
                    invite.email,
                    invite.project.title,
                )
            },
            status=200,
        )


class UserListAPIView(CoreAPIBaseMixin, ListAPIView):
    """
    List users in the system.

    **URL:** ``/project/api/users/list``

    **Methods:** ``GET``

    **Returns**:

    For each user:

    - ``email``: Email address of the user (string)
    - ``name``: Full name of the user (string)
    - ``sodar_uuid``: User UUID (string)
    - ``username``: Username of the user (string)
    """

    lookup_field = 'project__sodar_uuid'
    permission_classes = [IsAuthenticated]
    serializer_class = SODARUserSerializer

    def get_queryset(self):
        """
        Override get_queryset() to return users according to requesting user
        access.
        """
        qs = User.objects.all().order_by('pk')

        if self.request.user.is_superuser:
            return qs

        return qs.exclude(groups__name=SODAR_CONSTANTS['SYSTEM_USER_GROUP'])


class CurrentUserRetrieveAPIView(CoreAPIBaseMixin, RetrieveAPIView):
    """
    Return information on the user making the request.

    **URL:** ``/project/api/users/current``

    **Methods:** ``GET``

    **Returns**:

    For current user:

    - ``email``: Email address of the user (string)
    - ``name``: Full name of the user (string)
    - ``sodar_uuid``: User UUID (string)
    - ``username``: Username of the user (string)
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SODARUserSerializer

    def get_object(self):
        return self.request.user


# TODO: Update this for new API base classes
class RemoteProjectGetAPIView(CoreAPIBaseMixin, APIView):
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

        sync_data = remote_api.get_source_data(target_site)

        # Update access date for target site remote projects
        target_site.projects.all().update(date_access=timezone.now())

        return Response(sync_data, status=200)
