from django.urls import path

from . import views


app_name = "orders"

urlpatterns = [
    path("cart/", views.cart_page, name="cart"),
    path("orders/", views.my_order_page, name="orders_page"),
    path("myOrder/", views.my_order_page, name="my_order"),
    path("api/cart/", views.api_cart, name="api_cart"),
    path("api/cart/update/", views.api_cart_update, name="api_cart_update"),
    path("api/cart/remove/", views.api_cart_remove, name="api_cart_remove"),
    path("api/cart/checkout/", views.api_cart_checkout, name="api_cart_checkout"),
    path("api/orders/orders/", views.api_orders, name="api_orders"),
]
