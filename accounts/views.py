from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _

from core.utils import safe_redirect
from orders.models import Order
from store.models import Wishlist

from .forms import AddressForm, LoginForm, ProfileForm, RegisterForm, UserForm
from .models import Address, Profile


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        # keep the guest cart after login
        cart = self.request.session.get("cart")
        coupon = self.request.session.get("coupon_id")
        response = super().form_valid(form)
        if cart:
            self.request.session["cart"] = cart
        if coupon:
            self.request.session["coupon_id"] = coupon
        messages.success(self.request, _("Welcome back, %(name)s!") % {"name": form.get_user().first_name or form.get_user().username})
        return response


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cart = request.session.get("cart")
        user = form.save()
        login(request, user, backend="accounts.backends.EmailOrUsernameBackend")
        if cart:
            request.session["cart"] = cart
        messages.success(request, _("Your account has been created successfully!"))
        return safe_redirect(request, request.GET.get("next"), "accounts:dashboard")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def dashboard(request):
    orders = Order.objects.filter(user=request.user)
    context = {
        "recent_orders": orders[:5],
        "order_count": orders.count(),
        "pending_count": orders.filter(status__in=["pending", "confirmed", "processing", "shipped"]).count(),
        "delivered_count": orders.filter(status="delivered").count(),
        "wishlist_count": Wishlist.objects.filter(user=request.user).count(),
        "default_address": request.user.addresses.filter(is_default=True).first(),
    }
    return render(request, "accounts/dashboard.html", context)


@login_required
def profile(request):
    prof, _created = Profile.objects.get_or_create(user=request.user)
    uform = UserForm(request.POST or None, instance=request.user)
    pform = ProfileForm(request.POST or None, request.FILES or None, instance=prof)
    if request.method == "POST" and uform.is_valid() and pform.is_valid():
        uform.save()
        pform.save()
        messages.success(request, _("Profile updated."))
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"uform": uform, "pform": pform})


@login_required
def address_list(request):
    return render(request, "accounts/addresses.html", {"addresses": request.user.addresses.all()})


@login_required
def address_form(request, pk=None):
    instance = get_object_or_404(Address, pk=pk, user=request.user) if pk else None
    form = AddressForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        address = form.save(commit=False)
        address.user = request.user
        address.save()
        messages.success(request, _("Address saved."))
        return safe_redirect(request, request.GET.get("next"), "accounts:addresses")
    return render(request, "accounts/address_form.html", {"form": form, "editing": bool(instance)})


@login_required
@require_POST
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    was_default = address.is_default
    address.delete()
    if was_default:
        nxt = request.user.addresses.first()
        if nxt:
            nxt.is_default = True
            nxt.save()
    messages.info(request, _("Address deleted."))
    return redirect("accounts:addresses")
