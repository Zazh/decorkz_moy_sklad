from django.urls import path, re_path
from catalog import store_views

app_name = 'store'

urlpatterns = [
    path('', store_views.home, name='home'),
    path('catalog/', store_views.catalog_root, name='catalog_root'),

    # Товар в подкатегории: /catalog/parent/child/product-slug/
    re_path(
        r'^catalog/(?P<parent_slug>[^/]+)/(?P<cat_slug>[^/]+)/(?P<product_slug>[^/]+)/$',
        store_views.product_detail,
        name='product_detail',
    ),

    # 2 сегмента: подкатегория ИЛИ товар в категории
    re_path(
        r'^catalog/(?P<slug1>[^/]+)/(?P<slug2>[^/]+)/$',
        store_views.catalog_or_product,
        name='catalog_or_product',
    ),

    # 1 сегмент: категория
    re_path(
        r'^catalog/(?P<slug>[^/]+)/$',
        store_views.catalog_by_category,
        name='catalog_by_category',
    ),
]
