from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Transaction, Category, Budget, Note, FinancialGoal, UserPreference, SpendingAlert
from .forms import TransactionForm, CategoryForm, BudgetForm, NoteForm, FinancialGoalForm
import json

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'finance/main.html')

@login_required
def dashboard(request):
    # Get user's theme preference
    theme = UserPreference.objects.get_or_create(user=request.user)[0].theme
    
    # Get recent transactions
    recent_transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:5]
    
    # Calculate monthly totals
    today = timezone.now()
    first_day = today.replace(day=1)
    monthly_income = Transaction.objects.filter(
        user=request.user,
        transaction_type='income',
        date__gte=first_day
    ).aggregate(total=Sum('amount'))['total'] or 0

    monthly_expenses = Transaction.objects.filter(
        user=request.user,
        transaction_type='expense',
        date__gte=first_day
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Get unread alerts
    unread_alerts = SpendingAlert.objects.filter(user=request.user, is_read=False)
    
    # Get financial goals
    goals = FinancialGoal.objects.filter(user=request.user)

    # Get active budgets
    active_budgets = Budget.objects.filter(
        user=request.user,
        start_date__lte=today,
        end_date__gte=today
    ).select_related('category')
    
    context = {
        'title': 'Dashboard',
        'theme': theme,
        'recent_transactions': recent_transactions,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_balance': monthly_income - monthly_expenses,
        'unread_alerts': unread_alerts,
        'goals': goals,
        'active_budgets': active_budgets,
        'savings_rate': (monthly_income - monthly_expenses) / monthly_income * 100 if monthly_income > 0 else 0
    }
    
    return render(request, 'finance/dashboard.html', context)

@login_required
def financial_goals(request):
    if request.method == 'POST':
        form = FinancialGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, 'Financial goal created successfully!')
            return redirect('financial_goals')
    else:
        form = FinancialGoalForm()
    
    goals = FinancialGoal.objects.filter(user=request.user)
    return render(request, 'finance/goals.html', {'form': form, 'goals': goals, 'title': 'Financial Goals'})

@login_required
def user_preferences(request):
    preference = UserPreference.objects.get_or_create(user=request.user)[0]
    
    if request.method == 'POST':
        theme = request.POST.get('theme')
        notifications = request.POST.get('notifications') == 'on'
        
        preference.theme = theme
        preference.notification_enabled = notifications
        preference.save()
        
        messages.success(request, 'Preferences updated successfully!')
        return redirect('dashboard')
    
    return render(request, 'finance/preferences.html', {'preference': preference, 'title': 'User Preferences'})

@login_required
def mark_alert_read(request, alert_id):
    alert = get_object_or_404(SpendingAlert, id=alert_id, user=request.user)
    alert.is_read = True
    alert.save()
    return JsonResponse({'status': 'success'})

@login_required 
def transactions(request):
    transactions = Transaction.objects.filter(user=request.user).select_related('category', 'category__linked_goal')
    
    # Apply filters
    transaction_type = request.GET.get('type')
    category_id = request.GET.get('category')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    if category_id:
        transactions = transactions.filter(category_id=category_id)
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__lte=date_to)

    context = {
        'transactions': transactions,
        'categories': Category.objects.filter(user=request.user).select_related('linked_goal'),
        'total_income': transactions.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_expenses': transactions.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0,
        'title': 'Transactions'
    }
    context['net_balance'] = context['total_income'] - context['total_expenses']
    
    return render(request, 'finance/transactions.html', context)

@login_required
def transaction_form(request, pk=None):
    if pk:
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
        title = 'Edit Transaction'
    else:
        transaction = None
        title = 'New Transaction'
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, f'Transaction {"updated" if pk else "created"} successfully!')
            return redirect('transactions')
    else:
        form = TransactionForm(instance=transaction)
    
    return render(request, 'finance/transaction_form.html', {
        'form': form,
        'title': title,
        'transaction': transaction
    })

@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully!')
        return redirect('transactions')
    return render(request, 'finance/transaction_confirm_delete.html', {
        'transaction': transaction,
        'title': 'Delete Transaction'
    })

@login_required
def budgets(request):
    today = timezone.now().date()
    
    # Get active budgets (current or future end date)
    active_budgets = Budget.objects.filter(
        user=request.user,
        end_date__gte=today
    ).select_related('category').order_by('end_date')
    
    # Get past budgets
    past_budgets = Budget.objects.filter(
        user=request.user,
        end_date__lt=today
    ).select_related('category').order_by('-end_date')
    
    context = {
        'title': 'Budgets',
        'active_budgets': active_budgets,
        'past_budgets': past_budgets
    }
    
    return render(request, 'finance/budgets.html', context)

@login_required
def budget_form(request, pk=None):
    if pk:
        budget = get_object_or_404(Budget, pk=pk, user=request.user)
        title = 'Edit Budget'
    else:
        budget = None
        title = 'New Budget'
    
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            messages.success(request, f'Budget {"updated" if pk else "created"} successfully!')
            return redirect('budgets')
    else:
        form = BudgetForm(instance=budget)
    
    return render(request, 'finance/budget_form.html', {
        'form': form,
        'title': title,
        'budget': budget
    })

@login_required
def delete_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget deleted successfully!')
        return redirect('budgets')
    return render(request, 'finance/budget_confirm_delete.html', {
        'budget': budget,
        'title': 'Delete Budget'
    })

@login_required
def reports(request):
    # Add your reporting logic here
    return render(request, 'finance/reports.html', {'title': 'Reports'})

@login_required
def notes_list(request):
    # Get search parameters
    query = request.GET.get('q')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Base queryset
    notes = Note.objects.filter(user=request.user)

    # Apply search filters
    if query:
        notes = notes.filter(
            Q(title__icontains(query)) |
            Q(content__icontains(query))
        )
    if date_from:
        notes = notes.filter(created_at__date__gte=date_from)
    if date_to:
        notes = notes.filter(created_at__date__lte=date_to)

    # Order by most recently updated
    notes = notes.order_by('-updated_at')

    context = {
        'title': 'Financial Notes',
        'notes': notes,
    }
    
    return render(request, 'finance/notes.html', context)

@login_required
def note_form(request, pk=None):
    if pk:
        note = get_object_or_404(Note, pk=pk, user=request.user)
        title = 'Edit Note'
    else:
        note = None
        title = 'New Note'
    
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            messages.success(request, f'Note {"updated" if pk else "created"} successfully!')
            return redirect('notes-list')
    else:
        form = NoteForm(instance=note)
    
    return render(request, 'finance/note_form.html', {
        'form': form,
        'title': title,
        'note': note
    })

@login_required
def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    return render(request, 'finance/note_detail.html', {
        'note': note,
        'title': note.title
    })

@login_required
def delete_note(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Note deleted successfully!')
        return redirect('notes-list')
    return render(request, 'finance/note_confirm_delete.html', {
        'note': note,
        'title': 'Delete Note'
    })

@login_required
def create_category(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            category = Category.objects.create(
                user=request.user,
                name=data['name'],
                spending_limit=data.get('spending_limit') or None,
                limit_period=data.get('limit_period', 'monthly')
            )
            return JsonResponse({
                'success': True,
                'category': {
                    'id': category.id,
                    'name': category.name
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def delete_goal(request, pk):
    goal = get_object_or_404(FinancialGoal, pk=pk, user=request.user)
    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Goal deleted successfully!')
        return redirect('goals')
    return redirect('goals')
