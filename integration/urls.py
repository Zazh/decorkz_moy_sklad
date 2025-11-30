from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'categories', views.ProductCategoryViewSet, basename='category')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'sync-logs', views.SyncLogViewSet, basename='synclog')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', views.health_check, name='health_check'),
    path('sync/products/', views.sync_products_manual, name='sync_products'),
    path('sync/stock/', views.sync_stock_manual, name='sync_stock'),
]
