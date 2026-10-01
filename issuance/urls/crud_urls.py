from django.urls import path
from django.shortcuts import redirect

from ..views import *

app_name = 'crud'

urlpatterns = [
    path('create_new/', create_new, name='create_new'),
    path('pending/', pending_bijaks, name='pending'),
    path('print/<int:pk>/', print_page, name='print'),
    path('print-weight2/<int:pk>/', print_page_weight2, name='print_weight2'),
    path('print-with-stamp/<int:pk>/', print_page_with_stamp, name='print_with_stamp'),
    path('pdf/<int:pk>/', generate_pdf, name='generate_pdf'),
    # path('bijak/access/<str:token>/', access_view, name='bijak_access'),
    # path('bijak/print/<str:token>/', print_view, name='print'),
    path('preview/<int:pk>/', preview_page, name='preview'),

    # Redirect customer/driver/vehicle URLs to external modules
    path('add-customer/', lambda request: redirect('customers:add_customer'), name='add_customer'),
    path('add-driver/', lambda request: redirect('drivers:add_driver'), name='add_driver'),
    path('add-vehicle/', lambda request: redirect('fleet:add_vehicle'), name='add_vehicle'),
    path('add-caption/', lambda request: redirect('captions:add_caption'), name='add_caption'),

    path('customers/edit/<int:pk>/', lambda request, pk: redirect('customers:edit_customer', customer_id=pk), name='edit_customer'),
    path('driver/edit/<int:driver_id>/', lambda request, driver_id: redirect('drivers:edit_driver', driver_id=driver_id), name='edit_driver'),
    path('edit-vehicle/', lambda request: redirect('fleet:vehicle_list'), name='edit_vehicle'),
    path('edit-cargo/', edit_cargo, name='edit_cargo'),
    path('edit-bijak/<int:pk>/', edit_bijak, name='edit_bijak'),

    # Remove duplicate-customer, save-sender, save-driver as they are not in external modules
    # path('duplicate-customer/', duplicate_customer, name="duplicate_customer"),
    # path("save-sender/", save_customer, name="save_customer"),
    # path("save-driver/", save_driver, name="save_driver"),
    # path('add-vehicle/<int:driver_id>/', add_vehicle_with_driver, name='add_vehicle_with_driver'),

    # path('report/', include(('report.urls', 'report_dashboard'), namespace='report')),

]
