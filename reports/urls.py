from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='reports_dashboard'),
    path('data/expense_category', views.expense_category_data, name='expense_category_data'),
    path('data/income_expense', views.income_expense_data, name='income_expense_data'),
    path('export/csv', views.export_csv, name='export_csv'),
]
