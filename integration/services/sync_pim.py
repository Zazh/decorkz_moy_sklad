# integration/services/sync_pim.py

import logging
from django.utils import timezone

from products.models import Product
from references.models import Brand, Category
from mapping.models import BrandMapping, CategoryMapping
from integration.models import MoySkladProduct, SyncLog

logger = logging.getLogger(__name__)


class PIMSyncService:
    """Синхронизация MoySkladProduct → Product"""

    EXCLUDED_PATHS = [
        'Реклама',
        'Услуги',
        'Основные средства',
    ]

    def sync_products(self):
        """Синхронизация товаров: MoySkladProduct → Product"""
        sync_log = SyncLog.objects.create(
            sync_type='products',
            status='started'
        )

        created = 0
        updated = 0
        skipped = 0
        errors = 0

        try:
            moysklad_products = MoySkladProduct.objects.filter(
                archived=False
            ).order_by('updated_at')

            for ms_product in moysklad_products:
                try:
                    result = self._sync_product(ms_product)

                    if result is None:
                        skipped += 1
                    elif result == 'created':
                        created += 1
                    elif result == 'updated':
                        updated += 1

                except Exception as e:
                    logger.error(f"Ошибка синхронизации {ms_product.name}: {e}")
                    errors += 1

            sync_log.status = 'success'
            sync_log.items_processed = moysklad_products.count()
            sync_log.items_created = created
            sync_log.items_updated = updated
            sync_log.finished_at = timezone.now()
            sync_log.save()

            return {
                'created': created,
                'updated': updated,
                'skipped': skipped,
                'errors': errors,
                'total': moysklad_products.count()
            }

        except Exception as e:
            logger.error(f"Ошибка синхронизации: {e}")
            sync_log.status = 'error'
            sync_log.error_message = str(e)
            sync_log.finished_at = timezone.now()
            sync_log.save()
            raise

    def _sync_product(self, ms_product: MoySkladProduct):
        """
        Синхронизация одного товара.

        Returns:
            'created' | 'updated' | None (если пропущен)
        """
        # Проверяем исключённые группы
        path_name = ms_product.path_name or ''
        for excluded in self.EXCLUDED_PATHS:
            if path_name.startswith(excluded):
                return None

        # Артикул
        article = ms_product.article or ms_product.code or ms_product.moysklad_id
        if not article:
            logger.warning(f"Нет артикула для {ms_product.name}")
            return None

        article = article[:100]

        # Маппинг бренда и категории
        brand = self._get_brand(ms_product)
        category = self._get_category(ms_product)

        # Ищем существующий Product по moysklad
        existing_by_moysklad = Product.objects.filter(moysklad=ms_product).first()

        # Ищем существующий Product по article
        existing_by_article = Product.objects.filter(article=article).first()

        # Случай 1: Product уже есть для этого moysklad
        if existing_by_moysklad:
            if existing_by_moysklad.article != article:
                # Артикул изменился в МойСклад
                if existing_by_article and existing_by_article != existing_by_moysklad:
                    # Новый артикул уже занят другим Product — сравниваем даты
                    other_ms = existing_by_article.moysklad
                    if other_ms and other_ms.updated_at > ms_product.updated_at:
                        # Другой товар новее — пропускаем
                        return None
                    else:
                        # Текущий новее — удаляем старый Product
                        existing_by_article.delete()

            # Обновляем существующий Product
            existing_by_moysklad.article = article
            existing_by_moysklad.brand = brand
            existing_by_moysklad.category = category
            existing_by_moysklad.is_active = ms_product.is_active and not ms_product.archived
            existing_by_moysklad.save()
            return 'updated'

        # Случай 2: Product нет для этого moysklad, но артикул занят
        if existing_by_article:
            other_ms = existing_by_article.moysklad
            if other_ms and other_ms.updated_at > ms_product.updated_at:
                # Другой товар новее — пропускаем
                return None
            else:
                # Текущий новее — перепривязываем
                existing_by_article.moysklad = ms_product
                existing_by_article.brand = brand
                existing_by_article.category = category
                existing_by_article.is_active = ms_product.is_active and not ms_product.archived
                existing_by_article.save()
                return 'updated'

        # Случай 3: Создаём новый Product
        Product.objects.create(
            moysklad=ms_product,
            article=article,
            brand=brand,
            category=category,
            is_active=ms_product.is_active and not ms_product.archived,
        )
        return 'created'

    def _get_brand(self, ms_product: MoySkladProduct) -> Brand | None:
        """Получить бренд через маппинг."""
        raw_data = ms_product.raw_data or {}
        brand_name = None

        for attr in raw_data.get('attributes', []):
            if attr.get('name') == 'Бренд' and attr.get('value'):
                brand_name = str(attr['value']).strip()
                break

        if not brand_name:
            return None

        # Ищем маппинг
        mapping = BrandMapping.objects.filter(
            source='moysklad',
            source_name=brand_name
        ).select_related('brand').first()

        if mapping and mapping.brand:
            return mapping.brand

        return None

    def _get_category(self, ms_product: MoySkladProduct) -> Category | None:
        """Получить категорию через маппинг."""
        path_name = ms_product.path_name
        if not path_name:
            return None

        mapping = CategoryMapping.objects.filter(
            source='moysklad',
            source_name=path_name
        ).select_related('category').first()

        if mapping:
            return mapping.category

        return None


def sync_products():
    """Удобная функция для вызова из management command"""
    service = PIMSyncService()
    return service.sync_products()