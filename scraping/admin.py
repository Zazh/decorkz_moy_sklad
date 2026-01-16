# scraping/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import ScrapedProduct, ScrapedImage, ParserRun, ParserTask


class ScrapedImageInline(admin.TabularInline):
    model = ScrapedImage
    extra = 0
    readonly_fields = ['image_preview', 'source_url', 'is_downloaded']
    fields = ['image_preview', 'source_url', 'is_main', 'sort_order', 'is_downloaded']

    def image_preview(self, obj):
        if obj.local_file:
            return format_html('<img src="{}" style="max-height: 50px;"/>', obj.local_file.url)
        elif obj.source_url:
            return format_html('<img src="{}" style="max-height: 50px;"/>', obj.source_url)
        return "—"

    image_preview.short_description = "Превью"


class ProcessedFilter(admin.SimpleListFilter):
    title = 'Статус обработки'
    parameter_name = 'processed'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Обработанные'),
            ('no', 'Не обработанные'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(is_processed=True)
        if self.value() == 'no':
            return queryset.filter(is_processed=False)
        return queryset


@admin.register(ScrapedProduct)
class ScrapedProductAdmin(admin.ModelAdmin):
    list_display = [
        'sku',
        'brand_name',
        'title_short',
        'category_name',
        'images_count',
        'is_processed',
        'is_active',
        'parsed_at'
    ]
    list_filter = ['parser_task__target_brand', 'parser_task__target_category', ProcessedFilter, 'is_active']
    search_fields = ['sku', 'title', 'source_url']
    readonly_fields = [
        'parser_task',
        'source_url_link',
        'parsed_at',
        'created_at',
        'updated_at',
        'specifications_pretty',
        'missing_attributes'
    ]
    autocomplete_fields = ['processed_card']
    inlines = [ScrapedImageInline]

    fieldsets = (
        ('Источник', {
            'fields': ('parser_task', 'source_url_link', 'sku')
        }),
        ('Контент', {
            'fields': ('title', 'short_description', 'description')
        }),
        ('Характеристики', {
            'fields': ('specifications_pretty', 'missing_attributes', 'video_url')
        }),
        ('Обработка', {
            'fields': ('is_processed', 'processed_card')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
        ('Служебное', {
            'fields': ('parsed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = "Название"

    def brand_name(self, obj):
        return obj.parser_task.target_brand.name
    brand_name.short_description = "Бренд"

    def category_name(self, obj):
        return obj.parser_task.target_category.title
    category_name.short_description = "Категория"

    def source_url_link(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.source_url, obj.source_url[:60] + '...')
    source_url_link.short_description = "URL источника"

    def images_count(self, obj):
        count = obj.images.count()
        return count if count > 0 else "—"
    images_count.short_description = "Фото"

    def specifications_pretty(self, obj):
        if not obj.specifications:
            return "—"
        rows = ''.join(
            f'<tr><td><strong>{k}</strong></td><td>{v}</td></tr>'
            for k, v in obj.specifications.items()
        )
        return format_html('<table style="width:100%">{}</table>', rows)
    specifications_pretty.short_description = "Характеристики"

    def missing_attributes(self, obj):
        missing = obj.get_missing_required_attributes()
        if not missing:
            return format_html('<span style="color:green;">✓ Все обязательные атрибуты заполнены</span>')
        names = ', '.join(attr.name for attr in missing)
        return format_html('<span style="color:red;">Не хватает: {}</span>', names)
    missing_attributes.short_description = "Обязательные атрибуты"

    actions = ['mark_active', 'mark_inactive']

    @admin.action(description="Активировать выбранные")
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Деактивировать выбранные")
    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(ParserTask)
class ParserTaskAdmin(admin.ModelAdmin):
    list_display = [
        'parser_name',
        'target_brand',
        'target_category',
        'source_category_name',
        'status',
        'items_found',
        'items_parsed',
        'is_active',
        'last_run'
    ]
    list_filter = ['parser_name', 'status', 'is_active', 'target_brand', 'target_category']
    search_fields = ['source_url', 'source_category_name']
    autocomplete_fields = ['target_brand', 'target_category']
    readonly_fields = ['status', 'last_run', 'items_found', 'items_parsed', 'error_message', 'created_at', 'updated_at']

    fieldsets = (
        ('Источник', {
            'fields': ('parser_name', 'source_url', 'source_category_name')
        }),
        ('Связь со справочниками', {
            'fields': ('target_brand', 'target_category'),
            'description': 'Все товары из этого задания получат указанный бренд и категорию'
        }),
        ('Статус', {
            'fields': ('is_active', 'status', 'last_run', 'items_found', 'items_parsed', 'error_message')
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ParserRun)
class ParserRunAdmin(admin.ModelAdmin):
    list_display = [
        'parser_name',
        'status_badge',
        'total_items',
        'items_created',
        'items_updated',
        'errors_count',
        'duration_display',
        'started_at'
    ]
    list_filter = ['parser_name', 'status']
    readonly_fields = [
        'parser_name',
        'status',
        'total_items',
        'items_created',
        'items_updated',
        'errors_count',
        'error_message',
        'started_at',
        'finished_at'
    ]

    def status_badge(self, obj):
        colors = {
            'running': '#f0ad4e',
            'success': '#5cb85c',
            'error': '#d9534f',
        }
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Статус"

    def duration_display(self, obj):
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            return f"{minutes}м {seconds}с"
        return "—"
    duration_display.short_description = "Время"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False