from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _

from orders.models import Order, OrderItem
from pos.models import Sale
from store.models import Brand, Category, Product

from .forms import ContactForm
from .models import Banner, ContactMessage, Page, Subscriber
from .utils import safe_redirect


def home(request):
    products = Product.objects.active().select_related("brand").prefetch_related("variations", "translations")
    banners = Banner.objects.filter(is_active=True).prefetch_related("translations")
    home_categories = []
    for cat in Category.objects.filter(parent__isnull=True, is_active=True, show_on_home=True).prefetch_related("translations")[:6]:
        items = list(products.filter(category_id__in=cat.get_descendant_ids())[:10])
        if items:
            home_categories.append((cat, items))
    context = {
        "sliders": banners.filter(position="slider"),
        "side_banners": banners.filter(position="side")[:2],
        "middle_banners": banners.filter(position="middle")[:3],
        "categories": Category.objects.filter(parent__isnull=True, is_active=True).prefetch_related("translations"),
        "flash_products": products.filter(is_flash_sale=True)[:12],
        "featured_products": products.filter(is_featured=True)[:12],
        "best_sellers": products.order_by("-sold_count")[:12],
        "new_arrivals": products.filter(is_new_arrival=True)[:12],
        "home_categories": home_categories,
        "brands": Brand.objects.filter(is_active=True).exclude(logo="")[:12],
        "flash_end": (timezone.localtime() + timedelta(days=1)).replace(hour=0, minute=0, second=0),
    }
    return render(request, "core/home.html", context)


def page_detail(request, slug):
    page = get_object_or_404(Page.objects.prefetch_related("translations"), slug=slug, is_active=True)
    return render(request, "core/page.html", {"page": page})


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ContactMessage.objects.create(**form.cleaned_data)
        messages.success(request, _("Thanks! We received your message and will reply soon."))
        return redirect("core:contact")
    return render(request, "core/contact.html", {"form": form})


@require_POST
def subscribe(request):
    email = request.POST.get("email", "").strip().lower()
    if email and "@" in email:
        _sub, created = Subscriber.objects.get_or_create(email=email)
        messages.success(request, _("Subscribed successfully!") if created else _("You are already subscribed."))
    else:
        messages.error(request, _("Please enter a valid email."))
    return safe_redirect(request, request.META.get("HTTP_REFERER"), "core:home")


@staff_member_required
def staff_dashboard(request):
    now = timezone.now()
    today = timezone.localdate()
    valid = Order.objects.exclude(status__in=["cancelled", "returned"])
    last_30 = valid.filter(created_at__gte=now - timedelta(days=30))

    daily = (last_30.annotate(day=TruncDate("created_at")).values("day")
             .annotate(total=Sum("total"), n=Count("id")).order_by("day"))
    daily_map = {d["day"]: d for d in daily}
    chart = []
    for i in range(13, -1, -1):
        day = today - timedelta(days=i)
        d = daily_map.get(day, {})
        chart.append({"label": day.strftime("%d %b"), "total": float(d.get("total") or 0), "n": d.get("n", 0)})
    max_total = max([c["total"] for c in chart] + [1])
    for c in chart:
        c["pct"] = int(c["total"] * 100 / max_total)

    shop_today = Sale.objects.filter(status="completed", created_at__date=today).aggregate(s=Sum("total"), n=Count("id"))
    context = {
        "today_orders": Order.objects.filter(created_at__date=today).count(),
        "today_sales": valid.filter(created_at__date=today).aggregate(s=Sum("total"))["s"] or 0,
        "month_sales": last_30.aggregate(s=Sum("total"))["s"] or 0,
        "total_orders": Order.objects.count(),
        "pending_orders": Order.objects.filter(status="pending").count(),
        "payment_verify": Order.objects.filter(payment_status="pending").count(),
        "product_count": Product.objects.count(),
        "low_stock": Product.objects.filter(stock__lte=5, is_active=True).prefetch_related("translations").order_by("stock")[:10],
        "recent_orders": Order.objects.all()[:10],
        "top_products": (OrderItem.objects.filter(order__in=last_30).values("product_name")
                         .annotate(qty=Sum("quantity")).order_by("-qty")[:5]),
        "status_counts": [dict(row, label=dict(Order.STATUS_CHOICES).get(row["status"], row["status"]))
                          for row in Order.objects.values("status").annotate(n=Count("id")).order_by("-n")],
        "chart": chart,
        "unread_messages": ContactMessage.objects.filter(is_read=False).count(),
        "shop_today": shop_today["s"] or 0,
        "shop_today_n": shop_today["n"],
        "customers": Order.objects.values("phone").distinct().count(),
    }
    return render(request, "core/staff_dashboard.html", context)


def error_404(request, exception):
    return render(request, "404.html", status=404)


def error_403(request, exception=None):
    return render(request, "403.html", status=403)
