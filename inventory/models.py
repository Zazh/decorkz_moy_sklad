# inventory/models.py

from django.db import models


class Warehouse(models.Model):
    """Склады из МойСклад"""
    moysklad_id = models.CharField("ID МойСклад", max_length=255, unique=True)
    name = models.CharField("Название", max_length=100)

    is_active = models.BooleanField("Активен", default=True)
    is_default = models.BooleanField("По умолчанию", default=False)
    sort_order = models.IntegerField("Сортировка", default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Склад"
        verbose_name_plural = "Склады"
        ordering = ['-is_default', 'sort_order', 'name']
        db_table = 'pim_warehouse'

    def save(self, *args, **kwargs):
        if self.is_default:
            Warehouse.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Stock(models.Model):
    """Остатки по складам"""
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='stock_items',
        verbose_name="Товар"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='stock_items',
        verbose_name="Склад"
    )

    quantity = models.IntegerField("Количество", default=0)
    reserve = models.IntegerField("Резерв", default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Остаток"
        verbose_name_plural = "Остатки"
        unique_together = [['product', 'warehouse']]
        db_table = 'pim_stock'

    def __str__(self):
        return f"{self.product.sku} @ {self.warehouse.name}: {self.quantity}"

    @property
    def available(self):
        return max(0, self.quantity - self.reserve)