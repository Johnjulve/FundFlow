from django.contrib import admin
from .models import Transaction, Category, Budget, Note, FinancialGoal, SpendingAlert

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'transaction_type', 'category', 'date', 'user')
    list_filter = ('transaction_type', 'category', 'date', 'user')
    search_fields = ('description', 'notes')
    date_hierarchy = 'date'
    ordering = ('-date',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    list_filter = ('user',)
    search_fields = ('name',)

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'start_date', 'end_date', 'user')
    list_filter = ('category', 'start_date', 'end_date', 'user')
    search_fields = ('category__name',)
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at', 'user')
    list_filter = ('created_at', 'updated_at', 'user')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(FinancialGoal)
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'target_amount', 'current_amount', 'deadline', 'goal_type', 'user')
    list_filter = ('goal_type', 'deadline', 'user')
    search_fields = ('title', 'description')
    date_hierarchy = 'deadline'
    ordering = ('deadline',)

@admin.register(SpendingAlert)
class SpendingAlertAdmin(admin.ModelAdmin):
    list_display = ('message', 'created_at', 'is_read', 'user')
    list_filter = ('is_read', 'created_at', 'user')
    search_fields = ('message',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
