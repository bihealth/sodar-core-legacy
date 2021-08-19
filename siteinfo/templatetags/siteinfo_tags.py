from django import template

register = template.Library()


@register.simple_tag
def get_info_cls(value, base_class='col-md-7'):
    """Return info element class"""
    c = base_class
    if value == '':
        c += ' text-muted'
    return c


@register.simple_tag
def get_info_val(value):
    """Return info element value"""
    if value == '':
        value = '(Empty value)'
    return value
