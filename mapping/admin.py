# mapping/admin.py

from django.contrib import admin
from .models import BrandMapping, CategoryMapping, AttributeMapping


@admin.register(BrandMapping)
class BrandMappingAdmin(admin.ModelAdmin):
    list_display = ['source_name', 'source', 'brand', 'created_at']
    list_filter = ['source', 'brand']
    search_fields = ['source_name', 'brand__name']
    autocomplete_fields = ['brand']

    fieldsets = (
        ('Источник', {
            'fields': ('source', 'source_name')
        }),
        ('Маппинг', {
            'fields': ('brand',)
        }),
    )


@admin.register(CategoryMapping)
class CategoryMappingAdmin(admin.ModelAdmin):
    list_display = ['source_name_short', 'source', 'category', 'created_at']
    list_filter = ['source', 'category']
    search_fields = ['source_name', 'category__title']
    autocomplete_fields = ['category']

    fieldsets = (
        ('Источник', {
            'fields': ('source', 'source_name')
        }),
        ('Маппинг', {
            'fields': ('category',)
        }),
    )

    def source_name_short(self, obj):
        if len(obj.source_name) > 50:
            return obj.source_name[:50] + '...'
        return obj.source_name

    source_name_short.short_description = "Название в источнике"


@admin.register(AttributeMapping)
class AttributeMappingAdmin(admin.ModelAdmin):
    list_display = ['source_name', 'source', 'attribute', 'created_at']
    list_filter = ['source', 'attribute']
    search_fields = ['source_name', 'attribute__name']
    autocomplete_fields = ['attribute']

    fieldsets = (
        ('Источник', {
            'fields': ('source', 'source_name')
        }),
        ('Маппинг', {
            'fields': ('attribute',)
        }),
    )