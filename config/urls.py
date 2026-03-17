# config/urls.py

from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.template.response import TemplateResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from catalog.sitemaps import StaticSitemap, CategorySitemap, ProductSitemap, BlogSitemap

sitemaps = {
    'static': StaticSitemap,
    'categories': CategorySitemap,
    'products': ProductSitemap,
    'blog': BlogSitemap,
}


def robots_txt(request):
    return TemplateResponse(request, 'robots.txt', {
        'scheme': request.scheme,
        'host': request.get_host(),
    }, content_type='text/plain')


def llm_txt(request):
    return TemplateResponse(request, 'llm.txt', {
        'scheme': request.scheme,
        'host': request.get_host(),
    }, content_type='text/plain')


urlpatterns = [
    # SEO
    path('robots.txt', robots_txt, name='robots_txt'),
    path('llm.txt', llm_txt, name='llm_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

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