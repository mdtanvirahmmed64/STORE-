from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("track/", views.track_order, name="track"),
    path("my/", views.my_orders, name="my_orders"),
    path("<str:order_number>/", views.order_detail, name="detail"),
    path("<str:order_number>/success/", views.order_success, name="success"),
    path("<str:order_number>/invoice/", views.invoice, name="invoice"),
    path("<str:order_number>/cancel/", views.cancel_order, name="cancel"),
]
