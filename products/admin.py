# products/admin.py

from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'brand', 'is_active', 'archived', 'is_promo', 'last_sync']
    list_filter = ['is_active', 'archived', 'is_promo', 'is_kaspi', 'is_satu', 'brand']
    search_fields = ['sku', 'article', 'name', 'barcode', 'moysklad_id']
    autocomplete_fields = ['brand', 'categories']
    readonly_fields = ['moysklad_id', 'raw_data', 'created_at', 'updated_at', 'last_sync']

    fieldsets = (
        ('Идентификаторы', {
            'fields': ('moysklad_id', 'sku', 'article', 'barcode')
        }),
        ('Основное', {
            'fields': ('name', 'brand', 'categories')
        }),
        ('Характеристики', {
            'fields': ('weight', 'volume')
        }),
        ('Флаги', {
            'fields': ('is_active', 'archived', 'is_promo', 'is_kaspi', 'is_satu')
        }),
        ('МойСклад', {
            'fields': ('moysklad_path', 'raw_data'),
            'classes': ('collapse',)
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at', 'last_sync'),
            'classes': ('collapse',)
        }),
    )