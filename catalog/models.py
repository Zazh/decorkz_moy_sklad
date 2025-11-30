# catalog/models.py

from django.db import models
from django.utils.text import slugify


class Brand(models.Model):
    """Бренды товаров"""
    name = models.CharField("Название", max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    logo = models.ImageField("Логотип", upload_to='brands/', blank=True)
    description = models.TextField("Описание", blank=True)

    is_active = models.BooleanField("Активен", default=True)
    sort_order = models.IntegerField("Сортировка", default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Бренд"
        verbose_name_plural = "Бренды"
        ordering = ['sort_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AttributeDefinition(models.Model):
    """Справочник атрибутов для карточек"""

    VALUE_TYPES = [
        ('string', 'Строка'),
        ('integer', 'Целое число'),
        ('decimal', 'Десятичное'),
        ('boolean', 'Да/Нет'),
    ]

    FILTER_TYPES = [
        ('none', 'Не фильтруется'),
        ('exact', 'Точное совпадение'),
        ('range', 'Диапазон'),
        ('checkbox', 'Множественный выбор'),
    ]

    name = models.CharField("Название", max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    value_type = models.CharField("Тип значения", max_length=20, choices=VALUE_TYPES, default='string')
    filter_type = models.CharField("Тип фильтра", max_length=20, choices=FILTER_TYPES, default='checkbox')
    unit = models.CharField("Единица измерения", max_length=20, blank=True)

    is_active = models.BooleanField("Активен", default=True)
    sort_order = models.IntegerField("Сортировка", default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Атрибут"
        verbose_name_plural = "Атрибуты"
        ordering = ['sort_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        unit_str = f" ({self.unit})" if self.unit else ""
        return f"{self.name}{unit_str}"


class Category(models.Model):
    """Категории каталога"""
    title = models.CharField("Название", max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name="Родительская"
    )

    image = models.ImageField("Изображение", upload_to='categories/', blank=True)
    description = models.TextField("Описание", blank=True)

    attributes = models.ManyToManyField(
        AttributeDefinition,
        through='CategoryAttribute',
        related_name='categories',
        blank=True,
        verbose_name="Атрибуты"
    )

    is_active = models.BooleanField("Активна", default=True)
    sort_order = models.IntegerField("Сортировка", default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['sort_order', 'title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.parent:
            return f"{self.parent.title} → {self.title}"
        return self.title

    def get_required_attributes(self):
        """Обязательные атрибуты для этой категории"""
        return AttributeDefinition.objects.filter(
            categoryattribute__category=self,
            categoryattribute__is_required=True
        ).order_by('categoryattribute__sort_order')

    def get_filterable_attributes(self):
        """Атрибуты для фильтрации"""
        return AttributeDefinition.objects.filter(
            categoryattribute__category=self,
            categoryattribute__is_filterable=True
        ).exclude(filter_type='none').order_by('categoryattribute__sort_order')


class CategoryAttribute(models.Model):
    """Связь категории с атрибутом"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    attribute = models.ForeignKey(AttributeDefinition, on_delete=models.CASCADE)

    is_required = models.BooleanField("Обязательный", default=False)
    is_filterable = models.BooleanField("Фильтруемый", default=True)
    sort_order = models.IntegerField("Сортировка", default=0)

    class Meta:
        verbose_name = "Атрибут категории"
        verbose_name_plural = "Атрибуты категорий"
        unique_together = [['category', 'attribute']]
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.category.title} — {self.attribute.name}"