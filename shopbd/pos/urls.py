from django.urls import path

from . import views

app_name = "pos"

urlpatterns = [
    path("", views.terminal, name="terminal"),
    path("api/products/", views.product_search, name="product_search"),
    path("api/sale/", views.create_sale, name="create_sale"),
    path("sales/", views.sales_list, name="sales"),
    path("receipt/<str:number>/", views.receipt, name="receipt"),
    path("sale/<str:number>/return/", views.sale_return, name="sale_return"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
