"""Template tags intended for internal use within the projectroles app"""


from django import template
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from ..models import (
    Project,
    RoleAssignment,
    RemoteProject,
    SODAR_CONSTANTS,
    PROJECT_TAG_STARRED,
)
from ..plugins import get_active_plugins
from ..project_tags import get_tag_state


# Settings
HELP_HIGHLIGHT_DAYS = (
    settings.PROJECTROLES_HELP_HIGHLIGHT_DAYS
    if hasattr(settings, 'PROJECTROLES_HELP_HIGHLIGHT_DAYS')
    else 7
)

# Local constants
INDENT_PX = 25

# TODO: Remove
PROJECT_TYPE_DISPLAY = {'PROJECT': 'Project', 'CATEGORY': 'Category'}

# Behaviour for certain levels has not been specified/implemented yet
ACTIVE_LEVEL_TYPES = [
    SODAR_CONSTANTS['REMOTE_LEVEL_NONE'],
    SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
]

register = template.Library()


# SODAR and site operations ----------------------------------------------------


@register.simple_tag
def sodar_constant(value):
    """Get value from SODAR_CONSTANTS"""
    return SODAR_CONSTANTS[value] if value in SODAR_CONSTANTS else None


# TODO: Refactor into get_plugins(type)
@register.simple_tag
def get_backend_plugins():
    """Get active backend plugins"""
    return get_active_plugins('backend')


# TODO: Refactor into get_plugins(type)
@register.simple_tag
def get_site_apps():
    """Get active site apps"""
    return get_active_plugins('site_app')


@register.simple_tag
def get_site_app_messages(user):
    """Get messages from site apps"""
    plugins = get_active_plugins('site_app')
    ret = []

    for p in plugins:
        ret += p.get_messages(user)

    return ret


@register.simple_tag
def has_star(project, user):
    """Return True/False for project star tag state"""
    return user.has_perm(
        'projectroles.view_project', project
    ) and get_tag_state(project, user, PROJECT_TAG_STARRED)


@register.simple_tag
def get_remote_project_obj(site, project):
    """Return RemoteProject object for RemoteSite and Project"""
    try:
        return RemoteProject.objects.get(
            site=site, project_uuid=project.sodar_uuid
        )

    except RemoteProject.DoesNotExist:
        return None


@register.simple_tag
def allow_project_creation():
    """Check whether creating a project is allowed on the site"""
    if (
        settings.PROJECTROLES_SITE_MODE == SODAR_CONSTANTS['SITE_MODE_TARGET']
        and not settings.PROJECTROLES_TARGET_CREATE
    ):
        return False
    return True


@register.simple_tag
def is_app_hidden(plugin, user):
    """Check if app plugin is included in PROJECTROLES_HIDE_APPS"""
    if (
        hasattr(settings, 'PROJECTROLES_HIDE_APP_LINKS')
        and plugin.name in settings.PROJECTROLES_HIDE_APP_LINKS
        and not user.is_superuser
    ):
        return True
    return False


# Template rendering -----------------------------------------------------------


@register.simple_tag
def get_project_list(user, parent=None):
    """Return flat project list for displaying in templates"""
    project_list = []

    if user.is_superuser:
        project_list = Project.objects.filter(
            parent=parent, submit_status='OK'
        ).order_by('title')

    elif not user.is_anonymous():
        project_list = [
            p
            for p in Project.objects.filter(
                parent=parent, submit_status='OK'
            ).order_by('title')
            if p.has_role(user, include_children=True)
        ]

    def append_projects(project):
        lst = [project]

        for c in project.get_children():
            if user.is_superuser or c.has_role(user, include_children=True):
                lst += append_projects(c)

        return lst

    flat_list = []

    for p in project_list:
        flat_list += append_projects(p)

    return flat_list


@register.simple_tag
def get_project_list_indent(project, list_parent):
    """Return indent in pixels for project list"""
    project_depth = project.get_depth()

    if list_parent:
        project_depth -= list_parent.get_depth() + 1

    return project_depth * INDENT_PX


@register.simple_tag
def get_not_found_alert(project_results, app_search_data, search_type):
    """Return alert HTML for data which was not found during search, if any"""
    not_found = []

    if len(project_results) == 0 and (
        not search_type or search_type == 'project'
    ):
        not_found.append('Projects'),

    for results in [a['results'] for a in app_search_data]:
        if results:
            for k, result in results.items():
                type_match = False

                if not search_type or (
                    'search_type' in result
                    and search_type in result['search_types']
                ):
                    type_match = True

                if type_match and (
                    not result['items'] or len(result['items']) == 0
                ):
                    not_found.append(result['title'])

    if not_found:
        ret = (
            '<div class="alert alert-info pb-0 d-none" '
            'id="sodar-search-not-found-alert">\n'
            'No results found:\n<ul>\n'
        )
        for n in not_found:
            ret += '<li>{}</li>\n'.format(n)

        ret += '</ul>\n</div>\n'
        return ret

    return ''


@register.simple_tag
def get_project_list_value(app_plugin, column_id, project):
    return app_plugin.get_project_list_value(column_id, project)


@register.simple_tag
def get_project_column_count(app_plugins):
    """Return the amount of columns shown in project listings"""

    def get_active_list_columns(app_plugin):
        return len(
            [
                column
                for column, attributes in app_plugin.project_list_columns.items()
                if attributes['active']
            ]
        )

    return 3 + max(
        [get_active_list_columns(app_plugin) for app_plugin in app_plugins]
    )


@register.simple_tag
def get_user_role_html(project, user):
    """Return user role HTML"""
    if user.is_superuser:
        return '<span class="text-danger">Superuser</span>'

    try:
        role_as = RoleAssignment.objects.get(project=project, user=user)
        return role_as.role.name.split(' ')[1].capitalize()

    except RoleAssignment.DoesNotExist:
        return '<span class="text-muted">N/A</span>'


@register.simple_tag
def get_app_link_state(app_plugin, app_name, url_name):
    """Return "active" if plugin matches app_name and url_name is found in
    app_plugin.urls. """
    if app_name == app_plugin.name and url_name in [
        u.name for u in app_plugin.urls
    ]:
        return 'active'
    return ''


@register.simple_tag
def get_pr_link_state(app_urls, url_name, link_names=None):
    """Version of get_app_link_state() to be used within the projectroles app.
    If link_names is set, only return "active" if url_name is found in
    link_names."""
    if url_name in [u.name for u in app_urls]:
        if link_names:
            if not isinstance(link_names, list):
                link_names = [link_names]

            if url_name not in link_names:
                return ''

        return 'active'

    return ''


@register.simple_tag
def get_star(project, user):
    """Return HTML for project star tag state if it is set"""
    if user.has_perm('projectroles.view_project', project) and get_tag_state(
        project, user, PROJECT_TAG_STARRED
    ):
        return '<i class="fa fa-star text-warning sodar-tag-starred"></i>'
    return ''


@register.simple_tag
def get_help_highlight(user):
    """Return classes to highlight navbar help link if user has recently
    signed in"""
    if user.__class__.__name__ == 'User' and user.is_authenticated:
        delta_days = (timezone.now() - user.date_joined).days

        if delta_days < HELP_HIGHLIGHT_DAYS:
            return 'font-weight-bold text-warning'

    return ''


@register.simple_tag
def get_role_import_action(source_as, dest_project):
    """Return label for role import action based on existing assignment"""
    try:
        target_as = RoleAssignment.objects.get(
            project=dest_project, user=source_as.user
        )

        if target_as.role == source_as.role:
            return 'No action'

        return 'Update'

    except RoleAssignment.DoesNotExist:
        return 'Import'


@register.simple_tag
def get_login_info():
    """Return HTML info for the login page"""
    ret = '<p>Please log in'

    if hasattr(settings, 'ENABLE_LDAP') and settings.ENABLE_LDAP:
        ret += ' using your ' + settings.AUTH_LDAP_DOMAIN_PRINTABLE

        if (
            hasattr(settings, 'ENABLE_LDAP_SECONDARY')
            and settings.ENABLE_LDAP_SECONDARY
            and settings.AUTH_LDAP2_DOMAIN_PRINTABLE
        ):
            ret += ' or ' + settings.AUTH_LDAP2_DOMAIN_PRINTABLE

        ret += (
            ' account. Enter your user name as <code>username@{}'
            '</code>'.format(settings.AUTH_LDAP_USERNAME_DOMAIN)
        )

        if (
            settings.ENABLE_LDAP_SECONDARY
            and settings.AUTH_LDAP2_USERNAME_DOMAIN
        ):
            ret += ' or <code>username@{}</code>'.format(
                settings.AUTH_LDAP2_USERNAME_DOMAIN
            )

        if (
            hasattr(settings, 'PROJECTROLES_ALLOW_LOCAL_USERS')
            and settings.PROJECTROLES_ALLOW_LOCAL_USERS
        ):
            ret += (
                '. To access the site with local account enter your user '
                'name as <code>username</code>'
            )

    ret += '.</p>'
    return ret


@register.simple_tag
def get_target_project_select(site, project):
    """Return remote target project level selection HTML"""
    current_level = None

    try:
        rp = RemoteProject.objects.get(
            site__mode=SODAR_CONSTANTS['SITE_MODE_TARGET'],
            site=site,
            project_uuid=project.sodar_uuid,
        )
        current_level = rp.level

    except RemoteProject.DoesNotExist:
        pass

    ret = (
        '<select class="form-control form-control-sm" '
        'name="remote_access_{project}" '
        'id="sodar-pr-remote-project-select-{project}">'
        '\n'.format(project=project.sodar_uuid)
    )

    for level in ACTIVE_LEVEL_TYPES:
        selected = False
        legend = SODAR_CONSTANTS['REMOTE_ACCESS_LEVELS'][level]

        if level == current_level or (
            level == SODAR_CONSTANTS['REMOTE_LEVEL_NONE'] and not current_level
        ):
            selected = True

        ret += '<option value="{}" {}>{}</option>\n'.format(
            level, 'selected' if selected else '', legend
        )

    ret += '</select>\n'
    return ret


@register.simple_tag
def get_remote_access_legend(level):
    """Return legend text for remote project access level"""
    if level not in SODAR_CONSTANTS['REMOTE_ACCESS_LEVELS']:
        return 'N/A'
    return SODAR_CONSTANTS['REMOTE_ACCESS_LEVELS'][level]


@register.simple_tag
def get_sidebar_app_legend(title):
    """Return sidebar link legend HTML"""
    return '<br />'.join(title.split(' '))


@register.simple_tag
def get_admin_warning():
    """Return Django admin warning HTML"""
    ret = (
        '<p class="text-danger">SODAR Taskflow is '
        'enabled. Modifications made in the Django admin view '
        'are <strong>not</strong> automatically mirrored in '
        'remote systems managed by SODAR Taskflow.</p>'
    )
    ret += (
        '<p class="text-danger">Actions taken in the admin view may '
        'result in system malfunction or data loss! Please proceed with '
        'caution.</p>'
    )
    ret += (
        '<p><a class="btn btn-danger pull-right" role="button" '
        'target="_blank" href="{}">'
        '<i class="fa fa-gears"></i> Continue to Django Admin'
        '</a></p>'.format(reverse('admin:index'))
    )
    return ret
