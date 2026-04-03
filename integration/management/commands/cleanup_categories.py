# integration/management/commands/cleanup_categories.py

from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from references.models import Category
from products.models import Product


class Command(BaseCommand):
    help = 'Очистка дублей категорий: объединение подкатегорий-дублей с родителем и удаление пустых'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать что будет сделано'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write('=' * 60)
        self.stdout.write('Очистка дублей категорий')
        self.stdout.write('=' * 60)

        merged = 0
        deleted = 0

        # 1. Подкатегории, название которых совпадает с родителем
        #    (Краска → Краска, Клей → Клей, и т.д.)
        self.stdout.write('\n--- Подкатегории-дубли родителя ---')
        for child in Category.objects.filter(parent__isnull=False).select_related('parent'):
            if child.title.strip().lower() != child.parent.title.strip().lower():
                continue

            product_count = Product.objects.filter(category=child).count()
            self.stdout.write(
                f'  "{child.parent.title}" → "{child.title}" '
                f'({product_count} товаров, id={child.id})'
            )

            if not dry_run:
                # Перепривязать товары к родителю
                moved = Product.objects.filter(category=child).update(category=child.parent)
                child.delete()
                merged += 1
                self.stdout.write(f'    → Перенесено {moved} товаров, подкатегория удалена')

        # 2. Пустые категории (0 товаров, нет дочерних с товарами)
        self.stdout.write('\n--- Пустые категории ---')
        for cat in Category.objects.annotate(
            own_products=Count('products'),
            child_products=Count('children__products'),
        ).filter(own_products=0, child_products=0):
            self.stdout.write(f'  "{cat.title}" (id={cat.id}, parent={cat.parent})')
            if not dry_run:
                cat.delete()
                deleted += 1

        self.stdout.write('\n' + '=' * 60)
        if dry_run:
            self.stdout.write('DRY RUN — изменения не внесены')
        else:
            self.stdout.write(f'Объединено дублей: {merged}')
            self.stdout.write(f'Удалено пустых: {deleted}')
        self.stdout.write('=' * 60)
