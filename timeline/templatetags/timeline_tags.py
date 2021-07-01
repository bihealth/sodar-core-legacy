import html

from django import template
from django.urls import reverse
from django.utils.timezone import localtime

# Projectroles dependency
from projectroles.plugins import get_app_plugin

from timeline.api import TimelineAPI
from timeline.models import ProjectEvent

timeline = TimelineAPI()
register = template.Library()

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
def get_event_description(event, request=None):
    """Return printable version of event description"""
    return timeline.get_event_description(event, request)


@register.simple_tag
def get_details_events(project, view_classified):
    """Return recent events for card on project details page"""
    events = ProjectEvent.objects.filter(project=project)

    if not view_classified:
        events = events.exclude(classified=True)

    events = events.order_by('-pk')

    return [x for x in events if x.get_current_status().status_type == 'OK'][:5]


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
def get_app_url(event):
    """Return URL for event application"""
    url_kwargs = {}
    if event.project:
        url_kwargs['project'] = event.project.sodar_uuid

    # Projectroles is a special case
    if event.app == 'projectroles' and event.project:
        return reverse('projectroles:detail', kwargs=url_kwargs)
    elif event.app != 'projectroles':
        app_plugin = get_app_plugin(event.app, plugin_type='project_app')
        if app_plugin:
            return reverse(
                app_plugin.entry_point_url_id,
                kwargs=url_kwargs,
            )
        # Try site apps
        app_plugin = get_app_plugin(event.app, plugin_type='site_app')
        if app_plugin:
            return reverse(app_plugin.entry_point_url_id)
    return '#'


@register.simple_tag
def get_event_details(event):
    """Return HTML data for event detail popover"""
    ret = (
        '<table class="table table-striped sodar-card-table '
        'sodar-tl-table-detail">\n'
        '<thead>\n<tr><th>Timestamp</th>\n<th>Description</th>\n'
        '<th>Status</th></tr>\n</thead>\n<tbody>'
    )
    status_changes = event.get_status_changes(reverse=True)

    for status in status_changes:
        ret += (
            '\n<tr><td>{}</td>\n<td>{}</td>\n'
            '<td class="{}">{}</td>\n</tr>'.format(
                localtime(status.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                status.description[:256]
                + (
                    '<em class="text-muted"> (...)</em>'
                    if len(status.description) > 256
                    else ''
                ),
                get_status_style(status),
                status.status_type,
            )
        )
    ret += '\n</tbody>\n</table>'
    return ret


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
def collect_extra_data(event: ProjectEvent):
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
def has_extra_data(event: ProjectEvent):
    if event.extra_data is not None and len(event.extra_data) > 0:
        return True

    for status in event.get_status_changes():
        if status.extra_data is not None and len(status.extra_data) > 0:
            return True

    return False
