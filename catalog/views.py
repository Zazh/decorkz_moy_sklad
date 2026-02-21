from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count, Subquery, OuterRef, Exists

from products.models import Product
from references.models import Category, Brand
from cards.models import ProductCardImage
from pricing.models import Price
from catalog.filters import apply_filters, get_base_queryset


def dashboard(request):
    """Дашборд: дерево категорий + статистика качества данных."""
    total = Product.objects.filter(is_active=True).count()

    stats = Product.objects.filter(is_active=True).aggregate(
        with_card=Count('card'),
        with_brand=Count('brand'),
        with_category=Count('category'),
        with_moysklad=Count('moysklad'),
    )

    with_images = Product.objects.filter(
        is_active=True, card__images__isnull=False
    ).distinct().count()

    with_price = Product.objects.filter(
        is_active=True,
        prices__price_type__name='РРЦ',
        prices__is_active=True
    ).distinct().count()

    with_description = Product.objects.filter(
        is_active=True, card__isnull=False
    ).exclude(card__description='').count()

    # Категории с количеством товаров
    root_categories = Category.objects.filter(
        parent__isnull=True, is_active=True
    ).prefetch_related('children').annotate(
        product_count=Count('products', filter=Q(products__is_active=True)),
    ).order_by('sort_order', 'title')

    # Подготовим дерево с children_list и их product_count
    cat_tree = []
    child_counts = dict(
        Category.objects.filter(
            parent__isnull=False, is_active=True
        ).annotate(
            product_count=Count('products', filter=Q(products__is_active=True)),
        ).values_list('id', 'product_count')
    )

    for root in root_categories:
        children = root.children.filter(is_active=True).order_by('sort_order', 'title')
        children_list = []
        for child in children:
            child.product_count = child_counts.get(child.id, 0)
            child.children_list = []
            children_list.append(child)
        root.children_list = children_list
        cat_tree.append(root)

    # Товары без категории
    no_category_count = Product.objects.filter(
        is_active=True, category__isnull=True
    ).count()

    context = {
        'total': total,
        'stats': stats,
        'with_images': with_images,
        'with_price': with_price,
        'with_description': with_description,
        'cat_tree': cat_tree,
        'no_category_count': no_category_count,
    }
    return render(request, 'catalog/dashboard.html', context)


def product_list(request, slug=None):
    """Каталог товаров с фильтрами."""
    category = None
    category_ids = None

    if slug:
        category = get_object_or_404(Category, slug=slug, is_active=True)
        # Включаем дочерние категории
        category_ids = [category.id]
        category_ids += list(
            category.children.filter(is_active=True).values_list('id', flat=True)
        )

    # Базовый queryset с аннотациями
    qs = get_base_queryset()

    if category_ids:
        qs = qs.filter(category_id__in=category_ids)

    # Для подсчётов в сайдбаре (до применения фильтров)
    base_qs = qs

    # Применяем фильтры
    qs, active_filters = apply_filters(qs, request.GET)

    # Сортировка
    sort = request.GET.get('sort', 'article')
    sort_options = {
        'article': 'article',
        '-article': '-article',
        'title': 'card__title',
        '-title': '-card__title',
        'price': 'rrp_price',
        '-price': '-rrp_price',
    }
    qs = qs.order_by(sort_options.get(sort, 'article'))

    # Подсчёты для фильтров в сайдбаре
    sidebar = build_sidebar_counts(base_qs, category)

    # Пагинация
    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # Хлебные крошки
    breadcrumbs = []
    if category:
        if category.parent:
            breadcrumbs.append(category.parent)
        breadcrumbs.append(category)

    context = {
        'category': category,
        'page_obj': page_obj,
        'paginator': paginator,
        'active_filters': active_filters,
        'sidebar': sidebar,
        'sort': sort,
        'breadcrumbs': breadcrumbs,
        'total_filtered': paginator.count,
    }
    return render(request, 'catalog/product_list.html', context)


def product_detail(request, pk):
    """Детальная страница товара."""
    product = get_object_or_404(
        Product.objects.select_related(
            'brand', 'category', 'category__parent',
            'card', 'moysklad'
        ),
        pk=pk
    )

    images = []
    attributes = []
    if product.card:
        images = product.card.images.all().order_by('-is_main', 'sort_order')
        attributes = product.card.attributes.select_related(
            'attribute', 'attribute__default_unit'
        ).all()

    prices = product.prices.select_related('price_type').order_by('price_type__sort_order')

    # Полнота данных
    completeness = {
        'Карточка': product.card is not None,
        'Фото': images.exists() if hasattr(images, 'exists') else bool(images),
        'Описание': bool(product.card and product.card.description),
        'Бренд': product.brand is not None,
        'Категория': product.category is not None,
        'Цена': prices.filter(price_type__name='РРЦ').exists(),
        'Атрибуты': attributes.exists() if hasattr(attributes, 'exists') else bool(attributes),
    }

    context = {
        'product': product,
        'images': images,
        'attributes': attributes,
        'prices': prices,
        'completeness': completeness,
    }
    return render(request, 'catalog/product_detail.html', context)


def build_sidebar_counts(base_qs, category):
    """Подсчёты для боковой панели фильтров."""
    total = base_qs.count()

    # Бренды
    brand_counts = list(
        base_qs.filter(brand__isnull=False)
        .values('brand__slug', 'brand__name')
        .annotate(count=Count('id'))
        .order_by('brand__name')
    )
    no_brand_count = base_qs.filter(brand__isnull=True).count()

    # Фото
    has_photo = base_qs.filter(card__images__isnull=False).distinct().count()
    no_photo = total - has_photo

    # Цена
    has_price = base_qs.filter(
        prices__price_type__name='РРЦ', prices__is_active=True
    ).distinct().count()
    no_price = total - has_price

    # Описание
    has_desc = base_qs.filter(
        card__isnull=False
    ).exclude(card__description='').count()

    # Источник
    source_counts = list(
        base_qs.filter(card__isnull=False)
        .values('card__source')
        .annotate(count=Count('id'))
        .order_by('card__source')
    )

    # Подкатегории (если мы внутри родительской)
    subcategories = []
    if category and category.children.exists():
        subcategories = list(
            base_qs.filter(category__parent=category)
            .values('category__slug', 'category__title')
            .annotate(count=Count('id'))
            .order_by('category__title')
        )

    return {
        'total': total,
        'brand_counts': brand_counts,
        'no_brand_count': no_brand_count,
        'has_photo': has_photo,
        'no_photo': no_photo,
        'has_price': has_price,
        'no_price': no_price,
        'has_desc': has_desc,
        'no_desc': total - has_desc,
        'source_counts': source_counts,
        'subcategories': subcategories,
    }
