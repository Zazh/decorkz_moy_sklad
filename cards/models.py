# cards/models.py

from django.db import models


class ProductCard(models.Model):
    """
    Карточка товара — чистый контент.
    Создаётся вручную или из ScrapedProduct после обработки.
    """

    SOURCE_CHOICES = [
        ('manual', 'Ручной ввод'),
        ('parsed', 'Из парсинга'),
        ('moysklad', 'Из МойСклад'),
    ]

    # Контент
    title = models.CharField("Название", max_length=500)
    short_description = models.CharField("Короткое описание", max_length=1000, blank=True)
    description = models.TextField("Описание", blank=True)

    # Откуда появилась
    source = models.CharField(
        "Источник",
        max_length=20,
        choices=SOURCE_CHOICES,
        default='manual'
    )

    # Ссылка на исходные спарсенные данные (для истории)
    scraped_source_url = models.URLField(
        "URL источника парсинга",
        blank=True,
        help_text="Откуда были взяты данные (для справки)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Карточка контента"
        verbose_name_plural = "Карточки контента"
        ordering = ['-created_at']
        db_table = 'pim_product_card'

    def __str__(self):
        return self.title

    def get_main_image(self):
        """Главное изображение"""
        return self.images.filter(is_main=True).first() or self.images.first()


class ProductCardImage(models.Model):
    """Изображения карточки"""

    card = models.ForeignKey(
        ProductCard,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Карточка"
    )

    image = models.ImageField("Изображение", upload_to='cards/')
    alt = models.CharField("Alt текст", max_length=255, blank=True)

    is_main = models.BooleanField("Главное", default=False)
    sort_order = models.IntegerField("Сортировка", default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"
        ordering = ['-is_main', 'sort_order']
        db_table = 'pim_product_card_image'

    def __str__(self):
        return f"{self.card.title[:30]} — изображение {self.sort_order}"

    def save(self, *args, **kwargs):
        if self.is_main:
            ProductCardImage.objects.filter(
                card=self.card, is_main=True
            ).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)


class ProductCardAttribute(models.Model):
    """Атрибуты карточки — ссылаются на справочник"""

    card = models.ForeignKey(
        ProductCard,
        on_delete=models.CASCADE,
        related_name='attributes',
        verbose_name="Карточка"
    )

    attribute = models.ForeignKey(
        'references.AttributeDefinition',
        on_delete=models.PROTECT,
        related_name='card_values',
        verbose_name="Атрибут"
    )

    value = models.CharField("Значение", max_length=500)

    normalized_value = models.DecimalField(
        "Нормализованное значение",
        max_digits=20,
        decimal_places=6,
        null=True, blank=True,
        help_text="Для числовых атрибутов — значение в базовых единицах"
    )

    sort_order = models.IntegerField("Сортировка", default=0)

    class Meta:
        verbose_name = "Атрибут карточки"
        verbose_name_plural = "Атрибуты карточки"
        ordering = ['sort_order']
        db_table = 'pim_product_card_attribute'
        unique_together = [['card', 'attribute']]

    def __str__(self):
        unit = self.attribute.default_unit
        if unit:
            return f"{self.attribute.name}: {self.value} {unit.symbol}"
        return f"{self.attribute.name}: {self.value}"

    def save(self, *args, **kwargs):
        if self.attribute.value_type in ('integer', 'decimal') and self.attribute.default_unit:
            try:
                from decimal import Decimal
                val = Decimal(self.value.replace(',', '.').strip())
                self.normalized_value = self.attribute.default_unit.to_base(val)
            except:
                self.normalized_value = None
        super().save(*args, **kwargs)