# integration/models.py

from django.db import models


class MoySkladProduct(models.Model):
    """Сырые данные товара из МойСклад"""

    moysklad_id = models.CharField("ID в МойСклад", max_length=255, unique=True)
    name = models.CharField("Название", max_length=500)
    code = models.CharField("Код", max_length=255, blank=True, null=True)
    article = models.CharField("Артикул", max_length=255, blank=True, null=True)
    description = models.TextField("Описание", blank=True, null=True)

    # Цены (сырые, в копейках или как пришло)
    price = models.DecimalField("Цена", max_digits=12, decimal_places=2, default=0)
    cost = models.DecimalField("Себестоимость", max_digits=12, decimal_places=2, default=0)

    # Остатки (сырые)
    stock = models.IntegerField("Остаток", default=0)
    reserve = models.IntegerField("Резерв", default=0)

    # Статусы
    is_active = models.BooleanField("Активен", default=True)
    archived = models.BooleanField("В архиве", default=False)

    # Доп. поля
    external_code = models.CharField("Внешний код", max_length=255, blank=True, null=True)
    barcode = models.CharField("Штрихкод", max_length=255, blank=True, null=True)
    path_name = models.CharField("Путь в МойСклад", max_length=500, blank=True)

    # Категории для сайта (из доп. атрибутов МойСклад)
    site_category = models.CharField("Категория сайт", max_length=255, blank=True, default='')
    site_subcategory = models.CharField("Подкатегория сайт", max_length=255, blank=True, default='')

    # Сырые данные
    raw_data = models.JSONField("Полные данные из API", blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)
    last_sync = models.DateTimeField("Последняя синхронизация", auto_now=True)

    class Meta:
        verbose_name = "Товар МойСклад"
        verbose_name_plural = "Товары МойСклад"
        ordering = ['-updated_at']
        db_table = 'integration_moysklad_product'
        indexes = [
            models.Index(fields=['moysklad_id']),
            models.Index(fields=['article']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f"{self.name} ({self.article or self.code or self.moysklad_id})"


class MoySkladCategory(models.Model):
    """Категории (папки товаров) из МойСклад"""

    moysklad_id = models.CharField("ID в МойСклад", max_length=255, unique=True)
    name = models.CharField("Название", max_length=255)
    path_name = models.CharField("Полный путь", max_length=500, blank=True)

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='children',
        verbose_name="Родительская категория"
    )

    raw_data = models.JSONField("Полные данные из API", blank=True, null=True)

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Категория МойСклад"
        verbose_name_plural = "Категории МойСклад"
        ordering = ['name']
        db_table = 'integration_moysklad_category'

    def __str__(self):
        return self.path_name or self.name


class MoySkladBrand(models.Model):
    """Бренды из атрибутов МойСклад"""

    name = models.CharField("Название", max_length=255, unique=True)

    # Сколько товаров с этим брендом
    products_count = models.IntegerField("Кол-во товаров", default=0)

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Бренд МойСклад"
        verbose_name_plural = "Бренды МойСклад"
        ordering = ['name']
        db_table = 'integration_moysklad_brand'

    def __str__(self):
        return self.name


class MoySkladOrder(models.Model):
    """Заказы из МойСклад"""

    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('processing', 'В обработке'),
        ('shipped', 'Отгружен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]

    moysklad_id = models.CharField("ID в МойСклад", max_length=255, unique=True)
    number = models.CharField("Номер заказа", max_length=255)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='new')

    total_amount = models.DecimalField("Сумма", max_digits=12, decimal_places=2, default=0)

    customer_name = models.CharField("Имя клиента", max_length=255, blank=True, null=True)
    customer_phone = models.CharField("Телефон клиента", max_length=50, blank=True, null=True)
    customer_email = models.EmailField("Email клиента", blank=True, null=True)

    delivery_address = models.TextField("Адрес доставки", blank=True, null=True)
    comment = models.TextField("Комментарий", blank=True, null=True)

    order_date = models.DateTimeField("Дата заказа")

    raw_data = models.JSONField("Полные данные из API", blank=True, null=True)

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)
    last_sync = models.DateTimeField("Последняя синхронизация", auto_now=True)

    class Meta:
        verbose_name = "Заказ МойСклад"
        verbose_name_plural = "Заказы МойСклад"
        ordering = ['-order_date']
        db_table = 'integration_moysklad_order'
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
        ('brands', 'Бренды'),
    ]

    STATUS_CHOICES = [
        ('started', 'Начата'),
        ('success', 'Успешно'),
        ('error', 'Ошибка'),
    ]

    sync_type = models.CharField("Тип синхронизации", max_length=20, choices=SYNC_TYPES)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='started')

    items_processed = models.IntegerField("Обработано элементов", default=0)
    items_created = models.IntegerField("Создано элементов", default=0)
    items_updated = models.IntegerField("Обновлено элементов", default=0)

    error_message = models.TextField("Сообщение об ошибке", blank=True, null=True)

    started_at = models.DateTimeField("Начало", auto_now_add=True)
    finished_at = models.DateTimeField("Окончание", null=True, blank=True)

    class Meta:
        verbose_name = "Лог синхронизации"
        verbose_name_plural = "Логи синхронизации"
        ordering = ['-started_at']
        db_table = 'integration_sync_log'

    def __str__(self):
        return f"{self.get_sync_type_display()} - {self.get_status_display()} ({self.started_at.strftime('%d.%m.%Y %H:%M')})"