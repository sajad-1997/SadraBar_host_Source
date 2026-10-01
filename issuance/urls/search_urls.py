from django.urls import path

from issuance.views import *
from customers.views import search_customer as customers_search_customer
from drivers.views import search_driver as drivers_search_driver
from fleet.views import search_vehicle as fleet_search_vehicle, get_vehicle_by_driver as fleet_get_vehicle_by_driver

app_name = 'search'

urlpatterns = [
    # Use wrapper views for AJAX endpoints (cannot redirect)
    path('search/customer/', customers_search_customer, name='search_customer'),
    path('search/driver/', drivers_search_driver, name='search_driver'),
    path('search/vehicle/', fleet_search_vehicle, name='search_vehicle'),
    path('search/', search_shipment, name='search_shipment'),
    path("ajax/search-shipments/", ajax_search_shipment, name="ajax_search_shipment"),

    path('ajax/search-keyboard/', customers_search_customer, name='search_customer_keyboard'),
    path("ajax/get-vehicle/", fleet_get_vehicle_by_driver, name="get_vehicle_by_driver"),
]
