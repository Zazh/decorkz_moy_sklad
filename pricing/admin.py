# pricing/admin.py

from django.contrib import admin
from .models import PriceType, Price


@admin.register(PriceType)
class PriceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'moysklad_id', 'is_default', 'is_public', 'is_wholesale', 'sort_order']
    list_editable = ['is_default', 'is_public', 'is_wholesale', 'sort_order']
    list_filter = ['is_default', 'is_public', 'is_wholesale']
    search_fields = ['name', 'moysklad_id']


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ['product', 'price_type', 'price', 'old_price', 'discount_percent', 'is_active']
    list_filter = ['price_type', 'is_active']
    search_fields = ['product__sku', 'product__name']
    autocomplete_fields = ['product', 'price_type']

    def discount_percent(self, obj):
        if obj.discount_percent:
            return f"-{obj.discount_percent}%"
        return "—"

    discount_percent.short_description = "Скидка"