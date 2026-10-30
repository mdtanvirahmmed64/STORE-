import random
import string
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _g
from django.utils.translation import gettext_lazy as _

from accounts.models import DIVISION_CHOICES


class Coupon(models.Model):
    TYPE_CHOICES = [("percent", "Percentage (%)"), ("fixed", "Fixed amount (৳)")]
    code = models.CharField(max_length=30, unique=True)
    discount_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="percent")
    value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                       help_text="Percentage কুপনের সর্বোচ্চ ছাড় (ঐচ্ছিক)")
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=0, help_text="0 = আনলিমিটেড")
    used_count = models.PositiveIntegerField(default=0, editable=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.upper().strip()
        super().save(*args, **kwargs)

    def is_valid(self, subtotal):
        """Returns (ok, message)."""
        now = timezone.now()
        if not self.is_active or not (self.valid_from <= now <= self.valid_to):
            return False, _g("This coupon is expired or inactive.")
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False, _g("This coupon has reached its usage limit.")
        if subtotal < self.min_order_amount:
            return False, _g("Minimum order ৳%(amount)s required for this coupon.") % {
                "amount": f"{self.min_order_amount:.0f}"}
        return True, _g("Coupon applied successfully!")

    def get_discount(self, subtotal):
        if self.discount_type == "percent":
            d = subtotal * self.value / Decimal("100")
            if self.max_discount:
                d = min(d, self.max_discount)
        else:
            d = self.value
        return min(d, subtotal).quantize(Decimal("0.01"))


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("confirmed", _("Confirmed")),
        ("processing", _("Processing")),
        ("shipped", _("Shipped")),
        ("delivered", _("Delivered")),
        ("cancelled", _("Cancelled")),
        ("returned", _("Returned")),
    ]
    PAYMENT_METHOD_CHOICES = [
        ("cod", _("Cash on Delivery")),
        ("bkash", _("bKash")),
        ("nagad", _("Nagad")),
    ]
    PAYMENT_STATUS_CHOICES = [("unpaid", _("Unpaid")), ("pending", _("Verifying")), ("paid", _("Paid")),
                              ("refunded", _("Refunded"))]
    AREA_CHOICES = [("inside", _("Inside Dhaka")), ("outside", _("Outside Dhaka"))]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                             related_name="orders")

    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    division = models.CharField(max_length=30, choices=DIVISION_CHOICES, default="Dhaka")
    city = models.CharField(max_length=60)
    area = models.CharField(max_length=100)
    address_line = models.CharField(max_length=255)
    delivery_area = models.CharField(max_length=10, choices=AREA_CHOICES, default="inside")
    note = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)

    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default="cod")
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default="unpaid")
    transaction_id = models.CharField(max_length=60, blank=True)
    sender_number = models.CharField(max_length=20, blank=True)

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_number

    @staticmethod
    def generate_number():
        while True:
            num = "SB" + timezone.now().strftime("%y%m%d") + "".join(random.choices(string.digits, k=4))
            if not Order.objects.filter(order_number=num).exists():
                return num

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_number()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("orders:detail", args=[self.order_number])

    @property
    def can_cancel(self):
        return self.status in ("pending", "confirmed")

    @property
    def progress_steps(self):
        steps = ["pending", "confirmed", "processing", "shipped", "delivered"]
        current = steps.index(self.status) if self.status in steps else -1
        return [(s, dict(self.STATUS_CHOICES)[s], i <= current) for i, s in enumerate(steps)]

    def restock(self):
        for item in self.items.select_related("product"):
            if item.product:
                item.product.stock += item.quantity
                item.product.sold_count = max(0, item.product.sold_count - item.quantity)
                item.product.save(update_fields=["stock", "sold_count"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("store.Product", null=True, on_delete=models.SET_NULL, related_name="order_items")
    product_name = models.CharField(max_length=200)
    variation = models.CharField(max_length=200, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    @property
    def line_total(self):
        return self.price * self.quantity


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="history")
    status = models.CharField(max_length=15, choices=Order.STATUS_CHOICES)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "Order status history"

    def __str__(self):
        return f"{self.order} → {self.status}"
