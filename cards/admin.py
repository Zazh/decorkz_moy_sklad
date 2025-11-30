# cards/admin.py

from django.contrib import admin
from .models import ProductCard, ProductCardImage, ProductCardAttribute


class ProductCardImageInline(admin.TabularInline):
    model = ProductCardImage
    extra = 1


class ProductCardAttributeInline(admin.TabularInline):
    model = ProductCardAttribute
    extra = 1
    autocomplete_fields = ['attribute']


@admin.register(ProductCard)
class ProductCardAdmin(admin.ModelAdmin):
    list_display = ['sku', 'title', 'product', 'is_default', 'is_active', 'source']
    list_filter = ['is_active', 'is_default', 'source']
    search_fields = ['sku', 'title', 'product__name']
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['product']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductCardImageInline, ProductCardAttributeInline]

    fieldsets = (
        ('Основное', {
            'fields': ('product', 'sku', 'title', 'slug')
        }),
        ('Контент', {
            'fields': ('short_description', 'description', 'youtube_url')
        }),
        ('Настройки', {
            'fields': ('is_default', 'is_active', 'sort_order', 'source')
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )