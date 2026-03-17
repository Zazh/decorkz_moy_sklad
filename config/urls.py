# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Storefront (публичный каталог)
    path('', include('catalog.store_urls')),

    # Auth (Google SSO + allauth)
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('accounts.urls')),

    # Locations (где купить, контакты)
    path('', include('locations.urls')),

    # Blog
    path('blog/', include('blog.urls')),

    # PIM (админка данных)
    path('admin/', admin.site.urls),
    path('pim/', include('catalog.urls')),

    # API
    # path('api/', include('integration.urls')),  # убрали пока
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)