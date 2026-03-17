from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('favorites/', views.favorites_page, name='favorites'),
    path('api/favorites/toggle/', views.toggle_favorite, name='favorite_toggle'),
    path('api/favorites/ids/', views.favorite_ids, name='favorite_ids'),
    path('api/favorites/preview/', views.favorites_preview, name='favorites_preview'),
]
