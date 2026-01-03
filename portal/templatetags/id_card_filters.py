# templatetags/id_card_filters.py
from django import template

register = template.Library()

@register.filter
def filter_by_status(queryset, statuses):
    """Filter queryset by multiple statuses"""
    if not queryset:
        return queryset
    status_list = [s.strip() for s in statuses.split(',')]
    return queryset.filter(status__in=status_list)

@register.filter
def status_color(status):
    """Get Bootstrap color class for status"""
    color_map = {
        'draft': 'secondary',
        'submitted': 'info',
        'payment_pending': 'warning',
        'payment_confirmed': 'primary',
        'in_production': 'info',
        'ready_for_pickup': 'success',
        'delivered': 'success',
        'completed': 'success',
        'rejected': 'danger',
        'cancelled': 'secondary',
        'active': 'success',
        'inactive': 'secondary',
        'lost': 'danger',
        'damaged': 'warning',
        'expired': 'warning',
        'replaced': 'info',
    }
    return color_map.get(status, 'secondary')

@register.filter
def payment_balance_color(balance):
    """Get color class for payment balance"""
    if balance <= 0:
        return 'success'
    else:
        return 'warning'

@register.filter
def allowed_payment_statuses(application):
    """Check if payment is allowed for application status"""
    allowed_statuses = ['submitted', 'payment_pending']
    return application.status in allowed_statuses