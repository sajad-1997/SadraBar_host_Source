from django.urls import path
from . import views

app_name = 'user_management'

urlpatterns = [
    path('', views.user_management_dashboard, name='dashboard'),
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('drivers/blocked/', views.driver_block_list, name='driver_block_list'),
]
