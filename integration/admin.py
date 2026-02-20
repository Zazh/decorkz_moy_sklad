# integration/admin.py

from django.contrib import admin
from .models import MoySkladProduct, MoySkladCategory, MoySkladBrand, MoySkladOrder, SyncLog


@admin.register(MoySkladProduct)
class MoySkladProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'article', 'code', 'price', 'stock', 'site_category', 'site_subcategory', 'is_active', 'archived', 'last_sync']
    list_filter = ['is_active', 'archived', 'site_category', 'site_subcategory', 'created_at']
    search_fields = ['name', 'article', 'code', 'moysklad_id', 'barcode']
    readonly_fields = ['moysklad_id', 'raw_data', 'created_at', 'updated_at', 'last_sync']

    fieldsets = (
        ('Идентификаторы', {
            'fields': ('moysklad_id', 'code', 'article', 'barcode', 'external_code')
        }),
        ('Основное', {
            'fields': ('name', 'description', 'path_name')
        }),
        ('Категории сайта', {
            'fields': ('site_category', 'site_subcategory')
        }),
        ('Цены и остатки', {
            'fields': ('price', 'cost', 'stock', 'reserve')
        }),
        ('Статус', {
            'fields': ('is_active', 'archived')
        }),
        ('Сырые данные', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at', 'last_sync'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MoySkladCategory)
class MoySkladCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'path_name', 'parent', 'created_at']
    search_fields = ['name', 'path_name', 'moysklad_id']
    readonly_fields = ['moysklad_id', 'raw_data', 'created_at', 'updated_at']
    autocomplete_fields = ['parent']


@admin.register(MoySkladBrand)
class MoySkladBrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'products_count', 'created_at']
    search_fields = ['name']
    readonly_fields = ['products_count', 'created_at', 'updated_at']


@admin.register(MoySkladOrder)
class MoySkladOrderAdmin(admin.ModelAdmin):
    list_display = ['number', 'customer_name', 'status', 'total_amount', 'order_date']
    list_filter = ['status', 'order_date']
    search_fields = ['number', 'customer_name', 'customer_phone', 'moysklad_id']
    readonly_fields = ['moysklad_id', 'raw_data', 'created_at', 'updated_at', 'last_sync']

    fieldsets = (
        ('Заказ', {
            'fields': ('moysklad_id', 'number', 'status', 'total_amount', 'order_date')
        }),
        ('Клиент', {
            'fields': ('customer_name', 'customer_phone', 'customer_email')
        }),
        ('Доставка', {
            'fields': ('delivery_address', 'comment')
        }),
        ('Сырые данные', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at', 'last_sync'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ['sync_type', 'status', 'items_processed', 'items_created', 'items_updated', 'started_at',
                    'finished_at']
    list_filter = ['sync_type', 'status', 'started_at']
    readonly_fields = ['sync_type', 'status', 'items_processed', 'items_created', 'items_updated', 'error_message',
                       'started_at', 'finished_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False