# integration/management/commands/sync_all.py

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Полная синхронизация МойСклад → PIM (все этапы по порядку)'

    def add_arguments(self, parser):
        parser.add_argument('--no-images', action='store_true', help='Без скачивания фото')

    def handle(self, *args, **options):
        steps = [
            ('sync_products', 'Загрузка товаров из МойСклад', {}),
            ('sync_brands', 'Синхронизация брендов', {}),
            ('sync_site_categories', 'Создание категорий', {}),
            ('sync_pim', 'Синхронизация PIM (Product)', {}),
            ('sync_cards', 'Карточки контента + фото', {'no_images': options['no_images']}),
            ('sync_prices', 'Синхронизация цен', {}),
        ]

        total = len(steps)

        for i, (command, description, kwargs) in enumerate(steps, 1):
            self.stdout.write(f'\n{"=" * 60}')
            self.stdout.write(f'[{i}/{total}] {description}')
            self.stdout.write('=' * 60)

            try:
                call_command(command, **kwargs)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка на шаге {command}: {e}'))
                return

        self.stdout.write(f'\n{"=" * 60}')
        self.stdout.write(self.style.SUCCESS('Полная синхронизация завершена!'))
        self.stdout.write('=' * 60)
