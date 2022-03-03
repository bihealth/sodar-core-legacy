"""Ajax API views for the projectroles app"""

import logging
from dal import autocomplete

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse

from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rules.contrib.views import PermissionRequiredMixin

from projectroles.models import (
    Project,
    RoleAssignment,
    ProjectUserTag,
    PROJECT_TAG_STARRED,
    SODAR_CONSTANTS,
)
from projectroles.plugins import get_active_plugins, get_backend_api
from projectroles.project_tags import get_tag_state, set_tag_state
from projectroles.utils import get_display_name
from projectroles.views import (
    ProjectAccessMixin,
    APP_NAME,
    User,
)
from projectroles.views_api import SODARAPIProjectPermission


logger = logging.getLogger(__name__)


# SODAR Consants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
SUBMIT_STATUS_OK = SODAR_CONSTANTS['SUBMIT_STATUS_OK']
SYSTEM_USER_GROUP = SODAR_CONSTANTS['SYSTEM_USER_GROUP']

# Local Constants
INHERITED_OWNER_INFO = 'Ownership inherited from parent category'


# Base Classes and Mixins ------------------------------------------------------


class SODARBaseAjaxView(APIView):
    """
    Base Ajax view with Django session authentication.

    No permission classes or mixins used, you will have to supply your own if
    using this class directly.

    The allow_anonymous property can be used to control whether anonymous users
    should access an Ajax view when PROJECTROLES_ALLOW_ANONYMOUS==True.
    """

    allow_anonymous = False
    authentication_classes = [SessionAuthentication]
    renderer_classes = [JSONRenderer]

    @property
    def permission_classes(self):
        if self.allow_anonymous and getattr(
            settings,
            'PROJECTROLES_ALLOW_ANONYMOUS',
            False,
        ):
            return [AllowAny]
        return [IsAuthenticated]


class SODARBasePermissionAjaxView(PermissionRequiredMixin, SODARBaseAjaxView):
    """
    Base Ajax view with permission checks, to be used e.g. in site apps with no
    project context.

    User-based perms such as is_superuser can be used with this class.
    """

    def handle_no_permission(self):
        """Override handle_no_permission() to provide 403"""
        return HttpResponseForbidden()


class SODARBaseProjectAjaxView(ProjectAccessMixin, SODARBaseAjaxView):
    """Base Ajax view with SODAR project permission checks"""

    permission_classes = [SODARAPIProjectPermission]


# Projectroles Ajax Views ------------------------------------------------------


class ProjectListAjaxView(SODARBaseAjaxView):
    """View to retrieve project list entries from the client"""

    allow_anonymous = True

    @classmethod
    def _get_project_list(cls, user, parent=None):
        """
        Return a flat list of categories and projects.

        :param user: User for which the projects are visible
        :param parent: Project object of type CATEGORY or None
        """
        project_list = Project.objects.filter(
            submit_status=SUBMIT_STATUS_OK,
        )
        if user.is_anonymous:
            project_list = project_list.filter(
                Q(public_guest_access=True) | Q(has_public_children=True)
            )
        elif not user.is_superuser:
            project_list = [
                p
                for p in project_list
                if p.public_guest_access
                or p.has_public_children
                or (
                    user.is_authenticated
                    and p.roles.filter(user=user).count() > 0
                )
            ]

        # Populate final list
        ret = []
        parent_prefix = parent.full_title + ' / ' if parent else None
        for p in project_list:
            if (
                p not in ret
                and p != parent
                and (not parent or p.full_title.startswith(parent_prefix))
            ):
                ret.append(p)
                if p.parent and p.parent in ret:
                    continue  # Skip already collected parents
                p_parent = p.parent
                while p_parent and p_parent != parent:
                    if p_parent not in ret:
                        ret.append(p_parent)
                    p_parent = p_parent.parent
        # Sort by full title
        return sorted(ret, key=lambda x: x.full_title)

    def get(self, request, *args, **kwargs):
        parent_uuid = request.GET.get('parent', None)
        parent = (
            Project.objects.get(sodar_uuid=parent_uuid) if parent_uuid else None
        )
        if parent and parent.type != PROJECT_TYPE_CATEGORY:
            return Response(
                {
                    'detail': 'Querying for a project list under a project is '
                    'not allowed'
                },
                status=400,
            )

        project_list = self._get_project_list(request.user, parent)
        starred_projects = []
        if request.user.is_authenticated:
            starred_projects = [
                t.project
                for t in ProjectUserTag.objects.filter(
                    user=request.user, name=PROJECT_TAG_STARRED
                )
            ]
        full_title_idx = len(parent.full_title) + 3 if parent else 0

        ret = {
            'projects': [
                {
                    'title': p.title,
                    'type': p.type,
                    'full_title': p.full_title[full_title_idx:],
                    'public_guest_access': p.public_guest_access,
                    'remote': p.is_remote(),
                    'revoked': p.is_revoked(),
                    'starred': p in starred_projects,
                    'depth': p.get_depth(),
                    'uuid': str(p.sodar_uuid),
                }
                for p in project_list
            ],
            'parent_depth': parent.get_depth() + 1 if parent else 0,
            'messages': {},
            'user': {'superuser': request.user.is_superuser},
        }

        if len(ret['projects']) == 0:
            np_prefix = 'No {} '.format(
                get_display_name(PROJECT_TYPE_PROJECT, plural=True)
            )
            if parent:
                np_msg = 'or {} available under this {}.'.format(
                    get_display_name(PROJECT_TYPE_CATEGORY, plural=True),
                    get_display_name(PROJECT_TYPE_CATEGORY),
                )
            elif not request.user.is_superuser:
                np_msg = (
                    'available: access must be granted by {} personnel or a '
                    'superuser.'.format(get_display_name(PROJECT_TYPE_PROJECT))
                )
            else:
                np_msg = 'have been created.'
            ret['messages']['no_projects'] = np_prefix + np_msg

        return Response(ret, status=200)


class ProjectListColumnAjaxView(SODARBaseAjaxView):
    """View to retrieve project list extra column data from the client"""

    allow_anonymous = True

    @classmethod
    def _get_column_value(cls, app_plugin, column_id, project, user):
        """
        Return project list extra column value for a specific project and
        column.

        :param app_plugin: Project app plugin object
        :param column_id: Column ID string corresponding to
                          plugin.project_list_columns (string)
        :param project: Project object
        :param user: SODARUser object
        :return: String (may contain HTML)
        """
        try:
            val = app_plugin.get_project_list_value(column_id, project, user)
            return {'html': str(val) if val is not None else ''}
        except Exception as ex:
            logger.error(
                'Exception in {}.get_project_list_value(): "{}" '
                '(column_id={}; project={}; user={})'.format(
                    app_plugin.name,
                    ex,
                    column_id,
                    project.sodar_uuid,
                    user.username,
                )
            )
            return {'html': ''}

    def post(self, request, *args, **kwargs):
        ret = {}
        projects = Project.objects.filter(
            type=PROJECT_TYPE_PROJECT,
            sodar_uuid__in=request.data.get('projects'),
        )
        plugins = [
            ap
            for ap in get_active_plugins(plugin_type='project_app')
            if ap.project_list_columns
            and (
                ap.name != 'filesfolders'
                or getattr(settings, 'FILESFOLDERS_SHOW_LIST_COLUMNS', False)
            )
        ]
        for project in projects:
            # Only provide results for projects in which user has access
            if not request.user.has_perm('projectroles.view_project', project):
                logger.error(
                    'ProjectListColumnAjaxView: User {} not authorized to view '
                    'project "{}" ({})'.format(
                        request.user.username,
                        project.title,
                        project.sodar_uuid,
                    )
                )
                continue
            p_uuid = str(project.sodar_uuid)
            ret[p_uuid] = {}
            for app_plugin in plugins:
                ret[p_uuid][app_plugin.name] = {}
                for k, v in app_plugin.project_list_columns.items():
                    ret[p_uuid][app_plugin.name][k] = self._get_column_value(
                        app_plugin, k, project, request.user
                    )
        return Response(ret, status=200)


class ProjectListRoleAjaxView(SODARBaseAjaxView):
    """View to retrieve project list role data from the client"""

    allow_anonymous = True

    @classmethod
    def _get_user_role(cls, project, user):
        """Return user role for project"""
        ret = {'name': None, 'class': None, 'info': None}
        role_as = None
        if user.is_authenticated:
            role_as = RoleAssignment.objects.filter(
                project=project, user=user
            ).first()
            if project.is_owner(user):
                ret['name'] = 'Owner'
                if not role_as or role_as.role.name != PROJECT_ROLE_OWNER:
                    ret['class'] = 'text-muted'
                    ret['info'] = INHERITED_OWNER_INFO
            if role_as:
                ret['name'] = role_as.role.name.split(' ')[1].capitalize()
        if project.public_guest_access and not role_as:
            ret['name'] = 'Guest'
        if not ret['name']:
            ret['name'] = 'N/A'
            ret['class'] = 'text-muted'
        return ret

    def post(self, request, *args, **kwargs):
        ret = {}
        projects = Project.objects.filter(
            sodar_uuid__in=request.data.get('projects'),
        )
        for project in projects:
            # Only provide results for projects in which user has access
            if not request.user.has_perm('projectroles.view_project', project):
                logger.error(
                    'ProjectListRoleAjaxView: User {} not authorized to view '
                    'project "{}" ({})'.format(
                        request.user.username,
                        project.title,
                        project.sodar_uuid,
                    )
                )
                continue
            ret[str(project.sodar_uuid)] = self._get_user_role(
                project, request.user
            )
        return Response(ret, status=200)


class ProjectStarringAjaxView(SODARBaseProjectAjaxView):
    """View to handle starring and unstarring a project"""

    permission_required = 'projectroles.view_project'

    def post(self, request, *args, **kwargs):
        # HACK: Manually refuse access to anonymous as this view is an exception
        if request.user.is_anonymous:
            return Response({'detail': 'Anonymous access denied'}, status=401)

        project = self.get_project()
        user = request.user
        timeline = get_backend_api('timeline_backend')

        tag_state = get_tag_state(project, user)
        action_str = '{}star'.format('un' if tag_state else '')

        set_tag_state(project, user, PROJECT_TAG_STARRED)

        # Add event in Timeline
        if timeline:
            timeline.add_event(
                project=project,
                app_name=APP_NAME,
                user=user,
                event_name='project_{}'.format(action_str),
                description='{} project'.format(action_str),
                classified=True,
                status_type='INFO',
            )

        return Response(0 if tag_state else 1, status=200)


class UserAutocompleteAjaxView(autocomplete.Select2QuerySetView):
    """User autocompletion widget view"""

    def get_queryset(self):
        """
        Get a User queryset for SODARUserAutocompleteWidget.

        Optional values in self.forwarded:
        - "project": project UUID
        - "scope": string for expected scope (all/project/project_exclude)
        - "exclude": list of explicit User.sodar_uuid to exclude from queryset

        """
        current_user = self.request.user
        project_uuid = self.forwarded.get('project', None)
        exclude_uuids = self.forwarded.get('exclude', None)
        scope = self.forwarded.get('scope', 'all')

        # If project UUID is given, only show users that are in the project
        if scope in ['project', 'project_exclude'] and project_uuid not in [
            '',
            None,
        ]:
            project = Project.objects.filter(sodar_uuid=project_uuid).first()

            # If user has no permission for the project, return None
            if not self.request.user.has_perm(
                'projectroles.view_project', project
            ):
                return User.objects.none()

            project_users = [a.user.pk for a in project.get_all_roles()]

            if scope == 'project':  # Limit choices to current project users
                qs = User.objects.filter(pk__in=project_users)

            elif scope == 'project_exclude':  # Exclude project users
                qs = User.objects.exclude(pk__in=project_users)

        # Else include all users
        else:
            qs = User.objects.all()

        # Exclude users in the system group unless local users are allowed
        allow_local = getattr(settings, 'PROJECTROLES_ALLOW_LOCAL_USERS', False)

        if not allow_local and not current_user.is_superuser:
            qs = qs.exclude(groups__name=SYSTEM_USER_GROUP).exclude(
                groups__isnull=True
            )

        # Exclude UUIDs explicitly given
        if exclude_uuids:
            qs = qs.exclude(sodar_uuid__in=exclude_uuids)

        # Finally, filter by query
        if self.q:
            qs = qs.filter(
                Q(username__icontains=self.q)
                | Q(first_name__icontains=self.q)
                | Q(last_name__icontains=self.q)
                | Q(name__icontains=self.q)
                | Q(email__icontains=self.q)
            )

        return qs.order_by('name')

    def get_result_label(self, user):
        """Display options with name, username and email address"""
        display = '{}{}{}'.format(
            user.name if user.name else '',
            ' ({})'.format(user.username) if user.name else user.username,
            ' <{}>'.format(user.email) if user.email else '',
        )
        return display

    def get_result_value(self, user):
        """Use sodar_uuid in the User model instead of pk"""
        return str(user.sodar_uuid)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        return super().get(request, *args, **kwargs)


class UserAutocompleteRedirectAjaxView(UserAutocompleteAjaxView):
    """
    SODARUserRedirectWidget view (user autocompletion) redirecting to
    the create invite page.
    """

    def get_create_option(self, context, q):
        """Form the correct email invite option to append to results"""
        create_option = []
        validator = EmailValidator()
        display_create_option = False

        if self.create_field and q:
            page_obj = context.get('page_obj', None)

            if page_obj is None or page_obj.number == 1:

                # Only create invite if the email address is valid
                try:
                    validator(q)
                    display_create_option = True

                except ValidationError:
                    display_create_option = False

                # Prevent sending a duplicate invite
                existing_options = (
                    self.get_result_label(result).lower()
                    for result in context['object_list']
                )

                if q.lower() in existing_options:
                    display_create_option = False

        if display_create_option:
            create_option = [
                {
                    'id': q,
                    'text': ('Send an invite to "%(new_value)s"')
                    % {'new_value': q},
                    'create_id': True,
                }
            ]
        return create_option

    def post(self, request):
        """Send the invite form url to which the forwarded values will be
        send"""
        project_uuid = self.request.POST.get('project', None)
        project = Project.objects.filter(sodar_uuid=project_uuid).first()
        # create JSON with address to redirect to
        redirect_url = reverse(
            'projectroles:invite_create', kwargs={'project': project.sodar_uuid}
        )
        return JsonResponse({'success': True, 'redirect_url': redirect_url})
