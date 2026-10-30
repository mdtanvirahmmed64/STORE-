from decimal import Decimal

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

register = template.Library()
BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


@register.filter
def taka(value):
    """1234.5 -> ৳1,235  (Bangla: ৳১,২৩৫)"""
    try:
        text = f"৳{Decimal(value):,.0f}"
    except Exception:
        return value
    if (get_language() or "").startswith("bn"):
        text = text.translate(BN_DIGITS)
    return text


@register.simple_tag
def stars(rating):
    """Render 5 stars (full / half / empty) with Font Awesome."""
    try:
        r = float(rating or 0)
    except (TypeError, ValueError):
        r = 0
    html = []
    for i in range(1, 6):
        if r >= i:
            html.append('<i class="fa-solid fa-star"></i>')
        elif r >= i - 0.5:
            html.append('<i class="fa-solid fa-star-half-stroke"></i>')
        else:
            html.append('<i class="fa-regular fa-star"></i>')
    return format_html('<span class="stars">{}</span>', mark_safe("".join(html)))


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """Keep current GET params and change some: {% url_replace page=2 %}"""
    query = context["request"].GET.copy()
    for k, v in kwargs.items():
        if v in (None, ""):
            query.pop(k, None)
        else:
            query[k] = v
    return query.urlencode()


@register.filter
def status_color(status):
    return {
        "pending": "warning", "confirmed": "info", "processing": "info", "shipped": "primary",
        "delivered": "success", "cancelled": "danger", "returned": "danger",
        "unpaid": "muted", "paid": "success", "refunded": "danger",
    }.get(status, "muted")


@register.filter
def tr(obj, field):
    """{{ product|tr:"name" }} → the name in the visitor's language (falls back to the original)."""
    if obj is None:
        return ""
    if hasattr(obj, "tr"):
        return obj.tr(field)
    return getattr(obj, field, "")


@register.simple_tag
def theme_style(theme_vars):
    """Print the admin-chosen colors as CSS variables."""
    css = ";".join(f"{k}:{v}" for k, v in (theme_vars or {}).items())
    return format_html("<style>:root{{{}}}</style>", mark_safe(css.replace("<", "")))
