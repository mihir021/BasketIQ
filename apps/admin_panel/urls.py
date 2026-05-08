from django.urls import path
from apps.admin_panel import views

app_name = "admin_panel"

urlpatterns = [
    path("",           views.overview,    name="overview"),
    path("login/",     views.admin_login, name="login"),
    path("logout/",    views.admin_logout, name="logout"),
    path("users/",     views.users,       name="users"),
    path("orders/",    views.orders,      name="orders"),
    path("analytics/", views.analytics,   name="analytics"),
    path("products/",  views.products,    name="products"),
    path("ai/",        views.ai_insights, name="ai_insights"),
]
