from django.urls import path

from . import views


app_name = "expenses"

urlpatterns = [
    path("api/expenses/expenses/", views.api_expenses, name="api_expenses"),
    path("api/expenses/expense-graph/<str:graph_type>/", views.api_expense_graph, name="api_expense_graph"),
]
