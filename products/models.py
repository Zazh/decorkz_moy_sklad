# products/models.py

from django.db import models
from catalog.translit import translit_slugify


class Product(models.Model):
    """
    Товар для витрины.
    Связывает МойСклад (цены/остатки) с карточкой контента.
    """

    # Связь с МойСклад (цены, остатки)
    moysklad = models.OneToOneField(
        'integration.MoySkladProduct',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='product',
        verbose_name="МойСклад"
    )

    # Связь с карточкой контента
    card = models.OneToOneField(
        'cards.ProductCard',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='product',
        verbose_name="Карточка контента"
    )

    # Идентификация
    article = models.CharField(
        "Артикул",
        max_length=100,
        unique=True,
        db_index=True
    )
    slug = models.SlugField(
        "URL",
        max_length=255,
        unique=True,
        blank=True
    )

    # Классификация
    brand = models.ForeignKey(
        'references.Brand',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='products',
        verbose_name="Бренд"
    )
    category = models.ForeignKey(
        'references.Category',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='products',
        verbose_name="Категория"
    )

    # Статус
    is_active = models.BooleanField("Активен", default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at']
        db_table = 'pim_product'

    def __str__(self):
        return f"{self.article} — {self.title}"

    def get_absolute_url(self):
        """Плоский URL: /catalog/<leaf-category>/<product-slug>/"""
        from django.urls import reverse
        cat = self.category
        if cat:
            return reverse('store:catalog_or_product', kwargs={
                'slug1': cat.slug,
                'slug2': self.slug,
            })
        return f'/catalog/other/{self.slug}/'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_slug()
        super().save(*args, **kwargs)

    def generate_slug(self):
        """Генерация slug из названия товара (без категории — она в URL пути)."""
        title_part = translit_slugify(self.title) if self.card else ''
        if not title_part:
            title_part = translit_slugify(self.article) or 'product'

        base = title_part[:200]
        slug = base
        counter = 1

        while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base[:190]}-{counter}"
            counter += 1

        return slug

    # ═══════════════════════════════════════════════════════════
    # Данные из карточки контента (@property)
    # ═══════════════════════════════════════════════════════════

    @property
    def title(self):
        """Название из карточки"""
        return self.card.title if self.card else self.article

    @property
    def description(self):
        """Описание из карточки"""
        return self.card.description if self.card else ""

    @property
    def short_description(self):
        """Короткое описание из карточки"""
        return self.card.short_description if self.card else ""

    @property
    def main_image(self):
        """Главное изображение из карточки"""
        if self.card:
            return self.card.get_main_image()
        return None

    @property
    def images(self):
        """Все изображения из карточки"""
        if self.card:
            return self.card.images.all()
        return []

    @property
    def attributes(self):
        """Атрибуты из карточки"""
        if self.card:
            return self.card.attributes.all()
        return []

    # ═══════════════════════════════════════════════════════════
    # Данные из МойСклад (@property)
    # ═══════════════════════════════════════════════════════════

    @property
    def price(self):
        """Розничная цена (РРЦ) из Price"""
        from pricing.models import Price
        p = Price.objects.filter(
            product=self,
            price_type__name='РРЦ',
            is_active=True,
        ).first()
        return p.price if p else None

    @property
    def sku(self):
        """SKU из МойСклад"""
        if self.moysklad:
            return self.moysklad.code or self.moysklad.article
        return self.article

    @property
    def barcode(self):
        """Штрихкод из МойСклад"""
        if self.moysklad:
            return self.moysklad.barcode
        return None