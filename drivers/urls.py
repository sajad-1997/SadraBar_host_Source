from django.urls import path
from . import views

app_name = 'drivers'

urlpatterns = [
    path('', views.driver_list, name='driver_list'),
    path('add/', views.add_driver, name='add_driver'),
    path('edit/<int:driver_id>/', views.edit_driver, name='edit_driver'),
    path('search/', views.search_driver, name='search_driver'),
]
