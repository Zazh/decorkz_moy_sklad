# mapping/admin.py

from django.contrib import admin
from .models import BrandMapping, CategoryMapping, AttributeMapping


class UnmappedFilter(admin.SimpleListFilter):
    """Фильтр: связанные / не связанные"""
    title = 'Статус связи'
    parameter_name = 'mapped'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Связанные'),
            ('no', 'Не связанные'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(brand__isnull=False)
        if self.value() == 'no':
            return queryset.filter(brand__isnull=True)
        return queryset


@admin.register(BrandMapping)
class BrandMappingAdmin(admin.ModelAdmin):
    list_display = ['source_name', 'source', 'brand', 'is_mapped']
    list_filter = [UnmappedFilter, 'source', 'brand']
    search_fields = ['source_name', 'brand__name']
    autocomplete_fields = ['brand']
    list_editable = ['brand']
    list_per_page = 50

    fieldsets = (
        ('Источник', {
            'fields': ('source', 'source_name')
        }),
        ('Связь', {
            'fields': ('brand',)
        }),
    )

    actions = ['create_brand_from_mapping']

    def is_mapped(self, obj):
        return obj.brand is not None

    is_mapped.boolean = True
    is_mapped.short_description = 'Связан'

    @admin.action(description='Создать бренд из выбранных')
    def create_brand_from_mapping(self, request, queryset):
        """Создаёт Brand из source_name и связывает"""
        from references.models import Brand
        from django.utils.text import slugify

        created = 0
        for mapping in queryset.filter(brand__isnull=True):
            name = mapping.source_name.strip()

            # Проверяем существует ли
            brand = Brand.objects.filter(name__iexact=name).first()
            if brand:
                mapping.brand = brand
                mapping.save()
                continue

            # Создаём новый
            slug = slugify(name, allow_unicode=True) or 'brand'
            base_slug = slug[:45]
            counter = 1
            while Brand.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            brand = Brand.objects.create(name=name, slug=slug)
            mapping.brand = brand
            mapping.save()
            created += 1

        self.message_user(request, f'Создано брендов: {created}')


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