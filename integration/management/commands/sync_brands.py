# integration/management/commands/sync_brands.py

from django.core.management.base import BaseCommand
from catalog.translit import translit_slugify
from collections import defaultdict

from integration.models import MoySkladProduct
from references.models import Brand
from mapping.models import BrandMapping

EXCLUDED_CATEGORIES = [
    'Реклама',
    'Не загружать (прочее)',
]


class Command(BaseCommand):
    help = 'Синхронизация брендов из МойСклад → Brand + BrandMapping'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать что будет создано'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write('=' * 60)
        self.stdout.write('Синхронизация брендов из МойСклад')
        self.stdout.write('=' * 60)

        # Собираем уникальные названия брендов с количеством
        brand_counts = defaultdict(int)

        for ms in MoySkladProduct.objects.filter(archived=False):
            site_cat = ms.site_category or ''
            if site_cat in EXCLUDED_CATEGORIES:
                continue

            raw = ms.raw_data or {}
            for attr in raw.get('attributes', []):
                if attr.get('name') == 'Бренд' and attr.get('value'):
                    brand_name = str(attr['value']).strip()
                    if brand_name:
                        brand_counts[brand_name] += 1
                    break

        self.stdout.write(f'\nНайдено уникальных брендов: {len(brand_counts)}')

        created_brands = 0
        created_mappings = 0
        exists = 0

        sorted_brands = sorted(brand_counts.items(), key=lambda x: -x[1])

        for brand_name, count in sorted_brands:
            # Проверяем существует ли маппинг
            mapping = BrandMapping.objects.filter(
                source='moysklad',
                source_name=brand_name
            ).select_related('brand').first()

            if mapping and mapping.brand:
                exists += 1
                continue

            if dry_run:
                if mapping:
                    self.stdout.write(f'  [LINK] {brand_name} ({count} товаров) — маппинг есть, бренд нет')
                else:
                    self.stdout.write(f'  [NEW]  {brand_name} ({count} товаров)')
                created_brands += 1
                continue

            # Ищем или создаём Brand
            slug = translit_slugify(brand_name)
            brand, brand_created = Brand.objects.get_or_create(
                slug=slug,
                defaults={'name': brand_name},
            )
            if brand_created:
                created_brands += 1
                self.stdout.write(f'  + Бренд: {brand_name}')

            # Ищем или создаём BrandMapping и связываем
            if mapping:
                mapping.brand = brand
                mapping.save()
                self.stdout.write(f'  ~ Связан маппинг: {brand_name}')
            else:
                BrandMapping.objects.create(
                    source='moysklad',
                    source_name=brand_name,
                    brand=brand,
                )
                created_mappings += 1
                self.stdout.write(f'  + Маппинг: {brand_name} ({count} товаров)')

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(f'Новых брендов: {created_brands}')
        self.stdout.write(f'Новых маппингов: {created_mappings}')
        self.stdout.write(f'Уже связаны: {exists}')
        self.stdout.write('=' * 60)
