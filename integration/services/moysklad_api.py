import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class MoySkladAPI:
    """Класс для работы с API МойСклад"""

    def __init__(self):
        self.base_url = settings.MOYSKLAD_API_URL
        self.auth = self._get_auth()

    def _get_auth(self):
        """Получение аутентификации"""
        if settings.MOYSKLAD_TOKEN:
            return {'Authorization': f'Bearer {settings.MOYSKLAD_TOKEN}'}
        else:
            return HTTPBasicAuth(settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD)

    def _make_request(self, method, endpoint, **kwargs):
        """Базовый метод для выполнения запросов"""
        url = f"{self.base_url}/{endpoint}"

        try:
            if isinstance(self.auth, dict):
                kwargs['headers'] = {**kwargs.get('headers', {}), **self.auth}
                response = requests.request(method, url, **kwargs)
            else:
                response = requests.request(method, url, auth=self.auth, **kwargs)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к МойСклад API: {e}")
            raise

    def get_products(self, limit=100, offset=0):
        """Получение списка товаров"""
        params = {
            'limit': limit,
            'offset': offset
        }
        return self._make_request('GET', 'entity/product', params=params)

    def get_product(self, product_id):
        """Получение информации о конкретном товаре"""
        return self._make_request('GET', f'entity/product/{product_id}')

    def create_product(self, data):
        """Создание нового товара"""
        return self._make_request('POST', 'entity/product', json=data)

    def update_product(self, product_id, data):
        """Обновление товара"""
        return self._make_request('PUT', f'entity/product/{product_id}', json=data)

    def get_stock(self, limit=100, offset=0):
        """Получение остатков товаров"""
        params = {
            'limit': limit,
            'offset': offset
        }
        return self._make_request('GET', 'report/stock/all', params=params)

    def get_orders(self, limit=100, offset=0):
        """Получение списка заказов"""
        params = {
            'limit': limit,
            'offset': offset
        }
        return self._make_request('GET', 'entity/customerorder', params=params)

    def create_order(self, data):
        """Создание заказа"""
        return self._make_request('POST', 'entity/customerorder', json=data)

    def get_counterparties(self, limit=100, offset=0):
        """Получение списка контрагентов"""
        params = {
            'limit': limit,
            'offset': offset
        }
        return self._make_request('GET', 'entity/counterparty', params=params)

    def sync_all_products(self):
        """Синхронизация всех товаров"""
        all_products = []
        offset = 0
        limit = 100

        while True:
            response = self.get_products(limit=limit, offset=offset)
            products = response.get('rows', [])

            if not products:
                break

            all_products.extend(products)
            offset += limit

            # Проверка на последнюю страницу
            if len(products) < limit:
                break

        return all_products