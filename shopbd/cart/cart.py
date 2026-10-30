"""
Session based shopping cart.
Works for both guest users and logged-in users.
Session data format:
    {"<product_id>:<variation_ids>": {"product_id": 1, "variations": [3, 5], "quantity": 2}}
"""
from decimal import Decimal

from django.conf import settings

from store.models import Product, Variation


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not isinstance(cart, dict):
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        self._items = None

    @staticmethod
    def make_key(product_id, variation_ids):
        return f"{product_id}:{'-'.join(str(v) for v in sorted(variation_ids))}"

    def add(self, product, quantity=1, variation_ids=None, override=False):
        variation_ids = sorted(int(v) for v in (variation_ids or []))
        key = self.make_key(product.id, variation_ids)
        if key not in self.cart:
            self.cart[key] = {"product_id": product.id, "variations": variation_ids, "quantity": 0}
        new_qty = quantity if override else self.cart[key]["quantity"] + quantity
        self.cart[key]["quantity"] = max(1, min(new_qty, product.stock))
        self.save()
        return self.cart[key]["quantity"]

    def update(self, key, quantity):
        if key in self.cart:
            if quantity <= 0:
                self.remove(key)
                return
            product = Product.objects.filter(pk=self.cart[key]["product_id"]).first()
            limit = product.stock if product else quantity
            self.cart[key]["quantity"] = max(1, min(quantity, limit))
            self.save()

    def remove(self, key):
        if key in self.cart:
            del self.cart[key]
            self.save()

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.session.pop("coupon_id", None)
        self.session.modified = True

    def save(self):
        self._items = None
        self.session.modified = True

    # ------------ reading ------------
    def items(self):
        if self._items is not None:
            return self._items
        product_ids = {v["product_id"] for v in self.cart.values()}
        products = Product.objects.active().prefetch_related("translations").in_bulk(product_ids)
        var_ids = {vid for v in self.cart.values() for vid in v.get("variations", [])}
        variations = Variation.objects.in_bulk(var_ids)
        items, dirty = [], False
        for key, data in list(self.cart.items()):
            product = products.get(data["product_id"])
            if not product or product.stock <= 0:
                del self.cart[key]
                dirty = True
                continue
            qty = min(data["quantity"], product.stock)
            if qty != data["quantity"]:
                data["quantity"] = qty
                dirty = True
            vars_ = [variations[v] for v in data.get("variations", []) if v in variations]
            unit = product.final_price + sum((v.extra_price for v in vars_), Decimal("0"))
            items.append({
                "key": key,
                "product": product,
                "variations": vars_,
                "variation_text": ", ".join(f"{v.get_kind_display()}: {v.value}" for v in vars_),
                "quantity": qty,
                "unit_price": unit,
                "total_price": unit * qty,
            })
        if dirty:
            self.session.modified = True
        self._items = items
        return items

    def __iter__(self):
        return iter(self.items())

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    @property
    def subtotal(self):
        return sum((i["total_price"] for i in self.items()), Decimal("0"))

    # ------------ coupon ------------
    def get_coupon(self):
        from orders.models import Coupon
        cid = self.session.get("coupon_id")
        if not cid:
            return None
        coupon = Coupon.objects.filter(pk=cid).first()
        if not coupon or not coupon.is_valid(self.subtotal)[0]:
            self.session.pop("coupon_id", None)
            return None
        return coupon

    @property
    def discount(self):
        coupon = self.get_coupon()
        return coupon.get_discount(self.subtotal) if coupon else Decimal("0")

    def shipping_cost(self, area="inside"):
        from core.models import SiteSetting
        s = SiteSetting.load()
        if not self.items():
            return Decimal("0")
        if s.free_shipping_over and self.subtotal >= s.free_shipping_over:
            return Decimal("0")
        return s.shipping_inside_dhaka if area == "inside" else s.shipping_outside_dhaka

    def total(self, area="inside"):
        return self.subtotal - self.discount + self.shipping_cost(area)
