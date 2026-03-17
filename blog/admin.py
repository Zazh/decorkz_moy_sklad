from django.contrib import admin
from .models import Post, ContentBlock


class ContentBlockInline(admin.StackedInline):
    model = ContentBlock
    extra = 1


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'publish_date', 'is_active')
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ContentBlockInline]
