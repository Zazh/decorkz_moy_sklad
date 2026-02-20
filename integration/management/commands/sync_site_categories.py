# integration/management/commands/sync_site_categories.py

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from integration.models import MoySkladProduct
from references.models import Category


class Command(BaseCommand):
    help = 'Создание категорий каталога из атрибутов "Категория сайт" и "Подкатегория сайт"'

    EXCLUDED_CATEGORIES = [
        'Реклама',
        'Не загружать (прочее)',
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать что будет создано'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write('=' * 60)
        self.stdout.write('Создание категорий из МойСклад → Category')
        self.stdout.write('=' * 60)

        # Собираем уникальные категории и подкатегории
        products = MoySkladProduct.objects.filter(
            archived=False
        ).exclude(
            site_category=''
        )

        # Исключаем служебные категории
        for excluded in self.EXCLUDED_CATEGORIES:
            products = products.exclude(site_category=excluded)

        # Собираем уникальные пары
        category_data = {}  # {category_name: set(subcategory_names)}
        for ms in products.values_list('site_category', 'site_subcategory'):
            cat_name, subcat_name = ms
            if cat_name not in category_data:
                category_data[cat_name] = set()
            if subcat_name:
                category_data[cat_name].add(subcat_name)

        self.stdout.write(f'\nНайдено категорий: {len(category_data)}')
        total_subcats = sum(len(v) for v in category_data.values())
        self.stdout.write(f'Найдено подкатегорий: {total_subcats}')

        cats_created = 0
        cats_exists = 0
        subcats_created = 0
        subcats_exists = 0

        for cat_name in sorted(category_data.keys()):
            subcat_names = category_data[cat_name]

            if dry_run:
                self.stdout.write(f'\n  📁 {cat_name}')
                for sc in sorted(subcat_names):
                    self.stdout.write(f'    📄 {sc}')
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
                cats_exists += 1

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
                    subcats_exists += 1

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(f'Категории: {cats_created} создано, {cats_exists} уже было')
        self.stdout.write(f'Подкатегории: {subcats_created} создано, {subcats_exists} уже было')
        self.stdout.write('=' * 60)

        # Статистика по товарам без категории
        no_cat = MoySkladProduct.objects.filter(
            archived=False,
            site_category='',
        ).count()
        total = MoySkladProduct.objects.filter(archived=False).count()
        with_cat = total - no_cat
        self.stdout.write(f'\nТоваров с категорией: {with_cat}/{total} ({with_cat*100//total if total else 0}%)')

    def _generate_slug(self, title, parent=None):
        """Генерация уникального slug"""
        base = slugify(title, allow_unicode=True)
        if not base:
            base = slugify(title.lower().replace(' ', '-'))
        if not base:
            base = 'category'

        slug = base
        counter = 1
        while Category.objects.filter(slug=slug).exists():
            slug = f"{base}-{counter}"
            counter += 1
        return slug
