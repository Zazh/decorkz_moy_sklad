# scraping/management/commands/run_parser.py

from django.core.management.base import BaseCommand, CommandError
from scraping.parsers import get_parser, list_parsers, PARSERS


class Command(BaseCommand):
    help = 'Запуск парсера по имени'

    def add_arguments(self, parser):
        parser.add_argument(
            'parser_name',
            type=str,
            nargs='?',
            help='Имя парсера для запуска'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Показать список доступных парсеров'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Ограничить количество товаров (для тестирования)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать URL без парсинга'
        )

    def handle(self, *args, **options):
        # Показать список парсеров
        if options['list']:
            self.show_parsers_list()
            return

        # Проверка что указано имя парсера
        parser_name = options['parser_name']
        if not parser_name:
            self.stderr.write(self.style.ERROR('Укажите имя парсера'))
            self.stderr.write('Используйте --list для просмотра доступных парсеров')
            return

        # Проверка что парсер существует
        if parser_name not in PARSERS:
            self.stderr.write(self.style.ERROR(f"Парсер '{parser_name}' не найден"))
            self.show_parsers_list()
            return

        # Получаем парсер
        parser = get_parser(parser_name)

        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write(f"Парсер: {parser.name}")
        self.stdout.write(f"Бренд: {parser.brand}")
        self.stdout.write(f"URL: {parser.base_url}")
        self.stdout.write(f"{'=' * 60}\n")

        # Dry run — только показать URL
        if options['dry_run']:
            self.do_dry_run(parser, options['limit'])
            return

        # Запуск парсера
        self.stdout.write("Запуск парсинга...\n")

        try:
            result = parser.run(limit=options['limit'])

            self.stdout.write(f"\n{'=' * 60}")
            self.stdout.write(self.style.SUCCESS("Парсинг завершён!"))
            self.stdout.write(f"  Создано:   {result['created']}")
            self.stdout.write(f"  Обновлено: {result['updated']}")
            self.stdout.write(f"  Ошибок:    {result['errors']}")
            self.stdout.write(f"  Всего URL: {result['total']}")
            self.stdout.write(f"{'=' * 60}\n")

        except Exception as e:
            raise CommandError(f"Ошибка парсинга: {e}")

    def show_parsers_list(self):
        """Показать список доступных парсеров"""
        self.stdout.write("\nДоступные парсеры:")
        self.stdout.write("-" * 40)

        if not PARSERS:
            self.stdout.write(self.style.WARNING("  Нет зарегистрированных парсеров"))
            self.stdout.write("\n  Создайте парсер в scraping/parsers/")
            self.stdout.write("  и добавьте его в PARSERS в __init__.py")
        else:
            for name, parser_class in PARSERS.items():
                self.stdout.write(f"  {name:15} — {parser_class.brand}")

        self.stdout.write("-" * 40)
        self.stdout.write("\nИспользование:")
        self.stdout.write("  python manage.py run_parser <имя>")
        self.stdout.write("  python manage.py run_parser <имя> --limit=10")
        self.stdout.write("  python manage.py run_parser <имя> --dry-run\n")

    def do_dry_run(self, parser, limit: int):
        """Показать URL без парсинга"""
        self.stdout.write("[DRY-RUN] Получение списка URL...\n")

        try:
            urls = parser.get_product_urls()

            if limit > 0:
                urls = urls[:limit]

            self.stdout.write(f"Найдено URL: {len(urls)}\n")
            self.stdout.write("-" * 60)

            for i, url in enumerate(urls, 1):
                self.stdout.write(f"{i:4}. {url}")

            self.stdout.write("-" * 60)
            self.stdout.write(f"\nВсего: {len(urls)} URL")

            if limit > 0:
                self.stdout.write(self.style.WARNING(f"(ограничено --limit={limit})"))

        except Exception as e:
            raise CommandError(f"Ошибка получения URL: {e}")