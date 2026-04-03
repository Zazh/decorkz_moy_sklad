# integration/management/commands/sync_site_categories.py

from django.core.management.base import BaseCommand
from django.db.models import Count

from catalog.translit import translit_slugify
from integration.models import MoySkladProduct
from references.models import Category


class Command(BaseCommand):
    help = 'Синхронизация категорий каталога из атрибутов "Категория сайт" и "Подкатегория сайт"'

    EXCLUDED_CATEGORIES = [
        'Реклама',
        'Не загружать (прочее)',
        'Устаревшее',
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать что будет создано/деактивировано'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write('=' * 60)
        self.stdout.write('Синхронизация категорий: МойСклад → Category')
        self.stdout.write('=' * 60)

        # Собираем актуальные категории из МойСклад
        products = MoySkladProduct.objects.filter(
            archived=False
        ).exclude(
            site_category=''
        )
        for excluded in self.EXCLUDED_CATEGORIES:
            products = products.exclude(site_category=excluded)
            products = products.exclude(site_subcategory=excluded)

        # Собираем уникальные пары (категория, подкатегория)
        category_data = {}  # {category_name: set(subcategory_names)}
        for cat_name, subcat_name in products.values_list('site_category', 'site_subcategory'):
            if cat_name not in category_data:
                category_data[cat_name] = set()
            if subcat_name and subcat_name.strip().lower() != cat_name.strip().lower():
                category_data[cat_name].add(subcat_name)

        self.stdout.write(f'\nНайдено категорий: {len(category_data)}')
        total_subcats = sum(len(v) for v in category_data.values())
        self.stdout.write(f'Найдено подкатегорий: {total_subcats}')

        cats_created = 0
        cats_exists = 0
        subcats_created = 0
        subcats_exists = 0

        # Для отслеживания актуальных категорий
        active_category_ids = set()

        for cat_name in sorted(category_data.keys()):
            subcat_names = category_data[cat_name]

            if dry_run:
                self.stdout.write(f'\n  + {cat_name}')
                for sc in sorted(subcat_names):
                    self.stdout.write(f'      {sc}')
                continue

            # Создаём/находим родительскую категорию
            parent_cat, created = Category.objects.get_or_create(
                title=cat_name,
                parent=None,
                defaults={
                    'slug': self._generate_slug(cat_name),
                    'is_active': True,
                }
            )
            if created:
                cats_created += 1
                self.stdout.write(f'  + Категория: {cat_name}')
            else:
                # Реактивировать если была деактивирована
                if not parent_cat.is_active:
                    parent_cat.is_active = True
                    parent_cat.save(update_fields=['is_active'])
                    self.stdout.write(f'  ~ Реактивирована: {cat_name}')
                cats_exists += 1

            active_category_ids.add(parent_cat.id)

            # Создаём подкатегории
            for subcat_name in sorted(subcat_names):
                sub_cat, created = Category.objects.get_or_create(
                    title=subcat_name,
                    parent=parent_cat,
                    defaults={
                        'slug': self._generate_slug(subcat_name, parent_cat),
                        'is_active': True,
                    }
                )
                if created:
                    subcats_created += 1
                    self.stdout.write(f'    + Подкатегория: {subcat_name}')
                else:
                    if not sub_cat.is_active:
                        sub_cat.is_active = True
                        sub_cat.save(update_fields=['is_active'])
                        self.stdout.write(f'    ~ Реактивирована: {subcat_name}')
                    subcats_exists += 1

                active_category_ids.add(sub_cat.id)

        if not dry_run:
            # Деактивировать категории, которых больше нет в МойСклад
            stale = Category.objects.filter(
                is_active=True
            ).exclude(
                id__in=active_category_ids
            ).annotate(
                product_count=Count('products')
            )

            deactivated = 0
            for cat in stale:
                cat.is_active = False
                cat.save(update_fields=['is_active'])
                deactivated += 1
                self.stdout.write(
                    f'  - Деактивирована: {cat.title} '
                    f'({cat.product_count} товаров)'
                )

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(f'Категории: {cats_created} создано, {cats_exists} уже было')
        self.stdout.write(f'Подкатегории: {subcats_created} создано, {subcats_exists} уже было')
        if not dry_run:
            self.stdout.write(f'Деактивировано устаревших: {deactivated}')
        self.stdout.write('=' * 60)

        # Статистика
        no_cat = MoySkladProduct.objects.filter(
            archived=False,
            site_category='',
        ).count()
        total = MoySkladProduct.objects.filter(archived=False).count()
        with_cat = total - no_cat
        self.stdout.write(
            f'\nТоваров с категорией: {with_cat}/{total} '
            f'({with_cat * 100 // total if total else 0}%)'
        )

    def _generate_slug(self, title, parent=None):
        """Генерация уникального slug (транслит)"""
        base = translit_slugify(title)
        if not base:
            base = 'category'

        slug = base
        counter = 1
        while Category.objects.filter(slug=slug).exists():
            slug = f"{base}-{counter}"
            counter += 1
        return slug
