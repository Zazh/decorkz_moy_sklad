# scraping/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import ScrapedProduct, ScrapedImage, ParserRun


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


class MatchedFilter(admin.SimpleListFilter):
    title = 'Связь с PIM'
    parameter_name = 'matched'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Связанные'),
            ('no', 'Без связи'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(product__isnull=False)
        if self.value() == 'no':
            return queryset.filter(product__isnull=True)
        return queryset


@admin.register(ScrapedProduct)
class ScrapedProductAdmin(admin.ModelAdmin):
    list_display = [
        'sku',
        'brand',
        'title_short',
        'product_link',
        'images_count',
        'is_matched',
        'is_active',
        'parsed_at'
    ]
    list_filter = ['brand', 'parser_name', MatchedFilter, 'is_active']
    search_fields = ['sku', 'title', 'source_url', 'product__sku']
    readonly_fields = [
        'parser_name',
        'source_url_link',
        'parsed_at',
        'created_at',
        'updated_at',
        'specifications_pretty'
    ]
    autocomplete_fields = ['product']
    inlines = [ScrapedImageInline]

    fieldsets = (
        ('Источник', {
            'fields': ('parser_name', 'source_url_link', 'sku', 'brand')
        }),
        ('Контент', {
            'fields': ('title', 'short_description', 'description')
        }),
        ('Характеристики', {
            'fields': ('category', 'specifications_pretty', 'video_url')
        }),
        ('Связь с PIM', {
            'fields': ('product', 'is_matched')
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

    def source_url_link(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.source_url, obj.source_url[:60] + '...')

    source_url_link.short_description = "URL источника"

    def product_link(self, obj):
        if obj.product:
            return format_html(
                '<a href="/admin/products/product/{}/change/">{}</a>',
                obj.product.pk,
                obj.product.sku
            )
        return "—"

    product_link.short_description = "Товар PIM"

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

    actions = ['mark_active', 'mark_inactive']

    @admin.action(description="Активировать выбранные")
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Деактивировать выбранные")
    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)


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