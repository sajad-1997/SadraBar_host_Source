from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.customer_list, name='customer_list'),
    path('add/', views.add_customer, name='add_customer'),
    path('edit/<int:customer_id>/', views.edit_customer, name='edit_customer'),
    path('search/', views.search_customer, name='search_customer'),
]
