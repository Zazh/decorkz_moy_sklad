from django.urls import path
from . import views

app_name = 'locations'

urlpatterns = [
    path('points-of-sales/', views.points_of_sales, name='points_of_sales'),
    path('contacts/', views.contacts, name='contacts'),
]
