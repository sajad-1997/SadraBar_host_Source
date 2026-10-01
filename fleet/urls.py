from django.urls import path

from . import views

app_name = 'fleet'

urlpatterns = [
    path('', views.vehicle_list, name='vehicle_list'),
    path('add/', views.add_vehicle, name='add_vehicle'),
    path('edit/<int:vehicle_id>/', views.edit_vehicle, name='edit_vehicle'),
    path('search/', views.search_vehicle, name='search_vehicle'),
    path('get-by-driver/', views.get_vehicle_by_driver, name='get_vehicle_by_driver'),
]
