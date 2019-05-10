from django import template

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI

from ..models import File, HyperLink, FILESFOLDERS_FLAGS


APP_NAME = 'filesfolders'

register = template.Library()

# App settings API
app_settings = AppSettingAPI()


@register.filter
def get_class(obj):
    return obj.__class__.__name__


@register.simple_tag
def get_details_items(project):
    """Return recent files/links for card on project details page"""
    files = File.objects.filter(project=project).order_by('-date_modified')[:5]
    links = HyperLink.objects.filter(project=project).order_by(
        '-date_modified'
    )[:5]
    ret = list(files) + list(links)
    ret.sort(key=lambda x: x.date_modified, reverse=True)
    return ret[:5]


@register.simple_tag
def allow_public_links(project):
    """Return the boolean value for allow_public_links in project settings"""
    return app_settings.get_app_setting(APP_NAME, 'allow_public_links', project)


@register.simple_tag
def get_file_icon(file):
    """Return file icon"""
    mt = file.file.file.mimetype

    if mt == 'application/pdf':
        return 'file-pdf-o'

    elif (
        mt == 'application/vnd.openxmlformats-officedocument.'
        'presentationml.presentation'
    ):
        return 'file-powerpoint-o'

    elif 'compressed' in mt or 'zip' in mt:
        return 'file-archive-o'

    elif (
        'excel' in mt
        or mt == 'application/vnd.openxmlformats-'
        'officedocument.spreadsheetml.sheet'
    ):
        return 'file-excel-o'

    elif 'image/' in mt:
        return 'file-image-o'

    elif 'text/' in mt:
        return 'file-text-o'

    # Default if not found
    return 'file-o'


@register.simple_tag
def get_flag(flag_name, tooltip=True):
    """Return item flag HTML"""
    f = FILESFOLDERS_FLAGS[flag_name]
    tip_str = ''

    if tooltip:
        tip_str = (
            'title="{}" data-toggle="tooltip" '
            'data-placement="top"'.format(f['label'])
        )

    return (
        '<i class="fa fa-{} fa-fw text-{} sodar-ff-flag-icon" {}>'
        '</i>'.format(f['icon'], f['color'], tip_str)
    )


@register.simple_tag
def get_flag_status(val, choice):
    """Return item flag status HTML for form"""
    if val == choice:
        return 'checked="checked"'
    return ''


@register.simple_tag
def get_flag_classes(flag_name):
    """Return CSS classes for item link based on flag name"""
    return FILESFOLDERS_FLAGS[flag_name]['text_classes']
