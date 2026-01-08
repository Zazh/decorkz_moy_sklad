# integration/management/commands/migrate_cards.py

from django.core.management.base import BaseCommand
import os

from legacy.models import LegacyProduct
from products.models import Product
from cards.models import ProductCard, ProductCardImage, ProductCardAttribute
from references.models import AttributeDefinition


class Command(BaseCommand):
    help = 'Миграция карточек товаров из легаси базы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать что будет сделано'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Ограничить количество товаров'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']

        legacy_products = LegacyProduct.objects.select_related('category').prefetch_related(
            'images', 'attribute_values__attribute'
        )

        if limit:
            legacy_products = legacy_products[:limit]

        created = 0
        skipped = 0
        no_match = 0

        for legacy in legacy_products:
            # Ищем товар в новой базе
            product = Product.objects.filter(sku=legacy.sku).first()
            if not product:
                no_match += 1

            # Проверяем есть ли уже карточка
            if ProductCard.objects.filter(product=product, source='legacy').exists():
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(f"  [DRY-RUN] {legacy.sku}: {legacy.title}")
                created += 1
                continue

            # Создаём карточку
            card = ProductCard.objects.create(
                product=product,
                sku=legacy.sku,
                title=legacy.title,
                slug=legacy.slug,
                description=legacy.description or '',
                youtube_url=legacy.youtube_url or '',
                is_default=True,
                is_active=True,
                source='legacy'
            )

            # Переносим изображения
            for img in legacy.images.all():
                if img.image:
                    ProductCardImage.objects.create(
                        card=card,
                        image=img.image,  # путь уже совпадает
                        is_main=img.is_main,
                        alt=card.title
                    )

            # Переносим атрибуты
            for attr_value in legacy.attribute_values.all():
                attr_def, _ = AttributeDefinition.objects.get_or_create(
                    name=attr_value.attribute.name,
                    defaults={
                        'slug': attr_value.attribute.slug,
                        'value_type': self._map_value_type(attr_value.attribute.value_type),
                    }
                )

                ProductCardAttribute.objects.create(
                    card=card,
                    attribute=attr_def,
                    value=attr_value.value
                )

            created += 1

            if created % 100 == 0:
                self.stdout.write(f"  Обработано: {created}")

        self.stdout.write(self.style.SUCCESS(
            f"\nГотово! Создано: {created}, Пропущено: {skipped}, Без связи: {no_match}"
        ))

    def _map_value_type(self, legacy_type):
        mapping = {
            'str': 'string',
            'int': 'integer',
            'decimal': 'decimal',
            'bool': 'boolean',
        }
        return mapping.get(legacy_type, 'string')