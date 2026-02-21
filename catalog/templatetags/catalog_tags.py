import json
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def query_string(context, **kwargs):
    """Build query string preserving current GET params."""
    request = context['request']
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = str(value)
    qs = params.urlencode()
    return f'?{qs}' if qs else ''


@register.filter
def format_price(value):
    """12345.00 -> 12 345"""
    if value is None:
        return '—'
    try:
        return f'{int(value):,}'.replace(',', ' ')
    except (ValueError, TypeError):
        return str(value)


@register.filter
def format_json(value):
    """Pretty-print JSON."""
    if value is None:
        return ''
    try:
        return json.dumps(value, indent=2, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)


@register.filter
def percent(value, total):
    """Calculate percentage."""
    if not total:
        return 0
    try:
        return round(value / total * 100)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
