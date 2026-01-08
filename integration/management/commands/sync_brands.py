# integration/management/commands/sync_brands.py

from django.core.management.base import BaseCommand
from collections import defaultdict

from integration.models import MoySkladProduct
from mapping.models import BrandMapping


class Command(BaseCommand):
    help = 'Создание маппингов брендов из МойСклад'

    EXCLUDED_PATHS = [
        'Реклама',
        'Услуги',
        'Основные средства',
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать что будет создано'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write('=' * 60)
        self.stdout.write('Сбор брендов из МойСклад → BrandMapping')
        self.stdout.write('=' * 60)

        # Собираем уникальные названия брендов с количеством
        brand_counts = defaultdict(int)

        for ms in MoySkladProduct.objects.filter(archived=False):
            path_name = ms.path_name or ''
            if any(path_name.startswith(ex) for ex in self.EXCLUDED_PATHS):
                continue

            raw = ms.raw_data or {}
            for attr in raw.get('attributes', []):
                if attr.get('name') == 'Бренд' and attr.get('value'):
                    brand_name = str(attr['value']).strip()
                    if brand_name:
                        brand_counts[brand_name] += 1
                    break

        self.stdout.write(f'\nНайдено уникальных названий: {len(brand_counts)}')

        created = 0
        exists = 0

        # Сортируем по количеству товаров (больше → выше)
        sorted_brands = sorted(brand_counts.items(), key=lambda x: -x[1])

        for brand_name, count in sorted_brands:
            # Проверяем существует ли маппинг
            mapping_exists = BrandMapping.objects.filter(
                source='moysklad',
                source_name=brand_name
            ).exists()

            if mapping_exists:
                exists += 1
                continue

            if dry_run:
                self.stdout.write(f'  [NEW] {brand_name} ({count} товаров)')
            else:
                BrandMapping.objects.create(
                    source='moysklad',
                    source_name=brand_name,
                    brand=None  # Ждёт связи в админке
                )
                self.stdout.write(f'  + {brand_name} ({count} товаров)')

            created += 1

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(f'Создано маппингов: {created}')
        self.stdout.write(f'Уже существует: {exists}')
        self.stdout.write('=' * 60)

        if not dry_run and created > 0:
            self.stdout.write('\nТеперь перейди в админку:')
            self.stdout.write('  1. Создай бренды в Справочники → Бренды')
            self.stdout.write('  2. Свяжи маппинги в Маппинг → Маппинг брендов')