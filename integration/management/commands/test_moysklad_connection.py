from django.core.management.base import BaseCommand
from integration.services.moysklad_api import MoySkladAPI
from django.conf import settings


class Command(BaseCommand):
    help = 'Тестирование подключения к МойСклад API'

    def handle(self, *args, **options):
        self.stdout.write('=' * 50)
        self.stdout.write('Тестирование подключения к МойСклад API')
        self.stdout.write('=' * 50)

        # Проверка настроек
        self.stdout.write('\n1. Проверка настроек:')
        self.stdout.write(f'   API URL: {settings.MOYSKLAD_API_URL}')

        if settings.MOYSKLAD_TOKEN:
            self.stdout.write(f'   Токен: {"*" * 20} (установлен)')
        elif settings.MOYSKLAD_LOGIN and settings.MOYSKLAD_PASSWORD:
            self.stdout.write(f'   Логин: {settings.MOYSKLAD_LOGIN}')
            self.stdout.write(f'   Пароль: {"*" * len(settings.MOYSKLAD_PASSWORD)} (установлен)')
        else:
            self.stdout.write(self.style.ERROR('   ОШИБКА: Не указаны credentials!'))
            self.stdout.write('   Укажите либо MOYSKLAD_TOKEN, либо MOYSKLAD_LOGIN и MOYSKLAD_PASSWORD в .env')
            return

        # Попытка подключения
        self.stdout.write('\n2. Попытка подключения к API...')

        try:
            api = MoySkladAPI()

            # Получаем 1 товар для теста
            self.stdout.write('   Запрос товаров (limit=1)...')
            response = api.get_products(limit=1)

            # Проверяем ответ
            if 'rows' in response:
                self.stdout.write(self.style.SUCCESS('   ✓ Подключение успешно!'))

                # Показываем статистику
                meta = response.get('meta', {})
                total = meta.get('size', 0)
                self.stdout.write(f'\n3. Статистика:')
                self.stdout.write(f'   Всего товаров в МойСклад: {total}')

                # Показываем пример товара
                if response['rows']:
                    product = response['rows'][0]
                    self.stdout.write(f'\n4. Пример товара:')
                    self.stdout.write(f'   ID: {product.get("id")}')
                    self.stdout.write(f'   Название: {product.get("name")}')
                    self.stdout.write(f'   Артикул: {product.get("article", "нет")}')
                    self.stdout.write(f'   Код: {product.get("code", "нет")}')

                    # Проверяем цены
                    sale_prices = product.get('salePrices', [])
                    if sale_prices:
                        price = sale_prices[0].get('value', 0) / 100
                        self.stdout.write(f'   Цена: {price} руб.')

                self.stdout.write('\n' + '=' * 50)
                self.stdout.write(self.style.SUCCESS('Тест пройден успешно! Можно начинать синхронизацию.'))
                self.stdout.write('=' * 50)

            else:
                self.stdout.write(self.style.ERROR('   ✗ Неожиданный формат ответа'))
                self.stdout.write(f'   Ответ: {response}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Ошибка подключения!'))
            self.stdout.write(self.style.ERROR(f'   {str(e)}'))
            self.stdout.write('\nВозможные причины:')
            self.stdout.write('   1. Неверный логин/пароль или токен')
            self.stdout.write('   2. Нет доступа к API в настройках пользователя')
            self.stdout.write('   3. Проблемы с сетью')
            self.stdout.write('   4. Неверный URL API')