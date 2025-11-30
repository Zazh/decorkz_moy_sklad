from django.db import models


class Product(models.Model):
    """Модель для хранения товаров из МойСклад"""
    
    moysklad_id = models.CharField(max_length=255, unique=True, verbose_name='ID в МойСклад')
    name = models.CharField(max_length=500, verbose_name='Название')
    code = models.CharField(max_length=255, blank=True, null=True, verbose_name='Код')
    article = models.CharField(max_length=255, blank=True, null=True, verbose_name='Артикул')

    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Цена')
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Себестоимость')
    
    stock = models.IntegerField(default=0, verbose_name='Остаток')
    reserve = models.IntegerField(default=0, verbose_name='Резерв')
    
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    archived = models.BooleanField(default=False, verbose_name='В архиве')
    
    external_code = models.CharField(max_length=255, blank=True, null=True, verbose_name='Внешний код')
    
    barcode = models.CharField(max_length=255, blank=True, null=True, verbose_name='Штрихкод')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    
    last_sync = models.DateTimeField(auto_now=True, verbose_name='Последняя синхронизация')
    
    raw_data = models.JSONField(blank=True, null=True, verbose_name='Полные данные из API')
    
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['moysklad_id']),
            models.Index(fields=['article']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.article or self.code or self.moysklad_id})"


class ProductCategory(models.Model):
    """Модель для категорий товаров"""
    
    moysklad_id = models.CharField(max_length=255, unique=True, verbose_name='ID в МойСклад')
    name = models.CharField(max_length=255, verbose_name='Название')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                               related_name='children', verbose_name='Родительская категория')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Order(models.Model):
    """Модель для заказов"""
    
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('processing', 'В обработке'),
        ('shipped', 'Отгружен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]
    
    moysklad_id = models.CharField(max_length=255, unique=True, verbose_name='ID в МойСклад')
    number = models.CharField(max_length=255, verbose_name='Номер заказа')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='Статус')
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Сумма')
    
    customer_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Имя клиента')
    customer_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name='Телефон клиента')
    customer_email = models.EmailField(blank=True, null=True, verbose_name='Email клиента')
    
    delivery_address = models.TextField(blank=True, null=True, verbose_name='Адрес доставки')
    
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий')
    
    order_date = models.DateTimeField(verbose_name='Дата заказа')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    
    last_sync = models.DateTimeField(auto_now=True, verbose_name='Последняя синхронизация')
    
    raw_data = models.JSONField(blank=True, null=True, verbose_name='Полные данные из API')
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-order_date']
        indexes = [
            models.Index(fields=['moysklad_id']),
            models.Index(fields=['number']),
        ]
    
    def __str__(self):
        return f"Заказ #{self.number} от {self.order_date.strftime('%d.%m.%Y')}"


class SyncLog(models.Model):
    """Лог синхронизации"""
    
    SYNC_TYPES = [
        ('products', 'Товары'),
        ('orders', 'Заказы'),
        ('stock', 'Остатки'),
        ('categories', 'Категории'),
    ]
    
    STATUS_CHOICES = [
        ('started', 'Начата'),
        ('success', 'Успешно'),
        ('error', 'Ошибка'),
    ]
    
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES, verbose_name='Тип синхронизации')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='started', verbose_name='Статус')
    
    items_processed = models.IntegerField(default=0, verbose_name='Обработано элементов')
    items_created = models.IntegerField(default=0, verbose_name='Создано элементов')
    items_updated = models.IntegerField(default=0, verbose_name='Обновлено элементов')
    
    error_message = models.TextField(blank=True, null=True, verbose_name='Сообщение об ошибке')
    
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Начало')
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name='Окончание')
    
    class Meta:
        verbose_name = 'Лог синхронизации'
        verbose_name_plural = 'Логи синхронизации'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.get_sync_type_display()} - {self.get_status_display()} ({self.started_at.strftime('%d.%m.%Y %H:%M')})"
