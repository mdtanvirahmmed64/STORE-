from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("products/", views.product_list, name="product_list"),
    path("category/<str:slug>/", views.product_list, name="category"),
    path("product/<str:slug>/", views.product_detail, name="product_detail"),
    path("product/<str:slug>/review/", views.add_review, name="add_review"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("wishlist/toggle/<int:product_id>/", views.wishlist_toggle, name="wishlist_toggle"),
    path("api/search-suggest/", views.search_suggest, name="search_suggest"),
]
