from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'last_name', 'first_name', 'phone', 'city', 'is_active')
    list_filter = ('is_active', 'is_staff', 'city')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительно', {
            'fields': ('patronymic', 'phone', 'country', 'city', 'address'),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительно', {
            'fields': ('email', 'first_name', 'last_name', 'patronymic', 'phone'),
        }),
    )
