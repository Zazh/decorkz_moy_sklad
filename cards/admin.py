# cards/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import ProductCard, ProductCardImage, ProductCardAttribute


class ProductCardImageInline(admin.TabularInline):
    model = ProductCardImage
    extra = 1
    fields = ['image', 'image_preview', 'alt', 'is_main', 'sort_order']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px;"/>', obj.image.url)
        return "—"

    image_preview.short_description = "Превью"


class ProductCardAttributeInline(admin.TabularInline):
    model = ProductCardAttribute
    extra = 1
    fields = ['attribute', 'value', 'sort_order']
    autocomplete_fields = ['attribute']


@admin.register(ProductCard)
class ProductCardAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'source',
        'images_count',
        'attributes_count',
        'has_product',
        'updated_at'
    ]
    list_filter = ['source']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductCardImageInline, ProductCardAttributeInline]

    fieldsets = (
        ('Контент', {
            'fields': ('title', 'short_description', 'description')
        }),
        ('Источник', {
            'fields': ('source', 'scraped_source_url')
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def images_count(self, obj):
        count = obj.images.count()
        return count if count > 0 else "—"

    images_count.short_description = "Фото"

    def attributes_count(self, obj):
        count = obj.attributes.count()
        return count if count > 0 else "—"

    attributes_count.short_description = "Атрибуты"

    def has_product(self, obj):
        return hasattr(obj, 'product') and obj.product is not None

    has_product.boolean = True
    has_product.short_description = "Привязан"