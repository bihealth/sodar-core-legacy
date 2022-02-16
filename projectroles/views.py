"""UI views for the projectroles app"""

import json
import logging
import re
import ssl
from ipaddress import ip_address, ip_network

import requests
from urllib.parse import unquote_plus
import urllib.request

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect
from django.urls import resolve, reverse, reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import (
    TemplateView,
    DetailView,
    UpdateView,
    CreateView,
    DeleteView,
    View,
)
from django.views.generic.edit import ModelFormMixin, FormView
from django.views.generic.detail import ContextMixin

from rules.contrib.views import PermissionRequiredMixin, redirect_to_login

from django.conf import settings
from projectroles import email
from projectroles.app_settings import AppSettingAPI
from projectroles.forms import (
    ProjectForm,
    RoleAssignmentForm,
    ProjectInviteForm,
    RemoteSiteForm,
    RoleAssignmentOwnerTransferForm,
    LocalUserForm,
)
from projectroles.models import (
    Project,
    Role,
    RoleAssignment,
    ProjectInvite,
    RemoteSite,
    RemoteProject,
    SODAR_CONSTANTS,
    PROJECT_TAG_STARRED,
)
from projectroles.plugins import (
    get_active_plugins,
    get_app_plugin,
    get_backend_api,
)
from projectroles.project_tags import get_tag_state, remove_tag
from projectroles.remote_projects import RemoteProjectAPI
from projectroles.utils import get_expiry_date, get_display_name


logger = logging.getLogger(__name__)


# Access Django user model
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

# Settings
SEND_EMAIL = settings.PROJECTROLES_SEND_EMAIL

# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
SUBMIT_STATUS_OK = SODAR_CONSTANTS['SUBMIT_STATUS_OK']
SUBMIT_STATUS_PENDING = SODAR_CONSTANTS['SUBMIT_STATUS_PENDING']
SUBMIT_STATUS_PENDING_TASKFLOW = SODAR_CONSTANTS[
    'SUBMIT_STATUS_PENDING_TASKFLOW'
]
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_PEER = SODAR_CONSTANTS['SITE_MODE_PEER']
REMOTE_LEVEL_NONE = SODAR_CONSTANTS['REMOTE_LEVEL_NONE']
REMOTE_LEVEL_VIEW_AVAIL = SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL']
REMOTE_LEVEL_READ_INFO = SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']

# Local constants
APP_NAME = 'projectroles'
KIOSK_MODE = getattr(settings, 'PROJECTROLES_KIOSK_MODE', False)
PROJECT_COLUMN_COUNT = 2  # Default columns
MSG_NO_AUTH = 'User not authorized for requested action'
MSG_NO_AUTH_LOGIN = MSG_NO_AUTH + ', please log in'
ALERT_MSG_ROLE_CREATE = 'Membership granted with the role of "{role}".'
ALERT_MSG_ROLE_UPDATE = 'Member role changed to "{role}".'


# Access Django user model
User = auth.get_user_model()

# App settings API
app_settings = AppSettingAPI()


# General mixins ---------------------------------------------------------------


class LoginRequiredMixin(AccessMixin):
    """
    Customized variant of the one from ``django.contrib.auth.mixins``.
    Allows disabling by overriding function ``is_login_required``.
    """

    def is_login_required(self):
        if getattr(settings, 'PROJECTROLES_KIOSK_MODE', False) or getattr(
            settings, 'PROJECTROLES_ALLOW_ANONYMOUS', False
        ):
            return False
        return True

    def dispatch(self, request, *args, **kwargs):
        if self.is_login_required() and not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class LoggedInPermissionMixin(PermissionRequiredMixin):
    """Mixin for handling redirection for both unlogged users and authenticated
    users without permissions"""

    def has_permission(self):
        """
        Override for this mixin also to work with admin users without a
        permission object.
        """
        if getattr(settings, 'PROJECTROLES_KIOSK_MODE', False):
            return True
        try:
            return super().has_permission()
        except AttributeError:
            if self.request.user.is_superuser:
                return True
        return False

    def handle_no_permission(self):
        """Override to redirect user"""
        if self.request.user.is_authenticated:
            messages.error(self.request, MSG_NO_AUTH)
            return redirect(reverse('home'))
        else:
            messages.error(self.request, MSG_NO_AUTH_LOGIN)
            return redirect_to_login(self.request.get_full_path())


class ProjectAccessMixin:
    """Mixin for providing access to a Project object from request kwargs"""

    #: The model class to use for projects.  You can override this to replace it
    #: with a proxy model, for example.
    project_class = Project

    def get_project(self, request=None, kwargs=None):
        """
        Return SODAR Project object based or None if not found, based on
        the current request and view kwargs. If arguments are not provided,
        uses self.request and/or self.kwargs.

        :param request: Request object (optional)
        :param kwargs: View kwargs (optional)
        :return: Object of project_class or None if not found
        """
        request = request or getattr(self, 'request')
        kwargs = kwargs or getattr(self, 'kwargs')
        # Ensure kwargs can be accessed
        if kwargs is None:
            raise ImproperlyConfigured('View kwargs are not accessible')

        # Project class object
        if 'project' in kwargs:
            return self.project_class.objects.filter(
                sodar_uuid=kwargs['project']
            ).first()

        # Other object types
        if not request:
            raise ImproperlyConfigured('Current HTTP request is not accessible')

        model = None
        uuid_kwarg = None

        for k, v in kwargs.items():
            if re.match(r'[0-9a-f-]+', v):
                try:
                    app_name = resolve(request.path).app_name
                    if app_name.find('.') != -1:
                        app_name = app_name.split('.')[0]
                    model = apps.get_model(app_name, k)
                    uuid_kwarg = k
                    break
                except LookupError:
                    pass

        if not model:
            return None

        try:
            obj = model.objects.get(sodar_uuid=kwargs[uuid_kwarg])
            if hasattr(obj, 'project'):
                return obj.project
            # Some objects may have a get_project() func instead of foreignkey
            elif hasattr(obj, 'get_project') and callable(
                getattr(obj, 'get_project', None)
            ):
                return obj.get_project()
        except model.DoesNotExist:
            return None


class ProjectPermissionMixin(PermissionRequiredMixin, ProjectAccessMixin):
    """Mixin for providing a Project object and queryset for permission
    checking"""

    def get_permission_object(self):
        return self.get_project()

    def has_permission(self):
        """Overrides for project permission access"""
        project = self.get_project()
        if not project:
            raise Http404

        # Override permissions for superuser, owner or delegate
        perm_override = (
            self.request.user.is_superuser
            or project.is_owner_or_delegate(self.request.user)
        )
        if not perm_override and app_settings.get_app_setting(
            'projectroles', 'ip_restrict', project
        ):
            for k in (
                'HTTP_X_FORWARDED_FOR',
                'X_FORWARDED_FOR',
                'FORWARDED',
                'REMOTE_ADDR',
            ):
                v = self.request.META.get(k)
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
                elif client_address == ip_address(record):
                    break
            else:
                return False

        # Disable project app access for categories unless specifically enabled
        if project.type == PROJECT_TYPE_CATEGORY:
            request_url = resolve(self.request.get_full_path())
            if request_url.app_name != APP_NAME:
                app_plugin = get_app_plugin(request_url.app_name)
                if app_plugin and app_plugin.category_enable:
                    return True
                return False

        # Disable access for non-owner/delegate if remote project is revoked
        if project.is_revoked() and not perm_override:
            return False

        return super().has_permission()

    def get_queryset(self, *args, **kwargs):
        """Override ``get_queryset()`` to filter down to the currently selected
        object."""
        qs = super().get_queryset(*args, **kwargs)
        if qs.model == ProjectAccessMixin.project_class:
            return qs
        elif hasattr(qs.model, 'get_project_filter_key'):
            return qs.filter(
                **{qs.model.get_project_filter_key(): self.get_project()}
            )
        elif hasattr(qs.model, 'project') or hasattr(qs.model, 'get_project'):
            return qs.filter(project=self.get_project())
        else:
            raise AttributeError(
                'Model does not have "project" member, get_project() function '
                'or "get_project_filter_key()" function'
            )


class ProjectModifyPermissionMixin(
    LoggedInPermissionMixin, ProjectPermissionMixin
):
    """Mixin for handling access to project modifying views, denying access even
    for local superusers if the project is remote and thus immutable"""

    def has_permission(self):
        """Override has_permission() to check remote project status"""
        perm = super().has_permission()
        project = self.get_project()
        return (
            False
            if project.is_remote() and not self._get_allow_remote_edit()
            else perm
        )

    def _get_allow_remote_edit(self):
        return getattr(self, 'allow_remote_edit', False)

    def handle_no_permission(self):
        """Override handle_no_permission to redirect user"""
        project = self.get_project()
        if project and project.is_remote():
            messages.error(
                self.request,
                'Modifications are not allowed for remote {}'.format(
                    get_display_name(PROJECT_TYPE_PROJECT, plural=True)
                ),
            )
            return redirect(reverse('home'))
        elif self.request.user.is_authenticated:
            messages.error(self.request, MSG_NO_AUTH)
            return redirect(reverse('home'))
        else:
            messages.error(self.request, MSG_NO_AUTH_LOGIN)
            return redirect_to_login(self.request.get_full_path())


class RolePermissionMixin(ProjectModifyPermissionMixin):
    """Mixin to ensure permissions for RoleAssignment according to user role in
    project"""

    def has_permission(self):
        """Override has_permission to check perms depending on role"""
        if not super().has_permission():
            return False
        try:
            obj = RoleAssignment.objects.get(
                sodar_uuid=self.kwargs['roleassignment']
            )
            if obj.role.name == PROJECT_ROLE_OWNER:
                return False
            elif obj.role.name == PROJECT_ROLE_DELEGATE:
                return self.request.user.has_perm(
                    'projectroles.update_project_delegate',
                    self.get_permission_object(),
                )
            else:
                return self.request.user.has_perm(
                    'projectroles.update_project_members',
                    self.get_permission_object(),
                )
        except RoleAssignment.DoesNotExist:
            return False

    def get_permission_object(self):
        """Override get_permission_object for checking Project permission"""
        return self.get_project()


class HTTPRefererMixin:
    """Mixin for updating a correct referer url in session cookie regardless of
    page reload"""

    def get(self, request, *args, **kwargs):
        if 'HTTP_REFERER' in request.META:
            referer = request.META['HTTP_REFERER']
            if (
                'real_referer' not in request.session
                or referer != request.build_absolute_uri()
            ):
                request.session['real_referer'] = referer
        return super().get(request, *args, **kwargs)


class PluginContextMixin(ContextMixin):
    """Mixin for adding plugin list to context data"""

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['app_plugins'] = get_active_plugins(
            plugin_type='project_app', custom_order=True
        )
        return context


class ProjectContextMixin(
    HTTPRefererMixin, PluginContextMixin, ProjectAccessMixin
):
    """Mixin for adding context data to Project base view and other views
    extending it. Includes HTTPRefererMixin for correct referer URL"""

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # Project
        if hasattr(self, 'object') and isinstance(self.object, Project):
            context['project'] = self.get_object()
        elif hasattr(self, 'object') and hasattr(self.object, 'project'):
            context['project'] = self.object.project
        else:
            context['project'] = self.get_project()

        # Project tagging/starring
        if 'project' in context and not KIOSK_MODE:
            context['project_starred'] = get_tag_state(
                context['project'], self.request.user, PROJECT_TAG_STARRED
            )

        return context


class ProjectListContextMixin:
    """Mixin for adding context data for displaying the project list."""

    def _get_custom_cols(self, user):
        """
        Return list of custom columns for projects including project data.

        :param user: User object
        """
        i = 0
        cols = []
        for app_plugin in [
            ap
            for ap in get_active_plugins(plugin_type='project_app')
            if ap.project_list_columns
        ]:
            # HACK for filesfolders columns (see issues #737 and #738)
            if app_plugin.name == 'filesfolders' and not getattr(
                settings, 'FILESFOLDERS_SHOW_LIST_COLUMNS', False
            ):
                continue
            for k, v in app_plugin.project_list_columns.items():
                if not v['active']:
                    continue
                v['app_plugin'] = app_plugin
                v['column_id'] = k
                v['ordering'] = v.get('ordering') or i
                cols.append(v)
                i += 1
        return sorted(cols, key=lambda x: x['ordering'])

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['project_custom_cols'] = self._get_custom_cols(
            self.request.user
        )
        context['project_col_count'] = PROJECT_COLUMN_COUNT + len(
            context['project_custom_cols']
        )
        return context


class CurrentUserFormMixin:
    """Mixin for passing current user to form as current_user"""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'current_user': self.request.user})
        return kwargs


# Base Project Views -----------------------------------------------------------


class HomeView(
    LoginRequiredMixin,
    PluginContextMixin,
    ProjectListContextMixin,
    TemplateView,
):
    """Home view"""

    template_name = 'projectroles/home.html'


class ProjectDetailView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectListContextMixin,
    ProjectContextMixin,
    DetailView,
):
    """Project details view"""

    permission_required = 'projectroles.view_project'
    model = Project
    slug_url_kwarg = 'project'
    slug_field = 'sodar_uuid'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.request.user.is_superuser:
            context['role'] = None
        elif self.request.user.is_authenticated:
            try:
                role_as = RoleAssignment.objects.get(
                    user=self.request.user, project=self.object
                )
                context['role'] = role_as.role
            except RoleAssignment.DoesNotExist:
                context['role'] = None
        elif self.object.public_guest_access:
            context['role'] = Role.objects.filter(
                name=PROJECT_ROLE_GUEST
            ).first()
        else:
            context['role'] = None

        if settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE:
            context['target_projects'] = RemoteProject.objects.filter(
                project_uuid=self.object.sodar_uuid, site__mode=SITE_MODE_TARGET
            ).order_by('site__name')
        elif settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET:
            context['peer_projects'] = RemoteProject.objects.filter(
                project_uuid=self.object.sodar_uuid, site__mode=SITE_MODE_PEER
            ).order_by('site__name')

        return context


class ProjectSearchMixin:
    """Common functionalities for search views"""

    def get(self, request, *args, **kwargs):
        if not getattr(settings, 'PROJECTROLES_ENABLE_SEARCH', False):
            messages.error(request, 'Search not enabled')
            return redirect('home')
        context = self.get_context_data(*args, **kwargs)
        return super().render_to_response(context)


class ProjectSearchResultsView(
    LoginRequiredMixin, ProjectSearchMixin, TemplateView
):
    """View for displaying results of search within projects"""

    template_name = 'projectroles/search_results.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        plugins = get_active_plugins(plugin_type='project_app')
        search_terms = []
        search_type = None
        keyword_input = []
        search_keywords = {}

        if self.request.GET.get('m'):  # Multi search
            search_terms = [
                t.strip()
                for t in self.request.GET['m'].strip().split('\r\n')
                if len(t.strip()) >= 3
            ]
            if self.request.GET.get('k'):
                keyword_input = self.request.GET['k'].strip().split(' ')
            search_input = ''  # Clears input for basic search

        else:  # Single term search
            search_input = self.request.GET.get('s').strip()
            search_split = search_input.split(' ')
            search_term = search_split[0].strip()
            for i in range(1, len(search_split)):
                s = search_split[i].strip()
                if ':' in s:
                    keyword_input.append(s)
                elif s != '':
                    search_term += ' ' + s.lower()
            if search_term:
                search_terms = [search_term]

        for s in keyword_input:
            kw = s.split(':')[0].lower().strip()
            val = s.split(':')[1].lower().strip()
            if kw == 'type':
                search_type = val
            else:
                search_keywords[kw] = val

        context['search_input'] = search_input
        context['search_terms'] = search_terms
        context['search_type'] = search_type
        context['search_keywords'] = search_keywords

        # Get project results
        if not search_type or search_type == 'project':
            context['project_results'] = [
                p
                for p in Project.objects.find(
                    search_terms, project_type='PROJECT'
                )
                if self.request.user.has_perm('projectroles.view_project', p)
            ]

        # Get app results
        if search_type:
            search_apps = sorted(
                [
                    p
                    for p in plugins
                    if (p.search_enable and search_type in p.search_types)
                ],
                key=lambda x: x.plugin_ordering,
            )
        else:
            search_apps = sorted(
                [p for p in plugins if p.search_enable],
                key=lambda x: x.plugin_ordering,
            )

        context['app_search_data'] = []

        for plugin in search_apps:
            search_kwargs = {
                'user': self.request.user,
                'search_type': search_type,
                'search_terms': search_terms,
                'keywords': search_keywords,
            }
            search_res = {'plugin': plugin, 'results': None, 'error': None}
            try:
                search_res['results'] = plugin.search(**search_kwargs)
            except Exception as ex:
                if settings.DEBUG:
                    raise ex
                search_res['error'] = str(ex)
                logger.error(
                    'Exception raised by search() in {}: "{}" ({})'.format(
                        plugin.name,
                        ex,
                        '; '.join(
                            [
                                '{}={}'.format(k, v)
                                for k, v in search_kwargs.items()
                            ]
                        ),
                    )
                )
            context['app_search_data'].append(search_res)

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)
        if not context['search_terms']:
            messages.error(request, 'No search terms provided.')
            return redirect(reverse('home'))
        return super().get(request, *args, **kwargs)


class ProjectAdvancedSearchView(
    LoginRequiredMixin, ProjectSearchMixin, TemplateView
):
    """View for displaying advanced search form"""

    template_name = 'projectroles/search_advanced.html'


# Project Editing Views --------------------------------------------------------


class ProjectModifyMixin:
    """Mixin for Project creation/updating in UI and API views"""

    @staticmethod
    def _get_old_project_data(project):
        return {
            'title': project.title,
            'parent': project.parent,
            'description': project.description,
            'readme': project.readme.raw,
            'owner': project.get_owner().user,
            'public_guest_access': project.public_guest_access,
        }

    @staticmethod
    def _get_app_settings(data, instance):
        """
        Return a dictionary of project app settings and their values.

        :param data: Cleaned data from a form or serializer
        :param instance: Existing Project object or None
        :return: Dict
        """
        app_plugins = [p for p in get_active_plugins() if p.app_settings]
        project_settings = {}

        for plugin in app_plugins + [None]:
            if plugin:
                name = plugin.name
                p_settings = app_settings.get_setting_defs(
                    APP_SETTING_SCOPE_PROJECT, plugin=plugin
                )
            else:
                name = 'projectroles'
                p_settings = app_settings.get_setting_defs(
                    APP_SETTING_SCOPE_PROJECT, app_name=name
                )

            for s_key, s_val in p_settings.items():
                s_name = 'settings.{}.{}'.format(name, s_key)
                s_data = data.get(s_name)

                if s_data is None and not instance:
                    s_data = app_settings.get_default_setting(name, s_key)

                if s_val['type'] == 'JSON':
                    if s_data is None:
                        s_data = {}

                    project_settings[s_name] = json.dumps(s_data)

                elif s_data is not None:
                    project_settings[s_name] = s_data

        return project_settings

    @staticmethod
    def _get_project_update_data(old_data, project, owner, project_settings):
        extra_data = {}
        upd_fields = []

        if old_data['title'] != project.title:
            extra_data['title'] = project.title
            upd_fields.append('title')

        if old_data['parent'] != project.parent:
            extra_data['parent'] = (
                str(project.parent.sodar_uuid) if project.parent else None
            )
            upd_fields.append('parent')

        if old_data['owner'] != owner:
            extra_data['owner'] = owner.username
            upd_fields.append('owner')

        if old_data['description'] != project.description:
            extra_data['description'] = project.description
            upd_fields.append('description')

        if old_data['readme'] != project.readme.raw:
            extra_data['readme'] = project.readme.raw
            upd_fields.append('readme')

        if old_data['public_guest_access'] != project.public_guest_access:
            extra_data['public_guest_access'] = project.public_guest_access
            upd_fields.append('public_guest_access')

        # Settings
        for k, v in project_settings.items():
            a_name = k.split('.')[1]
            s_name = k.split('.')[2]
            s_def = app_settings.get_setting_def(s_name, app_name=a_name)
            old_v = app_settings.get_app_setting(a_name, s_name, project)

            if s_def['type'] == 'JSON':
                v = json.loads(v)

            if old_v != v:
                extra_data[k] = v
                upd_fields.append(k)

        return extra_data, upd_fields

    @classmethod
    def _create_timeline_event(
        cls, project, action, owner, old_data, project_settings, request
    ):
        timeline = get_backend_api('timeline_backend')

        if not timeline:
            return None

        type_str = project.type.capitalize()

        if action == 'create':
            tl_desc = 'create ' + type_str.lower() + ' with {owner} as owner'
            extra_data = {
                'title': project.title,
                'owner': owner.username,
                'description': project.description,
                'readme': project.readme.raw,
            }

            # Add settings to extra data
            for k, v in project_settings.items():
                a_name = k.split('.')[1]
                s_name = k.split('.')[2]
                s_def = app_settings.get_setting_def(s_name, app_name=a_name)

                if s_def['type'] == 'JSON':
                    v = json.loads(v)

                extra_data[k] = v

        else:  # Update
            tl_desc = 'update ' + type_str.lower()
            extra_data, upd_fields = cls._get_project_update_data(
                old_data, project, owner, project_settings
            )

            if len(upd_fields) > 0:
                tl_desc += ' (' + ', '.join(x for x in upd_fields) + ')'

        tl_event = timeline.add_event(
            project=project,
            app_name=APP_NAME,
            user=request.user,
            event_name='project_{}'.format(action),
            description=tl_desc,
            extra_data=extra_data,
        )

        if action == 'create':
            tl_event.add_object(owner, 'owner', owner.username)

        return tl_event

    @classmethod
    def _submit_with_taskflow(
        cls,
        project,
        owner,
        project_settings,
        action,
        request,
        old_parent=None,
        tl_event=None,
    ):
        """
        Submit project modification flow via SODAR Taskflow.

        :param project: Project object
        :param owner: User object of project owner
        :param project_settings: Dict
        :param action: "create" or "update" (string)
        :param request: Request object for triggering the update
        :param old_parent: Project object of old parent if it was changed
        :param tl_event: Timeline ProjectEvent object or None
        :raise: ConnectionError if unable to connect to SODAR Taskflow
        :raise: FlowSubmitException if SODAR Taskflow submission fails
        """
        taskflow = get_backend_api('taskflow')

        if tl_event:
            tl_event.set_status('SUBMIT')

        flow_data = {
            'project_title': project.title,
            'project_description': project.description,
            'parent_uuid': str(project.parent.sodar_uuid)
            if project.parent
            else '',
            'public_guest_access': project.public_guest_access,
            'owner_username': owner.username,
            'owner_uuid': str(owner.sodar_uuid),
            'owner_role_pk': Role.objects.get(name=PROJECT_ROLE_OWNER).pk,
            'settings': project_settings,
        }

        if action == 'update':
            old_owner = project.get_owner().user
            flow_data['old_owner_uuid'] = str(old_owner.sodar_uuid)
            flow_data['old_owner_username'] = old_owner.username
            flow_data['project_readme'] = project.readme.raw

            if old_parent:
                # Get inherited owners for project and its children to add
                new_roles = taskflow.get_inherited_users(project)
                flow_data['roles_add'] = new_roles
                new_users = set([r['username'] for r in new_roles])

                # Get old inherited owners from previous parent to remove
                old_roles = taskflow.get_inherited_users(old_parent)
                flow_data['roles_delete'] = [
                    r for r in old_roles if r['username'] not in new_users
                ]

        else:  # Create
            flow_data['roles_add'] = [
                {
                    'project_uuid': str(project.sodar_uuid),
                    'username': a.user.username,
                }
                for a in project.get_owners(inherited_only=True)
            ]

        try:
            taskflow.submit(
                project_uuid=str(project.sodar_uuid),
                flow_name='project_{}'.format(action),
                flow_data=flow_data,
                request=request,
            )

        except (
            requests.exceptions.ConnectionError,
            taskflow.FlowSubmitException,
        ) as ex:
            # NOTE: No need to update status as project will be deleted
            if action == 'create':
                project.delete()

            elif tl_event:  # Update
                tl_event.set_status('FAILED', str(ex))

            raise ex

    @classmethod
    def _handle_local_save(cls, project, owner, project_settings):
        """
        Handle local saving of project data if SODAR Taskflow is not
        enabled.
        """

        # Modify owner role if it does exist
        try:
            assignment = RoleAssignment.objects.get(
                project=project, role__name=PROJECT_ROLE_OWNER
            )
            assignment.user = owner
            assignment.save()

        # Else create a new one
        except RoleAssignment.DoesNotExist:
            assignment = RoleAssignment(
                project=project,
                user=owner,
                role=Role.objects.get(name=PROJECT_ROLE_OWNER),
            )
            assignment.save()

        # Modify settings
        for k, v in project_settings.items():
            app_settings.set_app_setting(
                app_name=k.split('.')[1],
                setting_name=k.split('.')[2],
                value=v,
                project=project,
                validate=False,
            )  # Already validated in form

    @classmethod
    def _notify_users(
        cls, project, action, owner, old_data, old_parent, request
    ):
        """
        Notify users about project creation and update. Displays app alerts
        and/or sends emails depending on the site configuration.
        """
        app_alerts = get_backend_api('appalerts_backend')
        # Create alerts and send emails
        owner_as = RoleAssignment.objects.get_assignment(owner, project)
        # Owner change notification
        if request.user != owner and (
            action == 'create' or old_data['owner'] != owner
        ):
            if app_alerts:
                app_alerts.add_alert(
                    app_name=APP_NAME,
                    alert_name='role_create',
                    user=owner,
                    message=ALERT_MSG_ROLE_CREATE.format(
                        project=project.title, role=owner_as.role.name
                    ),
                    url=reverse(
                        'projectroles:detail',
                        kwargs={'project': project.sodar_uuid},
                    ),
                    project=project,
                )
            if SEND_EMAIL:
                email.send_role_change_mail(
                    action,
                    project,
                    owner,
                    owner_as.role,
                    request,
                )
        # Project creation/moving for parent category owner
        if (
            project.parent
            and project.parent.get_owner().user != owner_as.user
            and project.parent.get_owner().user != request.user
        ):
            parent_owner = project.parent.get_owner().user
            if action == 'create' and request.user != parent_owner:
                if app_alerts:
                    app_alerts.add_alert(
                        app_name=APP_NAME,
                        alert_name='project_create_parent',
                        user=parent_owner,
                        message='New {} created under category '
                        '"{}": "{}".'.format(
                            project.type.lower(),
                            project.parent.title,
                            project.title,
                        ),
                        url=reverse(
                            'projectroles:detail',
                            kwargs={'project': project.sodar_uuid},
                        ),
                        project=project,
                    )
                if SEND_EMAIL:
                    email.send_project_create_mail(project, request)

            elif old_parent and request.user != parent_owner:
                app_alerts.add_alert(
                    app_name=APP_NAME,
                    alert_name='project_move_parent',
                    user=parent_owner,
                    message='{} moved under category '
                    '"{}": "{}".'.format(
                        project.type.capitalize(),
                        project.parent.title,
                        project.title,
                    ),
                    url=reverse(
                        'projectroles:detail',
                        kwargs={'project': project.sodar_uuid},
                    ),
                    project=project,
                )
                if SEND_EMAIL:
                    email.send_project_move_mail(project, request)

    def modify_project(self, data, request, instance=None):
        """
        Create or update a Project, either locally or using the SODAR Taskflow.
        This method should be called either in form_valid() in a Django form
        view or save() in a DRF serializer.

        :param data: Cleaned data from a form or serializer
        :param request: Request initiating the action
        :param instance: Existing Project object or None
        :raise: ConnectionError if unable to connect to SODAR Taskflow
        :raise: FlowSubmitException if SODAR Taskflow submission fails
        :return: Created or updated Project object
        """
        taskflow = get_backend_api('taskflow')
        action = 'update' if instance else 'create'
        old_data = {}
        old_project = None

        if instance:
            project = instance
            # In case of a PATCH request, get existing obj to fill out fields
            old_project = Project.objects.get(sodar_uuid=instance.sodar_uuid)
            old_data = self._get_old_project_data(old_project)  # Store old data

            project.title = data.get('title') or old_project.title
            project.description = (
                data.get('description') or old_project.description
            )
            project.type = data.get('type') or old_project.type
            project.readme = data.get('readme') or old_project.readme
            # NOTE: Must do this as parent can exist but be None
            project.parent = (
                data['parent'] if 'parent' in data else old_project.parent
            )
            project.public_guest_access = (
                data.get('public_guest_access') or False
            )
        else:
            project = Project(
                title=data.get('title'),
                description=data.get('description'),
                type=data.get('type'),
                readme=data.get('readme'),
                parent=data.get('parent'),
                public_guest_access=data.get('public_guest_access') or False,
            )

        use_taskflow = (
            True
            if taskflow and data.get('type') == PROJECT_TYPE_PROJECT
            else False
        )

        if action == 'create':
            project.submit_status = (
                SUBMIT_STATUS_PENDING_TASKFLOW
                if use_taskflow
                else SUBMIT_STATUS_PENDING
            )
            # HACK to avoid db error when running tests with DRF serializer
            # See: https://stackoverflow.com/a/60331668
            with transaction.atomic():
                project.save()  # Always save locally if creating (to get UUID)
        else:
            project.submit_status = SUBMIT_STATUS_OK

        # Save project with changes if updating without taskflow
        if action == 'update' and not use_taskflow:
            project.save()

        owner = data.get('owner')
        if not owner and old_project:  # In case of a PATCH request
            owner = old_project.get_owner().user
        # Get settings
        project_settings = self._get_app_settings(data, instance)
        # Create timeline event
        tl_event = self._create_timeline_event(
            project, action, owner, old_data, project_settings, request
        )

        # Get old parent for project moving
        old_parent = (
            old_project.parent
            if old_project
            and old_project.parent
            and old_project.parent != project.parent
            else None
        )

        # Submit with Taskflow if enabled
        # NOTE: may raise an exception which needs to be handled in caller
        if use_taskflow:
            self._submit_with_taskflow(
                project,
                owner,
                project_settings,
                action,
                request,
                old_parent,
                tl_event,
            )
        # Local save without Taskflow
        else:
            self._handle_local_save(project, owner, project_settings)

        # Post submit/save
        if action == 'create' and project.submit_status != SUBMIT_STATUS_OK:
            project.submit_status = SUBMIT_STATUS_OK
            project.save()

        # Call for additional actions for project update in plugins
        # NOTE: This is a WIP feature to be altered/expanded in a later release
        app_plugins = get_active_plugins(plugin_type='project_app')
        for p in app_plugins:
            try:
                p.handle_project_update(project, old_data)
            except Exception as ex:
                logger.error(
                    'Exception when calling handle_project_update() for app '
                    'plugin "{}": {}'.format(p.name, ex)
                )

        # If public access was updated, update has_public_children for parents
        if (
            old_project
            and project.parent
            and old_project.public_guest_access != project.public_guest_access
        ):
            try:
                project._update_public_children()
            except Exception as ex:
                logger.error(
                    'Exception in updating has_public_children: {}'.format(ex)
                )

        # Once all is done, update timeline event, create alerts and emails
        if tl_event:
            tl_event.set_status('OK')
        self._notify_users(
            project, action, owner, old_data, old_parent, request
        )
        return project


class ProjectModifyFormMixin(ProjectModifyMixin):
    """Mixin for Project creation/updating in Django form views"""

    def form_valid(self, form):
        """Handle project updating if form is valid"""
        instance = form.instance if form.instance.pk else None
        action = 'update' if instance else 'create'

        if instance and instance.parent:
            redirect_url = reverse(
                'projectroles:detail',
                kwargs={'project': instance.parent.sodar_uuid},
            )

        else:
            redirect_url = reverse('home')

        try:
            project = self.modify_project(
                data=form.cleaned_data,
                request=self.request,
                instance=form.instance if instance else None,
            )
            messages.success(
                self.request, '{} {}d'.format(project.type.capitalize(), action)
            )
            redirect_url = reverse(
                'projectroles:detail', kwargs={'project': project.sodar_uuid}
            )

        except Exception as ex:
            messages.error(
                self.request,
                'Unable to {} {}: {}'.format(
                    action, form.cleaned_data['type'].lower(), ex
                ),
            )

            if settings.DEBUG:
                raise ex

        return redirect(redirect_url)


class ProjectCreateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectModifyFormMixin,
    ProjectContextMixin,
    HTTPRefererMixin,
    CurrentUserFormMixin,
    CreateView,
):
    """Project creation view"""

    permission_required = 'projectroles.create_project'
    model = Project
    form_class = ProjectForm

    def has_permission(self):
        """
        Override has_permission() to ensure even superuser can't create
        project under a remote category as target
        """
        if not self.kwargs.get('project'):
            if self.request.user.is_superuser:
                return True  # Allow top level project creation for superuser
            return False  # Disallow for other users
        elif (
            settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET
            and self.kwargs.get('project')
        ):
            parent = Project.objects.filter(
                sodar_uuid=self.kwargs['project']
            ).first()
            if parent and parent.is_remote():
                return False
        return super().has_permission()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if 'project' in self.kwargs:
            context['parent'] = Project.objects.get(
                sodar_uuid=self.kwargs['project']
            )
        return context

    def get_form_kwargs(self):
        """Pass URL arguments to form"""
        kwargs = super().get_form_kwargs()
        kwargs.update(self.kwargs)
        return kwargs

    def get(self, request, *args, **kwargs):
        """Override get() to limit project creation under other projects"""

        # If site is in target mode and target creation is not allowed, redirect
        if (
            settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET
            and not settings.PROJECTROLES_TARGET_CREATE
        ):
            messages.error(
                request,
                'Creating local {} not allowed'.format(
                    get_display_name(PROJECT_TYPE_PROJECT, plural=True)
                ),
            )
            return redirect(reverse('home'))

        if 'project' in self.kwargs:
            project = Project.objects.get(sodar_uuid=self.kwargs['project'])

            if project.type != PROJECT_TYPE_CATEGORY:
                messages.error(
                    self.request,
                    'Creating nested {} is not allowed'.format(
                        get_display_name(PROJECT_TYPE_PROJECT, plural=True)
                    ),
                )
                return redirect(
                    reverse(
                        'projectroles:detail',
                        kwargs={'project': project.sodar_uuid},
                    )
                )

        return super().get(request, *args, **kwargs)


class ProjectUpdateView(
    LoginRequiredMixin,
    ProjectModifyPermissionMixin,
    ProjectContextMixin,
    ProjectModifyFormMixin,
    CurrentUserFormMixin,
    UpdateView,
):
    """Project updating view"""

    permission_required = 'projectroles.update_project'
    model = Project
    form_class = ProjectForm
    slug_url_kwarg = 'project'
    slug_field = 'sodar_uuid'
    allow_remote_edit = True


# RoleAssignment Views ---------------------------------------------------------


class ProjectRoleView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    TemplateView,
):
    """View for displaying project roles"""

    permission_required = 'projectroles.view_project_roles'
    template_name = 'projectroles/project_roles.html'
    model = Project

    def get_context_data(self, *args, **kwargs):
        project = self.get_project()
        context = super().get_context_data(*args, **kwargs)
        context['owner'] = project.get_owner()
        inherited_owners = project.get_owners(inherited_only=True)
        context['inherited_owners'] = [
            a for a in inherited_owners if a.user != context['owner'].user
        ]
        inherited_users = [a.user for a in inherited_owners]
        context['delegates'] = [
            a for a in project.get_delegates() if a.user not in inherited_users
        ]
        context['members'] = [
            a for a in project.get_members() if a.user not in inherited_users
        ]

        if project.is_remote():
            context[
                'remote_roles_url'
            ] = project.get_source_site().url + reverse(
                'projectroles:roles', kwargs={'project': project.sodar_uuid}
            )

        return context


class RoleAssignmentModifyMixin:
    """Mixin for RoleAssignment creation/updating in UI and API views"""

    def modify_assignment(
        self, data, request, project, instance=None, sodar_url=None
    ):
        """
        Create or update a RoleAssignment, either locally or using the SODAR
        Taskflow. This method should be called either in form_valid() in a
        Django form view or save() in a DRF serializer.

        :param data: Cleaned data from a form or serializer
        :param request: Request initiating the action
        :param project: Project object
        :param instance: Existing RoleAssignment object or None
        :param sodar_url: SODAR callback URL for taskflow (string, optional)
        :raise: ConnectionError if unable to connect to SODAR Taskflow
        :raise: FlowSubmitException if SODAR Taskflow submission fails
        :return: Created or updated RoleAssignment object
        """
        timeline = get_backend_api('timeline_backend')
        taskflow = get_backend_api('taskflow')
        app_alerts = get_backend_api('appalerts_backend')
        action = 'update' if instance else 'create'
        tl_event = None
        user = data.get('user')
        role = data.get('role')
        use_taskflow = taskflow.use_taskflow(project) if taskflow else False

        # Init Timeline event
        if timeline:
            tl_desc = '{} role {}"{}" for {{{}}}'.format(
                action, 'to ' if action == 'update' else '', role.name, 'user'
            )
            tl_event = timeline.add_event(
                project=project,
                app_name=APP_NAME,
                user=request.user,
                event_name='role_{}'.format(action),
                description=tl_desc,
            )
            tl_event.add_object(user, 'user', user.username)

        # Submit with taskflow
        if use_taskflow:
            if tl_event:
                tl_event.set_status('SUBMIT')
            flow_data = {
                'username': user.username,
                'user_uuid': str(user.sodar_uuid),
                'role_pk': role.pk,
            }

            try:
                taskflow.submit(
                    project_uuid=project.sodar_uuid,
                    flow_name='role_update',
                    flow_data=flow_data,
                    request=request,
                    sodar_url=sodar_url,
                )
            except taskflow.FlowSubmitException as ex:
                if tl_event:
                    tl_event.set_status('FAILED', str(ex))
                raise ex

            # Get object
            role_as = RoleAssignment.objects.get(project=project, user=user)

        # Local save without Taskflow
        elif action == 'create':
            role_as = RoleAssignment(project=project, user=user, role=role)

        else:
            role_as = RoleAssignment.objects.get(project=project, user=user)
            role_as.role = role

        role_as.save()

        if tl_event:
            tl_event.set_status('OK')

        if request.user != user:
            if app_alerts:
                if action == 'create':
                    alert_msg = ALERT_MSG_ROLE_CREATE
                else:  # Update
                    alert_msg = ALERT_MSG_ROLE_UPDATE
                app_alerts.add_alert(
                    app_name=APP_NAME,
                    alert_name='role_' + action,
                    user=user,
                    message=alert_msg.format(
                        project=project.title, role=role.name
                    ),
                    url=reverse(
                        'projectroles:detail',
                        kwargs={'project': project.sodar_uuid},
                    ),
                    project=project,
                )
            if SEND_EMAIL:
                email.send_role_change_mail(
                    action, project, user, role, request
                )

        return role_as


class RoleAssignmentModifyFormMixin(RoleAssignmentModifyMixin, ModelFormMixin):
    """Mixin for RoleAssignment creation and updating in Django form views"""

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        change_type = self.request.resolver_match.url_name.split('_')[1]
        project = self.get_project()

        if change_type != 'delete':
            context['preview_subject'] = email.get_role_change_subject(
                change_type, project
            )
            context['preview_body'] = email.get_role_change_body(
                change_type=change_type,
                project=project,
                user_name='{user_name}',
                issuer=self.request.user,
                role_name='{role_name}',
                project_url=self.request.build_absolute_uri(
                    reverse(
                        'projectroles:detail',
                        kwargs={'project': project.sodar_uuid},
                    )
                ),
            ).replace('\n', '\\n')

        return context

    def form_valid(self, form):
        """Handle RoleAssignment updating if form is valid"""
        instance = form.instance if form.instance.pk else None
        action = 'update' if instance else 'create'
        project = self.get_project()

        try:
            self.object = self.modify_assignment(
                data=form.cleaned_data,
                request=self.request,
                project=project,
                instance=form.instance if instance else None,
            )
            messages.success(
                self.request,
                'Membership {} for {} with the role of {}.'.format(
                    'added' if action == 'create' else 'updated',
                    self.object.user.username,
                    self.object.role.name,
                ),
            )

        except Exception as ex:
            messages.error(
                self.request, 'Membership updating failed: {}'.format(ex)
            )

        return redirect(
            reverse(
                'projectroles:roles',
                kwargs={'project': project.sodar_uuid},
            )
        )


class RoleAssignmentDeleteMixin:
    """Mixin for RoleAssignment deletion/destroying in UI and API views"""

    def delete_assignment(self, request, instance):
        timeline = get_backend_api('timeline_backend')
        taskflow = get_backend_api('taskflow')
        app_alerts = get_backend_api('appalerts_backend')
        tl_event = None
        project = instance.project
        user = instance.user
        role = instance.role
        use_taskflow = taskflow.use_taskflow(project) if taskflow else False

        # Init Timeline event
        if timeline:
            tl_event = timeline.add_event(
                project=project,
                app_name=APP_NAME,
                user=request.user,
                event_name='role_delete',
                description='delete role "{}" from {{{}}}'.format(
                    role.name, 'user'
                ),
            )
            tl_event.add_object(user, 'user', user.username)

        # Submit with taskflow
        if use_taskflow:
            if tl_event:
                tl_event.set_status('SUBMIT')
            flow_data = {
                'username': user.username,
                'user_uuid': str(user.sodar_uuid),
                'role_pk': role.pk,
            }
            try:
                taskflow.submit(
                    project_uuid=project.sodar_uuid,
                    flow_name='role_delete',
                    flow_data=flow_data,
                    request=request,
                )
                instance = None
            except taskflow.FlowSubmitException as ex:
                if tl_event:
                    tl_event.set_status('FAILED', str(ex))
                raise ex

        # Local save without Taskflow
        else:
            instance.delete()

        # Remove project star from user if it exists
        remove_tag(project=project, user=user)

        if tl_event:
            tl_event.set_status('OK')
        if app_alerts:
            app_alerts.add_alert(
                app_name=APP_NAME,
                alert_name='role_delete',
                user=user,
                message='Your membership in this {} has been removed.'.format(
                    get_display_name(project.type)
                ),
                project=project,
            )
        if SEND_EMAIL:
            email.send_role_change_mail('delete', project, user, None, request)

        return instance


class RoleAssignmentCreateView(
    LoginRequiredMixin,
    ProjectModifyPermissionMixin,
    ProjectContextMixin,
    CurrentUserFormMixin,
    RoleAssignmentModifyFormMixin,
    CreateView,
):
    """RoleAssignment creation view"""

    permission_required = 'projectroles.update_project_members'
    model = RoleAssignment
    form_class = RoleAssignmentForm

    def get_form_kwargs(self):
        """Pass URL arguments and current user to form"""
        kwargs = super().get_form_kwargs()
        kwargs.update(self.kwargs)
        return kwargs


class RoleAssignmentUpdateView(
    LoginRequiredMixin,
    RolePermissionMixin,
    ProjectContextMixin,
    RoleAssignmentModifyFormMixin,
    CurrentUserFormMixin,
    UpdateView,
):
    """RoleAssignment updating view"""

    permission_required = 'projectroles.update_project_members'
    model = RoleAssignment
    form_class = RoleAssignmentForm
    slug_url_kwarg = 'roleassignment'
    slug_field = 'sodar_uuid'


class RoleAssignmentDeleteView(
    LoginRequiredMixin,
    RolePermissionMixin,
    ProjectModifyPermissionMixin,
    ProjectContextMixin,
    CurrentUserFormMixin,
    RoleAssignmentDeleteMixin,
    DeleteView,
):
    """RoleAssignment deletion view"""

    permission_required = 'projectroles.update_project_members'
    model = RoleAssignment
    slug_url_kwarg = 'roleassignment'
    slug_field = 'sodar_uuid'

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        user = self.object.user
        project = self.object.project

        # Override perms for owner/delegate
        if self.object.role.name == PROJECT_ROLE_OWNER or (
            self.object.role.name == PROJECT_ROLE_DELEGATE
            and not self.request.user.has_perm(
                'projectroles.update_project_delegate', project
            )
        ):
            messages.error(
                self.request,
                'You do not have permission to remove the '
                'membership of {}'.format(self.object.role.name),
            )

        else:
            try:
                self.object = self.delete_assignment(
                    request=self.request, instance=self.object
                )
                messages.success(
                    self.request,
                    'Membership of {} removed.'.format(user.username),
                )

            except Exception as ex:
                messages.error(
                    self.request,
                    'Failed to remove membership of {}: {}'.format(
                        user.username, ex
                    ),
                )

        return redirect(
            reverse(
                'projectroles:roles', kwargs={'project': project.sodar_uuid}
            )
        )


class RoleAssignmentOwnerTransferMixin:
    """Mixin for owner RoleAssignment transfer in UI and API views"""

    def _create_timeline_event(self, old_owner, new_owner, project):
        timeline = get_backend_api('timeline_backend')
        # Init Timeline event
        if not timeline:
            return None

        tl_desc = 'transfer ownership from {{{}}} to {{{}}}'.format(
            'prev_owner', 'new_owner'
        )
        tl_event = timeline.add_event(
            project=project,
            app_name=APP_NAME,
            user=self.request.user,
            event_name='role_owner_transfer',
            description=tl_desc,
            extra_data={
                'prev_owner': old_owner.username,
                'new_owner': new_owner.username,
            },
        )
        tl_event.add_object(old_owner, 'prev_owner', old_owner.username)
        tl_event.add_object(new_owner, 'new_owner', new_owner.username)
        return tl_event

    def _handle_transfer(
        self, project, old_owner_as, new_owner, old_owner_role
    ):
        taskflow = get_backend_api('taskflow')

        # Handle inherited owner roles for categories if taskflow is enabled
        if taskflow and project.type == PROJECT_TYPE_CATEGORY:
            flow_data = {
                'roles_add': taskflow.get_inherited_roles(project, new_owner),
                'roles_delete': taskflow.get_inherited_roles(
                    project, old_owner_as.user
                ),
            }

            # Submit taskflow (Requires SODAR Taskflow v0.4.0+)
            # NOTE: Can raise exception
            taskflow.submit(
                project_uuid=None,  # Batch flow for multiple projects
                flow_name='role_update_irods_batch',
                flow_data=flow_data,
                request=self.request,
            )

        # If taskflow submission was successful / skipped, update database
        old_owner_as.role = old_owner_role
        old_owner_as.save()

        role_as = RoleAssignment.objects.get_assignment(new_owner, project)
        role_owner = Role.objects.get(name=PROJECT_ROLE_OWNER)

        if role_as:
            role_as.role = role_owner
            role_as.save()

        elif new_owner in [
            a.user for a in project.get_owners(inherited_only=True)
        ]:
            RoleAssignment.objects.create(
                project=project, user=new_owner, role=role_owner
            )

        else:
            # We should already catch this earlier, but just in case..
            raise Exception(
                'New owner must have direct or inherited role in project'
            )

        return True

    def transfer_owner(self, project, new_owner, old_owner_as, old_owner_role):
        """
        Transfer project ownership to a new user and assign a new role to the
        previous owner.

        :param project: Project object
        :param new_owner: User object
        :param old_owner_as: RoleAssignment object
        :param old_owner_role: Role object for the previous owner's new role
        :return:
        """
        app_alerts = get_backend_api('appalerts_backend')
        old_owner = old_owner_as.user
        owner_role = Role.objects.get(name=PROJECT_ROLE_OWNER)
        tl_event = self._create_timeline_event(old_owner, new_owner, project)

        try:
            self._handle_transfer(
                project, old_owner_as, new_owner, old_owner_role
            )
        except Exception as ex:
            if tl_event:
                tl_event.set_status('FAILED', str(ex))
            raise ex

        if tl_event:
            tl_event.set_status('OK')

        if self.request.user != old_owner:
            if app_alerts:
                app_alerts.add_alert(
                    app_name=APP_NAME,
                    alert_name='role_update',
                    user=old_owner,
                    message=ALERT_MSG_ROLE_UPDATE.format(
                        project=project.title, role=old_owner_role.name
                    ),
                    url=reverse(
                        'projectroles:detail',
                        kwargs={'project': project.sodar_uuid},
                    ),
                    project=project,
                )
            if SEND_EMAIL:
                email.send_role_change_mail(
                    'update', project, old_owner, old_owner_role, self.request
                )

        if self.request.user != new_owner:
            if app_alerts:
                app_alerts.add_alert(
                    app_name=APP_NAME,
                    alert_name='role_update',
                    user=new_owner,
                    message=ALERT_MSG_ROLE_UPDATE.format(
                        project=project.title, role=owner_role.name
                    ),
                    url=reverse(
                        'projectroles:detail',
                        kwargs={'project': project.sodar_uuid},
                    ),
                    project=project,
                )
            if SEND_EMAIL:
                email.send_role_change_mail(
                    'update',
                    project,
                    new_owner,
                    owner_role,
                    self.request,
                )


class RoleAssignmentOwnerTransferView(
    LoginRequiredMixin,
    ProjectModifyPermissionMixin,
    CurrentUserFormMixin,
    ProjectContextMixin,
    RoleAssignmentOwnerTransferMixin,
    FormView,
):
    permission_required = 'projectroles.update_project_owner'
    template_name = 'projectroles/roleassignment_owner_transfer.html'
    form_class = RoleAssignmentOwnerTransferForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        project = self.get_project()
        owner_as = RoleAssignment.objects.filter(
            project=project, role__name=PROJECT_ROLE_OWNER
        )[0]
        kwargs.update({'project': project, 'current_owner': owner_as.user})
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        owner_as = RoleAssignment.objects.filter(
            project=self.get_project(), role__name=PROJECT_ROLE_OWNER
        )[0]
        context.update({'current_owner': owner_as.user})
        return context

    def form_valid(self, form):
        project = form.project
        old_owner = form.current_owner
        old_owner_as = project.get_owner()
        new_owner = form.cleaned_data['new_owner']
        old_owner_role = form.cleaned_data['old_owner_role']
        redirect_url = reverse(
            'projectroles:roles', kwargs={'project': project.sodar_uuid}
        )

        try:
            self.transfer_owner(
                project, new_owner, old_owner_as, old_owner_role
            )

        except Exception as ex:
            # TODO: Add logging
            messages.error(
                self.request, 'Unable to transfer ownership: {}'.format(ex)
            )

        success_msg = (
            'Successfully transferred ownership from '
            '{} to {}.'.format(old_owner.username, new_owner.username)
        )

        if SEND_EMAIL:
            success_msg += ' Notification(s) have been sent by email.'

        messages.success(self.request, success_msg)
        return redirect(redirect_url)


# ProjectInvite Views ----------------------------------------------------------


class ProjectInviteMixin:
    """Mixin for ProjectInvite helpers"""

    @classmethod
    def handle_invite(cls, invite, request, resend=False, add_message=True):
        """
        Handle invite creation, email sending/resending and logging to timeline.

        :param invite: ProjectInvite object
        :param request: Django request object
        :param resend: Send or resend (bool)
        :param add_message: Add Django message on success/failure (bool)
        """
        timeline = get_backend_api('timeline_backend')
        send_str = 'resend' if resend else 'send'
        status_type = 'OK'
        status_desc = None

        if SEND_EMAIL:
            sent_mail = email.send_invite_mail(invite, request)
            if sent_mail == 0:
                status_type = 'FAILED'
                status_desc = 'Email sending failed'
        else:
            status_type = 'FAILED'
            status_desc = 'PROJECTROLES_SEND_EMAIL not True'

        if status_type != 'OK' and not resend:
            status_desc += ', invite not created'

        # Add event in Timeline
        if timeline:
            timeline.add_event(
                project=invite.project,
                app_name=APP_NAME,
                user=request.user,
                event_name='invite_{}'.format(send_str),
                description='{} project invite with role "{}" to {}'.format(
                    send_str, invite.role.name, invite.email
                ),
                status_type=status_type,
                status_desc=status_desc,
            )

        if add_message and status_type == 'OK':
            messages.success(
                request,
                'Invite for "{}" role in {} sent to {}, expires on {}'.format(
                    invite.role.name,
                    invite.project.title,
                    invite.email,
                    timezone.localtime(invite.date_expire).strftime(
                        '%Y-%m-%d %H:%M'
                    ),
                ),
            )
        elif add_message and not resend:  # NOTE: Delete invite if send fails
            invite.delete()
            messages.error(request, status_desc)

    @classmethod
    def revoke_invite(cls, invite, project, request):
        timeline = get_backend_api('timeline_backend')

        if invite:
            invite.active = False
            invite.save()

        # Add event in Timeline
        if timeline:
            timeline.add_event(
                project=project,
                app_name=APP_NAME,
                user=request.user,
                event_name='invite_revoke',
                description='revoke invite sent to "{}"'.format(
                    invite.email if invite else 'N/A'
                ),
                status_type='OK' if invite else 'FAILED',
            )

        return invite


class ProjectInviteView(
    LoginRequiredMixin,
    ProjectContextMixin,
    ProjectModifyPermissionMixin,
    TemplateView,
):
    """View for displaying and modifying project invites"""

    permission_required = 'projectroles.invite_users'
    template_name = 'projectroles/project_invites.html'
    model = ProjectInvite

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context['invites'] = ProjectInvite.objects.filter(
            project=context['project'],
            active=True,
            date_expire__gt=timezone.now(),
        )

        return context


class ProjectInviteCreateView(
    LoginRequiredMixin,
    ProjectContextMixin,
    ProjectModifyPermissionMixin,
    ProjectInviteMixin,
    CurrentUserFormMixin,
    CreateView,
):
    """ProjectInvite creation view"""

    model = ProjectInvite
    form_class = ProjectInviteForm
    permission_required = 'projectroles.invite_users'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        project = self.get_permission_object()

        context['preview_subject'] = email.get_invite_subject(project)
        context['preview_body'] = email.get_invite_body(
            project=project,
            issuer=self.request.user,
            role_name='{role_name}',
            invite_url='http://XXXXXXXXXXXXXXXXXXXXXXX',
            date_expire_str='YYYY-MM-DD HH:MM',
        ).replace('\n', '\\n')
        context['preview_message'] = email.get_invite_message(
            '{message}'
        ).replace('\n', '\\n')
        context['preview_footer'] = email.get_email_footer().replace(
            '\n', '\\n'
        )

        return context

    def get_form_kwargs(self):
        """Pass current user and optional email/role to form"""
        kwargs = super().get_form_kwargs()
        kwargs.update({'project': self.get_permission_object().sodar_uuid})

        email = self.request.GET.get('e', None)
        role_pk = self.request.GET.get('r', None)

        kwargs.update({'mail': unquote_plus(email) if email else None})
        kwargs.update({'role': role_pk})

        return kwargs

    def form_valid(self, form):
        self.object = form.save()

        # Send mail and add to timeline
        self.handle_invite(invite=self.object, request=self.request)

        return redirect(
            reverse(
                'projectroles:invites',
                kwargs={'project': self.object.project.sodar_uuid},
            )
        )


class ProjectInviteProcessMixin:
    """Mixin for accepting and processing project invites"""

    @classmethod
    def get_invite_type(cls, invite):
        """Return invite type ("ldap", "local" or "error")"""
        # Check if domain is associated with LDAP
        domain = invite.email.split('@')[1].split('.')[0].lower()

        if settings.ENABLE_LDAP and domain in (
            getattr(settings, 'AUTH_LDAP_USERNAME_DOMAIN', '').lower(),
            getattr(settings, 'AUTH_LDAP2_USERNAME_DOMAIN', '').lower(),
            *[a.lower() for a in getattr(settings, 'LDAP_ALT_DOMAINS', [])],
        ):
            return 'ldap'

        elif settings.PROJECTROLES_ALLOW_LOCAL_USERS:
            return 'local'

        return 'error'

    @classmethod
    def revoke_failed_invite(
        cls, invite, user=None, failed=True, fail_desc='', timeline=None
    ):
        """Set invite.active to False and save the invite"""
        invite.active = False
        invite.save()

        if failed and timeline and user:
            # Add event in Timeline
            timeline.add_event(
                project=invite.project,
                app_name=APP_NAME,
                user=user,
                event_name='invite_accept',
                description='accept project invite',
                status_type='FAILED',
                status_desc=fail_desc,
            )

    def get_invite(self, secret):
        """Get invite, display message if not found"""
        try:
            return ProjectInvite.objects.get(secret=secret)
        except ProjectInvite.DoesNotExist:
            messages.error(self.request, 'Error: Invite does not exist!')

    def user_role_exists(self, invite, user, timeline=None):
        """
        Display message and revoke invite if user already has roles in project
        """
        if invite.project.has_role(user):
            messages.warning(
                self.request,
                mark_safe(
                    'You already have roles set in the {project}. You can '
                    'access the {project} <a href="{url}">here</a>.'.format(
                        project=get_display_name(invite.project.type),
                        url=reverse(
                            'projectroles:detail',
                            kwargs={'project': invite.project.sodar_uuid},
                        ),
                    )
                ),
            )
            self.revoke_failed_invite(
                invite,
                user,
                failed=True,
                fail_desc='User already has roles in {}'.format(
                    get_display_name(invite.project.type)
                ),
                timeline=timeline,
            )
            return True
        return False

    def is_invite_expired(self, invite, user=None):
        """Display message and send email to issuer if invite is expired"""
        if invite.date_expire < timezone.now():
            messages.error(
                self.request,
                'Error: Your invite has expired! '
                'Please contact the person who invited you: {} ({})'.format(
                    invite.issuer.name, invite.issuer.email
                ),
            )

            # Send notification of expiry to issuer
            if SEND_EMAIL:
                email.send_expiry_note(
                    invite,
                    self.request,
                    user_name=user.get_full_name() if user else invite.email,
                )

            self.revoke_failed_invite(
                invite, user, failed=True, fail_desc='Invite expired'
            )
            return True
        return False

    def create_assignment(self, invite, user, timeline=None):
        """Create role assignment for invited user"""
        taskflow = get_backend_api('taskflow')
        app_alerts = get_backend_api('appalerts_backend')
        tl_event = None

        if timeline:
            tl_event = timeline.add_event(
                project=invite.project,
                app_name=APP_NAME,
                user=user,
                event_name='invite_accept',
                description='accept project invite with role of "{}"'.format(
                    invite.role.name
                ),
            )

        # Submit with taskflow (only for projects)
        if taskflow and invite.project.type == PROJECT_TYPE_PROJECT:
            if tl_event:
                tl_event.set_status('SUBMIT')

            flow_data = {
                'username': user.username,
                'user_uuid': str(user.sodar_uuid),
                'role_pk': invite.role.pk,
            }

            try:
                taskflow.submit(
                    project_uuid=str(invite.project.sodar_uuid),
                    flow_name='role_update',
                    flow_data=flow_data,
                    request=self.request,
                )

            except taskflow.FlowSubmitException as ex:
                if tl_event:
                    tl_event.set_status('FAILED', str(ex))

                messages.error(self.request, str(ex))
                return False

            # Get object
            RoleAssignment.objects.get(project=invite.project, user=user)

            tl_event.set_status('OK')

        # Local save without Taskflow
        else:
            role_as = RoleAssignment(
                user=user, project=invite.project, role=invite.role
            )
            role_as.save()

            if tl_event:
                tl_event.set_status('OK')

        # ..notify the issuer by alert and email..
        if app_alerts:
            app_alerts.add_alert(
                app_name=APP_NAME,
                alert_name='invite_accept',
                user=invite.issuer,
                message='Invitation sent to "{}" for project "{}" with the '
                'role "{}" was accepted.'.format(
                    user.email, invite.project.title, invite.role.name
                ),
                url=reverse(
                    'projectroles:detail',
                    kwargs={'project': invite.project.sodar_uuid},
                ),
                project=invite.project,
            )
        if SEND_EMAIL:
            email.send_accept_note(invite, self.request, user)

        # ..deactivate the invite..
        self.revoke_failed_invite(invite, user, failed=False, timeline=timeline)

        # ..and finally redirect user to the project front page
        messages.success(
            self.request,
            'Welcome to {} "{}"! You have been assigned the role of '
            '{}.'.format(
                get_display_name(invite.project.type),
                invite.project.title,
                invite.role.name,
            ),
        )

        return True


class ProjectInviteAcceptView(ProjectInviteProcessMixin, View):
    """View to handle accepting a project invite"""

    def get(self, *args, **kwargs):
        timeline = get_backend_api('timeline_backend')
        invite = self.get_invite(secret=kwargs['secret'])
        user = self.request.user

        if not invite:
            return redirect(reverse('home'))

        if (
            not user.is_anonymous
            and user.is_authenticated
            and user.email == invite.email
            and self.user_role_exists(invite, user, timeline)
        ):
            return redirect(reverse('home'))

        invite_type = self.get_invite_type(invite)

        if invite_type == 'ldap':
            return redirect(
                reverse(
                    'projectroles:invite_process_ldap',
                    kwargs={'secret': kwargs['secret']},
                )
            )

        elif invite_type == 'local':
            return redirect(
                reverse(
                    'projectroles:invite_process_local',
                    kwargs={'secret': kwargs['secret']},
                )
            )

        # Error
        messages.error(self.request, 'Local users not allowed on this site.')
        return redirect(reverse('home'))


class ProjectInviteProcessLDAPView(
    LoginRequiredMixin, ProjectInviteProcessMixin, View
):
    """View to handle accepting a project LDAP invite"""

    def get(self, *args, **kwargs):
        timeline = get_backend_api('timeline_backend')
        invite = self.get_invite(kwargs['secret'])

        if not invite:
            return redirect(reverse('home'))

        # Check invite has correct type
        if self.get_invite_type(invite) == 'local':
            messages.error(
                self.request,
                'Error: Invite was issued for local user, but LDAP invite '
                'view was requested.',
            )
            return redirect(reverse('home'))

        # Check if user already accepted the invite
        if self.user_role_exists(invite, self.request.user, timeline=timeline):
            return redirect(reverse('home'))

        # Check if invite expired
        if self.is_invite_expired(invite, self.request.user):
            return redirect(reverse('home'))

        # If we get this far, create RoleAssignment..
        if not self.create_assignment(
            invite, self.request.user, timeline=timeline
        ):
            return redirect(reverse('home'))

        return redirect(
            reverse(
                'projectroles:detail',
                kwargs={'project': invite.project.sodar_uuid},
            )
        )


class ProjectInviteProcessLocalView(ProjectInviteProcessMixin, FormView):
    """View to handle accepting a project local invite"""

    form_class = LocalUserForm
    template_name = 'projectroles/user_form.html'

    def get(self, *args, **kwargs):
        invite = self.get_invite(self.kwargs['secret'])
        timeline = get_backend_api('timeline_backend')

        if not invite:
            return redirect(reverse('home'))

        # Check if local users are enabled
        if not settings.PROJECTROLES_ALLOW_LOCAL_USERS:
            messages.error(
                self.request,
                'Error: Invite of non-LDAP user, but local users are not '
                'allowed!',
            )
            return redirect(reverse('home'))

        # Check invite for correct type
        if self.get_invite_type(invite) == 'ldap':
            messages.error(
                self.request,
                'Error: Invite was issued for LDAP user, but local invite '
                'view was requested.',
            )
            return redirect(reverse('home'))

        # Check if invited user exists
        user = User.objects.filter(email=invite.email).first()

        # Check if invite has expired
        if self.is_invite_expired(invite, user):
            return redirect(reverse('home'))

        # A user is not logged in
        if self.request.user.is_anonymous:
            # Redirect to login if user exists and
            if user:
                messages.info(
                    self.request,
                    'A user with that email already exists. Please login '
                    'first to accept the invite.',
                )
                return redirect(
                    reverse('login')
                    + '?next='
                    + reverse(
                        'projectroles:invite_process_local',
                        kwargs={'secret': invite.secret},
                    )
                )

            # Show form if user doesn't exists and no user is logged in
            return super().get(*args, **kwargs)

        # Logged in but the invited user does not exist yet
        if not user:
            messages.error(
                self.request,
                'Error: Logged in user is not allowed to accept other\'s '
                'invites.',
            )
            return redirect(reverse('home'))

        # Logged in user is not invited user
        if not self.request.user == user:
            messages.error(
                self.request,
                'Error: Invited user exists, but logged in user is not '
                'invited user.',
            )
            return redirect(reverse('home'))

        # User exists but is not local
        if not user.is_local():
            messages.error(
                self.request, 'Error: User exists, but is not local.'
            )
            return redirect(reverse('home'))

        # Create role if user exists
        if not self.create_assignment(invite, user, timeline=timeline):
            return redirect(reverse('home'))

        return redirect(
            reverse(
                'projectroles:detail',
                kwargs={'project': invite.project.sodar_uuid},
            )
        )

    def get_initial(self):
        """Returns the initial data for the form."""
        initial = super().get_initial()

        try:
            invite = ProjectInvite.objects.get(secret=self.kwargs['secret'])
        except ProjectInvite.DoesNotExist:
            return initial

        username_base = invite.email.split('@')[0]
        i = 0
        while True:
            username = username_base + str(i if i else '')
            try:
                User.objects.get(username=username)
                i += 1
            except User.DoesNotExist:
                break

        initial.update({'email': invite.email, 'username': username})
        return initial

    def form_valid(self, form):
        timeline = get_backend_api('timeline_backend')
        invite = self.get_invite(self.kwargs['secret'])

        if not invite:
            return redirect(reverse('home'))

        # Check if local users are allowed
        if not settings.PROJECTROLES_ALLOW_LOCAL_USERS:
            messages.error(
                self.request,
                'Error: Invite of non-LDAP user, but local users are not '
                'allowed!',
            )
            return redirect(reverse('home'))

        # Check invite for correct type
        if self.get_invite_type(invite) == 'ldap':
            messages.error(
                self.request,
                'Error: Invite was issued for LDAP user, but local invite '
                'view was requested.',
            )
            return redirect(reverse('home'))

        # Check if invite is expired
        if self.is_invite_expired(invite):
            return redirect(reverse('home'))

        user = User.objects.create_user(
            form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
        )

        if self.user_role_exists(invite, user, timeline=timeline):
            return redirect(
                reverse(
                    'projectroles:detail',
                    kwargs={'project': invite.project.sodar_uuid},
                )
            )

        # If we get this far, create RoleAssignment..
        if not self.create_assignment(invite, user, timeline=timeline):
            user.delete()
            redirect(reverse('home'))

        return redirect(
            reverse(
                'projectroles:detail',
                kwargs={'project': invite.project.sodar_uuid},
            )
        )


class ProjectInviteResendView(
    LoginRequiredMixin, ProjectModifyPermissionMixin, ProjectInviteMixin, View
):
    """View to handle resending a project invite"""

    permission_required = 'projectroles.invite_users'

    def get(self, *args, **kwargs):
        try:
            invite = ProjectInvite.objects.get(
                sodar_uuid=self.kwargs['projectinvite'], active=True
            )

        except ProjectInvite.DoesNotExist:
            messages.error(self.request, 'Error: Invite not found!')
            return redirect(
                reverse(
                    'projectroles:invites',
                    kwargs={'project': self.get_project()},
                )
            )

        # Reset invite expiration date
        invite.date_expire = get_expiry_date()
        invite.save()

        # Resend mail and add to timeline
        self.handle_invite(invite=invite, request=self.request, resend=True)

        return redirect(
            reverse(
                'projectroles:invites',
                kwargs={'project': invite.project.sodar_uuid},
            )
        )


class ProjectInviteRevokeView(
    LoginRequiredMixin,
    ProjectModifyPermissionMixin,
    ProjectContextMixin,
    ProjectInviteMixin,
    TemplateView,
):
    """Batch delete/move confirm view"""

    template_name = 'projectroles/invite_revoke_confirm.html'
    permission_required = 'projectroles.invite_users'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['project'] = self.get_project()

        if 'projectinvite' in self.kwargs:
            try:
                context['invite'] = ProjectInvite.objects.get(
                    sodar_uuid=self.kwargs['projectinvite']
                )

            except ProjectInvite.DoesNotExist:
                pass

        return context

    def post(self, request, **kwargs):
        """Override post() to handle POST from confirmation template"""
        project = self.get_project()
        invite = ProjectInvite.objects.filter(
            sodar_uuid=kwargs['projectinvite']
        ).first()

        if (
            invite
            and invite.role.name == PROJECT_ROLE_DELEGATE
            and not request.user.has_perm(
                'projectroles.update_project_delegate', project
            )
        ):
            invite = None  # Causes revoke_failed_invite() to add failed timeline event
            messages.error(
                self.request, 'No perms for updating delegate invite!'
            )
        elif invite:
            messages.success(self.request, 'Invite revoked.')
        else:
            messages.error(self.request, 'Invite not found!')

        self.revoke_invite(invite, project, request)
        return redirect(
            reverse(
                'projectroles:invites', kwargs={'project': project.sodar_uuid}
            )
        )


# User management views --------------------------------------------------------


class UserUpdateView(LoginRequiredMixin, HTTPRefererMixin, UpdateView):
    """Display and process the user update view"""

    form_class = LocalUserForm
    template_name = 'projectroles/user_form.html'
    success_url = reverse_lazy('home')

    def get_object(self, **kwargs):
        return self.request.user

    def get(self, *args, **kwargs):
        if not self.request.user.is_local():
            messages.error(
                self.request, 'Error: LDAP user can\'t edit user details'
            )
            return redirect(reverse('home'))
        return super().get(*args, **kwargs)

    def get_success_url(self):
        messages.success(
            self.request, 'User successfully updated, please log in again'
        )
        return reverse('home')


# Remote site and project views ------------------------------------------------


class RemoteSiteListView(
    LoginRequiredMixin, LoggedInPermissionMixin, TemplateView
):
    """Main view for displaying remote site list"""

    permission_required = 'projectroles.update_remote'
    template_name = 'projectroles/remote_sites.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        site_mode = (
            SITE_MODE_TARGET
            if settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE
            else SITE_MODE_SOURCE
        )

        sites = RemoteSite.objects.filter(mode=site_mode).order_by('name')

        if (
            sites.count() > 0
            and settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET
        ):
            sites = sites[:1]

        context['sites'] = sites
        return context

    # TODO: Remove this once implementing #76
    def get(self, request, *args, **kwargs):
        if getattr(settings, 'PROJECTROLES_DISABLE_CATEGORIES', False):
            messages.warning(
                request,
                '{} {} and nesting disabled, '
                'remote {} sync disabled'.format(
                    get_display_name(PROJECT_TYPE_PROJECT, title=True),
                    get_display_name(PROJECT_TYPE_CATEGORY, plural=True),
                    get_display_name(PROJECT_TYPE_PROJECT),
                ),
            )
            return redirect('home')

        return super().get(request, *args, **kwargs)


class RemoteSiteModifyMixin(ModelFormMixin):
    def form_valid(self, form):
        if self.object:
            form_action = 'updated'

        elif settings.PROJECTROLES_SITE_MODE == 'TARGET':
            form_action = 'set'

        else:
            form_action = 'created'

        self.object = form.save()

        messages.success(
            self.request,
            '{} site "{}" {}'.format(
                self.object.mode.capitalize(), self.object.name, form_action
            ),
        )
        return redirect(reverse('projectroles:remote_sites'))


class RemoteSiteCreateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    RemoteSiteModifyMixin,
    HTTPRefererMixin,
    CurrentUserFormMixin,
    CreateView,
):
    """RemoteSite creation view"""

    model = RemoteSite
    form_class = RemoteSiteForm
    permission_required = 'projectroles.update_remote'

    def get(self, request, *args, **kwargs):
        """Override get() to disallow rendering this view if current site is
        in TARGET mode and a source site already exists"""
        if (
            settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET
            and RemoteSite.objects.filter(mode=SITE_MODE_SOURCE).count() > 0
        ):
            messages.error(request, 'Source site has already been set')
            return redirect(reverse('projectroles:remote_sites'))

        return super().get(request, args, kwargs)


class RemoteSiteUpdateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    RemoteSiteModifyMixin,
    HTTPRefererMixin,
    CurrentUserFormMixin,
    UpdateView,
):
    """RemoteSite updating view"""

    model = RemoteSite
    form_class = RemoteSiteForm
    permission_required = 'projectroles.update_remote'
    slug_url_kwarg = 'remotesite'
    slug_field = 'sodar_uuid'


class RemoteSiteDeleteView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    RemoteSiteModifyMixin,
    HTTPRefererMixin,
    CurrentUserFormMixin,
    DeleteView,
):
    """RemoteSite deletion view"""

    model = RemoteSite
    form_class = RemoteSiteForm
    permission_required = 'projectroles.update_remote'
    slug_url_kwarg = 'remotesite'
    slug_field = 'sodar_uuid'

    def get_success_url(self):
        messages.success(
            self.request,
            '{} site "{}" deleted'.format(
                self.object.mode.capitalize(), self.object.name
            ),
        )

        return reverse('projectroles:remote_sites')


class RemoteProjectListView(
    LoginRequiredMixin, LoggedInPermissionMixin, TemplateView
):
    """View for displaying the project lsit for remote site sync"""

    permission_required = 'projectroles.update_remote'
    template_name = 'projectroles/remote_projects.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        site = RemoteSite.objects.get(sodar_uuid=self.kwargs['remotesite'])
        context['site'] = site

        # Projects in SOURCE mode: all local projects of type PROJECT
        if settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE:
            projects = Project.objects.filter(type=PROJECT_TYPE_PROJECT)
        # Projects in TARGET mode: retrieve from source
        else:  # SITE_MODE_TARGET
            remote_uuids = [p.project_uuid for p in site.projects.all()]
            projects = Project.objects.filter(
                type=PROJECT_TYPE_PROJECT, sodar_uuid__in=remote_uuids
            )

        if projects:
            context['projects'] = projects.order_by('full_title')

        return context


class RemoteProjectBatchUpdateView(
    LoginRequiredMixin, LoggedInPermissionMixin, TemplateView
):
    """
    Manually created form view for updating project access in batch for a
    remote target site.
    """

    permission_required = 'projectroles.update_remote'
    template_name = 'projectroles/remoteproject_update.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        # Current site
        context['site'] = RemoteSite.objects.filter(
            sodar_uuid=kwargs['remotesite']
        ).first()
        return context

    def post(self, request, *args, **kwargs):
        timeline = get_backend_api('timeline_backend')
        post_data = request.POST
        context = self.get_context_data(*args, **kwargs)
        site = context['site']
        confirmed = True if 'update-confirmed' in post_data else False
        redirect_url = reverse(
            'projectroles:remote_projects',
            kwargs={'remotesite': site.sodar_uuid},
        )

        # Ensure site is in SOURCE mode
        if settings.PROJECTROLES_SITE_MODE != SITE_MODE_SOURCE:
            messages.error(
                request,
                'Site in TARGET mode, cannot update {} access'.format(
                    get_display_name(PROJECT_TYPE_PROJECT)
                ),
            )
            return redirect(redirect_url)

        access_fields = {
            k: v for k, v in post_data.items() if k.startswith('remote_access')
        }

        ######################
        # Confirmation needed
        ######################

        if not confirmed:
            # Pass on (only) changed projects to confirmation form
            modifying_access = []

            for k, v in access_fields.items():
                project_uuid = k.split('_')[2]
                remote_obj = RemoteProject.objects.filter(
                    site=site, project_uuid=project_uuid
                ).first()
                if (not remote_obj and v != REMOTE_LEVEL_NONE) or (
                    remote_obj and remote_obj.level != v
                ):
                    modifying_access.append(
                        {
                            'project': Project.objects.get(
                                sodar_uuid=project_uuid
                            ),
                            'old_level': REMOTE_LEVEL_NONE
                            if not remote_obj
                            else remote_obj.level,
                            'new_level': v,
                        }
                    )

            if not modifying_access:
                messages.warning(
                    request,
                    'No changes to {} access detected'.format(
                        get_display_name(PROJECT_TYPE_PROJECT)
                    ),
                )
                return redirect(redirect_url)

            context['modifying_access'] = modifying_access
            return super().render_to_response(context)

        ############
        # Confirmed
        ############

        for k, v in access_fields.items():
            project_uuid = k.split('_')[2]
            project = Project.objects.filter(sodar_uuid=project_uuid).first()
            # Update or create a RemoteProject object
            try:
                rp = RemoteProject.objects.get(
                    site=site, project_uuid=project_uuid
                )
                rp.level = v
            except RemoteProject.DoesNotExist:
                rp = RemoteProject(
                    site=site,
                    project_uuid=project_uuid,
                    project=project,
                    level=v,
                )
            rp.save()

            if timeline and project:
                tl_desc = 'update remote access for site {{{}}} to "{}"'.format(
                    'site',
                    SODAR_CONSTANTS['REMOTE_ACCESS_LEVELS'][v].lower(),
                )
                tl_event = timeline.add_event(
                    project=project,
                    app_name=APP_NAME,
                    user=request.user,
                    event_name='update_remote',
                    description=tl_desc,
                    classified=True,
                    status_type='OK',
                )
                tl_event.add_object(site, 'site', site.name)

        # All OK
        messages.success(
            request,
            'Access level updated for {} {} in site "{}"'.format(
                len(access_fields.items()),
                get_display_name(
                    PROJECT_TYPE_PROJECT, count=len(access_fields.items())
                ),
                context['site'].name,
            ),
        )
        return redirect(redirect_url)


class RemoteProjectSyncView(
    LoginRequiredMixin, LoggedInPermissionMixin, TemplateView
):
    """Target site view for synchronizing remote projects from a source site"""

    permission_required = 'projectroles.update_remote'
    template_name = 'projectroles/remoteproject_sync.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        # Current site
        context['site'] = RemoteSite.objects.filter(
            sodar_uuid=kwargs['remotesite']
        ).first()
        return context

    def get(self, request, *args, **kwargs):
        """Override get() for a confirmation view"""
        redirect_url = reverse('projectroles:remote_sites')
        if settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE:
            messages.error(
                request, 'Site in SOURCE mode, remote sync not allowed'
            )
            return redirect(redirect_url)

        from projectroles.views_api import (
            CORE_API_MEDIA_TYPE,
            CORE_API_DEFAULT_VERSION,
        )

        remote_api = RemoteProjectAPI()
        context = self.get_context_data(*args, **kwargs)
        site = context['site']
        api_url = site.get_url() + reverse(
            'projectroles:api_remote_get', kwargs={'secret': site.secret}
        )

        try:
            api_req = urllib.request.Request(api_url)
            api_req.add_header(
                'accept',
                '{}; version={}'.format(
                    CORE_API_MEDIA_TYPE, CORE_API_DEFAULT_VERSION
                ),
            )
            response = urllib.request.urlopen(api_req)
            remote_data = json.loads(response.read().decode('utf-8'))

        except Exception as ex:
            ex_str = str(ex)
            if (
                isinstance(ex, urllib.error.URLError)
                and isinstance(ex.reason, ssl.SSLError)
                and ex.reason.reason == 'WRONG_VERSION_NUMBER'
            ):
                ex_str = 'Most likely server cannot handle HTTPS requests.'
            if len(ex_str) >= 255:
                ex_str = ex_str[:255]
            messages.error(
                request,
                'Unable to synchronize {}: {}'.format(
                    get_display_name(PROJECT_TYPE_PROJECT, plural=True), ex_str
                ),
            )
            return redirect(redirect_url)

        # Sync data
        try:
            update_data = remote_api.sync_remote_data(
                site, remote_data, request
            )
        except Exception as ex:
            messages.error(
                request, 'Remote sync cancelled with exception: {}'.format(ex)
            )
            if settings.DEBUG:
                raise ex
            return redirect(redirect_url)

        # Check for updates
        user_count = len(
            [v for v in update_data['users'].values() if 'status' in v]
        )
        project_count = len(
            [v for v in update_data['projects'].values() if 'status' in v]
        )
        app_settings_count = len(
            [
                v
                for v in update_data['app_settings'].values()
                if 'status' in v and v['status'] != 'skipped'
            ]
        )
        role_count = 0

        for p in [p for p in update_data['projects'].values() if 'roles' in p]:
            for _ in [r for r in p['roles'].values() if 'status' in r]:
                role_count += 1

        # Redirect if no changes were detected
        if (
            user_count == 0
            and project_count == 0
            and role_count == 0
            and app_settings_count == 0
        ):
            messages.warning(
                request,
                'No changes in remote site detected, nothing to synchronize',
            )
            return redirect(redirect_url)

        context['update_data'] = update_data
        context['user_count'] = user_count
        context['project_count'] = project_count
        context['role_count'] = role_count
        context['app_settings_count'] = app_settings_count
        messages.success(
            request,
            '{} data updated according to source site'.format(
                get_display_name(PROJECT_TYPE_PROJECT, title=True)
            ),
        )
        return super().render_to_response(context)
