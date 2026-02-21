from django.db.models import Q, Count, Subquery, OuterRef

from products.models import Product
from pricing.models import Price


def get_base_queryset():
    """Базовый queryset с аннотациями (цена, кол-во фото)."""
    rrp_subquery = Price.objects.filter(
        product_id=OuterRef('pk'),
        price_type__name='РРЦ',
        is_active=True
    ).values('price')[:1]

    return Product.objects.filter(
        is_active=True
    ).select_related(
        'brand', 'category', 'category__parent', 'card', 'moysklad'
    ).annotate(
        rrp_price=Subquery(rrp_subquery),
        image_count=Count('card__images', distinct=True),
        attr_count=Count('card__attributes', distinct=True),
    )


def apply_filters(queryset, params):
    """Применить все фильтры из GET-параметров."""
    active = {}

    # Бренд
    brands = params.getlist('brand')
    if brands:
        if 'none' in brands:
            queryset = queryset.filter(brand__isnull=True)
            active['brand'] = ['none']
        else:
            queryset = queryset.filter(brand__slug__in=brands)
            active['brand'] = brands

    # Фото
    has_photo = params.get('has_photo')
    if has_photo == '1':
        queryset = queryset.filter(image_count__gt=0)
        active['has_photo'] = '1'
    elif has_photo == '0':
        queryset = queryset.filter(image_count=0)
        active['has_photo'] = '0'

    # Цена
    price_min = params.get('price_min')
    price_max = params.get('price_max')
    if price_min:
        try:
            queryset = queryset.filter(rrp_price__gte=int(price_min))
            active['price_min'] = price_min
        except ValueError:
            pass
    if price_max:
        try:
            queryset = queryset.filter(rrp_price__lte=int(price_max))
            active['price_max'] = price_max
        except ValueError:
            pass

    has_price = params.get('has_price')
    if has_price == '1':
        queryset = queryset.filter(rrp_price__isnull=False)
        active['has_price'] = '1'
    elif has_price == '0':
        queryset = queryset.filter(rrp_price__isnull=True)
        active['has_price'] = '0'

    # Описание
    has_description = params.get('has_description')
    if has_description == '1':
        queryset = queryset.filter(card__isnull=False).exclude(card__description='')
        active['has_description'] = '1'
    elif has_description == '0':
        queryset = queryset.filter(Q(card__isnull=True) | Q(card__description=''))
        active['has_description'] = '0'

    # Атрибуты
    has_attributes = params.get('has_attributes')
    if has_attributes == '1':
        queryset = queryset.filter(attr_count__gt=0)
        active['has_attributes'] = '1'
    elif has_attributes == '0':
        queryset = queryset.filter(attr_count=0)
        active['has_attributes'] = '0'

    # Источник
    source = params.get('source')
    if source in ('manual', 'parsed', 'moysklad'):
        queryset = queryset.filter(card__source=source)
        active['source'] = source

    # Категория
    has_category = params.get('has_category')
    if has_category == '0':
        queryset = queryset.filter(category__isnull=True)
        active['has_category'] = '0'
    elif has_category == '1':
        queryset = queryset.filter(category__isnull=False)
        active['has_category'] = '1'

    # Поиск
    q = params.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(article__icontains=q) |
            Q(card__title__icontains=q) |
            Q(moysklad__name__icontains=q)
        )
        active['q'] = q

    return queryset, active
