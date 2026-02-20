# integration/management/commands/sync_prices.py

import logging
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone

from products.models import Product
from pricing.models import PriceType, Price
from integration.models import SyncLog

logger = logging.getLogger(__name__)

EXCLUDED_CATEGORIES = [
    'Реклама',
    'Не загружать (прочее)',
]


class Command(BaseCommand):
    help = 'Синхронизация типов цен и цен из МойСклад'

    def handle(self, *args, **options):
        sync_log = SyncLog.objects.create(sync_type='products', status='started')

        try:
            # Этап 1: Синхронизация типов цен
            self.stdout.write('=' * 60)
            self.stdout.write('Этап 1: Типы цен (PriceType)')
            self.stdout.write('=' * 60)
            price_types_map = self._sync_price_types()

            # Этап 2: Синхронизация цен товаров
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write('Этап 2: Цены товаров (Price)')
            self.stdout.write('=' * 60)
            result = self._sync_prices(price_types_map)

            sync_log.status = 'success'
            sync_log.items_processed = result['total']
            sync_log.items_created = result['created']
            sync_log.items_updated = result['updated']
            sync_log.finished_at = timezone.now()
            sync_log.save()

            self.stdout.write(self.style.SUCCESS(
                f'\nГотово!\n'
                f'  Товаров обработано: {result["total"]}\n'
                f'  Цен создано: {result["created"]}\n'
                f'  Цен обновлено: {result["updated"]}\n'
                f'  Ошибок: {result["errors"]}'
            ))

        except Exception as e:
            sync_log.status = 'error'
            sync_log.error_message = str(e)
            sync_log.finished_at = timezone.now()
            sync_log.save()
            raise

    def _sync_price_types(self):
        """Собрать уникальные типы цен из raw_data всех товаров и создать PriceType."""
        products = Product.objects.filter(
            moysklad__isnull=False,
            is_active=True,
        ).select_related('moysklad')

        # Собираем уникальные типы
        types_seen = {}  # moysklad_id → {name, externalCode}

        for product in products:
            raw = product.moysklad.raw_data or {}
            for sp in raw.get('salePrices', []):
                pt = sp.get('priceType', {})
                pt_id = pt.get('id')
                if pt_id and pt_id not in types_seen:
                    types_seen[pt_id] = {
                        'name': pt.get('name', ''),
                        'external_code': pt.get('externalCode', ''),
                    }

        created = 0
        updated = 0
        price_types_map = {}  # moysklad_id → PriceType

        for ms_id, data in types_seen.items():
            pt, was_created = PriceType.objects.update_or_create(
                moysklad_id=ms_id,
                defaults={
                    'name': data['name'],
                    'external_code': data['external_code'],
                }
            )
            price_types_map[ms_id] = pt
            if was_created:
                created += 1
                self.stdout.write(f'  + {data["name"]}')
            else:
                updated += 1

        self.stdout.write(f'\nТипов цен: {created} создано, {updated} обновлено')
        return price_types_map

    def _sync_prices(self, price_types_map):
        """Создать/обновить Price для каждого товара по каждому типу цены."""
        products = Product.objects.filter(
            moysklad__isnull=False,
            is_active=True,
        ).select_related('moysklad')

        for cat in EXCLUDED_CATEGORIES:
            products = products.exclude(moysklad__site_category=cat)

        total = 0
        created = 0
        updated = 0
        errors = 0

        for product in products:
            raw = product.moysklad.raw_data or {}
            sale_prices = raw.get('salePrices', [])

            for sp in sale_prices:
                pt_id = sp.get('priceType', {}).get('id')
                if not pt_id or pt_id not in price_types_map:
                    continue

                value = Decimal(str(sp.get('value', 0))) / 100
                price_type = price_types_map[pt_id]

                try:
                    price_obj, was_created = Price.objects.update_or_create(
                        product=product,
                        price_type=price_type,
                        defaults={
                            'price': value,
                            'is_active': value > 0,
                        }
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1
                except Exception as e:
                    errors += 1
                    logger.error(f'Ошибка цены {product.article} / {price_type.name}: {e}')

            total += 1

            if total % 500 == 0:
                self.stdout.write(f'  Обработано: {total}')

        return {
            'total': total,
            'created': created,
            'updated': updated,
            'errors': errors,
        }
