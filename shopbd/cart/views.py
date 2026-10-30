from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _

from core.utils import safe_redirect
from orders.models import Coupon
from store.models import Product, Variation

from .cart import Cart


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _int(value, default=1):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def cart_detail(request):
    cart = Cart(request)
    return render(request, "cart/cart_detail.html", {"cart": cart, "coupon": cart.get_coupon()})


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product.objects.active(), pk=product_id)
    cart = Cart(request)
    if not product.in_stock:
        msg, ok = _("Sorry, this product is out of stock."), False
    else:
        valid_ids = set(product.variations.filter(is_active=True).values_list("id", flat=True))
        raw = [x for key in request.POST if key.startswith("variation") for x in request.POST.getlist(key)]
        variation_ids = [v for v in (_int(x, 0) for x in raw) if v in valid_ids]
        # one variation per kind is required if the product has that kind
        kinds_needed = set(product.variations.filter(is_active=True).values_list("kind", flat=True))
        kinds_given = set(product.variations.filter(id__in=variation_ids).values_list("kind", flat=True))
        if kinds_needed - kinds_given:
            missing = ", ".join(str(dict(Variation.KIND_CHOICES)[k]) for k in sorted(kinds_needed - kinds_given))
            msg, ok = _("Please select %(options)s.") % {"options": missing}, False
        else:
            cart.add(product, quantity=max(1, _int(request.POST.get("quantity"))), variation_ids=variation_ids)
            msg, ok = _("“%(name)s” added to cart.") % {"name": product.tr("name")}, True

    if _is_ajax(request):
        return JsonResponse({"ok": ok, "message": msg, "cart_count": len(cart)}, status=200 if ok else 400)
    (messages.success if ok else messages.error)(request, msg)
    if ok and request.POST.get("buy_now"):
        return redirect("orders:checkout")
    return safe_redirect(request, request.POST.get("next"), product.get_absolute_url())


@require_POST
def cart_update(request):
    cart = Cart(request)
    cart.update(request.POST.get("key", ""), _int(request.POST.get("quantity"), 1))
    if _is_ajax(request):
        return JsonResponse({"ok": True, "cart_count": len(cart)})
    return redirect("cart:detail")


@require_POST
def cart_remove(request):
    cart = Cart(request)
    cart.remove(request.POST.get("key", ""))
    messages.info(request, _("Item removed from cart."))
    return redirect("cart:detail")


@require_POST
def apply_coupon(request):
    cart = Cart(request)
    code = request.POST.get("code", "").strip().upper()
    coupon = Coupon.objects.filter(code=code).first()
    if not coupon:
        messages.error(request, _("Invalid coupon code."))
    else:
        ok, msg = coupon.is_valid(cart.subtotal)
        if ok:
            request.session["coupon_id"] = coupon.id
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    return safe_redirect(request, request.POST.get("next"), "cart:detail")


@require_POST
def remove_coupon(request):
    request.session.pop("coupon_id", None)
    messages.info(request, _("Coupon removed."))
    return safe_redirect(request, request.POST.get("next"), "cart:detail")
