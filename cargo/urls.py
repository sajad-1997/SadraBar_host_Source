from django.urls import path
from . import views

app_name = 'cargo'

urlpatterns = [
    path('', views.cargo_list, name='cargo_list'),
    path('add/', views.add_cargo, name='add_cargo'),
    path('edit/<int:cargo_id>/', views.edit_cargo, name='edit_cargo'),
    path('search/', views.search_cargo, name='search_cargo'),
]
