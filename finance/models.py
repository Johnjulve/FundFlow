from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db.models import Sum

class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    spending_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    limit_period = models.CharField(max_length=10, choices=[('weekly', 'Weekly'), ('monthly', 'Monthly')], default='monthly')
    goal = models.ForeignKey('FinancialGoal', on_delete=models.SET_NULL, null=True, blank=True, related_name='categories')
    linked_goal = models.ForeignKey('FinancialGoal', on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_categories')
    
    def __str__(self):
        return self.name
    
    def affects_goal(self):
        return self.goal is not None

    def has_active_goal(self):
        return bool(self.linked_goal)

    def get_goal_type(self):
        return self.linked_goal.goal_type if self.linked_goal else None
    
    class Meta:
        verbose_name_plural = 'Categories'

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPES)
    notes = models.TextField(blank=True)  # For contextual notes
    
    def __str__(self):
        return f'{self.transaction_type} - {self.amount} - {self.date.strftime("%Y-%m-%d")}'
    
    def affects_goal(self):
        if not self.category or not self.category.goal:
            return False
        
        # Check if transaction type matches goal type
        if self.transaction_type == 'income' and self.category.goal.goal_type == 'savings':
            self.category.goal.current_amount += self.amount
            self.category.goal.save()
            return True
        elif self.transaction_type == 'expense' and self.category.goal.goal_type == 'expense_reduction':
            self.category.goal.current_amount += self.amount
            self.category.goal.save()
            return True
        return False

    def update_goal_progress(self):
        if not self.category or not self.category.linked_goal:
            return False
        
        goal = self.category.linked_goal
        if (self.transaction_type == 'income' and goal.goal_type == 'savings') or \
           (self.transaction_type == 'expense' and goal.goal_type == 'expense_reduction'):
            if self.transaction_type == 'income':
                goal.current_amount += self.amount
            else:
                goal.current_amount -= self.amount
            goal.save()
            return True
        return False

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.update_goal_progress()

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    start_date = models.DateField()
    end_date = models.DateField()
    
    def __str__(self):
        return f'{self.category.name} - {self.amount}'

    def get_spent_amount(self):
        return Transaction.objects.filter(
            user=self.user,
            category=self.category,
            transaction_type='expense',
            date__date__gte=self.start_date,
            date__date__lte=self.end_date
        ).aggregate(total=Sum('amount'))['total'] or 0

    def get_remaining_amount(self):
        return self.amount - self.get_spent_amount()

    def get_progress_percentage(self):
        if self.amount > 0:
            return (self.get_spent_amount() / self.amount) * 100
        return 0

    def get_days_remaining(self):
        today = timezone.now().date()
        if today > self.end_date:
            return 0
        elif today < self.start_date:
            return (self.end_date - self.start_date).days
        else:
            return (self.end_date - today).days

    class Meta:
        ordering = ['-end_date']

class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-updated_at']

class FinancialGoal(models.Model):
    GOAL_TYPES = [
        ('savings', 'Savings'),
        ('expense_reduction', 'Expense Reduction'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deadline = models.DateField()
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

    def progress_percentage(self):
        return (self.current_amount / self.target_amount) * 100

class UserPreference(models.Model):
    THEME_CHOICES = [
        ('light', 'Light Mode'),
        ('dark', 'Dark Mode'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    notification_enabled = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username}'s preferences"

class SpendingAlert(models.Model):
    ALERT_TYPES = [
        ('limit_reached', 'Spending Limit Reached'),
        ('goal_milestone', 'Goal Milestone Reached'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.alert_type} - {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-created_at']
