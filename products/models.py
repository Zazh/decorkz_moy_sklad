# products/models.py

from django.db import models
from decimal import Decimal


class Product(models.Model):
    """Товар — ядро, синхронизируется из МойСклад"""

    # Идентификаторы
    moysklad_id = models.CharField("ID МойСклад", max_length=255, unique=True)
    sku = models.CharField("SKU (код)", max_length=100, unique=True, db_index=True)
    article = models.CharField("Артикул", max_length=100, blank=True, db_index=True)
    barcode = models.CharField("Штрихкод", max_length=50, blank=True, db_index=True)

    # Базовая информация
    name = models.CharField("Название", max_length=500)

    # Связи
    brand = models.ForeignKey(
        'catalog.Brand',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='products',
        verbose_name="Бренд"
    )
    categories = models.ManyToManyField(
        'catalog.Category',
        related_name='products',
        blank=True,
        verbose_name="Категории"
    )

    # Физические характеристики
    weight = models.DecimalField("Вес (кг)", max_digits=10, decimal_places=3, null=True, blank=True)
    volume = models.DecimalField("Объём (м³)", max_digits=10, decimal_places=6, null=True, blank=True)

    # Флаги из МойСклад
    is_kaspi = models.BooleanField("Товар Kaspi", default=False)
    is_satu = models.BooleanField("Товар Satu", default=False)
    is_promo = models.BooleanField("Акция", default=False)

    # Путь в МойСклад
    moysklad_path = models.CharField("Путь в МойСклад", max_length=500, blank=True)

    # Статусы
    is_active = models.BooleanField("Активен", default=True)
    archived = models.BooleanField("В архиве", default=False)

    # Сырые данные
    raw_data = models.JSONField("Сырые данные", default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_sync = models.DateTimeField("Последняя синхронизация", auto_now=True)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def get_min_price(self):
        """Минимальная цена из raw_data"""
        min_price = self.raw_data.get('minPrice', {}).get('value', 0)
        return Decimal(min_price) / 100 if min_price else None