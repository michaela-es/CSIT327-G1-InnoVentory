from django import template
from datetime import datetime, date
from django.utils.timezone import make_aware

register = template.Library()

@register.filter
def relative_date(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time())
        value = make_aware(value)
    return value