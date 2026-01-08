# integration/management/commands/sync_pim.py

from django.core.management.base import BaseCommand
from integration.services.sync_pim import PIMSyncService


class Command(BaseCommand):
    help = 'Синхронизация товаров и цен в PIM модели'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stock',
            action='store_true',
            help='Синхронизировать только остатки'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Синхронизировать всё: товары, цены и остатки'
        )

    def handle(self, *args, **options):
        service = PIMSyncService()

        if options['stock']:
            self.stdout.write('Синхронизация остатков...')
            result = service.sync_stock()
            self.stdout.write(self.style.SUCCESS(
                f"Остатки: обновлено {result['updated']} из {result['total']}"
            ))
        elif options['all']:
            self.stdout.write('Синхронизация товаров и цен...')
            result = service.sync_all()
            self.stdout.write(self.style.SUCCESS(
                f"Товары: создано {result['created']}, обновлено {result['updated']}"
            ))

            self.stdout.write('Синхронизация остатков...')
            result = service.sync_stock()
            self.stdout.write(self.style.SUCCESS(
                f"Остатки: обновлено {result['updated']} из {result['total']}"
            ))
        else:
            self.stdout.write('Синхронизация товаров и цен...')
            result = service.sync_all()
            self.stdout.write(self.style.SUCCESS(
                f"Товары: создано {result['created']}, обновлено {result['updated']}"
            ))