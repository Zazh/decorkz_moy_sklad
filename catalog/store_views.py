"""
Storefront views — публичный каталог товаров с SEO.
Используют шаблоны из /templates/ (Tailwind + vanilla JS).

URL-структура (плоская):
  /catalog/                          — все товары
  /catalog/<category>/               — leaf-категория (товары)
  /catalog/<category>/<product>/     — товар
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count, Subquery, OuterRef, F, Exists, Prefetch
from django.http import Http404
from django.core.cache import cache

from products.models import Product
from references.models import Category
from pricing.models import Price
from catalog.filters import apply_filters, get_base_queryset

CACHE_TTL = 60 * 60 * 24  # 24 часа (сбрасывается после sync)


def home(request):
    """Главная страница."""
    return render(request, 'home.html', {
        'og_title': 'Decorkz.kz — магазин молдингов и декора',
        'meta_description': 'Магазин молдингов и декоративных элементов для интерьера. Быстрая доставка по Казахстану.',
        'meta_keywords': 'молдинги, декор, купить, Казахстан, интерьер, каталог',
    })



def catalog_root(request):
    """Каталог — все товары."""
    qs = get_base_queryset()

    # Аннотация: есть ли скидка (old_price > price на РРЦ)
    discount_sub = Price.objects.filter(
        product_id=OuterRef('pk'),
        price_type__name='РРЦ',
        is_active=True,
        old_price__isnull=False,
    ).exclude(old_price__lte=F('price'))
    qs = qs.annotate(has_discount=Exists(discount_sub))

    base_qs = qs
    qs, active_filters = apply_filters(qs, request.GET)

    # Сортировка: распродажа первой, затем по алфавиту
    sort = request.GET.get('sort', 'default')
    if sort == 'default' or sort not in ('title', '-title', 'price', '-price'):
        qs = qs.order_by('-has_discount', 'card__title')
        sort = 'default'
    else:
        sort_options = {
            'title': 'card__title',
            '-title': '-card__title',
            'price': 'rrp_price',
            '-price': '-rrp_price',
        }
        qs = qs.order_by(sort_options.get(sort, 'card__title'))

    sidebar = _build_sidebar(base_qs, None)

    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'nav_categories': _get_nav_categories(),
        'page_obj': page_obj,
        'paginator': paginator,
        'active_filters': active_filters,
        'sidebar': sidebar,
        'sort': sort,
        'active_cat': '',
        'active_parent_cat': '',
        'og_title': 'Каталог — Decorkz.kz',
        'meta_description': 'Каталог молдингов, плинтусов, реек и декоративных элементов. Быстрая доставка по Казахстану.',
        'meta_keywords': 'молдинги, декор, плинтусы, рейки, каталог, Казахстан',
    }
    return render(request, 'catalog.html', context)



def catalog_by_category(request, slug):
    """Каталог по категории — показывает товары категории и всех подкатегорий."""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    return _render_product_list(request, category)



def catalog_or_product(request, slug1, slug2):
    """
    /catalog/<slug1>/<slug2>/
    slug1 — leaf-категория, slug2 — товар.
    """
    product = get_object_or_404(Product, slug=slug2, is_active=True)
    return _render_product_detail(request, product)



def product_detail(request, parent_slug, cat_slug, product_slug):
    """
    /catalog/<parent>/<child>/<product-slug>/
    Старый URL — 301 редирект на новый плоский URL.
    """
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    return redirect(product.get_absolute_url(), permanent=True)


# ═══════════════════════════════════════════════════════════
# Внутренние функции рендеринга
# ═══════════════════════════════════════════════════════════

def _get_nav_categories():
    """Категории для бокового сайдбара (кэш).

    Возвращает root-категории с prefetch подкатегорий.
    Навигация группирует по parent, URL ведут на leaf-категории.
    """
    cached = cache.get('nav_categories')
    if cached is not None:
        return cached

    children_qs = Category.objects.filter(
        is_active=True
    ).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).order_by('sort_order', 'title')

    cats = list(Category.objects.filter(
        parent__isnull=True, is_active=True
    ).prefetch_related(
        Prefetch('children', queryset=children_qs, to_attr='active_children')
    ).annotate(
        product_count=Count(
            'products', filter=Q(products__is_active=True)
        ) + Count(
            'children__products', filter=Q(children__products__is_active=True)
        )
    ).order_by('sort_order', 'title'))

    cache.set('nav_categories', cats, CACHE_TTL)
    return cats


def _render_product_list(request, category):
    """Рендер списка товаров leaf-категории."""
    category_ids = [category.id]
    category_ids += list(
        category.children.filter(is_active=True).values_list('id', flat=True)
    )

    qs = get_base_queryset()
    qs = qs.filter(category_id__in=category_ids)

    base_qs = qs

    # Фильтры
    qs, active_filters = apply_filters(qs, request.GET)

    # Сортировка
    sort = request.GET.get('sort', 'title')
    sort_options = {
        'title': 'card__title',
        '-title': '-card__title',
        'price': 'rrp_price',
        '-price': '-rrp_price',
    }
    qs = qs.order_by(sort_options.get(sort, 'card__title'))

    sidebar = _build_sidebar(base_qs, category)

    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # Определяем активную родительскую категорию для навигации
    subcategories = list(
        category.children.filter(is_active=True)
        .annotate(product_count=Count('products', filter=Q(products__is_active=True)))
        .order_by('sort_order', 'title')
    )
    is_parent = len(subcategories) > 0
    if is_parent:
        active_parent_cat = category.slug
    elif category.parent:
        active_parent_cat = category.parent.slug
    else:
        active_parent_cat = ''

    og_title = f'{category.title} — Decorkz.kz'

    context = {
        'category': category,
        'nav_categories': _get_nav_categories(),
        'active_cat': category.slug,
        'active_parent_cat': active_parent_cat,
        'page_obj': page_obj,
        'paginator': paginator,
        'active_filters': active_filters,
        'sidebar': sidebar,
        'sort': sort,
        'subcategories': subcategories if is_parent else [],
        'breadcrumbs': [category.parent] if category.parent else [],
        'og_title': og_title,
        'meta_description': f'{category.title} — купить молдинги и декор в Казахстане. Широкий ассортимент.',
        'meta_keywords': f'{category.title}, молдинги, декор, купить, Казахстан',
    }
    return render(request, 'catalog.html', context)


def _render_product_detail(request, product):
    """Рендер страницы товара."""
    product = Product.objects.select_related(
        'brand', 'category', 'category__parent',
        'card', 'moysklad'
    ).get(pk=product.pk)

    images = []
    attributes = []
    if product.card:
        images = product.card.images.all().order_by('-is_main', 'sort_order')
        attributes = product.card.attributes.select_related(
            'attribute', 'attribute__default_unit'
        ).all()

    # Цена РРЦ
    rrp_price = None
    rrp = product.prices.filter(
        price_type__name='РРЦ', is_active=True
    ).first()
    if rrp:
        rrp_price = rrp.price

    # Breadcrumbs — только leaf-категория (без parent)
    breadcrumbs = []
    if product.category:
        breadcrumbs.append(product.category)

    # SEO
    og_title = f'{product.title} — Decorkz.kz'
    og_image = ''
    main_img = images.filter(is_main=True).first() if hasattr(images, 'filter') else None
    if not main_img and images:
        main_img = images[0] if images else None
    if main_img:
        og_image = request.build_absolute_uri(main_img.image.url)

    context = {
        'product': product,
        'images': images,
        'attributes': attributes,
        'rrp_price': rrp_price,
        'breadcrumbs': breadcrumbs,
        'og_title': og_title,
        'meta_description': f'{product.title} — купить в Decorkz.kz. {product.short_description[:120] if product.short_description else "Доставка по Казахстану."}',
        'meta_keywords': f'{product.title}, {product.category.title if product.category else "декор"}, молдинги, купить',
        'og_image': og_image,
    }
    return render(request, 'product.html', context)


def _build_sidebar(base_qs, category):
    """Подсчёты для фильтров (кэш 5 мин)."""
    import json
    from django.db.models import Min, Max, Case, When, Value, IntegerField, Sum

    cache_key = f'sidebar_{category.slug if category else "all"}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    total = base_qs.count()

    brand_counts = list(
        base_qs.filter(brand__isnull=False)
        .values('brand__slug', 'brand__name')
        .annotate(count=Count('id'))
        .order_by('brand__name')
    )

    # Price histogram — один запрос вместо 30
    price_qs = base_qs.filter(rrp_price__isnull=False, rrp_price__gt=0)
    agg = price_qs.aggregate(price_min=Min('rrp_price'), price_max=Max('rrp_price'))
    price_min = int(agg['price_min']) if agg['price_min'] else 0
    price_max = int(agg['price_max']) if agg['price_max'] else 0

    price_buckets = []
    if price_min < price_max:
        num_buckets = 30
        step = max(1, (price_max - price_min) // num_buckets)
        annotations = {}
        for i in range(num_buckets):
            lo = price_min + i * step
            hi = lo + step if i < num_buckets - 1 else price_max + 1
            annotations[f'b{i}'] = Sum(Case(
                When(rrp_price__gte=lo, rrp_price__lt=hi, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ))
        result = price_qs.aggregate(**annotations)
        price_buckets = [result.get(f'b{i}', 0) or 0 for i in range(num_buckets)]

    country_counts = list(
        base_qs.filter(country__gt='')
        .values('country')
        .annotate(count=Count('id'))
        .order_by('country')
    )

    sidebar = {
        'total': total,
        'brand_counts': brand_counts,
        'country_counts': country_counts,
        'price_min': price_min,
        'price_max': price_max,
        'price_buckets_json': json.dumps(price_buckets),
    }
    cache.set(cache_key, sidebar, CACHE_TTL)
    return sidebar
