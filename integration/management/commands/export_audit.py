# integration/management/commands/export_audit.py

import csv
import os
from django.core.management.base import BaseCommand
from django.db.models import Q

from integration.models import MoySkladProduct


EXCLUDED_PATHS = [
    'Реклама',
    'Услуги',
    'Основные средства',
    'Не загружать (прочее)',
]


class Command(BaseCommand):
    help = 'Экспорт аудита товаров в CSV (отдельные файлы по проблемам)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dir',
            type=str,
            default='_data',
            help='Директория для файлов'
        )

    def handle(self, *args, **options):
        out_dir = options['dir']
        os.makedirs(out_dir, exist_ok=True)

        excluded_q = Q()
        for path in EXCLUDED_PATHS:
            excluded_q |= Q(path_name__startswith=path)

        ms_qs = MoySkladProduct.objects.filter(
            archived=False
        ).exclude(excluded_q).order_by('path_name', 'name')

        # Собираем данные один раз
        products = []
        for ms in ms_qs.iterator():
            raw = ms.raw_data or {}
            attrs = {}
            for attr in raw.get('attributes', []):
                name = attr.get('name', '')
                value = attr.get('value', '')
                if isinstance(value, dict):
                    value = value.get('name', str(value))
                attrs[name] = str(value).strip()

            products.append({
                'ms': ms,
                'brand_raw': attrs.get('Бренд', ''),
                'main_group': attrs.get('Глав.группа', ''),
                'sub_group': attrs.get('Подгруппа', ''),
                'material': attrs.get('Материал', ''),
            })

        # 1. Без бренда
        no_brand = [p for p in products if not p['brand_raw']]
        self.write_csv(
            os.path.join(out_dir, '1_no_brand.csv'),
            no_brand,
            ['Артикул', 'Название', 'Путь МойСклад', 'Бренд (заполнить)'],
            lambda p: {
                'Артикул': p['ms'].article or p['ms'].code or '',
                'Название': p['ms'].name,
                'Путь МойСклад': p['ms'].path_name or '',
                'Бренд (заполнить)': '',
            }
        )
        self.stdout.write(f'  1_no_brand.csv — {len(no_brand)} товаров без бренда')

        # 2. Без цены
        no_price = [p for p in products if p['ms'].price <= 0]
        self.write_csv(
            os.path.join(out_dir, '2_no_price.csv'),
            no_price,
            ['Артикул', 'Название', 'Путь МойСклад', 'Текущая цена', 'Цена (заполнить)'],
            lambda p: {
                'Артикул': p['ms'].article or p['ms'].code or '',
                'Название': p['ms'].name,
                'Путь МойСклад': p['ms'].path_name or '',
                'Текущая цена': '0',
                'Цена (заполнить)': '',
            }
        )
        self.stdout.write(f'  2_no_price.csv — {len(no_price)} товаров без цены')

        # 3. Без глав.группы
        no_group = [p for p in products if not p['main_group']]
        self.write_csv(
            os.path.join(out_dir, '3_no_category.csv'),
            no_group,
            ['Артикул', 'Название', 'Путь МойСклад', 'Глав.группа (заполнить)', 'Подгруппа (заполнить)'],
            lambda p: {
                'Артикул': p['ms'].article or p['ms'].code or '',
                'Название': p['ms'].name,
                'Путь МойСклад': p['ms'].path_name or '',
                'Глав.группа (заполнить)': '',
                'Подгруппа (заполнить)': '',
            }
        )
        self.stdout.write(f'  3_no_category.csv — {len(no_group)} товаров без глав.группы')

        self.stdout.write(self.style.SUCCESS(f'\nГотово! Файлы в {os.path.abspath(out_dir)}'))

    def write_csv(self, filepath, data, fieldnames, row_func):
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            for item in data:
                writer.writerow(row_func(item))