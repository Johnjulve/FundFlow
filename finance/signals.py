from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from .models import Transaction, Category, SpendingAlert

@receiver(post_save, sender=Transaction)
def check_spending_limits(sender, instance, created, **kwargs):
    if not created or instance.transaction_type != 'expense':
        return

    category = instance.category
    if not category or not category.spending_limit:
        return

    # Calculate the start date based on limit period
    today = timezone.now().date()
    if category.limit_period == 'weekly':
        start_date = today - timedelta(days=today.weekday())
    else:  # monthly
        start_date = today.replace(day=1)

    # Calculate total spending in this period
    total_spending = Transaction.objects.filter(
        user=instance.user,
        category=category,
        transaction_type='expense',
        date__date__gte=start_date,
        date__date__lte=today
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Check if spending limit is exceeded
    if total_spending > category.spending_limit:
        SpendingAlert.objects.create(
            user=instance.user,
            category=category,
            alert_type='limit_reached',
            message=f'You have exceeded your {category.limit_period} spending limit for {category.name}. '
                    f'Limit: ${category.spending_limit}, Current spending: ${total_spending}'
        )
