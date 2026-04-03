# integration/management/commands/sync_all.py

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.core.cache import cache
from django.test import RequestFactory

from references.models import Category


class Command(BaseCommand):
    help = 'Полная синхронизация МойСклад → PIM (все этапы по порядку)'

    def add_arguments(self, parser):
        parser.add_argument('--no-images', action='store_true', help='Без скачивания фото')

    def handle(self, *args, **options):
        steps = [
            ('sync_products', 'Загрузка товаров из МойСклад', {}),
            ('sync_brands', 'Синхронизация брендов', {}),
            ('sync_pim', 'Синхронизация PIM (Product + категории)', {}),
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

        # Сбрасываем кэш каталога
        cache.clear()
        self.stdout.write(self.style.SUCCESS('Кэш каталога очищен'))

        # Прогреваем кэш
        self._warmup_cache()

        self.stdout.write(f'\n{"=" * 60}')
        self.stdout.write(self.style.SUCCESS('Полная синхронизация завершена!'))
        self.stdout.write('=' * 60)

    def _warmup_cache(self):
        """Прогрев кэша: главная, каталог, первая страница каждой категории."""
        from catalog.store_views import home, catalog_root, catalog_by_category

        from django.conf import settings
        host = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost'
        factory = RequestFactory(SERVER_NAME=host)
        warmed = 0

        # Главная
        home(factory.get('/'))
        warmed += 1

        # Каталог
        catalog_root(factory.get('/catalog/'))
        warmed += 1

        # Категории
        slugs = list(
            Category.objects.filter(is_active=True).values_list('slug', flat=True)
        )
        for slug in slugs:
            try:
                catalog_by_category(factory.get(f'/catalog/{slug}/'), slug=slug)
                warmed += 1
            except Exception:
                pass

        self.stdout.write(self.style.SUCCESS(f'Кэш прогрет: {warmed} страниц'))
