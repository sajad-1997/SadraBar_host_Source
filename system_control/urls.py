from django.urls import path

from . import views

app_name = 'system_control'

urlpatterns = [
    path('', views.index, name='index'),
    path('users/', views.users, name='users'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('roles/', views.roles, name='roles'),
    path('modules/', views.modules, name='modules'),
    path('quotas/', views.quotas, name='quotas'),
    path('wallets/', views.wallets, name='wallets'),
    path('wallets/user/<int:user_id>/', views.wallet_detail, name='wallet_detail'),
    path('wallets/role/<str:role_code>/', views.role_wallet_detail, name='role_wallet_detail'),
    path('security/', views.security_dashboard, name='security_dashboard'),
]
