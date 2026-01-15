from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-income/', views.add_income, name='add_income'),
    path('add-expense/', views.add_expense, name='add_expense'),
    path('set-budget/', views.set_budget, name='set_budget'),
    path('add-category/', views.add_category, name='add_category'),
    path('add-source/', views.add_source, name='add_source'),
    path('budgets/', views.list_budgets, name='list_budgets'),
    path('budgets/<int:pk>/edit/', views.edit_budget, name='edit_budget'),
    path('budgets/<int:pk>/delete/', views.delete_budget, name='delete_budget'),
    path('incomes/', views.list_incomes, name='list_incomes'),
    path('incomes/<int:pk>/edit/', views.edit_income, name='edit_income'),
    path('incomes/<int:pk>/delete/', views.delete_income, name='delete_income'),
    path('expenses/', views.list_expenses, name='list_expenses'),
    path('expenses/<int:pk>/edit/', views.edit_expense, name='edit_expense'),
    path('expenses/<int:pk>/delete/', views.delete_expense, name='delete_expense'),
    path('sources/', views.list_sources, name='list_sources'),
    path('sources/<int:pk>/edit/', views.edit_source, name='edit_source'),
    path('sources/<int:pk>/delete/', views.delete_source, name='delete_source'),
    path('categories/', views.list_categories, name='list_categories'),
    path('categories/<int:pk>/edit/', views.edit_category, name='edit_category'),
    path('categories/<int:pk>/delete/', views.delete_category, name='delete_category'),
    path('export-excel/', views.export_excel, name='export_excel'),
    path('export-pdf/', views.export_pdf, name='export_pdf'),
]
