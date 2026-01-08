# mapping/models.py

from django.db import models


class BrandMapping(models.Model):
    """Маппинг брендов из разных источников на справочник"""

    SOURCE_CHOICES = [
        ('moysklad', 'МойСклад'),
        ('parser', 'Парсер'),
    ]

    source = models.CharField(
        "Источник",
        max_length=50,
        choices=SOURCE_CHOICES
    )
    source_name = models.CharField(
        "Название в источнике",
        max_length=255,
        help_text="Как бренд называется в МойСклад или на сайте"
    )

    brand = models.ForeignKey(
        'references.Brand',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mappings',
        verbose_name="Бренд"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Маппинг бренда"
        verbose_name_plural = "Маппинг брендов"
        db_table = 'mapping_brand'
        unique_together = [['source', 'source_name']]
        ordering = ['source_name']

    def __str__(self):
        if self.brand:
            return f"{self.source_name} → {self.brand.name}"
        return f"{self.source_name} (не связан)"

class CategoryMapping(models.Model):
    """Маппинг категорий из разных источников на справочник"""

    SOURCE_CHOICES = [
        ('moysklad', 'МойСклад'),
        ('parser', 'Парсер'),
    ]

    category = models.ForeignKey(
        'references.Category',
        on_delete=models.CASCADE,
        related_name='mappings',
        verbose_name="Категория"
    )

    source = models.CharField(
        "Источник",
        max_length=50,
        choices=SOURCE_CHOICES
    )
    source_name = models.CharField(
        "Название в источнике",
        max_length=500,
        help_text="Путь или название категории в источнике"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Маппинг категории"
        verbose_name_plural = "Маппинг категорий"
        db_table = 'mapping_category'
        unique_together = [['source', 'source_name']]
        ordering = ['category__title', 'source']

    def __str__(self):
        return f"{self.source_name} ({self.source}) → {self.category.title}"


class AttributeMapping(models.Model):
    """Маппинг атрибутов (синонимы) из разных источников"""

    SOURCE_CHOICES = [
        ('moysklad', 'МойСклад'),
        ('parser', 'Парсер'),
    ]

    attribute = models.ForeignKey(
        'references.AttributeDefinition',
        on_delete=models.CASCADE,
        related_name='mappings',
        verbose_name="Атрибут"
    )

    source = models.CharField(
        "Источник",
        max_length=50,
        choices=SOURCE_CHOICES
    )
    source_name = models.CharField(
        "Название в источнике",
        max_length=255,
        help_text="Как атрибут называется в источнике (Power, Мощн., и т.д.)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Маппинг атрибута"
        verbose_name_plural = "Маппинг атрибутов"
        db_table = 'mapping_attribute'
        unique_together = [['source', 'source_name']]
        ordering = ['attribute__name', 'source']

    def __str__(self):
        return f"{self.source_name} ({self.source}) → {self.attribute.name}"