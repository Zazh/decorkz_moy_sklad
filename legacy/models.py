# legacy/models.py

from django.db import models


class LegacyProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().using('legacy')


class LegacyProduct(models.Model):
    """Read-only модель товара из легаси базы"""
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    youtube_url = models.URLField(blank=True)
    category = models.ForeignKey(
        'LegacyCategory',
        on_delete=models.DO_NOTHING,
        related_name='products',
        db_column='category_id'
    )

    objects = LegacyProductManager()

    class Meta:
        managed = False
        db_table = 'products_product'

    def __str__(self):
        return f"{self.title} ({self.sku})"


class LegacyCategory(models.Model):
    """Read-only модель категории из легаси"""
    title = models.CharField(max_length=100)
    slug = models.SlugField()
    parent = models.ForeignKey(
        'self',
        null=True,
        on_delete=models.DO_NOTHING,
        related_name='children',
        db_column='parent_id'
    )

    objects = LegacyProductManager()

    class Meta:
        managed = False
        db_table = 'products_productcategory'

    def __str__(self):
        return self.title


class LegacyProductImage(models.Model):
    """Read-only модель изображений из легаси"""
    product = models.ForeignKey(
        LegacyProduct,
        on_delete=models.DO_NOTHING,
        related_name='images',
        db_column='product_id'
    )
    image = models.CharField(max_length=255)
    is_main = models.BooleanField(default=False)

    objects = LegacyProductManager()

    class Meta:
        managed = False
        db_table = 'products_productimage'


class LegacyAttribute(models.Model):
    """Read-only модель атрибута из легаси"""
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    value_type = models.CharField(max_length=10)

    objects = LegacyProductManager()

    class Meta:
        managed = False
        db_table = 'products_attribute'

    def __str__(self):
        return self.name


class LegacyProductAttributeValue(models.Model):
    """Read-only модель значений атрибутов из легаси"""
    product = models.ForeignKey(
        LegacyProduct,
        on_delete=models.DO_NOTHING,
        related_name='attribute_values',
        db_column='product_id'
    )
    attribute = models.ForeignKey(
        LegacyAttribute,
        on_delete=models.DO_NOTHING,
        db_column='attribute_id'
    )
    value = models.CharField(max_length=255)

    objects = LegacyProductManager()

    class Meta:
        managed = False
        db_table = 'products_productattributevalue'

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"