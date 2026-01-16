# scraping/management/commands/parse_category.py

from django.core.management.base import BaseCommand, CommandError
from scraping.models import ParserTask
from scraping.parsers import get_parser, PARSERS


class Command(BaseCommand):
    help = 'Парсинг по заданию ParserTask'

    def add_arguments(self, parser):
        parser.add_argument(
            'task_id',
            type=int,
            nargs='?',
            help='ID задания ParserTask'
        )
        parser.add_argument('--list', action='store_true', help='Показать все задания')
        parser.add_argument('--limit', type=int, default=0, help='Лимит товаров')
        parser.add_argument('--dry-run', action='store_true', help='Только показать что будет спарсено')

    def handle(self, *args, **options):
        # Показать список заданий
        if options['list']:
            self.show_tasks()
            return

        task_id = options['task_id']
        if not task_id:
            self.stderr.write(self.style.ERROR('Укажите ID задания или --list'))
            return

        # Получаем задание
        try:
            task = ParserTask.objects.select_related('target_brand', 'target_category').get(pk=task_id)
        except ParserTask.DoesNotExist:
            raise CommandError(f"Задание с ID={task_id} не найдено")

        # Проверяем парсер
        if task.parser_name not in PARSERS:
            raise CommandError(f"Парсер '{task.parser_name}' не найден. Доступные: {', '.join(PARSERS.keys())}")

        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write(f"Задание #{task.id}")
        self.stdout.write(f"Парсер: {task.parser_name}")
        self.stdout.write(f"Бренд: {task.target_brand}")
        self.stdout.write(f"Категория: {task.target_category}")
        self.stdout.write(f"URL: {task.source_url}")
        if options['limit']:
            self.stdout.write(f"Лимит: {options['limit']}")
        self.stdout.write(f"{'=' * 60}\n")

        # Показываем обязательные атрибуты категории
        required_attrs = task.target_category.get_required_attributes()
        if required_attrs:
            self.stdout.write("Обязательные атрибуты категории:")
            for attr in required_attrs:
                self.stdout.write(f"  - {attr.name} (code={attr.code})")
            self.stdout.write("")

        # Создаём парсер
        parser = get_parser(task.parser_name, category_url=task.source_url)

        # Dry run
        if options['dry_run']:
            self.stdout.write("[DRY-RUN] Загрузка первой страницы...\n")
            soup = parser.fetch(task.source_url)
            if soup:
                products = parser.parse_catalog_page(soup)
                self.stdout.write(f"Найдено товаров: {len(products)}\n")
                for p in products[:10]:
                    specs = p.get('specifications', {})
                    specs_str = ', '.join(f"{k}={v.get('value')}" for k, v in specs.items() if k != '_raw')
                    self.stdout.write(f"  {p['sku']}: {specs_str or 'без размеров'}")
                if len(products) > 10:
                    self.stdout.write(f"  ... и ещё {len(products) - 10}")
            else:
                self.stdout.write(self.style.ERROR("Не удалось загрузить страницу"))
            return

        # Запуск парсинга
        result = parser.run_task(task, limit=options['limit'])

        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write(self.style.SUCCESS("Парсинг завершён!"))
        self.stdout.write(f"  Создано:   {result['created']}")
        self.stdout.write(f"  Обновлено: {result['updated']}")
        self.stdout.write(f"  Ошибок:    {result['errors']}")
        self.stdout.write(f"  Всего:     {result['total']}")
        self.stdout.write(f"{'=' * 60}\n")

    def show_tasks(self):
        """Показать список заданий"""
        tasks = ParserTask.objects.select_related('target_brand', 'target_category').all()

        if not tasks:
            self.stdout.write("Нет заданий. Создайте в админке: Scraping → Задания на парсинг")
            return

        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write("Задания на парсинг:")
        self.stdout.write(f"{'=' * 60}")

        for task in tasks:
            status_icon = {
                'pending': '⏳',
                'running': '🔄',
                'completed': '✅',
                'error': '❌'
            }.get(task.status, '?')

            active = '✓' if task.is_active else '✗'
            self.stdout.write(
                f"  [{task.id}] {status_icon} {task.target_brand} / {task.target_category} "
                f"(active={active}, parsed={task.items_parsed})"
            )

        self.stdout.write(f"\nИспользование:")
        self.stdout.write(f"  python manage.py parse_category <ID>")
        self.stdout.write(f"  python manage.py parse_category <ID> --dry-run")
        self.stdout.write(f"  python manage.py parse_category <ID> --limit=10\n")