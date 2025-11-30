from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from .models import Product, ProductCategory, Order, SyncLog
from .serializers import ProductSerializer, ProductCategorySerializer, OrderSerializer, SyncLogSerializer
from .services.moysklad_api import MoySkladAPI
import logging

logger = logging.getLogger(__name__)


class ProductViewSet(viewsets.ModelViewSet):
    """API для работы с товарами"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filterset_fields = ['is_active', 'archived']
    search_fields = ['name', 'article', 'code']
    ordering_fields = ['created_at', 'updated_at', 'price', 'stock']


class ProductCategoryViewSet(viewsets.ModelViewSet):
    """API для работы с категориями"""
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer


class OrderViewSet(viewsets.ModelViewSet):
    """API для работы с заказами"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filterset_fields = ['status']
    search_fields = ['number', 'customer_name', 'customer_phone']
    ordering_fields = ['order_date', 'created_at']


class SyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API для просмотра логов синхронизации"""
    queryset = SyncLog.objects.all()
    serializer_class = SyncLogSerializer
    filterset_fields = ['sync_type', 'status']
    ordering_fields = ['started_at']


@api_view(['GET'])
def health_check(request):
    """Проверка работоспособности сервиса"""
    return Response({
        'status': 'ok',
        'service': 'МойСклад Integration',
        'timestamp': timezone.now()
    })


@api_view(['POST'])
def sync_products_manual(request):
    """Ручной запуск синхронизации товаров"""
    try:
        sync_log = SyncLog.objects.create(
            sync_type='products',
            status='started'
        )
        
        api = MoySkladAPI()
        products = api.sync_all_products()
        
        items_created = 0
        items_updated = 0
        
        for product_data in products:
            moysklad_id = product_data.get('id')
            
            price = 0
            sale_prices = product_data.get('salePrices', [])
            if sale_prices:
                price = sale_prices[0].get('value', 0) / 100
            
            product_info = {
                'name': product_data.get('name', ''),
                'code': product_data.get('code'),
                'article': product_data.get('article'),
                'description': product_data.get('description'),
                'price': price,
                'archived': product_data.get('archived', False),
                'external_code': product_data.get('externalCode'),
                'raw_data': product_data,
            }
            
            product, created = Product.objects.update_or_create(
                moysklad_id=moysklad_id,
                defaults=product_info
            )
            
            if created:
                items_created += 1
            else:
                items_updated += 1
        
        sync_log.status = 'success'
        sync_log.items_processed = len(products)
        sync_log.items_created = items_created
        sync_log.items_updated = items_updated
        sync_log.finished_at = timezone.now()
        sync_log.save()
        
        return Response({
            'success': True,
            'created': items_created,
            'updated': items_updated,
            'total': len(products)
        })
        
    except Exception as e:
        logger.error(f"Ошибка синхронизации: {e}")
        
        if 'sync_log' in locals():
            sync_log.status = 'error'
            sync_log.error_message = str(e)
            sync_log.finished_at = timezone.now()
            sync_log.save()
        
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def sync_stock_manual(request):
    """Ручной запуск синхронизации остатков"""
    try:
        sync_log = SyncLog.objects.create(
            sync_type='stock',
            status='started'
        )
        
        api = MoySkladAPI()
        stock_data = api.get_stock(limit=1000)
        
        items_updated = 0
        
        for item in stock_data.get('rows', []):
            meta = item.get('meta', {})
            href = meta.get('href', '')
            if '/product/' in href:
                moysklad_id = href.split('/product/')[-1]
            else:
                continue
            
            try:
                product = Product.objects.get(moysklad_id=moysklad_id)
                product.stock = item.get('stock', 0)
                product.reserve = item.get('reserve', 0)
                product.save(update_fields=['stock', 'reserve', 'last_sync'])
                items_updated += 1
            except Product.DoesNotExist:
                logger.warning(f"Товар с ID {moysklad_id} не найден")
        
        sync_log.status = 'success'
        sync_log.items_processed = len(stock_data.get('rows', []))
        sync_log.items_updated = items_updated
        sync_log.finished_at = timezone.now()
        sync_log.save()
        
        return Response({
            'success': True,
            'updated': items_updated
        })
        
    except Exception as e:
        logger.error(f"Ошибка синхронизации остатков: {e}")
        
        if 'sync_log' in locals():
            sync_log.status = 'error'
            sync_log.error_message = str(e)
            sync_log.finished_at = timezone.now()
            sync_log.save()
        
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
