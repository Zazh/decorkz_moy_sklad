# integration/services/sync_pim.py

import logging
from django.utils import timezone

from products.models import Product
from references.models import Brand, Category
from mapping.models import BrandMapping
from integration.models import MoySkladProduct, SyncLog
from catalog.translit import translit_slugify

logger = logging.getLogger(__name__)


class PIMSyncService:
    """Синхронизация MoySkladProduct → Product"""

    EXCLUDED_PATHS = [
        'Реклама',
        'Услуги',
        'Основные средства',
        'Не загружать (прочее)',
        'Устаревшее',
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
            # Заполнить site_category_id из raw_data где пустой
            self._backfill_category_ids()

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

            # Деактивировать товары, архивированные в МойСклад
            archived_deactivated = Product.objects.filter(
                moysklad__archived=True,
                is_active=True,
            ).update(is_active=False)
            if archived_deactivated:
                logger.info(f"Деактивировано архивных товаров: {archived_deactivated}")

            # Деактивировать категории без активных товаров
            from django.db.models import Count, Q
            empty_cats = Category.objects.filter(
                is_active=True
            ).annotate(
                own=Count('products', filter=Q(products__is_active=True)),
                child=Count('children__products', filter=Q(children__products__is_active=True)),
            ).filter(own=0, child=0)
            cats_deactivated = empty_cats.update(is_active=False)
            if cats_deactivated:
                logger.info(f"Деактивировано пустых категорий: {cats_deactivated}")

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
                'total': moysklad_products.count(),
                'archived_deactivated': archived_deactivated,
                'cats_deactivated': cats_deactivated,
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
        # Проверяем исключённые категории (и подкатегории)
        site_cat = ms_product.site_category or ''
        site_subcat = ms_product.site_subcategory or ''
        is_excluded = False
        for excluded in self.EXCLUDED_PATHS:
            if site_cat == excluded or site_subcat == excluded:
                is_excluded = True
                break

        # Фолбэк: проверка по path_name (для товаров без site_category)
        if not is_excluded:
            path_name = ms_product.path_name or ''
            for excluded in self.EXCLUDED_PATHS:
                if path_name.startswith(excluded):
                    is_excluded = True
                    break

        if is_excluded:
            # Деактивировать Product если он существует
            Product.objects.filter(moysklad=ms_product, is_active=True).update(is_active=False)
            return None

        # Артикул: приоритет — код МойСклад, потом артикул
        article = ms_product.code or ms_product.article or ms_product.moysklad_id
        if not article:
            logger.warning(f"Нет артикула для {ms_product.name}")
            return None

        article = article[:100]

        # Маппинг бренда, категории и страны
        brand = self._get_brand(ms_product)
        category = self._get_category(ms_product)
        country = self._get_country(ms_product)

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
            existing_by_moysklad.country = country
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
                existing_by_article.country = country
                existing_by_article.is_active = ms_product.is_active and not ms_product.archived
                existing_by_article.save()
                return 'updated'

        # Случай 3: Создаём новый Product
        Product.objects.create(
            moysklad=ms_product,
            article=article,
            brand=brand,
            category=category,
            country=country,
            is_active=ms_product.is_active and not ms_product.archived,
        )
        return 'created'

    def _get_brand(self, ms_product: MoySkladProduct) -> Brand | None:
        """Получить бренд через маппинг."""
        raw_data = ms_product.raw_data or {}
        brand_name = None

        for attr in raw_data.get('attributes', []):
            if attr.get('name') == 'Бренд' and attr.get('value'):
                val = attr['value']
                if isinstance(val, dict):
                    brand_name = val.get('name', '').strip()
                else:
                    brand_name = str(val).strip()
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
        """Получить или создать категорию по ID справочника МойСклад."""
        cat_name = (ms_product.site_category or '').strip()
        cat_id = (ms_product.site_category_id or '').strip()
        subcat_name = (ms_product.site_subcategory or '').strip()
        subcat_id = (ms_product.site_subcategory_id or '').strip()

        if not cat_name or not cat_id:
            return None

        # Не создаём категории для исключённых
        if cat_name in self.EXCLUDED_PATHS or subcat_name in self.EXCLUDED_PATHS:
            return None

        # Родительская категория — get or create по moysklad_id
        parent, created = Category.objects.get_or_create(
            moysklad_id=cat_id,
            defaults={
                'title': cat_name,
                'slug': self._generate_slug(cat_name),
                'parent': None,
                'is_active': True,
            }
        )
        if not created and parent.title != cat_name:
            # Название изменилось в МойСклад — обновляем
            logger.info(f"Категория переименована: {parent.title} → {cat_name}")
            parent.title = cat_name
            parent.save(update_fields=['title'])
        elif created:
            logger.info(f"Создана категория: {cat_name}")

        # Подкатегория
        if subcat_name and subcat_id and subcat_id != cat_id:
            child, created = Category.objects.get_or_create(
                moysklad_id=subcat_id,
                defaults={
                    'title': subcat_name,
                    'slug': self._generate_slug(subcat_name),
                    'parent': parent,
                    'is_active': True,
                }
            )
            if not created and child.title != subcat_name:
                logger.info(f"Подкатегория переименована: {child.title} → {subcat_name}")
                child.title = subcat_name
                child.save(update_fields=['title'])
            elif created:
                logger.info(f"Создана подкатегория: {cat_name} → {subcat_name}")
            return child

        return parent

    def _generate_slug(self, title):
        """Генерация уникального slug."""
        base = translit_slugify(title)
        if not base:
            base = 'category'
        slug = base
        counter = 1
        while Category.objects.filter(slug=slug).exists():
            slug = f"{base}-{counter}"
            counter += 1
        return slug

    def _backfill_category_ids(self):
        """Заполнить site_category_id/site_subcategory_id из raw_data где пустые."""
        qs = MoySkladProduct.objects.filter(site_category_id='').exclude(site_category='')
        updated = 0
        for ms in qs.iterator():
            changed = False
            for attr in (ms.raw_data or {}).get('attributes', []):
                val = attr.get('value')
                if not isinstance(val, dict):
                    continue
                href = val.get('meta', {}).get('href', '')
                uid = href.rsplit('/', 1)[-1] if href else ''
                if attr.get('name') == 'Категория сайт' and uid:
                    ms.site_category_id = uid
                    changed = True
                elif attr.get('name') == 'Подкатегория сайт' and uid:
                    ms.site_subcategory_id = uid
                    changed = True
            if changed:
                ms.save(update_fields=['site_category_id', 'site_subcategory_id'])
                updated += 1
        if updated:
            logger.info(f"Backfill category IDs: {updated}")

    def _get_country(self, ms_product: MoySkladProduct) -> str:
        """Извлечь страну из raw_data['country']['name']."""
        raw_data = ms_product.raw_data or {}
        country = raw_data.get('country')
        if isinstance(country, dict):
            return country.get('name', '')
        return ''


def sync_products():
    """Удобная функция для вызова из management command"""
    service = PIMSyncService()
    return service.sync_products()