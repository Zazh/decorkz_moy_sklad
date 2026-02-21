from django.urls import path, re_path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('all/', views.product_list, name='product_list_all'),
    re_path(r'^category/(?P<slug>.+)/$', views.product_list, name='product_list_category'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
]
