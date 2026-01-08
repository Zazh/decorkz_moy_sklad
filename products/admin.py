# products/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'article',
        'title',
        'brand',
        'category',
        'moysklad_link',
        'card_link',
        'price_display',
        'stock_display',
        'is_active'
    ]
    list_filter = ['is_active', 'brand', 'category']
    search_fields = ['article', 'slug', 'card__title', 'moysklad__name']
    autocomplete_fields = ['moysklad', 'card', 'brand', 'category']
    readonly_fields = ['created_at', 'updated_at', 'slug']

    fieldsets = (
        ('Идентификация', {
            'fields': ('article', 'slug')
        }),
        ('Связи', {
            'fields': ('moysklad', 'card')
        }),
        ('Классификация', {
            'fields': ('brand', 'category')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def title(self, obj):
        return obj.title

    title.short_description = "Название"

    def price_display(self, obj):
        return f"{obj.price:,.0f}" if obj.price else "—"

    price_display.short_description = "Цена"

    def stock_display(self, obj):
        return obj.stock if obj.stock > 0 else "—"

    stock_display.short_description = "Остаток"

    def moysklad_link(self, obj):
        if obj.moysklad:
            return format_html(
                '<a href="/admin/integration/moyskladproduct/{}/change/">✓</a>',
                obj.moysklad.pk
            )
        return "—"

    moysklad_link.short_description = "МС"

    def card_link(self, obj):
        if obj.card:
            return format_html(
                '<a href="/admin/cards/productcard/{}/change/">✓</a>',
                obj.card.pk
            )
        return "—"

    card_link.short_description = "Карточка"