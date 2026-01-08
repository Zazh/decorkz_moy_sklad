# integration/management/commands/reset_pim_data.py

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Очистка всех данных PIM (кроме пользователей и справочников Units)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Подтверждение удаления данных'
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                '\n⚠️  Эта команда удалит ВСЕ данные из таблиц PIM!\n'
                '   Будут сохранены: пользователи, UnitGroup, Unit\n'
                '\n   Для подтверждения добавьте --confirm\n'
            ))
            return

        self.stdout.write('\n🗑️  Начинаем очистку данных...\n')

        # Порядок важен из-за FK
        tables_to_clear = [
            # cards
            ('pim_product_card_attribute', 'Атрибуты карточек'),
            ('pim_product_card_image', 'Изображения карточек'),
            ('pim_product_card', 'Карточки контента'),

            # products
            ('pim_product', 'Товары'),

            # scraping
            ('scraping_scrapedimage', 'Спарсенные изображения'),
            ('scraping_parserrun', 'Логи парсеров'),
            ('scraping_scrapedproduct', 'Спарсенные товары'),

            # inventory
            ('pim_stock', 'Остатки'),
            ('pim_warehouse', 'Склады'),

            # pricing
            ('pim_price', 'Цены'),
            ('pim_price_type', 'Типы цен'),

            # mapping
            ('mapping_attribute', 'Маппинг атрибутов'),
            ('mapping_category', 'Маппинг категорий'),
            ('mapping_brand', 'Маппинг брендов'),

            # integration
            ('integration_sync_log', 'Логи синхронизации'),
            ('integration_moysklad_order', 'Заказы МойСклад'),
            ('integration_moysklad_product', 'Товары МойСклад'),
            ('integration_moysklad_category', 'Категории МойСклад'),
            ('integration_moysklad_brand', 'Бренды МойСклад'),

            # references (кроме Units)
            ('ref_category', 'Категории'),
            ('ref_attribute', 'Атрибуты'),
            ('ref_brand', 'Бренды'),
        ]

        with connection.cursor() as cursor:
            for table_name, description in tables_to_clear:
                try:
                    cursor.execute(f'TRUNCATE TABLE "{table_name}" CASCADE;')
                    self.stdout.write(f'  ✓ {description} ({table_name})')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'  ⚠ {description} ({table_name}): {e}'
                    ))

        self.stdout.write(self.style.SUCCESS('\n✅ Очистка завершена!\n'))
        self.stdout.write('Сохранены: пользователи, UnitGroup, Unit\n')