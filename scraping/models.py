# scraping/models.py

from django.db import models


class ScrapedProduct(models.Model):
    """Спарсенный товар с сайта производителя"""

    # Связь с заданием
    parser_task = models.ForeignKey(
        'ParserTask',
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="Задание"
    )

    # Идентификация
    source_url = models.URLField("URL источника", unique=True, max_length=500)
    sku = models.CharField("Артикул производителя", max_length=100, db_index=True)

    # Контент
    title = models.CharField("Название", max_length=500)
    short_description = models.CharField("Короткое описание", max_length=1000, blank=True)
    description = models.TextField("Описание", blank=True)

    # Стандартизированные характеристики
    specifications = models.JSONField(
        "Характеристики",
        default=dict,
        blank=True,
        help_text='Формат: {"_raw": {...}, "length": {"value": 2000, "unit": "mm"}, ...}'
    )

    documents = models.JSONField("Документы (PDF)", default=list, blank=True)
    video_url = models.URLField("Видео", blank=True, max_length=500)

    # Статусы
    is_active = models.BooleanField("Активен", default=True)
    is_processed = models.BooleanField("Обработан", default=False)

    # Результат обработки
    processed_card = models.ForeignKey(
        'cards.ProductCard',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_scraped',
        verbose_name="Созданная карточка"
    )

    # Timestamps
    parsed_at = models.DateTimeField("Дата парсинга", auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Спарсенный товар"
        verbose_name_plural = "Спарсенные товары"
        ordering = ['-parsed_at']
        indexes = [
            models.Index(fields=['parser_task', 'sku']),
        ]

    def __str__(self):
        return f"[{self.parser_task.target_brand}] {self.sku}"

    @property
    def brand(self):
        return self.parser_task.target_brand

    @property
    def category(self):
        return self.parser_task.target_category

    def get_missing_required_attributes(self):
        """Какие обязательные атрибуты не заполнены"""
        required = self.parser_task.target_category.get_required_attributes()
        missing = []
        for attr in required:
            code = attr.code or attr.slug
            if code not in self.specifications:
                missing.append(attr)
        return missing


class ScrapedImage(models.Model):
    """Изображение спарсенного товара"""

    product = models.ForeignKey(
        ScrapedProduct,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Товар"
    )

    source_url = models.URLField("URL изображения", max_length=500)

    # Локальная копия (заполняется при скачивании)
    local_file = models.ImageField(
        "Локальный файл",
        upload_to='scraped/',
        blank=True
    )

    is_main = models.BooleanField("Главное", default=False)
    is_downloaded = models.BooleanField("Скачано", default=False)
    sort_order = models.IntegerField("Сортировка", default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"
        ordering = ['-is_main', 'sort_order']

    def __str__(self):
        return f"{self.product.sku} — img {self.sort_order}"


class ParserRun(models.Model):
    """Лог запуска парсера"""

    STATUS_CHOICES = [
        ('running', 'Выполняется'),
        ('success', 'Успешно'),
        ('error', 'Ошибка'),
    ]

    parser_name = models.CharField("Парсер", max_length=50, db_index=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='running')

    total_items = models.IntegerField("Всего URL", default=0)
    items_created = models.IntegerField("Создано", default=0)
    items_updated = models.IntegerField("Обновлено", default=0)
    errors_count = models.IntegerField("Ошибок", default=0)

    error_message = models.TextField("Сообщение об ошибке", blank=True)

    started_at = models.DateTimeField("Начало", auto_now_add=True)
    finished_at = models.DateTimeField("Окончание", null=True, blank=True)

    class Meta:
        verbose_name = "Запуск парсера"
        verbose_name_plural = "Запуски парсеров"
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.parser_name} — {self.get_status_display()} ({self.started_at:%d.%m.%Y %H:%M})"

    @property
    def duration(self):
        if self.finished_at and self.started_at:
            return self.finished_at - self.started_at
        return None


# scraping/models.py — новая модель

class ParserTask(models.Model):
    """Задание на парсинг категории"""

    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('running', 'Выполняется'),
        ('completed', 'Завершено'),
        ('error', 'Ошибка'),
    ]

    # Источник
    parser_name = models.CharField("Парсер", max_length=50, db_index=True)
    source_url = models.URLField("URL категории", max_length=500)
    source_category_name = models.CharField(
        "Название категории на сайте",
        max_length=255,
        blank=True,
        help_text="Как категория называется на сайте-источнике"
    )

    # Связь с нашими справочниками
    target_brand = models.ForeignKey(
        'references.Brand',
        on_delete=models.PROTECT,
        related_name='parser_tasks',
        verbose_name="Бренд"
    )
    target_category = models.ForeignKey(
        'references.Category',
        on_delete=models.PROTECT,
        related_name='parser_tasks',
        verbose_name="Категория",
        help_text="Товары получат обязательные атрибуты этой категории"
    )

    # Статус
    is_active = models.BooleanField("Активно", default=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='pending')

    # Статистика
    last_run = models.DateTimeField("Последний запуск", null=True, blank=True)
    items_found = models.IntegerField("Найдено товаров", default=0)
    items_parsed = models.IntegerField("Спарсено товаров", default=0)
    error_message = models.TextField("Ошибка", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Задание на парсинг"
        verbose_name_plural = "Задания на парсинг"
        ordering = ['-created_at']
        unique_together = [['parser_name', 'source_url']]
        db_table = 'scraping_parser_task'

    def __str__(self):
        return f"[{self.parser_name}] {self.target_brand} / {self.target_category}"

    def get_required_attributes(self):
        """Обязательные атрибуты для этой категории"""
        return self.target_category.get_required_attributes()