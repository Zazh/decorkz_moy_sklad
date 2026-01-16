# scraping/parsers/decor_dizayn.py

import re
import logging
from typing import Optional

from bs4 import BeautifulSoup
from django.utils import timezone

from .base import BaseParser, ParsedProduct

logger = logging.getLogger(__name__)


class DecorDizaynParser(BaseParser):
    """
    Парсер сайта decor-dizayn.ru
    """

    name = "decor_dizayn"
    brand = "Decor Dizayn"
    base_url = "https://decor-dizayn.ru"
    rate_limit = 1.5

    def __init__(self, category_url: str = None):
        super().__init__()
        self.category_url = category_url

        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
        })

    def normalize_sku(self, raw_sku: str) -> str:
        """Нормализация артикула"""
        if not raw_sku:
            return ""

        match = re.search(r'(DD\d+[A-Za-z]*(?:\([^)]+\))?)', raw_sku, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        return raw_sku.strip().upper()

    def get_product_urls(self) -> list[str]:
        """Собрать URL всех товаров из каталога"""
        if not self.category_url:
            raise ValueError("category_url не задан")

        urls = []
        page = 1

        while True:
            if page == 1:
                page_url = self.category_url
            else:
                page_url = f"{self.category_url.rstrip('/')}/?PAGEN_1={page}"

            logger.info(f"[{self.name}] Загрузка страницы {page}: {page_url}")
            soup = self.fetch(page_url)

            if not soup:
                break

            product_cards = soup.select('[data-entity="item"]')

            if not product_cards:
                logger.warning(f"[{self.name}] Товары не найдены на странице {page}")
                break

            for card in product_cards:
                link = card.select_one('a[href*="/catalog/"]')
                if link and link.get('href'):
                    url = self.make_absolute_url(link['href'])
                    if url not in urls:
                        urls.append(url)

            logger.info(f"[{self.name}] Страница {page}: найдено {len(product_cards)} товаров")

            next_page = soup.select_one('.pagination .next:not(.disabled), .bx-pag-next:not(.disabled)')
            if not next_page:
                break

            page += 1
            if page > 100:
                break

        logger.info(f"[{self.name}] Всего URL: {len(urls)}")
        return urls

    def parse_product(self, url: str) -> Optional[ParsedProduct]:
        """Парсинг страницы товара"""
        soup = self.fetch(url)
        if not soup:
            return None

        # === Название (h2.product_name) ===
        title = ""
        h2 = soup.select_one('h2.product_name')
        if h2:
            title = h2.get_text(strip=True)

        # === SKU из названия ===
        sku = ""
        match = re.search(r'(DD\d+[A-Za-z]*(?:\([^)]+\))?)', title, re.IGNORECASE)
        if match:
            sku = match.group(1)

        if not sku:
            logger.warning(f"[{self.name}] SKU не найден: {url}")
            return None

        # === Характеристики (.data .item) ===
        specs_raw = {}
        specs_standard = {}

        data_block = soup.select_one('.data')
        if data_block:
            items = data_block.select('.item')
            for item in items:
                name_el = item.select_one('div')
                value_el = item.select_one('p')
                if name_el and value_el:
                    name = name_el.get_text(strip=True)
                    value = value_el.get_text(strip=True)
                    specs_raw[name] = value

            # Стандартизируем
            specs_standard = self._standardize_specs(specs_raw)

        # === Изображения (.newGall__thumbImg[full]) ===
        images = []
        for img in soup.select('.newGall__thumbImg[full]'):
            full_url = img.get('full', '')
            if full_url:
                images.append(self.make_absolute_url(full_url))

        # Если нет галереи — пробуем основное изображение
        if not images:
            main_img = soup.select_one('.newGall__detailImg')
            if main_img and main_img.get('src'):
                images.append(self.make_absolute_url(main_img['src']))

        # === Описание ===
        description = ""
        desc_el = soup.select_one('.description, .detail-text, [itemprop="description"]')
        if desc_el:
            description = desc_el.get_text(strip=True)

        return ParsedProduct(
            source_url=url,
            sku=self.normalize_sku(sku),
            title=title,
            brand=self.brand,
            description=description,
            specifications={
                '_raw': specs_raw,
                **specs_standard
            },
            images=images,
        )

    def _standardize_specs(self, raw_specs: dict) -> dict:
        """
        Стандартизация характеристик.
        Вход: {"Длина (мм)": "2000 мм", "Высота (мм)": "36 мм"}
        Выход: {"length": {"value": 2000, "unit": "mm", "display": "2000 мм"}}
        """
        result = {}

        # Маппинг названий → стандартные коды
        mapping = {
            'длина': 'length',
            'высота': 'height',
            'толщина': 'thickness',
            'ширина': 'width',
            'вес': 'weight',
            'материал': 'material',
        }

        for raw_name, raw_value in raw_specs.items():
            raw_name_lower = raw_name.lower()

            for rus_name, code in mapping.items():
                if rus_name in raw_name_lower:
                    # Пробуем извлечь число
                    num_match = re.search(r'(\d+(?:[.,]\d+)?)', raw_value)
                    if num_match:
                        value = float(num_match.group(1).replace(',', '.'))
                        if value == int(value):
                            value = int(value)

                        # Определяем единицу измерения
                        unit = 'mm'  # по умолчанию
                        if 'см' in raw_value:
                            unit = 'cm'
                        elif 'м' in raw_value and 'мм' not in raw_value:
                            unit = 'm'
                        elif 'кг' in raw_value:
                            unit = 'kg'
                        elif 'г' in raw_value and 'кг' not in raw_value:
                            unit = 'g'

                        result[code] = {
                            'value': value,
                            'unit': unit,
                            'display': raw_value
                        }
                    else:
                        # Не число — сохраняем как строку
                        result[code] = {
                            'value': raw_value,
                            'unit': None,
                            'display': raw_value
                        }
                    break

        return result

    def parse_catalog_page(self, soup: BeautifulSoup) -> list[dict]:
        """Парсинг каталога (для dry-run)"""
        products = []
        cards = soup.select('[data-entity="item"]')

        for card in cards:
            try:
                data_title_el = card.select_one('[data-title]')
                sku = data_title_el.get('data-title', '') if data_title_el else ''

                link = card.select_one('a[href*="/catalog/"]')
                url = self.make_absolute_url(link.get('href', '')) if link else ''

                if sku and url:
                    products.append({
                        'sku': self.normalize_sku(sku),
                        'title': sku,
                        'url': url,
                    })

            except Exception as e:
                logger.error(f"[{self.name}] Ошибка парсинга карточки: {e}")

        return products

    def run_task(self, task, limit: int = 0) -> dict:
        """Запуск парсинга по заданию"""
        from scraping.models import ScrapedProduct, ScrapedImage, ParserRun

        self.category_url = task.source_url
        logger.info(f"[{self.name}] Парсинг задания: {task}")

        task.status = 'running'
        task.save(update_fields=['status'])

        run = ParserRun.objects.create(parser_name=self.name, status='running')

        created = 0
        updated = 0
        errors = 0

        try:
            # 1. Собираем URL из каталога
            urls = self.get_product_urls()

            if limit:
                urls = urls[:limit]

            run.total_items = len(urls)
            run.save(update_fields=['total_items'])

            # 2. Парсим каждую страницу товара
            for i, url in enumerate(urls, 1):
                try:
                    parsed = self.parse_product(url)

                    if not parsed:
                        errors += 1
                        continue

                    # Сохраняем товар
                    obj, is_created = ScrapedProduct.objects.update_or_create(
                        source_url=parsed.source_url,
                        defaults={
                            'parser_task': task,
                            'sku': parsed.sku,
                            'title': parsed.title,
                            'description': parsed.description,
                            'specifications': parsed.specifications,
                        }
                    )

                    # Сохраняем изображения
                    if parsed.images and (is_created or not obj.images.exists()):
                        obj.images.all().delete()
                        for idx, img_url in enumerate(parsed.images):
                            ScrapedImage.objects.create(
                                product=obj,
                                source_url=img_url,
                                is_main=(idx == 0),
                                sort_order=idx
                            )

                    if is_created:
                        created += 1
                        logger.debug(f"[{self.name}] Создан: {parsed.sku}")
                    else:
                        updated += 1
                        logger.debug(f"[{self.name}] Обновлён: {parsed.sku}")

                    if i % 10 == 0:
                        logger.info(f"[{self.name}] Прогресс: {i}/{len(urls)}")

                except Exception as e:
                    logger.error(f"[{self.name}] Ошибка {url}: {e}")
                    errors += 1

            # Успех
            run.status = 'success'
            run.items_created = created
            run.items_updated = updated
            run.errors_count = errors
            run.finished_at = timezone.now()
            run.save()

            task.status = 'completed'
            task.last_run = timezone.now()
            task.items_found = len(urls)
            task.items_parsed = created + updated
            task.error_message = ''
            task.save()

            return {
                'created': created,
                'updated': updated,
                'errors': errors,
                'total': len(urls)
            }

        except Exception as e:
            logger.error(f"[{self.name}] Критическая ошибка: {e}")

            run.status = 'error'
            run.error_message = str(e)
            run.finished_at = timezone.now()
            run.save()

            task.status = 'error'
            task.error_message = str(e)
            task.save()

            raise