from django.contrib import admin
from .models import Product, ProductCategory, Order, SyncLog


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'article', 'price', 'stock', 'is_active', 'last_sync']
    list_filter = ['is_active', 'archived', 'created_at']
    search_fields = ['name', 'article', 'code', 'moysklad_id']
    readonly_fields = ['moysklad_id', 'created_at', 'updated_at', 'last_sync']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'code', 'article', 'description')
        }),
        ('Цены и остатки', {
            'fields': ('price', 'cost', 'stock', 'reserve')
        }),
        ('Статус', {
            'fields': ('is_active', 'archived')
        }),
        ('Дополнительно', {
            'fields': ('external_code', 'barcode', 'moysklad_id')
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at', 'last_sync'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'created_at']
    search_fields = ['name', 'moysklad_id']
    readonly_fields = ['moysklad_id', 'created_at', 'updated_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['number', 'customer_name', 'status', 'total_amount', 'order_date']
    list_filter = ['status', 'order_date']
    search_fields = ['number', 'customer_name', 'customer_phone', 'moysklad_id']
    readonly_fields = ['moysklad_id', 'created_at', 'updated_at', 'last_sync']
    
    fieldsets = (
        ('Информация о заказе', {
            'fields': ('number', 'status', 'total_amount', 'order_date')
        }),
        ('Клиент', {
            'fields': ('customer_name', 'customer_phone', 'customer_email')
        }),
        ('Доставка', {
            'fields': ('delivery_address', 'comment')
        }),
        ('Служебная информация', {
            'fields': ('moysklad_id', 'created_at', 'updated_at', 'last_sync'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ['sync_type', 'status', 'items_processed', 'items_created', 
                    'items_updated', 'started_at', 'finished_at']
    list_filter = ['sync_type', 'status', 'started_at']
    readonly_fields = ['sync_type', 'status', 'items_processed', 'items_created', 
                       'items_updated', 'error_message', 'started_at', 'finished_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
