from django.core.management.base import BaseCommand
from django.utils import timezone
from integration.models import Product, SyncLog
from integration.services.moysklad_api import MoySkladAPI
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Синхронизация остатков товаров из МойСклад'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем синхронизацию остатков...')
        
        sync_log = SyncLog.objects.create(
            sync_type='stock',
            status='started'
        )
        
        try:
            api = MoySkladAPI()
            stock_data = api.get_stock(limit=1000)
            
            items_updated = 0
            
            for item in stock_data.get('rows', []):
                # Извлекаем ID товара из meta.href
                meta = item.get('meta', {})
                href = meta.get('href', '')
                if '/product/' in href:
                    moysklad_id = href.split('/product/')[-1]
                else:
                    continue
                
                try:
                    product = Product.objects.get(moysklad_id=moysklad_id)
                    product.stock = item.get('stock', 0)
                    product.reserve = item.get('reserve', 0)
                    product.save(update_fields=['stock', 'reserve', 'last_sync'])
                    items_updated += 1
                    self.stdout.write(f'  Обновлен остаток: {product.name} - {product.stock} шт.')
                except Product.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'  Товар с ID {moysklad_id} не найден'
                    ))
            
            sync_log.status = 'success'
            sync_log.items_processed = len(stock_data.get('rows', []))
            sync_log.items_updated = items_updated
            sync_log.finished_at = timezone.now()
            sync_log.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'\nСинхронизация остатков завершена: {items_updated} обновлено'
            ))
            
        except Exception as e:
            sync_log.status = 'error'
            sync_log.error_message = str(e)
            sync_log.finished_at = timezone.now()
            sync_log.save()
            
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))
