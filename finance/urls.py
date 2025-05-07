from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('transactions/', views.transactions, name='transactions'),
    path('transaction/new/', views.transaction_form, name='new-transaction'),
    path('transaction/edit/<int:pk>/', views.transaction_form, name='edit-transaction'),
    path('transaction/delete/<int:pk>/', views.delete_transaction, name='delete-transaction'),
    path('budgets/', views.budgets, name='budgets'),
    path('budget/new/', views.budget_form, name='new-budget'),
    path('budget/edit/<int:pk>/', views.budget_form, name='edit-budget'),
    path('budget/delete/<int:pk>/', views.delete_budget, name='delete-budget'),
    path('notes/', views.notes_list, name='notes-list'),
    path('note/new/', views.note_form, name='new-note'),
    path('note/edit/<int:pk>/', views.note_form, name='edit-note'),
    path('note/delete/<int:pk>/', views.delete_note, name='delete-note'),
    path('goals/', views.financial_goals, name='financial_goals'),
    path('goals/<int:pk>/delete/', views.delete_goal, name='goal-delete'),
    path('preferences/', views.user_preferences, name='user_preferences'),
    path('mark-alert-read/<int:alert_id>/', views.mark_alert_read, name='mark-alert-read'),
    path('api/create-category/', views.create_category, name='create-category'),
]
