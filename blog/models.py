from django.db import models
from django.utils.text import slugify


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    description = models.CharField('Описание', max_length=500, blank=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    image = models.ImageField('Изображение', upload_to='blog_images', blank=True)
    publish_date = models.DateTimeField('Дата публикации')
    is_active = models.BooleanField('Активна', default=True)

    class Meta:
        ordering = ['-publish_date']
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ContentBlock(models.Model):
    CONTENT_CHOICES = [
        ('p', 'Параграф'),
        ('h2', 'Заголовок 2'),
        ('h3', 'Заголовок 3'),
        ('ul', 'Маркированный список'),
        ('ol', 'Нумерованный список'),
    ]
    post = models.ForeignKey(Post, related_name='blocks', on_delete=models.CASCADE)
    content_type = models.CharField('Тип', max_length=2, choices=CONTENT_CHOICES)
    text = models.TextField('Текст')
    bold = models.BooleanField('Жирный', default=False)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Блок контента'
        verbose_name_plural = 'Блоки контента'

    def __str__(self):
        return f'{self.get_content_type_display()}: {self.text[:50]}'
