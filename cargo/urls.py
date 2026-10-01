from django.urls import path
from . import views

app_name = 'cargo'

urlpatterns = [
    path('', views.cargo_list, name='cargo_list'),
    path('add/', views.add_cargo, name='add_cargo'),
    path('edit/<int:cargo_id>/', views.edit_cargo, name='edit_cargo'),
    path('search/', views.search_cargo, name='search_cargo'),
    path('search-name/', views.search_cargo_name, name='search_cargo_name'),
    path('search-city/', views.search_city, name='search_city'),
]
