# cards/models.py

from django.db import models
from django.utils.text import slugify


class ProductCard(models.Model):
    """Карточка товара — контент для сайта"""
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cards',
        null=True, blank=True,
        verbose_name="Товар"
    )
    sku = models.CharField("SKU", max_length=100, db_index=True)

    title = models.CharField("Название", max_length=255)
    slug = models.SlugField("URL", unique=True, blank=True)
    description = models.TextField("Описание", blank=True)
    short_description = models.CharField("Короткое описание", max_length=500, blank=True)

    youtube_url = models.URLField("YouTube URL", blank=True)

    is_default = models.BooleanField("По умолчанию", default=False)
    is_active = models.BooleanField("Активна", default=True)
    sort_order = models.IntegerField("Сортировка", default=0)

    source = models.CharField("Источник", max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Карточка товара"
        verbose_name_plural = "Карточки товаров"
        ordering = ['-is_default', 'sort_order']
        db_table = 'pim_product_card'

    def __str__(self):
        return f"{self.title} ({self.sku})"

    def save(self, *args, **kwargs):
        # Привязка по SKU
        if not self.product and self.sku:
            from products.models import Product
            self.product = Product.objects.filter(sku=self.sku).first()

        # Генерация slug
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or self.sku
            slug = base
            counter = 1
            while ProductCard.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug

        # Только одна default карточка на товар
        if self.is_default and self.product:
            ProductCard.objects.filter(
                product=self.product, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)

        super().save(*args, **kwargs)

    def get_main_image(self):
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
    alt = models.CharField("Alt", max_length=255, blank=True)

    is_main = models.BooleanField("Главное", default=False)
    sort_order = models.IntegerField("Сортировка", default=0)

    class Meta:
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"
        ordering = ['-is_main', 'sort_order']
        db_table = 'pim_product_card_image'

    def save(self, *args, **kwargs):
        if self.is_main:
            ProductCardImage.objects.filter(
                card=self.card, is_main=True
            ).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.card.sku} — изображение {self.pk}"


class ProductCardAttribute(models.Model):
    """Атрибуты карточки"""
    card = models.ForeignKey(
        ProductCard,
        on_delete=models.CASCADE,
        related_name='attributes',
        verbose_name="Карточка"
    )
    attribute = models.ForeignKey(
        'catalog.AttributeDefinition',
        on_delete=models.PROTECT,
        related_name='card_values',
        verbose_name="Атрибут"
    )

    value = models.CharField("Значение", max_length=255)
    sort_order = models.IntegerField("Сортировка", default=0)

    class Meta:
        verbose_name = "Атрибут карточки"
        verbose_name_plural = "Атрибуты карточек"
        unique_together = [['card', 'attribute']]
        ordering = ['sort_order']
        db_table = 'pim_product_card_attribute'

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"