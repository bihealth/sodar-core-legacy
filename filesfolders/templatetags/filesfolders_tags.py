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
    ret = 'file-outline'
    mt = file.file.file.mimetype
    if mt == 'application/pdf':
        ret = 'file-pdf-outline'
    elif (
        mt == 'application/vnd.openxmlformats-officedocument.'
        'presentationml.presentation'
    ):
        ret = 'file-powerpoint-outline'
    elif 'compressed' in mt or 'zip' in mt:
        ret = 'archive-outline'
    elif (
        'excel' in mt
        or mt == 'application/vnd.openxmlformats-'
        'officedocument.spreadsheetml.sheet'
    ):
        ret = 'file-excel-outline'
    elif 'image/' in mt:
        ret = 'file-image-outline'
    elif 'text/' in mt:
        ret = 'file-document-outline'
    # Default if not found
    return 'mdi:' + ret


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
        '<i class="iconify text-{} sodar-ff-flag-icon" data-icon="{}" {}>'
        '</i>'.format(f['color'], f['icon'], tip_str)
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
