"""
Shop (offline) sales and multi-branch management.

  Branch         – a physical shop (e.g. Dhanmondi, Uttara)
  BranchStaff    – which user works in which branch, and as manager or cashier
  BranchStock    – how many pieces of a product a branch has on its shelf
  Sale/SaleItem  – one counter sale (= one printed receipt)
  StockTransfer  – move stock between the online warehouse and branches

The online shop keeps using Product.stock ("Online stock").
"""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Branch(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True,
                            help_text="ছোট কোড, রশিদ নম্বরে ব্যবহার হয় (যেমন DHN, UTT)")
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    receipt_footer = models.CharField(max_length=255, blank=True,
                                      default="Thank you for shopping with us! Goods sold can be exchanged within 7 days with receipt.")
    sell_without_stock = models.BooleanField(
        default=False, help_text="টিক দিলে শাখায় স্টক না থাকলেও বিক্রি করা যাবে (স্টক মাইনাসে যাবে না, ০ থাকবে)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Branches"

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        self.code = self.code.upper().strip()
        super().save(*args, **kwargs)

    def stock_of(self, product):
        row = BranchStock.objects.filter(branch=self, product=product).first()
        return row.quantity if row else 0


class BranchStaff(models.Model):
    ROLE_CHOICES = [("manager", _("Manager")), ("cashier", _("Cashier"))]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="branch_staff")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="staff")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="cashier")
    can_give_discount = models.BooleanField(default=True)
    max_discount_percent = models.PositiveSmallIntegerField(default=10, help_text="ক্যাশিয়ার সর্বোচ্চ কত % ছাড় দিতে পারবে")

    class Meta:
        verbose_name = "Branch staff"
        verbose_name_plural = "Branch staff"

    def __str__(self):
        return f"{self.user} @ {self.branch} ({self.get_role_display()})"


class BranchStock(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="stocks")
    product = models.ForeignKey("store.Product", on_delete=models.CASCADE, related_name="branch_stocks")
    quantity = models.PositiveIntegerField(default=0)
    low_stock_alert = models.PositiveIntegerField(default=5)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("branch", "product")
        ordering = ["branch", "product__name"]
        verbose_name = "Branch stock"
        verbose_name_plural = "Branch stock"

    def __str__(self):
        return f"{self.product} @ {self.branch.code}: {self.quantity}"

    @property
    def is_low(self):
        return self.quantity <= self.low_stock_alert


class Sale(models.Model):
    PAYMENT_CHOICES = [
        ("cash", _("Cash")),
        ("card", _("Card")),
        ("bkash", _("bKash")),
        ("nagad", _("Nagad")),
    ]
    STATUS_CHOICES = [("completed", _("Completed")), ("returned", _("Returned"))]

    number = models.CharField(max_length=30, unique=True, editable=False)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="sales")
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                related_name="pos_sales")
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    change_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default="cash")
    transaction_id = models.CharField(max_length=60, blank=True)
    note = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="completed")
    returned_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="+")
    returned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Shop sale"
        verbose_name_plural = "Shop sales (POS)"

    def __str__(self):
        return self.number

    def get_absolute_url(self):
        return reverse("pos:receipt", args=[self.number])

    @property
    def item_count(self):
        return sum(i.quantity for i in self.items.all())

    @staticmethod
    def next_number(branch):
        day = timezone.localdate()
        prefix = f"{branch.code}-{day:%y%m%d}-"
        last = Sale.objects.filter(number__startswith=prefix).order_by("-number").values_list("number", flat=True).first()
        seq = int(last.rsplit("-", 1)[1]) + 1 if last else 1
        return f"{prefix}{seq:04d}"

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = Sale.next_number(self.branch)
        super().save(*args, **kwargs)

    @transaction.atomic
    def mark_returned(self, user):
        """Customer returned everything: put the stock back on the branch shelf."""
        if self.status == "returned":
            return
        for item in self.items.select_related("product"):
            if item.product_id:
                stock, _created = BranchStock.objects.get_or_create(branch=self.branch, product_id=item.product_id)
                BranchStock.objects.filter(pk=stock.pk).update(quantity=F("quantity") + item.quantity)
        self.status = "returned"
        self.returned_by = user
        self.returned_at = timezone.now()
        self.save(update_fields=["status", "returned_by", "returned_at"])


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("store.Product", null=True, on_delete=models.SET_NULL, related_name="pos_items")
    product_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, blank=True)
    variation = models.CharField(max_length=200, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class StockTransfer(models.Model):
    """Leave a branch empty to mean the ONLINE stock (Product.stock)."""
    from_branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.PROTECT, related_name="transfers_out",
                                    help_text="খালি রাখলে = অনলাইন স্টক থেকে")
    to_branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.PROTECT, related_name="transfers_in",
                                  help_text="খালি রাখলে = অনলাইন স্টকে")
    product = models.ForeignKey("store.Product", on_delete=models.CASCADE, related_name="stock_transfers")
    quantity = models.PositiveIntegerField()
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        src = self.from_branch.code if self.from_branch else "ONLINE"
        dst = self.to_branch.code if self.to_branch else "ONLINE"
        return f"{self.product} x{self.quantity}: {src} → {dst}"

    def clean(self):
        if self.from_branch_id == self.to_branch_id:
            raise ValidationError("From and To cannot be the same.")
        if not self.quantity:
            raise ValidationError("Quantity must be at least 1.")
        if self.pk is None and self.product_id:
            available = (self.from_branch.stock_of(self.product) if self.from_branch_id else self.product.stock)
            if available < self.quantity:
                raise ValidationError(f"Only {available} pcs available at the source.")

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if not is_new:
            return  # a transfer is applied only once
        from store.models import Product
        if self.from_branch_id:
            row, _c = BranchStock.objects.get_or_create(branch_id=self.from_branch_id, product_id=self.product_id)
            BranchStock.objects.filter(pk=row.pk).update(quantity=F("quantity") - self.quantity)
        else:
            Product.objects.filter(pk=self.product_id).update(stock=F("stock") - self.quantity)
        if self.to_branch_id:
            row, _c = BranchStock.objects.get_or_create(branch_id=self.to_branch_id, product_id=self.product_id)
            BranchStock.objects.filter(pk=row.pk).update(quantity=F("quantity") + self.quantity)
        else:
            Product.objects.filter(pk=self.product_id).update(stock=F("stock") + self.quantity)
