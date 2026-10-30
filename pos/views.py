import json
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from core.models import SiteSetting
from orders.models import Order
from store.models import Product, Variation

from .access import allowed_branches, can_see_all_branches, current_branch, is_manager, pos_required, staff_record
from .models import Branch, BranchStock, Sale, SaleItem


def _dec(value, default="0"):
    try:
        return Decimal(str(value if value not in (None, "") else default))
    except (InvalidOperation, ValueError):
        return Decimal(default)


def _pos_context(request, branch, **extra):
    ctx = {
        "branch": branch,
        "branches": allowed_branches(request.user),
        "is_manager": is_manager(request.user, branch),
        "can_see_all": can_see_all_branches(request.user),
        "site": SiteSetting.load(),
    }
    ctx.update(extra)
    return ctx


# ---------------------------------------------------------------- terminal
@pos_required
def terminal(request):
    branch = current_branch(request)
    rec = staff_record(request.user)
    max_discount = 100 if request.user.is_superuser or (rec and rec.role == "manager") else (
        rec.max_discount_percent if rec and rec.can_give_discount else 0)
    return render(request, "pos/terminal.html", _pos_context(
        request, branch, max_discount=max_discount, payment_choices=Sale.PAYMENT_CHOICES))


@pos_required
def product_search(request):
    """JSON list of products with this branch's stock. Exact SKU/barcode match comes first."""
    branch = current_branch(request)
    q = request.GET.get("q", "").strip()
    qs = Product.objects.filter(is_active=True).prefetch_related("translations", "variations")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(sku__iexact=q) | Q(translations__name__icontains=q)).distinct()
    else:
        qs = qs.order_by("-sold_count")
    products = list(qs[:60])
    stock = dict(BranchStock.objects.filter(branch=branch, product__in=products).values_list("product_id", "quantity"))
    results = []
    for p in products:
        results.append({
            "id": p.id,
            "name": p.tr("name"),
            "sku": p.sku,
            "price": str(p.final_price),
            "image": p.image.url if p.image else "",
            "stock": stock.get(p.id, 0),
            "exact": bool(q) and p.sku.lower() == q.lower(),
            "variations": [
                {"id": v.id, "kind": v.kind, "kind_label": str(v.get_kind_display()), "value": v.value,
                 "extra": str(v.extra_price)}
                for v in p.variations.all() if v.is_active
            ],
        })
    results.sort(key=lambda r: not r["exact"])
    return JsonResponse({"results": results, "branch": branch.id, "sell_without_stock": branch.sell_without_stock})


@pos_required
@require_POST
def create_sale(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": _("Invalid request.")}, status=400)

    branch = allowed_branches(request.user).filter(pk=data.get("branch")).first()
    if not branch:
        return JsonResponse({"ok": False, "error": _("You cannot sell from this branch.")}, status=403)
    lines = data.get("items") or []
    if not lines:
        return JsonResponse({"ok": False, "error": _("The cart is empty.")}, status=400)
    payment = data.get("payment_method", "cash")
    if payment not in dict(Sale.PAYMENT_CHOICES):
        payment = "cash"

    try:
        with transaction.atomic():
            ids = {int(line["product_id"]) for line in lines}
            products = Product.objects.in_bulk(ids)
            stocks = {s.product_id: s for s in BranchStock.objects.select_for_update().filter(branch=branch, product_id__in=ids)}
            sale_lines, subtotal = [], Decimal("0")
            needed = {}
            for line in lines:
                product = products.get(int(line["product_id"]))
                qty = int(line.get("quantity") or 0)
                if not product or qty < 1:
                    raise ValueError(_("Invalid product in cart."))
                valid = {v.id: v for v in product.variations.filter(is_active=True)}
                chosen = [valid[int(v)] for v in line.get("variation_ids", []) if int(v) in valid]
                unit = product.final_price + sum((v.extra_price for v in chosen), Decimal("0"))
                subtotal += unit * qty
                needed[product.id] = needed.get(product.id, 0) + qty
                sale_lines.append((product, chosen, unit, qty))

            if not branch.sell_without_stock:
                for pid, qty in needed.items():
                    have = stocks[pid].quantity if pid in stocks else 0
                    if have < qty:
                        raise ValueError(_("Not enough stock for “%(name)s” in this branch (available: %(n)s).")
                                         % {"name": products[pid].tr("name"), "n": have})

            # discount (amount or %), limited by the cashier's permission
            rec = staff_record(request.user)
            max_pct = Decimal("100") if is_manager(request.user, branch) else (
                Decimal(rec.max_discount_percent) if rec and rec.can_give_discount else Decimal("0"))
            value = _dec(data.get("discount_value"))
            discount = (subtotal * value / 100) if data.get("discount_type") == "percent" else value
            discount = max(Decimal("0"), min(discount, subtotal)).quantize(Decimal("0.01"))
            if subtotal and discount * 100 / subtotal > max_pct + Decimal("0.001"):
                raise ValueError(_("You can give at most %(p)s%% discount.") % {"p": max_pct})
            total = subtotal - discount
            paid = _dec(data.get("paid_amount"), str(total))
            if payment == "cash" and paid < total:
                raise ValueError(_("Paid amount is less than the total."))
            if payment != "cash":
                paid = total

            sale = Sale.objects.create(
                branch=branch, cashier=request.user,
                customer_name=str(data.get("customer_name", ""))[:100],
                customer_phone=str(data.get("customer_phone", ""))[:20],
                subtotal=subtotal, discount=discount, total=total, paid_amount=paid, change_amount=paid - total,
                payment_method=payment, transaction_id=str(data.get("transaction_id", ""))[:60],
                note=str(data.get("note", ""))[:255],
            )
            SaleItem.objects.bulk_create([
                SaleItem(sale=sale, product=p, product_name=p.name, sku=p.sku,
                         variation=", ".join(f"{v.get_kind_display()}: {v.value}" for v in chosen),
                         unit_price=unit, quantity=qty)
                for p, chosen, unit, qty in sale_lines
            ])
            for pid, qty in needed.items():
                row = stocks.get(pid) or BranchStock.objects.create(branch=branch, product_id=pid, quantity=0)
                new_qty = max(0, row.quantity - qty)
                BranchStock.objects.filter(pk=row.pk).update(quantity=new_qty)
                Product.objects.filter(pk=pid).update(sold_count=F("sold_count") + qty)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse({"ok": True, "number": sale.number, "total": str(sale.total),
                         "receipt_url": sale.get_absolute_url() + "?print=1"})


# ---------------------------------------------------------------- receipt & history
def _get_sale(request, number):
    sale = get_object_or_404(Sale.objects.select_related("branch", "cashier").prefetch_related("items"), number=number)
    if not allowed_branches(request.user).filter(pk=sale.branch_id).exists():
        raise Http404
    return sale


@pos_required
def receipt(request, number):
    sale = _get_sale(request, number)
    return render(request, "pos/receipt.html", {"sale": sale, "site": SiteSetting.load(),
                                                "autoprint": request.GET.get("print") == "1"})


@pos_required
def sales_list(request):
    branch = current_branch(request)
    sales = Sale.objects.filter(branch=branch).select_related("cashier").prefetch_related("items")
    date_from, date_to = parse_date(request.GET.get("from", "") or ""), parse_date(request.GET.get("to", "") or "")
    if not date_from and not date_to:
        date_from = date_to = timezone.localdate()
    if date_from:
        sales = sales.filter(created_at__date__gte=date_from)
    if date_to:
        sales = sales.filter(created_at__date__lte=date_to)
    q = request.GET.get("q", "").strip()
    if q:
        sales = sales.filter(Q(number__icontains=q) | Q(customer_phone__icontains=q) | Q(customer_name__icontains=q))
    if not is_manager(request.user, branch):
        sales = sales.filter(cashier=request.user)
    done = sales.filter(status="completed")
    summary = done.aggregate(total=Sum("total"), count=Count("id"), discount=Sum("discount"))
    by_method = {row["payment_method"]: row["s"] for row in done.values("payment_method").annotate(s=Sum("total"))}
    page = Paginator(sales, 30).get_page(request.GET.get("page"))
    return render(request, "pos/sales.html", _pos_context(
        request, branch, page_obj=page, sales=page.object_list, summary=summary, q=q,
        by_method=[(label, by_method.get(key) or 0) for key, label in Sale.PAYMENT_CHOICES],
        date_from=date_from, date_to=date_to))


@pos_required
@require_POST
def sale_return(request, number):
    sale = _get_sale(request, number)
    if not is_manager(request.user, sale.branch):
        raise PermissionDenied
    sale.mark_returned(request.user)
    messages.success(request, _("Sale %(n)s returned. Stock added back to the branch.") % {"n": sale.number})
    return redirect("pos:sales")


# ---------------------------------------------------------------- multi-branch dashboard
@pos_required
def dashboard(request):
    user = request.user
    branches = list(allowed_branches(user))
    if not can_see_all_branches(user) and not is_manager(user):
        raise PermissionDenied
    today = timezone.localdate()
    start_30 = today - timedelta(days=29)
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    sales = Sale.objects.filter(branch__in=branches, status="completed")

    rows = []
    for b in branches:
        bs = sales.filter(branch=b)
        t = bs.filter(created_at__date=today).aggregate(s=Sum("total"), n=Count("id"))
        m = bs.filter(created_at__date__gte=start_30).aggregate(s=Sum("total"), n=Count("id"))
        low = BranchStock.objects.filter(branch=b, quantity__lte=F("low_stock_alert")).count()
        rows.append({"branch": b, "today": t["s"] or 0, "today_n": t["n"], "month": m["s"] or 0, "month_n": m["n"],
                     "avg": (m["s"] or 0) / m["n"] if m["n"] else 0, "low": low,
                     "stock_units": BranchStock.objects.filter(branch=b).aggregate(u=Sum("quantity"))["u"] or 0})

    # daily chart: shop sales per branch + online orders
    daily = {(r["branch_id"], r["day"]): float(r["s"]) for r in
             sales.filter(created_at__date__gte=days[0]).annotate(day=TruncDate("created_at"))
             .values("branch_id", "day").annotate(s=Sum("total"))}
    show_online = can_see_all_branches(user)
    online_qs = Order.objects.exclude(status__in=["cancelled", "returned"])
    online_daily = {r["day"]: float(r["s"]) for r in
                    online_qs.filter(created_at__date__gte=days[0]).annotate(day=TruncDate("created_at"))
                    .values("day").annotate(s=Sum("total"))} if show_online else {}
    chart = []
    for d in days:
        parts = [{"name": b.code, "value": daily.get((b.id, d), 0.0)} for b in branches]
        if show_online:
            parts.append({"name": "Online", "value": online_daily.get(d, 0.0)})
        chart.append({"label": d.strftime("%d %b"), "parts": parts, "total": sum(p["value"] for p in parts)})
    peak = max([c["total"] for c in chart] + [1])
    for c in chart:
        for p in c["parts"]:
            p["pct"] = round(p["value"] * 100 / peak, 2)

    online_today = online_qs.filter(created_at__date=today).aggregate(s=Sum("total"), n=Count("id")) if show_online else None
    online_month = online_qs.filter(created_at__date__gte=start_30).aggregate(s=Sum("total"), n=Count("id")) if show_online else None
    shop_today = sum(r["today"] for r in rows)
    shop_month = sum(r["month"] for r in rows)

    month_items = SaleItem.objects.filter(sale__in=sales.filter(created_at__date__gte=start_30))
    top_products = month_items.values("product_name").annotate(qty=Sum("quantity")).order_by("-qty")[:8]
    cashiers = (sales.filter(created_at__date=today).values("cashier__username", "branch__code")
                .annotate(s=Sum("total"), n=Count("id")).order_by("-s"))
    payments = [(label, sales.filter(created_at__date__gte=start_30, payment_method=key).aggregate(s=Sum("total"))["s"] or 0)
                for key, label in Sale.PAYMENT_CHOICES]
    low_stock = (BranchStock.objects.filter(branch__in=branches, quantity__lte=F("low_stock_alert"))
                 .select_related("branch", "product").order_by("quantity")[:12])

    return render(request, "pos/dashboard.html", _pos_context(
        request, current_branch(request), rows=rows, chart=chart, show_online=show_online,
        online_today=online_today, online_month=online_month, shop_today=shop_today, shop_month=shop_month,
        top_products=top_products, cashiers=cashiers, payments=payments, low_stock=low_stock,
        legend=[b.code for b in branches] + (["Online"] if show_online else []), today=today))
