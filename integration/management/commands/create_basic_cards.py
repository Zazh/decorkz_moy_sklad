# integration/management/commands/create_basic_cards.py

import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile

from products.models import Product
from cards.models import ProductCard, ProductCardImage
from integration.services.moysklad_api import MoySkladAPI


class Command(BaseCommand):
    help = 'Создание базовых карточек для товаров с фото из МойСклад'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Только показать что будет сделано')
        parser.add_argument('--limit', type=int, default=0, help='Ограничить количество')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']

        api = MoySkladAPI()
        headers = api.auth if isinstance(api.auth, dict) else {}
        auth = None if isinstance(api.auth, dict) else api.auth

        # Товары с карточками
        products_with_cards = set(ProductCard.objects.values_list('product_id', flat=True))

        # Товары с фото, но без карточек
        candidates = []
        for p in Product.objects.all():
            if p.id in products_with_cards:
                continue
            images_meta = p.raw_data.get('images', {}).get('meta', {})
            if images_meta.get('size', 0) > 0:
                candidates.append(p)

        self.stdout.write(f'Найдено товаров с фото без карточек: {len(candidates)}')

        if limit:
            candidates = candidates[:limit]

        created = 0
        errors = 0

        for product in candidates:
            try:
                if dry_run:
                    self.stdout.write(f'  [DRY-RUN] {product.sku}: {product.name[:50]}')
                    created += 1
                    continue

                # Создаём карточку
                card = ProductCard(
                    product=product,
                    sku=product.sku,
                    title=product.name,
                    is_default=True,
                    is_active=True,
                    source='moysklad'
                )
                # Генерируем короткий slug
                from django.utils.text import slugify
                base_slug = slugify(product.sku, allow_unicode=True) or 'product'
                slug = base_slug[:45]
                counter = 1
                while ProductCard.objects.filter(slug=slug).exists():
                    slug = f'{base_slug[:40]}-{counter}'
                    counter += 1
                card.slug = slug
                card.save()

                # Загружаем изображения
                images_url = product.raw_data['images']['meta']['href']
                resp = requests.get(images_url, headers=headers, auth=auth)
                images_data = resp.json().get('rows', [])

                for i, img_data in enumerate(images_data):
                    miniature_url = img_data.get('miniature', {}).get('href', '')
                    original_url = miniature_url.replace('?miniature=true', '')

                    if not original_url:
                        continue

                    img_resp = requests.get(original_url, headers=headers, auth=auth)
                    if img_resp.status_code != 200:
                        continue

                    # Ограничиваем filename чтобы путь cards/filename не превысил 100 символов
                    original_filename = img_data.get('filename', f'{product.sku}_{i}.jpg')
                    ext = original_filename.rsplit('.', 1)[-1] if '.' in original_filename else 'jpg'
                    filename = f'{product.sku}_{i}.{ext}'[:90]
                    card_image = ProductCardImage(
                        card=card,
                        is_main=(i == 0),
                        alt=product.name
                    )
                    card_image.image.save(filename, ContentFile(img_resp.content), save=True)

                created += 1
                if created % 50 == 0:
                    self.stdout.write(f'  Обработано: {created}')

            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f'  Ошибка {product.sku}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\nГотово! Создано: {created}, Ошибок: {errors}'))