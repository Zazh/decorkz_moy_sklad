# cards/management/commands/convert_images.py

"""
Конвертация всех изображений карточек в WebP.
Пропускает уже сконвертированные (.webp).
"""

import os
from django.core.management.base import BaseCommand
from django.conf import settings

from cards.models import ProductCardImage
from cards.services import convert_image_to_webp


class Command(BaseCommand):
    help = 'Конвертировать изображения карточек в WebP'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Показать что будет сделано')
        parser.add_argument('--quality', type=int, default=80, help='Качество WebP (1-100)')
        parser.add_argument('--limit', type=int, default=0, help='Ограничить количество')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        quality = options['quality']
        limit = options['limit']

        images = ProductCardImage.objects.all()
        total = images.count()

        # Считаем уже webp
        already_webp = 0
        to_convert = []
        missing = 0

        for img in images:
            if not img.image:
                continue
            name = img.image.name
            if name.lower().endswith('.webp'):
                already_webp += 1
                continue

            file_path = os.path.join(settings.MEDIA_ROOT, name)
            if not os.path.exists(file_path):
                missing += 1
                continue

            to_convert.append(img)

        self.stdout.write(f'Всего изображений: {total}')
        self.stdout.write(f'Уже WebP: {already_webp}')
        self.stdout.write(f'К конвертации: {len(to_convert)}')
        self.stdout.write(f'Файл не найден: {missing}')

        if dry_run:
            for img in to_convert[:20]:
                self.stdout.write(f'  {img.image.name}')
            if len(to_convert) > 20:
                self.stdout.write(f'  ... и ещё {len(to_convert) - 20}')
            return

        if limit:
            to_convert = to_convert[:limit]

        converted = 0
        errors = 0
        saved_bytes = 0

        for i, img in enumerate(to_convert):
            old_path = os.path.join(settings.MEDIA_ROOT, img.image.name)
            old_size = os.path.getsize(old_path) if os.path.exists(old_path) else 0

            ok = convert_image_to_webp(img, quality=quality)
            if ok:
                new_path = os.path.join(settings.MEDIA_ROOT, img.image.name)
                new_size = os.path.getsize(new_path) if os.path.exists(new_path) else 0
                saved_bytes += old_size - new_size
                converted += 1
            else:
                errors += 1

            if (i + 1) % 200 == 0:
                self.stdout.write(f'  Обработано: {i + 1}/{len(to_convert)}')

        saved_mb = saved_bytes / (1024 * 1024)
        self.stdout.write(self.style.SUCCESS(
            f'\nГотово!\n'
            f'  Сконвертировано: {converted}\n'
            f'  Ошибок: {errors}\n'
            f'  Экономия: {saved_mb:.1f} МБ'
        ))
