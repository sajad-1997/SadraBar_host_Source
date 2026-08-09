from django.urls import path

from issuance.views.bijak_token_views import bijak_access_view, bijak_print_by_token

app_name = 'token'

urlpatterns = [
    path("access/<str:token>/", bijak_access_view, name="bijak_access"),
    path("print/<str:token>/", bijak_print_by_token, name="bijak_print_token"),
]
