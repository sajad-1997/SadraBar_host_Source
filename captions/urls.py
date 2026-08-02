from django.urls import path
from . import views

app_name = 'captions'

urlpatterns = [
    path('', views.caption_list, name='caption_list'),
    path('add/', views.add_caption, name='add_caption'),
    path('edit/<int:caption_id>/', views.edit_caption, name='edit_caption'),
    path('search/', views.search_caption, name='search_caption'),
]
