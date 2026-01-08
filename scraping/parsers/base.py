# scraping/parsers/base.py

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import requests
from bs4 import BeautifulSoup
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class ParsedProduct:
    """Стандартизированный результат парсинга"""
    source_url: str
    sku: str
    title: str
    brand: str = ""
    short_description: str = ""
    description: str = ""
    category: str = ""
    specifications: dict = field(default_factory=dict)
    images: list = field(default_factory=list)
    documents: list = field(default_factory=list)
    video_url: str = ""


class BaseParser(ABC):
    """
    Базовый класс для всех парсеров.

    Для создания нового парсера:
    1. Наследуйся от BaseParser
    2. Укажи name, brand, base_url
    3. Реализуй get_product_urls() и parse_product()
    """

    # ═══════════════════════════════════════════════════════════
    # НАСТРОЙКИ — переопределить в наследниках
    # ═══════════════════════════════════════════════════════════

    name: str = "base"
    brand: str = ""
    base_url: str = ""
    rate_limit: float = 1.0  # Секунд между запросами

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
        })

    # ═══════════════════════════════════════════════════════════
    # АБСТРАКТНЫЕ МЕТОДЫ — обязательно реализовать
    # ═══════════════════════════════════════════════════════════

    @abstractmethod
    def get_product_urls(self) -> list[str]:
        """
        Получить список URL всех товаров для парсинга.

        Returns:
            Список URL страниц товаров
        """
        pass

    @abstractmethod
    def parse_product(self, url: str) -> Optional[ParsedProduct]:
        """
        Парсинг одной страницы товара.

        Args:
            url: URL страницы товара

        Returns:
            ParsedProduct или None если не удалось спарсить
        """
        pass

    # ═══════════════════════════════════════════════════════════
    # ОПЦИОНАЛЬНЫЕ МЕТОДЫ — переопределить при необходимости
    # ═══════════════════════════════════════════════════════════

    def normalize_sku(self, raw_sku: str) -> str:
        """Нормализация артикула"""
        if not raw_sku:
            return ""
        return raw_sku.strip().upper().replace(" ", "")

    def should_skip(self, url: str) -> bool:
        """Проверка — нужно ли пропустить URL"""
        return False

    def before_run(self):
        """Хук перед запуском парсинга"""
        pass

    def after_run(self, result: dict):
        """Хук после завершения парсинга"""
        pass

    # ═══════════════════════════════════════════════════════════
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ — общие для всех парсеров
    # ═══════════════════════════════════════════════════════════

    def fetch(self, url: str, **kwargs) -> Optional[BeautifulSoup]:
        """
        Загрузка и парсинг страницы.

        Args:
            url: URL для загрузки
            **kwargs: Дополнительные параметры для requests

        Returns:
            BeautifulSoup объект или None при ошибке
        """
        time.sleep(self.rate_limit)

        try:
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.name}] Ошибка загрузки {url}: {e}")
            return None

    def fetch_json(self, url: str, **kwargs) -> Optional[dict]:
        """
        Загрузка JSON.

        Args:
            url: URL API
            **kwargs: Дополнительные параметры для requests

        Returns:
            dict или None при ошибке
        """
        time.sleep(self.rate_limit)

        try:
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.name}] Ошибка загрузки JSON {url}: {e}")
            return None

    def extract_text(self, soup: BeautifulSoup, selector: str, default: str = "") -> str:
        """
        Безопасное извлечение текста по CSS селектору.

        Args:
            soup: BeautifulSoup объект
            selector: CSS селектор
            default: Значение по умолчанию

        Returns:
            Текст элемента или default
        """
        element = soup.select_one(selector)
        if element:
            return element.get_text(strip=True)
        return default

    def extract_texts(self, soup: BeautifulSoup, selector: str) -> list[str]:
        """
        Извлечение текста из всех элементов по селектору.

        Args:
            soup: BeautifulSoup объект
            selector: CSS селектор

        Returns:
            Список текстов
        """
        elements = soup.select(selector)
        return [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]

    def extract_attr(self, soup: BeautifulSoup, selector: str, attr: str, default: str = "") -> str:
        """
        Безопасное извлечение атрибута.

        Args:
            soup: BeautifulSoup объект
            selector: CSS селектор
            attr: Имя атрибута
            default: Значение по умолчанию

        Returns:
            Значение атрибута или default
        """
        element = soup.select_one(selector)
        if element:
            return element.get(attr, default)
        return default

    def extract_attrs(self, soup: BeautifulSoup, selector: str, attr: str) -> list[str]:
        """
        Извлечение атрибута из всех элементов.

        Args:
            soup: BeautifulSoup объект
            selector: CSS селектор
            attr: Имя атрибута

        Returns:
            Список значений атрибута
        """
        elements = soup.select(selector)
        return [el.get(attr) for el in elements if el.get(attr)]

    def make_absolute_url(self, url: str) -> str:
        """Преобразование относительного URL в абсолютный"""
        if not url:
            return ""
        if url.startswith('http'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return self.base_url.rstrip('/') + url
        return self.base_url.rstrip('/') + '/' + url

    # ═══════════════════════════════════════════════════════════
    # ОСНОВНОЙ МЕТОД ЗАПУСКА
    # ═══════════════════════════════════════════════════════════

    def run(self, limit: int = 0) -> dict:
        """
        Запуск полного цикла парсинга.

        Args:
            limit: Ограничение количества товаров (0 = без ограничения)

        Returns:
            Словарь с результатами: created, updated, errors
        """
        from scraping.models import ScrapedProduct, ScrapedImage, ParserRun

        logger.info(f"[{self.name}] Запуск парсера")

        # Создаём запись о запуске
        run = ParserRun.objects.create(
            parser_name=self.name,
            status='running'
        )

        created = 0
        updated = 0
        errors = 0

        try:
            self.before_run()

            # Получаем URL товаров
            urls = self.get_product_urls()

            if limit > 0:
                urls = urls[:limit]

            run.total_items = len(urls)
            run.save(update_fields=['total_items'])

            logger.info(f"[{self.name}] Найдено {len(urls)} URL для парсинга")

            for i, url in enumerate(urls, 1):
                try:
                    if self.should_skip(url):
                        logger.debug(f"[{self.name}] Пропуск: {url}")
                        continue

                    parsed = self.parse_product(url)

                    if not parsed:
                        logger.warning(f"[{self.name}] Не удалось спарсить: {url}")
                        errors += 1
                        continue

                    # Сохраняем в БД
                    obj, is_created = ScrapedProduct.objects.update_or_create(
                        source_url=parsed.source_url,
                        defaults={
                            'parser_name': self.name,
                            'sku': parsed.sku,
                            'title': parsed.title,
                            'short_description': parsed.short_description,
                            'description': parsed.description,
                            'brand': parsed.brand or self.brand,
                            'category': parsed.category,
                            'specifications': parsed.specifications,
                            'documents': parsed.documents,
                            'video_url': parsed.video_url,
                        }
                    )

                    # Сохраняем изображения (только для новых или если нет фото)
                    if is_created or not obj.images.exists():
                        obj.images.all().delete()
                        for idx, img_url in enumerate(parsed.images):
                            ScrapedImage.objects.create(
                                product=obj,
                                source_url=img_url,
                                sort_order=idx,
                                is_main=(idx == 0)
                            )

                    if is_created:
                        created += 1
                        logger.debug(f"[{self.name}] Создан: {parsed.sku}")
                    else:
                        updated += 1
                        logger.debug(f"[{self.name}] Обновлён: {parsed.sku}")

                    # Прогресс каждые 50 товаров
                    if i % 50 == 0:
                        logger.info(f"[{self.name}] Прогресс: {i}/{len(urls)}")

                except Exception as e:
                    logger.error(f"[{self.name}] Ошибка парсинга {url}: {e}")
                    errors += 1

            # Успешное завершение
            run.status = 'success'
            run.items_created = created
            run.items_updated = updated
            run.errors_count = errors
            run.finished_at = timezone.now()
            run.save()

            result = {
                'created': created,
                'updated': updated,
                'errors': errors,
                'total': len(urls)
            }

            self.after_run(result)

            logger.info(
                f"[{self.name}] Завершено: создано {created}, "
                f"обновлено {updated}, ошибок {errors}"
            )

            return result

        except Exception as e:
            logger.error(f"[{self.name}] Критическая ошибка: {e}")
            run.status = 'error'
            run.error_message = str(e)
            run.finished_at = timezone.now()
            run.save()
            raise