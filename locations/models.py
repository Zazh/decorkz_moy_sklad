from django.db import models


class Location(models.Model):
    CITY_CHOICES = [
        ('almaty', 'Алматы'),
        ('astana', 'Астана'),
    ]

    city = models.CharField('Город', max_length=50, choices=CITY_CHOICES)
    name = models.CharField('Название', max_length=200)
    address = models.CharField('Адрес', max_length=500)
    phones = models.TextField('Телефоны', blank=True, help_text='Разделять переносом строки')
    schedule = models.TextField('График работы', blank=True, help_text='Разделять переносом строки')
    map_url = models.URLField('Ссылка на карту', blank=True)
    is_official = models.BooleanField('Фирменный салон', default=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активна', default=True)

    class Meta:
        ordering = ['city', 'sort_order']
        verbose_name = 'Точка продаж'
        verbose_name_plural = 'Точки продаж'

    def __str__(self):
        return f'{self.get_city_display()} — {self.name}'


class CompanyInfo(models.Model):
    company_name = models.CharField('Название компании', max_length=200)
    email = models.EmailField('Email', blank=True)
    phone = models.CharField('Телефон', max_length=100, blank=True)
    address = models.CharField('Адрес', max_length=500, blank=True)
    map_url = models.URLField('Ссылка на карту', blank=True)

    class Meta:
        verbose_name = 'Информация о компании'
        verbose_name_plural = 'Информация о компании'

    def __str__(self):
        return self.company_name


class SocialLink(models.Model):
    company = models.ForeignKey(CompanyInfo, related_name='socials', on_delete=models.CASCADE)
    name = models.CharField('Название', max_length=100)
    url = models.URLField('Ссылка')
    svg_icon = models.TextField('SVG иконка', help_text='SVG-код иконки (без тега &lt;svg&gt; обёртки — только внутренний path/g)')
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['sort_order']
        verbose_name = 'Социальная сеть'
        verbose_name_plural = 'Социальные сети'

    def __str__(self):
        return self.name
