"""
Пересоздание всех slug'ов с транслитерацией (кириллица → латиница).
Также переименовывает файлы изображений с кириллическими именами.
"""
import os
import re
from django.core.management.base import BaseCommand
from django.conf import settings

from catalog.translit import translit_slugify, safe_filename
from products.models import Product
from references.models import Category, Brand, AttributeDefinition
from cards.models import ProductCardImage


class Command(BaseCommand):
    help = 'Пересоздать все slug в транслите и переименовать файлы с кириллицей'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Только показать что изменится')
        parser.add_argument('--skip-images', action='store_true', help='Не переименовывать файлы')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        skip_images = options['skip_images']

        self.stdout.write('=' * 60)
        self.stdout.write('Пересоздание slug с транслитерацией')
        self.stdout.write('=' * 60)

        self._regenerate_category_slugs(dry_run)
        self._regenerate_brand_slugs(dry_run)
        self._regenerate_attribute_slugs(dry_run)
        self._regenerate_product_slugs(dry_run)

        if not skip_images:
            self._rename_image_files(dry_run)

        self.stdout.write('\nГотово!')

    def _regenerate_category_slugs(self, dry_run):
        self.stdout.write('\n--- Категории ---')
        updated = 0
        for cat in Category.objects.all():
            new_slug = translit_slugify(cat.title)
            if not new_slug:
                new_slug = 'category'
            # Уникальность
            base = new_slug
            counter = 1
            while Category.objects.filter(slug=new_slug).exclude(pk=cat.pk).exists():
                new_slug = f'{base}-{counter}'
                counter += 1

            if cat.slug != new_slug:
                self.stdout.write(f'  {cat.slug} -> {new_slug}')
                if not dry_run:
                    cat.slug = new_slug
                    cat.save(update_fields=['slug'])
                updated += 1
        self.stdout.write(f'  Категорий обновлено: {updated}')

    def _regenerate_brand_slugs(self, dry_run):
        self.stdout.write('\n--- Бренды ---')
        updated = 0
        for brand in Brand.objects.all():
            new_slug = translit_slugify(brand.name)
            if not new_slug:
                new_slug = 'brand'
            base = new_slug
            counter = 1
            while Brand.objects.filter(slug=new_slug).exclude(pk=brand.pk).exists():
                new_slug = f'{base}-{counter}'
                counter += 1

            if brand.slug != new_slug:
                self.stdout.write(f'  {brand.slug} -> {new_slug}')
                if not dry_run:
                    brand.slug = new_slug
                    brand.save(update_fields=['slug'])
                updated += 1
        self.stdout.write(f'  Брендов обновлено: {updated}')

    def _regenerate_attribute_slugs(self, dry_run):
        self.stdout.write('\n--- Атрибуты ---')
        updated = 0
        for attr in AttributeDefinition.objects.all():
            new_slug = translit_slugify(attr.name)
            if not new_slug:
                new_slug = 'attr'
            base = new_slug
            counter = 1
            while AttributeDefinition.objects.filter(slug=new_slug).exclude(pk=attr.pk).exists():
                new_slug = f'{base}-{counter}'
                counter += 1

            if attr.slug != new_slug:
                self.stdout.write(f'  {attr.slug} -> {new_slug}')
                if not dry_run:
                    attr.slug = new_slug
                    attr.save(update_fields=['slug'])
                updated += 1
        self.stdout.write(f'  Атрибутов обновлено: {updated}')

    def _regenerate_product_slugs(self, dry_run):
        self.stdout.write('\n--- Товары ---')
        updated = 0
        total = Product.objects.count()
        for i, product in enumerate(Product.objects.select_related('category', 'card').all()):
            new_slug = product.generate_slug()
            if product.slug != new_slug:
                if updated < 20:  # показываем первые 20
                    self.stdout.write(f'  {product.slug} -> {new_slug}')
                if not dry_run:
                    product.slug = new_slug
                    product.save(update_fields=['slug'])
                updated += 1

            if (i + 1) % 500 == 0:
                self.stdout.write(f'  ... обработано {i + 1}/{total}')

        self.stdout.write(f'  Товаров обновлено: {updated}/{total}')

    def _rename_image_files(self, dry_run):
        self.stdout.write('\n--- Переименование файлов изображений ---')
        renamed = 0
        errors = 0

        # Проверяем файлы с не-ASCII символами
        has_non_ascii = re.compile('[^\\x00-\\x7F]')

        for img in ProductCardImage.objects.all():
            if not img.image:
                continue

            old_name = img.image.name  # e.g. 'cards/П 03 20/60_0.jpg'
            if not has_non_ascii.search(old_name):
                continue

            # Транслитерируем все сегменты пути, кроме первого ('cards/')
            parts = old_name.split('/')
            # Первый сегмент ('cards') оставляем как есть
            # Все остальные сегменты — это файл или поддиректории из-за / в имени
            # Склеиваем всё кроме первого сегмента в одно имя файла
            if len(parts) > 1:
                prefix = parts[0]  # 'cards'
                # Всё остальное — это исходное имя файла (/ были частью имени)
                file_part = '_'.join(parts[1:])
            else:
                prefix = ''
                file_part = parts[0]

            new_file = safe_filename(file_part)
            if not new_file:
                continue

            if prefix:
                new_name = f'{prefix}/{new_file}'
            else:
                new_name = new_file

            if old_name == new_name:
                continue

            # Уникальность имени файла
            base_new, ext = os.path.splitext(new_name)
            counter = 1
            while ProductCardImage.objects.filter(image=new_name).exclude(pk=img.pk).exists():
                new_name = f'{base_new}_{counter}{ext}'
                counter += 1

            if renamed < 30:
                self.stdout.write(f'  {old_name} -> {new_name}')

            if not dry_run:
                old_path = os.path.join(settings.MEDIA_ROOT, old_name)
                new_path = os.path.join(settings.MEDIA_ROOT, new_name)

                try:
                    if os.path.exists(old_path):
                        os.makedirs(os.path.dirname(new_path), exist_ok=True)
                        os.rename(old_path, new_path)
                        img.image.name = new_name
                        img.save(update_fields=['image'])
                        renamed += 1
                    else:
                        # Файл не найден на диске — обновляем только запись в БД
                        img.image.name = new_name
                        img.save(update_fields=['image'])
                        renamed += 1
                        self.stdout.write(f'  [DB only] {old_name} -> {new_name}')
                except Exception as e:
                    self.stdout.write(f'  ОШИБКА: {old_name} -> {e}')
                    errors += 1
            else:
                renamed += 1

        self.stdout.write(f'  Файлов переименовано: {renamed}')
        if errors:
            self.stdout.write(f'  Ошибок: {errors}')
