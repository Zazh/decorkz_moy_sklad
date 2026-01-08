# references/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Brand, AttributeDefinition, Category, CategoryAttribute, UnitGroup, Unit


class UnitInline(admin.TabularInline):
    model = Unit
    extra = 1
    fields = ['symbol', 'name', 'aliases', 'multiplier', 'is_base', 'sort_order']
    ordering = ['-is_base', 'sort_order']


@admin.register(UnitGroup)
class UnitGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_unit_symbol', 'units_list', 'created_at']
    search_fields = ['name', 'base_unit_symbol']
    inlines = [UnitInline]

    def units_list(self, obj):
        units = obj.units.all().order_by('-is_base', 'sort_order')[:5]
        if not units:
            return "—"
        symbols = [f"<strong>{u.symbol}</strong>" if u.is_base else u.symbol for u in units]
        return format_html(", ".join(symbols))

    units_list.short_description = "Единицы"


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'group', 'multiplier', 'is_base', 'aliases_display']
    list_filter = ['group', 'is_base']
    search_fields = ['symbol', 'name', 'aliases']
    list_editable = ['multiplier', 'is_base']
    autocomplete_fields = ['group']

    fieldsets = (
        ('Основное', {
            'fields': ('group', 'name', 'symbol')
        }),
        ('Конвертация', {
            'fields': ('multiplier', 'is_base'),
            'description': 'Multiplier — коэффициент для перевода в базовую единицу'
        }),
        ('Синонимы для парсинга', {
            'fields': ('aliases',),
            'description': 'JSON список вариантов написания: ["kg", "КГ", "килограмм"]'
        }),
        ('Сортировка', {
            'fields': ('sort_order',),
            'classes': ('collapse',)
        }),
    )

    def aliases_display(self, obj):
        if not obj.aliases:
            return "—"
        return ", ".join(obj.aliases[:5])

    aliases_display.short_description = "Синонимы"


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'mappings_count', 'products_count', 'is_active', 'sort_order']
    list_editable = ['is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        ('Основное', {
            'fields': ('name', 'slug', 'logo', 'description')
        }),
        ('Статус', {
            'fields': ('is_active', 'sort_order')
        }),
    )

    def mappings_count(self, obj):
        count = obj.mappings.count()
        return count if count > 0 else '—'

    mappings_count.short_description = 'Синонимов'

    def products_count(self, obj):
        return obj.products.count()

    products_count.short_description = 'Товаров'

@admin.register(AttributeDefinition)
class AttributeDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'value_type', 'filter_type', 'unit_display', 'is_active', 'sort_order']
    list_editable = ['is_active', 'sort_order']
    list_filter = ['value_type', 'filter_type', 'is_active', 'unit_group']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['unit_group', 'default_unit']

    fieldsets = (
        ('Основное', {
            'fields': ('name', 'slug')
        }),
        ('Тип', {
            'fields': ('value_type', 'filter_type')
        }),
        ('Единицы измерения', {
            'fields': ('unit_group', 'default_unit', 'unit'),
            'description': 'unit_group и default_unit — для новой логики. unit — legacy поле.'
        }),
        ('Статус', {
            'fields': ('is_active', 'sort_order')
        }),
    )

    def unit_display(self, obj):
        if obj.default_unit:
            return obj.default_unit.symbol
        elif obj.unit:
            return obj.unit
        return "—"

    unit_display.short_description = "Единица"


class CategoryAttributeInline(admin.TabularInline):
    model = CategoryAttribute
    extra = 1
    autocomplete_fields = ['attribute']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'parent', 'is_active', 'sort_order']
    list_editable = ['is_active', 'sort_order']
    list_filter = ['is_active', 'parent']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['parent']
    inlines = [CategoryAttributeInline]