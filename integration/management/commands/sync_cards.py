# integration/management/commands/sync_cards.py

import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from products.models import Product
from cards.models import ProductCard, ProductCardImage
from integration.models import SyncLog
from integration.services.moysklad_api import MoySkladAPI

logger = logging.getLogger(__name__)

# Пауза между запросами (сек) — чтобы не превышать лимит МойСклад
REQUEST_DELAY = 0.15

EXCLUDED_CATEGORIES = [
    'Реклама',
    'Не загружать (прочее)',
]


class Command(BaseCommand):
    help = 'Синхронизация карточек контента из МойСклад (название, описание, фото)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Только показать что будет сделано')
        parser.add_argument('--limit', type=int, default=0, help='Ограничить количество')
        parser.add_argument('--offset', type=int, default=0, help='Пропустить первые N товаров')
        parser.add_argument('--no-images', action='store_true', help='Без скачивания фото')
        parser.add_argument('--force-images', action='store_true', help='Перекачать фото даже если уже есть')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        offset = options['offset']
        skip_images = options['no_images']
        force_images = options['force_images']

        sync_log = SyncLog.objects.create(sync_type='products', status='started')

        # HTTP-сессия с переиспользованием соединений и retry
        api = MoySkladAPI()
        self.session = requests.Session()

        # Retry: 3 попытки с экспоненциальной задержкой при таймаутах и 429
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=5, pool_maxsize=5)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

        if isinstance(api.auth, dict):
            self.session.headers.update(api.auth)
        else:
            self.session.auth = api.auth

        # Все активные товары с данными МойСклад
        products = Product.objects.filter(
            moysklad__isnull=False,
            is_active=True,
        ).select_related('moysklad', 'card')

        # Исключаем служебные категории
        for cat in EXCLUDED_CATEGORIES:
            products = products.exclude(moysklad__site_category=cat)

        total = products.count()
        self.stdout.write(f'Товаров для обработки: {total}')

        if offset:
            products = products[offset:]
        if limit:
            products = products[:limit]

        created = 0
        updated = 0
        images_downloaded = 0
        errors = 0

        processed = 0
        for product in products.iterator(chunk_size=100):
            ms = product.moysklad
            processed += 1

            if processed % 100 == 0:
                self.stdout.write(f'  Прогресс: {processed} товаров, фото: {images_downloaded}')

            try:
                if product.card:
                    # Обновляем существующую карточку
                    card = product.card
                    changed = False
                    if card.title != ms.name:
                        card.title = ms.name
                        changed = True
                    new_desc = ms.description or ''
                    if card.source == 'moysklad' and card.description != new_desc:
                        card.description = new_desc
                        changed = True
                    if changed:
                        card.save()
                        updated += 1

                        if dry_run:
                            self.stdout.write(f'  [UPD] {product.article}: {ms.name[:60]}')
                else:
                    # Создаём новую карточку
                    if dry_run:
                        has_img = self._has_images(ms)
                        self.stdout.write(f'  [NEW] {"img" if has_img else "   "} {product.article}: {ms.name[:60]}')
                        created += 1
                        continue

                    card = ProductCard.objects.create(
                        title=ms.name,
                        description=ms.description or '',
                        source='moysklad',
                    )
                    product.card = card
                    product.save(update_fields=['card'])
                    created += 1

                # Скачиваем фото
                if not dry_run and not skip_images:
                    ms_image_count = self._get_ms_image_count(ms)
                    local_image_count = card.images.count()
                    need_sync = force_images or (local_image_count == 0 and ms_image_count > 0)

                    # Умная проверка: количество фото изменилось в МойСклад
                    if not need_sync and ms_image_count != local_image_count and ms_image_count > 0:
                        need_sync = True

                    # Проверка по дате: товар обновлён в МойСклад после последней синхр. фото
                    if not need_sync and ms_image_count > 0 and card.images_synced_at:
                        ms_updated = self._get_ms_updated(ms)
                        if ms_updated and ms_updated > card.images_synced_at:
                            need_sync = True

                    if need_sync:
                        # Удаляем старые фото перед перекачкой
                        if local_image_count > 0:
                            card.images.all().delete()
                        img_count = self._download_images(ms, card)
                        if img_count > 0:
                            images_downloaded += img_count
                        # Запоминаем время синхронизации фото
                        card.images_synced_at = timezone.now()
                        card.save(update_fields=['images_synced_at'])

            except Exception as e:
                errors += 1
                logger.error(f'Ошибка {product.article}: {e}')

        sync_log.status = 'success'
        sync_log.items_processed = total
        sync_log.items_created = created
        sync_log.items_updated = updated
        sync_log.finished_at = timezone.now()
        sync_log.save()

        self.stdout.write(self.style.SUCCESS(
            f'\nГотово!\n'
            f'  Создано карточек: {created}\n'
            f'  Обновлено: {updated}\n'
            f'  Фото скачано: {images_downloaded}\n'
            f'  Ошибок: {errors}'
        ))

    def _get_ms_updated(self, ms):
        """Дата обновления товара в МойСклад из raw_data (всегда aware)"""
        raw = ms.raw_data or {}
        updated_str = raw.get('updated')
        if updated_str:
            try:
                dt = parse_datetime(updated_str)
                if dt and timezone.is_naive(dt):
                    dt = timezone.make_aware(dt)
                return dt
            except (ValueError, TypeError):
                return None
        return None

    def _get_ms_image_count(self, ms):
        raw = ms.raw_data or {}
        return raw.get('images', {}).get('meta', {}).get('size', 0)

    def _has_images(self, ms):
        return self._get_ms_image_count(ms) > 0

    def _download_images(self, ms, card):
        raw = ms.raw_data or {}
        images_meta = raw.get('images', {}).get('meta', {})

        if images_meta.get('size', 0) == 0:
            return 0

        images_url = images_meta.get('href')
        if not images_url:
            return 0

        try:
            time.sleep(REQUEST_DELAY)
            resp = self.session.get(images_url, timeout=30)
            resp.raise_for_status()
            images_data = resp.json().get('rows', [])
        except Exception as e:
            logger.warning(f'Не удалось получить список фото {ms.name}: {e}')
            return 0

        count = 0
        article = ms.code or ms.article or 'product'

        for i, img_data in enumerate(images_data):
            try:
                miniature_url = img_data.get('miniature', {}).get('href', '')
                original_url = miniature_url.replace('?miniature=true', '')
                if not original_url:
                    continue

                time.sleep(REQUEST_DELAY)
                img_resp = self.session.get(original_url, timeout=60)
                if img_resp.status_code != 200:
                    continue

                from catalog.translit import safe_filename
                from cards.services import convert_uploaded_bytes_to_webp

                original_filename = img_data.get('filename', f'{article}_{i}.jpg')
                ext = original_filename.rsplit('.', 1)[-1] if '.' in original_filename else 'jpg'
                filename = safe_filename(f'{article}_{i}.{ext}')[:90]

                # Конвертируем в WebP до сохранения на диск
                webp_bytes, webp_filename = convert_uploaded_bytes_to_webp(
                    img_resp.content, filename
                )
                if webp_bytes:
                    save_bytes = webp_bytes
                    save_filename = webp_filename[:90]
                else:
                    save_bytes = img_resp.content
                    save_filename = filename

                card_image = ProductCardImage(
                    card=card,
                    is_main=(i == 0 and not card.images.filter(is_main=True).exists()),
                    alt=card.title[:255],
                )
                card_image.image.save(save_filename, ContentFile(save_bytes), save=True)
                count += 1

            except Exception as e:
                logger.warning(f'Ошибка скачивания фото {article}_{i}: {e}')

        return count
