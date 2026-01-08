# scraping/models.py

from django.db import models


class ScrapedProduct(models.Model):
    """Спарсенный товар с сайта производителя"""

    # Идентификация
    parser_name = models.CharField("Парсер", max_length=50, db_index=True)
    source_url = models.URLField("URL источника", unique=True, max_length=500)
    sku = models.CharField("Артикул производителя", max_length=100, db_index=True)

    # Контент
    title = models.CharField("Название", max_length=500)
    short_description = models.CharField("Короткое описание", max_length=1000, blank=True)
    description = models.TextField("Описание", blank=True)

    # Классификация
    brand = models.CharField("Бренд", max_length=100, db_index=True)
    category = models.CharField("Категория", max_length=255, blank=True)

    # Структурированные данные
    specifications = models.JSONField("Характеристики", default=dict, blank=True)
    documents = models.JSONField("Документы (PDF)", default=list, blank=True)
    video_url = models.URLField("Видео", blank=True, max_length=500)

    # Связь с товаром из МойСклад (заполняется вручную или автоматически)
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='scraped_data',
        verbose_name="Товар PIM"
    )

    # Статусы
    is_active = models.BooleanField("Активен", default=True)
    is_matched = models.BooleanField("Связан с товаром", default=False)

    # Timestamps
    parsed_at = models.DateTimeField("Дата парсинга", auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Спарсенный товар"
        verbose_name_plural = "Спарсенные товары"
        ordering = ['-parsed_at']
        indexes = [
            models.Index(fields=['parser_name', 'sku']),
            models.Index(fields=['brand', 'sku']),
        ]

    def __str__(self):
        return f"[{self.brand}] {self.sku} — {self.title[:50]}"

    def save(self, *args, **kwargs):
        self.is_matched = self.product is not None
        super().save(*args, **kwargs)


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