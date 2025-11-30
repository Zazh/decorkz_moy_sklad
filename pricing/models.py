# pricing/models.py

from django.db import models


class PriceType(models.Model):
    """Типы цен из МойСклад"""
    moysklad_id = models.CharField("ID МойСклад", max_length=255, unique=True)
    name = models.CharField("Название", max_length=100)
    external_code = models.CharField("Внешний код", max_length=255, blank=True)

    is_default = models.BooleanField("По умолчанию", default=False)
    is_public = models.BooleanField("Публичная", default=False)
    is_wholesale = models.BooleanField("Оптовая", default=False)

    sort_order = models.IntegerField("Сортировка", default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Тип цены"
        verbose_name_plural = "Типы цен"
        ordering = ['sort_order', 'name']
        db_table = 'pim_price_type'

    def save(self, *args, **kwargs):
        if self.is_default:
            PriceType.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Price(models.Model):
    """Цены товаров"""
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='prices',
        verbose_name="Товар"
    )
    price_type = models.ForeignKey(
        PriceType,
        on_delete=models.CASCADE,
        related_name='prices',
        verbose_name="Тип цены"
    )

    price = models.DecimalField("Цена", max_digits=12, decimal_places=2)
    old_price = models.DecimalField("Старая цена", max_digits=12, decimal_places=2, null=True, blank=True)

    is_active = models.BooleanField("Активна", default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Цена"
        verbose_name_plural = "Цены"
        unique_together = [['product', 'price_type']]
        db_table = 'pim_price'

    def __str__(self):
        return f"{self.product.sku} — {self.price_type.name}: {self.price}"

    @property
    def has_discount(self):
        return bool(self.old_price and self.old_price > self.price)

    @property
    def discount_percent(self):
        if self.has_discount:
            return int(round((self.old_price - self.price) / self.old_price * 100))
        return 0