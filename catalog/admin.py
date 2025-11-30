# catalog/admin.py

from django.contrib import admin
from .models import Brand, AttributeDefinition, Category, CategoryAttribute


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'sort_order']
    list_editable = ['is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(AttributeDefinition)
class AttributeDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'value_type', 'filter_type', 'unit', 'is_active', 'sort_order']
    list_editable = ['is_active', 'sort_order']
    list_filter = ['value_type', 'filter_type', 'is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


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