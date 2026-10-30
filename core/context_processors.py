from django.db.models import Prefetch

from cart.cart import Cart
from pos.access import has_pos_access
from store.models import Category, Wishlist

from .models import Page, SiteSetting, ThemeSetting


def site_context(request):
    if request.path.startswith("/admin/"):
        return {}
    wish_ids = set()
    if request.user.is_authenticated:
        wish_ids = set(Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True))
    SiteSetting.load()  # make sure the row exists
    theme = ThemeSetting.load()
    active_children = Category.objects.filter(is_active=True).prefetch_related("translations")
    return {
        "site": SiteSetting.objects.prefetch_related("translations").get(pk=1),
        "theme": theme,
        "theme_vars": theme.css_variables(),
        "menu_categories": Category.objects.filter(parent__isnull=True, is_active=True)
        .prefetch_related("translations", Prefetch("children", queryset=active_children)),
        "footer_pages": Page.objects.filter(is_active=True, show_in_footer=True).prefetch_related("translations"),
        "cart_count": len(Cart(request)),
        "wishlist_count": len(wish_ids),
        "wish_ids": wish_ids,
        "pos_access": has_pos_access(request.user) if request.user.is_authenticated else False,
    }
