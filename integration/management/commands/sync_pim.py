# integration/management/commands/sync_pim.py

from django.core.management.base import BaseCommand
from integration.services.sync_pim import PIMSyncService


class Command(BaseCommand):
    help = 'Синхронизация MoySkladProduct → Product'

    def handle(self, *args, **options):
        self.stdout.write('Синхронизация товаров...')

        service = PIMSyncService()
        result = service.sync_products()

        self.stdout.write(self.style.SUCCESS(
            f"\nГотово!\n"
            f"  Создано: {result['created']}\n"
            f"  Обновлено: {result['updated']}\n"
            f"  Пропущено: {result['skipped']}\n"
            f"  Ошибок: {result['errors']}\n"
            f"  Архивных деактивировано: {result['archived_deactivated']}\n"
            f"  Категорий деактивировано: {result['cats_deactivated']}\n"
            f"  Всего: {result['total']}"
        ))