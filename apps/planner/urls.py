from django.urls import path

from . import views


app_name = "planner"

urlpatterns = [
    path("aiGroceryPlanner/", views.planner_page, name="ai_grocery_planner"),
    path("planner/", views.planner_page, name="planner"),
    path("pantryChef/", views.pantry_page, name="pantry_chef"),
    path("api/planner/generate/", views.api_planner_generate, name="api_planner_generate"),
    path("api/planner/add-to-cart/", views.api_planner_add_to_cart, name="api_planner_add_to_cart"),
    path("api/pantry/suggest/", views.api_pantry_suggest, name="api_pantry_suggest"),
    path("api/pantry/search/", views.api_ingredient_search, name="api_ingredient_search"),
]
