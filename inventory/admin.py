# inventory/admin.py

from django.contrib import admin
from .models import Warehouse, Stock


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'moysklad_id', 'is_active', 'is_default', 'sort_order']
    list_editable = ['is_active', 'is_default', 'sort_order']
    list_filter = ['is_active', 'is_default']
    search_fields = ['name', 'moysklad_id']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'warehouse', 'quantity', 'reserve', 'available', 'updated_at']
    list_filter = ['warehouse']
    search_fields = ['product__sku', 'product__name']
    autocomplete_fields = ['product', 'warehouse']

    def available(self, obj):
        return obj.available

    available.short_description = "Доступно"