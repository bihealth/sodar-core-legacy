import html

from django import template
from django.urls import reverse
from django.utils.timezone import localtime

from djangoplugins.models import Plugin

from timeline.api import TimelineAPI
from timeline.models import ProjectEvent


timeline = TimelineAPI()
register = template.Library()


ICON_PROJECTROLES = 'mdi:cube'
ICON_UNKNOWN_APP = 'mdi:help-circle'
STATUS_STYLES = {
    'OK': 'bg-success',
    'INIT': 'bg-secondary',
    'SUBMIT': 'bg-warning',
    'FAILED': 'bg-danger',
    'INFO': 'bg-info',
    'CANCEL': 'bg-dark',
}


# Event helpers ----------------------------------------------------------------


@register.simple_tag
def get_timestamp(event):
    """Return printable timestamp of event in local timezone"""
    return localtime(event.get_timestamp()).strftime('%Y-%m-%d %H:%M:%S')


@register.simple_tag
def get_event_description(event, plugin_lookup, request=None):
    """Return printable version of event description"""
    return timeline.get_event_description(event, plugin_lookup, request)


@register.simple_tag
def get_details_events(project, view_classified=False):
    """Return recent events for card on project details page"""
    c_kwargs = {'classified': False} if not view_classified else {}
    return ProjectEvent.objects.filter(project=project, **c_kwargs).order_by(
        '-pk'
    )[:5]


@register.simple_tag
def get_plugin_lookup():
    """Return lookup dict of app plugins with app name as key"""
    return {p.name: p.get_plugin() for p in Plugin.objects.all()}


@register.simple_tag
def get_app_icon_html(event, plugin_lookup):
    """Return icon link HTML for app by plugin lookup"""
    url = None
    url_kwargs = {}
    if event.project:
        url_kwargs['project'] = event.project.sodar_uuid
    title = event.app
    icon = ICON_UNKNOWN_APP  # Default in case the plugin is not found

    if event.app == 'projectroles':
        if event.project:
            url = reverse('projectroles:detail', kwargs=url_kwargs)
        title = 'Projectroles'
        icon = ICON_PROJECTROLES
    elif event.app in plugin_lookup.keys():
        plugin = plugin_lookup[event.app]
        entry_point = getattr(plugin, 'entry_point_url_id', None)
        if entry_point:
            url = reverse(entry_point, kwargs=url_kwargs)
        title = plugin.title
        if getattr(plugin, 'icon', None):
            icon = plugin.icon

    return (
        '<a {} title="{}" data-toggle="tooltip" data-placement="top">'
        '<i class="iconify" data-icon="{}"></i></a>'.format(
            'href="{}"'.format(url) if url else '', title, icon
        )
    )


# Template rendering -----------------------------------------------------------


@register.simple_tag
def get_status_style(status):
    """Retrn status style class"""
    return (
        (STATUS_STYLES[status.status_type] + ' text-light')
        if status.status_type in STATUS_STYLES
        else 'bg-light'
    )


@register.simple_tag
def get_event_extra_data(event):
    return json_to_html(event.extra_data)


def json_to_html(obj):
    str_list = []
    html_print_obj(obj, str_list, 0)
    return ''.join(str_list)


def html_print_obj(obj, str_list: list, indent):
    if isinstance(obj, dict):
        html_print_dict(obj, str_list, indent)
    elif isinstance(obj, list):
        html_print_array(obj, str_list, indent)
    elif isinstance(obj, str):
        str_list.append('&quot;')
        str_list.append(html.escape(obj))
        str_list.append('&quot;')
    elif isinstance(obj, int):
        str_list.append(str(obj))
    elif isinstance(obj, bool):
        str_list.append(str(obj))
    elif obj is None:
        str_list.append('null')


def html_print_dict(dct: dict, str_list, indent):
    str_list.append('<span class="json-open-bracket">{</span>\n')
    str_list.append('<span class="json-collapse-1" style="display: inline;">')

    indent += 1
    for key, value in dct.items():
        str_list.append('<span class="json-indent">')
        str_list.append('  ' * indent)
        str_list.append('</span>')
        str_list.append('<span class="json-property">')

        str_list.append(html.escape(str(key)))

        str_list.append('</span>')
        str_list.append('<span class="json-semi-colon">: </span>')

        str_list.append('<span class="json-value">')
        html_print_obj(value, str_list, indent)

        str_list.append('</span>')
        str_list.append('<span class="json-comma">,</span>\n')

    if len(dct) > 0:
        del str_list[-1]
        str_list.append('\n')

    str_list.append('</span>')
    str_list.append('  ' * (indent - 1))
    str_list.append('<span class="json-close-bracket">}</span>')


def html_print_array(array, str_list, indent):
    str_list.append('<span class="json-open-bracket">[</span>\n')
    str_list.append('<span class="json-collapse-1" style="display: inline;">')

    indent += 1
    for value in array:
        str_list.append('<span class="json-indent">')
        str_list.append('  ' * indent)
        str_list.append('</span>')
        str_list.append('<span class="json-value">')
        html_print_obj(value, str_list, indent)
        str_list.append('</span>')
        str_list.append('<span class="json-comma">,</span>\n')
    if len(array) > 0:
        del str_list[-1]
        str_list.append('\n')

    str_list.append('</span>')
    str_list.append('  ' * (indent - 1))
    str_list.append('<span class="json-close-bracket">]</span>')


# Filters ----------------------------------------------------------------------


@register.filter
def collect_extra_data(event):
    ls = []
    if event.extra_data is not None and len(event.extra_data) > 0:
        ls.append(('extra-data', 'Extra Data', event))
    for status in event.get_status_changes():
        if status.extra_data is not None and len(status.extra_data) > 0:
            ls.append(
                ('status-extra-data', 'Status: ' + status.status_type, status)
            )
    return ls


@register.filter
def has_extra_data(event):
    if event.extra_data is not None and len(event.extra_data) > 0:
        return True
    for status in event.get_status_changes():
        if status.extra_data is not None and len(status.extra_data) > 0:
            return True
    return False
