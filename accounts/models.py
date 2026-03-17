from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    """Кастомная модель пользователя с дополнительными полями."""

    patronymic = models.CharField('Отчество', max_length=150, blank=True)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    country = models.CharField('Страна', max_length=100, blank=True, default='Казахстан')
    city = models.CharField('Город', max_length=100, blank=True)
    address = models.CharField('Адрес', max_length=500, blank=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        db_table = 'accounts_user'

    def __str__(self):
        return self.get_full_name() or self.email or self.username

    def get_full_name(self):
        parts = [self.last_name, self.first_name, self.patronymic]
        return ' '.join(p for p in parts if p)


class Favorite(models.Model):
    """Избранные товары пользователя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Товар',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        db_table = 'accounts_favorite'
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.product}'
