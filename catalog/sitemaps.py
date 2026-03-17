from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from products.models import Product
from references.models import Category
from blog.models import Post


class StaticSitemap(Sitemap):
    priority = 1.0
    changefreq = 'weekly'

    def items(self):
        return ['store:home', 'store:catalog_root', 'locations:contacts', 'locations:points_of_sales', 'blog:post_list']

    def location(self, item):
        return reverse(item)


class CategorySitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return Category.objects.filter(is_active=True, children__isnull=True).distinct()

    def location(self, obj):
        return reverse('store:catalog_by_category', kwargs={'slug': obj.slug})


class ProductSitemap(Sitemap):
    priority = 0.7
    changefreq = 'weekly'
    limit = 1000

    def items(self):
        return Product.objects.filter(is_active=True).select_related('category')

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else None


class BlogSitemap(Sitemap):
    priority = 0.6
    changefreq = 'monthly'

    def items(self):
        return Post.objects.filter(is_active=True)

    def location(self, obj):
        return reverse('blog:post_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.publish_date
