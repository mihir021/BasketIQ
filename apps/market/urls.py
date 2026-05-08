from django.urls import path

from . import views


app_name = "market"

urlpatterns = [
    path("", views.home, name="home"),
    path("index/", views.index_page, name="index"),
    path("market/", views.index_page, name="market"),
    path("product/<str:product_id>/", views.product_page, name="product"),
    path("api/auth/products/", views.api_products, name="api_products"),
    path("api/auth/products/best-sellers/", views.api_best_sellers, name="api_best_sellers"),
    path("api/auth/products/offers/", views.api_offers, name="api_offers"),
    path("api/auth/products/<str:product_id>/", views.api_product_detail, name="api_product_detail"),
    path(
        "api/auth/products/<str:product_id>/suggestions/",
        views.api_product_suggestions,
        name="api_product_suggestions",
    ),
    path("api/session/track/", views.api_track_session, name="api_track_session"),
    path("api/analytics/trending/", views.api_analytics_trending, name="api_analytics_trending"),
    path("contact/", views.contact_page, name="contact"),
    path("api/contact/", views.api_contact_message, name="api_contact"),
]
