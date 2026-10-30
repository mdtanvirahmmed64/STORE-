import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _

from accounts.models import Address
from cart.cart import Cart
from core.models import SiteSetting
from store.models import Product

from .forms import CheckoutForm, TrackOrderForm
from .models import Coupon, Order, OrderItem, OrderStatusHistory

logger = logging.getLogger(__name__)


def _initial_from_user(user):
    if not user.is_authenticated:
        return {}
    initial = {"full_name": user.get_full_name() or user.username, "email": user.email,
               "phone": getattr(getattr(user, "profile", None), "phone", "")}
    addr = user.addresses.filter(is_default=True).first()
    if addr:
        initial.update(full_name=addr.full_name, phone=addr.phone, division=addr.division, city=addr.city,
                       area=addr.area, address_line=addr.address_line,
                       delivery_area="inside" if addr.inside_dhaka else "outside")
    return initial


def checkout(request):
    cart = Cart(request)
    if not cart.items():
        messages.warning(request, _("Your cart is empty."))
        return redirect("cart:detail")

    site = SiteSetting.load()
    form = CheckoutForm(request.POST or None, initial=_initial_from_user(request.user), settings_obj=site)

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            order = _place_order(request, cart, data)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("cart:detail")

        if request.user.is_authenticated and data.get("save_address"):
            exists = request.user.addresses.filter(phone=data["phone"], address_line=data["address_line"]).exists()
            if not exists:
                Address.objects.create(user=request.user, full_name=data["full_name"], phone=data["phone"],
                                       division=data["division"], city=data["city"], area=data["area"],
                                       address_line=data["address_line"])

        guest_orders = request.session.get("guest_orders", [])
        guest_orders.append(order.order_number)
        request.session["guest_orders"] = guest_orders[-20:]
        cart.clear()
        _send_order_email(order, site)
        return redirect("orders:success", order_number=order.order_number)

    area = form["delivery_area"].value() or "inside"
    context = {
        "form": form,
        "cart": cart,
        "coupon": cart.get_coupon(),
        "site": site,
        "shipping_inside": cart.shipping_cost("inside"),
        "shipping_outside": cart.shipping_cost("outside"),
        "shipping": cart.shipping_cost(area),
        "total": cart.total(area),
        "addresses": request.user.addresses.all() if request.user.is_authenticated else [],
    }
    return render(request, "orders/checkout.html", context)


@transaction.atomic
def _place_order(request, cart, data):
    items = cart.items()
    # lock product rows so two customers can't buy the last item at the same time
    locked = Product.objects.select_for_update().in_bulk([i["product"].id for i in items])
    for item in items:
        p = locked[item["product"].id]
        if p.stock < item["quantity"]:
            raise ValueError(_("Sorry, only %(n)s pcs of “%(name)s” left in stock. Please update your cart.")
                             % {"n": p.stock, "name": p.tr("name")})

    coupon = cart.get_coupon()
    subtotal = cart.subtotal
    discount = cart.discount
    shipping = cart.shipping_cost(data["delivery_area"])
    payment_method = data["payment_method"]

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        full_name=data["full_name"], phone=data["phone"], email=data.get("email", ""),
        division=data["division"], city=data["city"], area=data["area"], address_line=data["address_line"],
        delivery_area=data["delivery_area"], note=data.get("note", ""),
        subtotal=subtotal, discount=discount, shipping_cost=shipping, total=subtotal - discount + shipping,
        coupon=coupon, payment_method=payment_method,
        payment_status="pending" if payment_method in ("bkash", "nagad") else "unpaid",
        transaction_id=data.get("transaction_id", "") if payment_method != "cod" else "",
        sender_number=data.get("sender_number", "") if payment_method != "cod" else "",
    )
    OrderItem.objects.bulk_create([
        OrderItem(order=order, product=i["product"], product_name=i["product"].name,
                  variation=i["variation_text"], price=i["unit_price"], quantity=i["quantity"])
        for i in items
    ])
    for i in items:
        Product.objects.filter(pk=i["product"].id).update(stock=F("stock") - i["quantity"],
                                                          sold_count=F("sold_count") + i["quantity"])
    if coupon:
        Coupon.objects.filter(pk=coupon.pk).update(used_count=F("used_count") + 1)
    OrderStatusHistory.objects.create(order=order, status="pending", note="Order placed")
    return order


def _send_order_email(order, site):
    if not order.email:
        return
    try:
        body = render_to_string("orders/email_confirmation.txt", {"order": order, "site": site})
        send_mail(f"Order {order.order_number} received - {site.site_name}", body, None, [order.email],
                  fail_silently=True)
    except Exception:  # email must never break checkout
        logger.exception("Order email failed")


def _get_order_for_request(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related("items__product__translations", "history"),
                              order_number=order_number)
    allowed = (
        (request.user.is_authenticated and (order.user_id == request.user.id or request.user.is_staff))
        or order_number in request.session.get("guest_orders", [])
        or order_number in request.session.get("tracked_orders", [])
    )
    if not allowed:
        raise Http404("Order not found")
    return order


def order_success(request, order_number):
    order = _get_order_for_request(request, order_number)
    return render(request, "orders/success.html", {"order": order})


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items")
    status = request.GET.get("status")
    if status:
        orders = orders.filter(status=status)
    page_obj = Paginator(orders, 10).get_page(request.GET.get("page"))
    return render(request, "orders/my_orders.html", {
        "page_obj": page_obj, "orders": page_obj.object_list, "status": status,
        "status_choices": Order.STATUS_CHOICES,
    })


def order_detail(request, order_number):
    order = _get_order_for_request(request, order_number)
    return render(request, "orders/order_detail.html", {"order": order})


def invoice(request, order_number):
    order = _get_order_for_request(request, order_number)
    return render(request, "orders/invoice.html", {"order": order, "site": SiteSetting.load()})


@require_POST
def cancel_order(request, order_number):
    order = _get_order_for_request(request, order_number)
    if order.can_cancel:
        with transaction.atomic():
            order.restock()
            order.status = "cancelled"
            order.save(update_fields=["status", "updated_at"])
            OrderStatusHistory.objects.create(order=order, status="cancelled", note="Cancelled by customer")
        messages.success(request, _("Your order has been cancelled."))
    else:
        messages.error(request, _("This order can no longer be cancelled."))
    return redirect("orders:detail", order_number=order.order_number)


def track_order(request):
    form = TrackOrderForm(request.GET or None)
    order = None
    if request.GET and form.is_valid():
        phone = form.cleaned_data["phone"].replace(" ", "").replace("-", "")
        order = Order.objects.filter(order_number__iexact=form.cleaned_data["order_number"].strip(),
                                     phone=phone).first()
        if order:
            tracked = request.session.get("tracked_orders", [])
            if order.order_number not in tracked:
                tracked.append(order.order_number)
                request.session["tracked_orders"] = tracked[-20:]
        else:
            messages.error(request, _("No order found with that order number and phone."))
    return render(request, "orders/track.html", {"form": form, "order": order})
