from django.urls import path

from issuance.views import *

app_name = 'search'

urlpatterns = [
    path('search/customer/', search_customer, name='search_customer'),
    path('search/driver/', search_driver, name='search_driver'),
    path('search/vehicle/', search_vehicle, name='search_vehicle'),
    path('search/shipments/', search_shipment, name='search_shipment'),
    path("ajax/search-shipments/", ajax_search_shipment, name="ajax_search_shipment"),

    path('ajax/search-keyboard/', search_customer, name='search_customer_keyboard'),
    path("ajax/get-vehicle/", get_vehicle_by_driver, name="get_vehicle_by_driver"),
]
