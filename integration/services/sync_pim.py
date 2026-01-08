import logging
from decimal import Decimal

from django.utils import timezone
from django.utils.text import slugify

from references.models import Brand
from products.models import Product
from pricing.models import PriceType, Price
from inventory.models import Warehouse, Stock
from integration.models import SyncLog
from .moysklad_api import MoySkladAPI

logger = logging.getLogger(__name__)


class PIMSyncService:
    """Синхронизация данных из МойСклад в новые PIM модели"""

    # Исключённые группы — не загружаем в PIM
    EXCLUDED_PATHS = [
        'Реклама',
        'Услуги',
        'Основные средства общие',
    ]

    # Маппинг атрибутов МойСклад → поля Product
    ATTRIBUTE_MAPPING = {
        'Товар Каспи': 'is_kaspi',
        'Товар Satu': 'is_satu',
        'Акция': 'is_promo',
    }

    def __init__(self):
        self.api = MoySkladAPI()

    def sync_all(self):
        """Полная синхронизация: товары + цены"""
        sync_log = SyncLog.objects.create(
            sync_type='products',
            status='started'
        )

        try:
            products_data = self.api.sync_all_products()

            created = 0
            updated = 0
            skipped = 0

            for raw_data in products_data:
                result = self._sync_product(raw_data)
                if result is None:
                    skipped += 1
                    continue

                product, is_created = result
                if product:
                    self._sync_prices(product, raw_data)
                    if is_created:
                        created += 1
                    else:
                        updated += 1

            sync_log.status = 'success'
            sync_log.items_processed = len(products_data)
            sync_log.items_created = created
            sync_log.items_updated = updated
            sync_log.finished_at = timezone.now()
            sync_log.save()

            return {'created': created, 'updated': updated, 'skipped': skipped, 'total': len(products_data)}

        except Exception as e:
            logger.error(f"Ошибка синхронизации: {e}")
            sync_log.status = 'error'
            sync_log.error_message = str(e)
            sync_log.finished_at = timezone.now()
            sync_log.save()
            raise

    def _sync_product(self, raw_data: dict):
        """Синхронизация одного товара. Возвращает None если товар исключён."""
        moysklad_id = raw_data.get('id')
        if not moysklad_id:
            return None

        # Проверяем исключённые группы
        moysklad_path = (raw_data.get('pathName') or '')[:500]
        for excluded in self.EXCLUDED_PATHS:
            if moysklad_path.startswith(excluded):
                return None

        # SKU = code (приоритет) или article или id
        sku = raw_data.get('code') or raw_data.get('article') or moysklad_id
        sku = sku[:100]

        # Бренд
        brand = self._get_or_create_brand(raw_data)

        # Штрихкод
        barcodes = raw_data.get('barcodes', [])
        barcode = barcodes[0].get('ean13', '')[:50] if barcodes else ''

        # Флаги из атрибутов
        flags = self._extract_flags(raw_data)

        # Обрезаем длинные поля
        article = (raw_data.get('article') or '')[:100]
        name = (raw_data.get('name') or '')[:500]

        product, created = Product.objects.update_or_create(
            moysklad_id=moysklad_id,
            defaults={
                'sku': sku,
                'article': article,
                'barcode': barcode,
                'name': name,
                'brand': brand,
                'weight': raw_data.get('weight'),
                'volume': raw_data.get('volume'),
                'moysklad_path': moysklad_path,
                'archived': raw_data.get('archived', False),
                'is_kaspi': flags.get('is_kaspi', False),
                'is_satu': flags.get('is_satu', False),
                'is_promo': flags.get('is_promo', False),
                'raw_data': raw_data,
            }
        )

        return product, created

    def _get_or_create_brand(self, raw_data: dict):
        """Извлекает бренд из атрибутов"""
        for attr in raw_data.get('attributes', []):
            if attr.get('name') == 'Бренд' and attr.get('value'):
                brand_name = attr['value'].strip()

                # Сначала ищем по имени
                brand = Brand.objects.filter(name__iexact=brand_name).first()
                if brand:
                    return brand

                # Создаём новый
                base_slug = slugify(brand_name, allow_unicode=True) or 'brand'
                slug = base_slug
                counter = 1
                while Brand.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                brand = Brand.objects.create(
                    name=brand_name,
                    slug=slug
                )
                return brand
        return None

    def _extract_flags(self, raw_data: dict) -> dict:
        """Извлекает флаги из атрибутов"""
        flags = {}
        for attr in raw_data.get('attributes', []):
            field_name = self.ATTRIBUTE_MAPPING.get(attr.get('name'))
            if field_name and attr.get('type') == 'boolean':
                flags[field_name] = attr.get('value', False)
        return flags

    def _sync_prices(self, product: Product, raw_data: dict):
        """Синхронизация цен товара"""
        sale_prices = raw_data.get('salePrices', [])

        for price_data in sale_prices:
            price_type_data = price_data.get('priceType', {})
            price_type_id = price_type_data.get('id')

            if not price_type_id:
                continue

            # Цена в копейках → в тенге
            value = Decimal(price_data.get('value', 0)) / 100

            # Пропускаем нулевые цены
            if value <= 0:
                continue

            # Тип цены
            price_type, _ = PriceType.objects.get_or_create(
                moysklad_id=price_type_id,
                defaults={
                    'name': price_type_data.get('name', 'Без названия'),
                    'external_code': price_type_data.get('externalCode', ''),
                }
            )

            # Цена
            Price.objects.update_or_create(
                product=product,
                price_type=price_type,
                defaults={
                    'price': value,
                    'is_active': True,
                }
            )

    def sync_stock(self):
        """Синхронизация остатков"""
        sync_log = SyncLog.objects.create(
            sync_type='stock',
            status='started'
        )

        try:
            # Получаем все остатки
            all_stock = []
            offset = 0
            limit = 1000

            while True:
                stock_data = self.api.get_stock(limit=limit, offset=offset)
                rows = stock_data.get('rows', [])
                if not rows:
                    break
                all_stock.extend(rows)
                offset += limit
                if len(rows) < limit:
                    break

            # Дефолтный склад
            warehouse, _ = Warehouse.objects.get_or_create(
                moysklad_id='default',
                defaults={'name': 'Основной склад', 'is_default': True}
            )

            updated = 0

            for item in all_stock:
                meta = item.get('meta', {})
                href = meta.get('href', '')

                if '/entity/product/' not in href:
                    continue

                # Извлекаем ID: убираем query params и берём последний сегмент
                product_path = href.split('/entity/product/')[-1]
                moysklad_id = product_path.split('?')[0]

                try:
                    product = Product.objects.get(moysklad_id=moysklad_id)
                    Stock.objects.update_or_create(
                        product=product,
                        warehouse=warehouse,
                        defaults={
                            'quantity': int(item.get('stock', 0)),
                            'reserve': int(item.get('reserve', 0)),
                        }
                    )
                    updated += 1
                except Product.DoesNotExist:
                    continue

            sync_log.status = 'success'
            sync_log.items_processed = len(all_stock)
            sync_log.items_updated = updated
            sync_log.finished_at = timezone.now()
            sync_log.save()

            return {'updated': updated, 'total': len(all_stock)}

        except Exception as e:
            logger.error(f"Ошибка синхронизации остатков: {e}")
            sync_log.status = 'error'
            sync_log.error_message = str(e)
            sync_log.finished_at = timezone.now()
            sync_log.save()
            raise

    def cleanup_excluded(self):
        """Удаляет уже загруженные товары из исключённых групп"""
        deleted = 0
        for excluded in self.EXCLUDED_PATHS:
            count, _ = Product.objects.filter(moysklad_path__startswith=excluded).delete()
            deleted += count
        return deleted