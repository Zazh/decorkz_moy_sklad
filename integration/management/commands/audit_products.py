# integration/management/commands/audit_products.py

from collections import Counter

from django.core.management.base import BaseCommand
from django.db.models import Q, Count

from products.models import Product
from integration.models import MoySkladProduct
from mapping.models import BrandMapping, CategoryMapping


# Те же исключения что в sync_pim
EXCLUDED_PATHS = [
    'Реклама',
    'Услуги',
    'Основные средства',
    'Не загружать (прочее)',
]


class Command(BaseCommand):
    help = 'Аудит заполненности товаров: бренд, категория, карточка, цена, размеры'

    def add_arguments(self, parser):
        parser.add_argument(
            '--details',
            action='store_true',
            help='Показать список товаров без данных (первые 20)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Количество примеров в --details (по умолчанию 20)'
        )

    def handle(self, *args, **options):
        show_details = options['details']
        details_limit = options['limit']

        # Исключаем товары из excluded paths
        excluded_q = Q()
        for path in EXCLUDED_PATHS:
            excluded_q |= Q(moysklad__path_name__startswith=path)

        base_qs = Product.objects.filter(is_active=True).exclude(excluded_q)
        total = base_qs.count()

        # Также для MoySkladProduct
        ms_excluded_q = Q()
        for path in EXCLUDED_PATHS:
            ms_excluded_q |= Q(path_name__startswith=path)

        ms_base_qs = MoySkladProduct.objects.filter(archived=False).exclude(ms_excluded_q)

        self.stdout.write(f"\n{'=' * 70}")
        self.stdout.write(f"АУДИТ ТОВАРОВ — активных (без {', '.join(EXCLUDED_PATHS)}): {total}")
        self.stdout.write(f"{'=' * 70}\n")

        # 1. Без бренда
        no_brand = base_qs.filter(brand__isnull=True)
        self.print_stat('Без бренда', no_brand.count(), total)
        if show_details:
            self.print_examples(no_brand, details_limit)

        # 2. Без категории
        no_category = base_qs.filter(category__isnull=True)
        self.print_stat('Без категории', no_category.count(), total)
        if show_details:
            self.print_examples(no_category, details_limit)

        # 3. Без карточки контента
        no_card = base_qs.filter(card__isnull=True)
        self.print_stat('Без карточки', no_card.count(), total)

        # 4. Без цены
        no_price = base_qs.filter(moysklad__isnull=False, moysklad__price__lte=0)
        self.print_stat('Без цены (price ≤ 0)', no_price.count(), total)
        if show_details:
            self.print_examples(no_price, details_limit)

        # 5. С карточкой, но без фото
        no_images = base_qs.filter(
            card__isnull=False
        ).annotate(
            img_count=Count('card__images')
        ).filter(img_count=0)
        self.print_stat('С карточкой, но без фото', no_images.count(), total)

        # 6. Бренды
        self.stdout.write(f"\n{'=' * 70}")
        self.stdout.write("АНАЛИЗ БРЕНДОВ ИЗ МОЙСКЛАД")
        self.stdout.write(f"{'=' * 70}\n")
        self.analyze_brands(ms_base_qs)

        # 7. Категории
        self.stdout.write(f"\n{'=' * 70}")
        self.stdout.write("АНАЛИЗ КАТЕГОРИЙ (path_name)")
        self.stdout.write(f"{'=' * 70}\n")
        self.analyze_categories(ms_base_qs)

        # 8. Размеры / атрибуты
        self.stdout.write(f"\n{'=' * 70}")
        self.stdout.write("АНАЛИЗ РАЗМЕРОВ / ХАРАКТЕРИСТИК")
        self.stdout.write(f"{'=' * 70}\n")
        self.analyze_dimensions(ms_base_qs)

        # Итого
        self.stdout.write(f"\n{'=' * 70}")
        self.stdout.write("ИТОГО")
        self.stdout.write(f"{'=' * 70}\n")

        complete = base_qs.filter(
            brand__isnull=False,
            category__isnull=False,
            card__isnull=False,
            moysklad__price__gt=0,
        )
        self.print_stat('Полные (бренд + категория + карточка + цена)', complete.count(), total)

    def print_stat(self, label, count, total):
        pct = (count / total * 100) if total > 0 else 0
        bar_filled = int(pct / 2)
        bar = '█' * bar_filled + '░' * (50 - bar_filled)

        if pct > 50:
            style = self.style.ERROR
        elif pct > 20:
            style = self.style.WARNING
        else:
            style = self.style.SUCCESS

        self.stdout.write(f"  {label}:")
        self.stdout.write(f"    {style(f'{count:>5} / {total}')} ({pct:.1f}%)")
        self.stdout.write(f"    [{bar}]")
        self.stdout.write("")

    def print_examples(self, queryset, limit):
        items = queryset.select_related('moysklad')[:limit]
        for item in items:
            parts = [f"  → {item.article}"]
            if item.moysklad:
                parts.append(f"| {item.moysklad.name[:40]}")
                if item.moysklad.path_name:
                    parts.append(f"| {item.moysklad.path_name[:30]}")
            self.stdout.write(' '.join(parts))

        remaining = queryset.count() - limit
        if remaining > 0:
            self.stdout.write(f"  ... и ещё {remaining}")
        self.stdout.write("")

    def analyze_brands(self, ms_qs):
        brand_counter = Counter()
        no_brand_count = 0
        total_checked = 0

        for ms in ms_qs.only('raw_data'):
            raw = ms.raw_data or {}
            total_checked += 1
            brand_found = False

            for attr in raw.get('attributes', []):
                if attr.get('name') == 'Бренд' and attr.get('value'):
                    brand_name = str(attr['value']).strip()
                    if brand_name:
                        brand_counter[brand_name] += 1
                        brand_found = True
                    break

            if not brand_found:
                no_brand_count += 1

        self.stdout.write(f"  Проверено: {total_checked}")
        self.stdout.write(f"  С брендом: {total_checked - no_brand_count}")
        self.stdout.write(f"  Без бренда: {no_brand_count}")
        self.stdout.write(f"\n  Топ брендов:\n")

        for brand_name, count in brand_counter.most_common(30):
            mapping = BrandMapping.objects.filter(
                source='moysklad', source_name=brand_name
            ).select_related('brand').first()

            if mapping and mapping.brand:
                status = f"✓ → {mapping.brand.name}"
            elif mapping:
                status = "⚠ маппинг без бренда"
            else:
                status = "✗ нет маппинга"

            self.stdout.write(f"    {count:>4}  {brand_name:<30} {status}")

    def analyze_categories(self, ms_qs):
        path_counter = Counter()

        for ms in ms_qs.only('path_name'):
            path = ms.path_name or '(пусто)'
            top_level = path.split('/')[0] if '/' in path else path
            path_counter[top_level] += 1

        self.stdout.write(f"  Категории верхнего уровня:\n")

        for path, count in path_counter.most_common(30):
            mapping = CategoryMapping.objects.filter(
                source='moysklad', source_name__startswith=path
            ).first()

            if mapping:
                status = f"✓ → {mapping.category.title}"
            else:
                status = "✗ нет маппинга"

            self.stdout.write(f"    {count:>4}  {path:<40} {status}")

    def analyze_dimensions(self, ms_qs):
        attr_names = Counter()
        has_any_dimension = 0
        total_checked = 0

        dimension_keywords = [
            'длина', 'высота', 'ширина', 'толщина', 'размер',
            'вес', 'масса', 'диаметр', 'объём', 'объем',
        ]

        for ms in ms_qs.only('raw_data'):
            raw = ms.raw_data or {}
            total_checked += 1
            found = False

            for attr in raw.get('attributes', []):
                attr_name = attr.get('name', '')
                attr_names[attr_name] += 1
                if any(kw in attr_name.lower() for kw in dimension_keywords):
                    found = True

            if found:
                has_any_dimension += 1

        self.stdout.write(f"  Проверено: {total_checked}")
        self.stdout.write(f"  С размерами: {has_any_dimension}")
        self.stdout.write(f"  Без размеров: {total_checked - has_any_dimension}")
        self.stdout.write(f"\n  Все атрибуты из raw_data:\n")

        for name, count in attr_names.most_common(30):
            is_dim = '📏' if any(kw in name.lower() for kw in dimension_keywords) else '  '
            self.stdout.write(f"    {is_dim} {count:>4}  {name}")