from django.contrib import admin
from .models import Location, CompanyInfo, SocialLink


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'address', 'is_official', 'is_active', 'sort_order')
    list_filter = ('city', 'is_official', 'is_active')
    list_editable = ('sort_order', 'is_active', 'is_official')


class SocialLinkInline(admin.TabularInline):
    model = SocialLink
    extra = 1


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'email', 'phone')
    inlines = [SocialLinkInline]
