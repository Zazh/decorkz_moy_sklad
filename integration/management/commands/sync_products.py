from django.core.management.base import BaseCommand
from django.utils import timezone
from integration.models import Product, SyncLog
from integration.services.moysklad_api import MoySkladAPI
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Синхронизация товаров из МойСклад'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем синхронизацию товаров...')
        
        sync_log = SyncLog.objects.create(
            sync_type='products',
            status='started'
        )
        
        try:
            api = MoySkladAPI()
            products = api.sync_all_products()
            
            items_created = 0
            items_updated = 0
            
            for product_data in products:
                moysklad_id = product_data.get('id')
                
                # Получение цены
                price = 0
                sale_prices = product_data.get('salePrices', [])
                if sale_prices:
                    price = sale_prices[0].get('value', 0) / 100
                
                # Подготовка данных
                product_info = {
                    'name': product_data.get('name', ''),
                    'code': product_data.get('code'),
                    'article': product_data.get('article'),
                    'description': product_data.get('description'),
                    'price': price,
                    'archived': product_data.get('archived', False),
                    'external_code': product_data.get('externalCode'),
                    'raw_data': product_data,
                }
                
                # Создание или обновление товара
                product, created = Product.objects.update_or_create(
                    moysklad_id=moysklad_id,
                    defaults=product_info
                )
                
                if created:
                    items_created += 1
                    self.stdout.write(f'  Создан: {product.name}')
                else:
                    items_updated += 1
                    self.stdout.write(f'  Обновлен: {product.name}')
            
            # Обновление лога
            sync_log.status = 'success'
            sync_log.items_processed = len(products)
            sync_log.items_created = items_created
            sync_log.items_updated = items_updated
            sync_log.finished_at = timezone.now()
            sync_log.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'\nСинхронизация завершена: {items_created} создано, {items_updated} обновлено'
            ))
            
        except Exception as e:
            sync_log.status = 'error'
            sync_log.error_message = str(e)
            sync_log.finished_at = timezone.now()
            sync_log.save()
            
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))
