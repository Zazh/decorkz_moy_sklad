from django.core.management.base import BaseCommand
from integration.services.moysklad_api import MoySkladAPI


class Command(BaseCommand):
    help = 'Показать товары из МойСклад (первые 10)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Количество товаров для отображения (по умолчанию 10)'
        )

    def handle(self, *args, **options):
        limit = options['limit']

        self.stdout.write('=' * 80)
        self.stdout.write(f'Получение товаров из МойСклад (первые {limit})')
        self.stdout.write('=' * 80)

        try:
            api = MoySkladAPI()
            response = api.get_products(limit=limit)

            products = response.get('rows', [])
            total = response.get('meta', {}).get('size', 0)

            self.stdout.write(f'\nВсего товаров в МойСклад: {total}')
            self.stdout.write(f'Показано: {len(products)}\n')

            for i, product in enumerate(products, 1):
                self.stdout.write('-' * 80)
                self.stdout.write(f'{i}. {product.get("name")}')
                self.stdout.write(f'   ID: {product.get("id")}')
                self.stdout.write(f'   Артикул: {product.get("article", "нет")}')
                self.stdout.write(f'   Код: {product.get("code", "нет")}')

                # Цена
                sale_prices = product.get('salePrices', [])
                if sale_prices:
                    price = sale_prices[0].get('value', 0) / 100
                    currency = sale_prices[0].get('currency', {}).get('name', 'руб.')
                    self.stdout.write(f'   Цена: {price} {currency}')
                else:
                    self.stdout.write(f'   Цена: не указана')

                # Архивный?
                archived = product.get('archived', False)
                if archived:
                    self.stdout.write(f'   Статус: АРХИВНЫЙ')

                # Описание (первые 100 символов)
                description = product.get('description', '')
                if description:
                    desc_short = description[:100] + '...' if len(description) > 100 else description
                    self.stdout.write(f'   Описание: {desc_short}')

            self.stdout.write('\n' + '=' * 80)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))