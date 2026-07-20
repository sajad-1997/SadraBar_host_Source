from django.urls import path
from .views import index, tariff, reserve, services, tracking, contact, register, contact_submit_view

urlpatterns = [
    path('', index, name='home'),
    path('tariff/', tariff, name='tariff'),
    path('reserve/', reserve, name='reserve'),
    path('services/', services, name='services'),
    path('tracking/', tracking, name='tracking'),
    path('contact/', contact, name='contact'),
    path('register/', register, name='register'),
    path('contact/submit/', contact_submit_view, name='contact_submit'),

]