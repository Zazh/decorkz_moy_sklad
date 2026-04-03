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
        if value is None or value == '':
            params.pop(key, None)
            # Also remove list values (e.g. multiple &brand=)
            while key in params:
                params.pop(key)
        else:
            params[key] = str(value)
    qs = params.urlencode()
    return f'?{qs}' if qs else ''


@register.simple_tag
def get_root_categories():
    """Return active root categories with prefetched children for navigation."""
    from django.db.models import Q, Count, Prefetch
    from references.models import Category

    children_qs = Category.objects.filter(
        is_active=True
    ).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).filter(
        product_count__gt=0
    ).order_by('sort_order', 'title')

    return [
        cat for cat in Category.objects.filter(
            parent__isnull=True, is_active=True
        ).prefetch_related(
            Prefetch('children', queryset=children_qs, to_attr='active_children')
        ).annotate(
            product_count=Count(
                'products', filter=Q(products__is_active=True), distinct=True
            ) + Count(
                'children__products', filter=Q(children__products__is_active=True), distinct=True
            )
        ).order_by('sort_order', 'title')
        if cat.product_count > 0
    ]


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
