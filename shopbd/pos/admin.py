from django.contrib import admin, messages
from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.html import format_html

from .models import Branch, BranchStaff, BranchStock, Sale, SaleItem, StockTransfer


class BranchStaffInline(admin.TabularInline):
    model = BranchStaff
    extra = 0
    autocomplete_fields = ["user"]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "phone", "is_active", "today_sales", "open_pos")
    list_editable = ("is_active",)
    search_fields = ("name", "code")
    inlines = [BranchStaffInline]

    @admin.display(description="Today's sales")
    def today_sales(self, obj):
        agg = obj.sales.filter(status="completed", created_at__date=timezone.localdate()).aggregate(
            s=Sum("total"), n=Count("id"))
        return f"৳{(agg['s'] or 0):,.0f} ({agg['n']})"

    @admin.display(description="POS")
    def open_pos(self, obj):
        return format_html('<a class="button" href="/pos/?branch={}" target="_blank">Open POS</a>', obj.pk)


@admin.register(BranchStaff)
class BranchStaffAdmin(admin.ModelAdmin):
    list_display = ("user", "branch", "role", "can_give_discount", "max_discount_percent")
    list_filter = ("branch", "role")
    autocomplete_fields = ["user"]


@admin.register(BranchStock)
class BranchStockAdmin(admin.ModelAdmin):
    list_display = ("product", "branch", "quantity", "low_stock_alert", "status", "updated_at")
    list_editable = ("quantity", "low_stock_alert")
    list_filter = ("branch", "product__category")
    search_fields = ("product__name", "product__sku")
    autocomplete_fields = ["product"]
    list_per_page = 50

    @admin.display(description="Status")
    def status(self, obj):
        if obj.quantity == 0:
            return format_html('<b style="color:#e5383b">{}</b>', "Out of stock")
        if obj.is_low:
            return format_html('<b style="color:#f59f00">{}</b>', "Low")
        return "OK"


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    can_delete = False
    readonly_fields = ("product", "product_name", "sku", "variation", "unit_price", "quantity")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("number", "branch", "created_at", "customer_name", "customer_phone", "total",
                    "payment_method", "cashier", "status", "receipt")
    list_filter = ("branch", "status", "payment_method", "created_at")
    search_fields = ("number", "customer_name", "customer_phone", "transaction_id")
    date_hierarchy = "created_at"
    readonly_fields = ("number", "branch", "cashier", "subtotal", "discount", "total", "paid_amount", "change_amount",
                       "payment_method", "transaction_id", "status", "returned_by", "returned_at", "created_at")
    fields = readonly_fields + ("customer_name", "customer_phone", "note")
    inlines = [SaleItemInline]
    actions = ["mark_returned"]

    def has_add_permission(self, request):
        return False  # sales are made from the POS screen

    @admin.display(description="Receipt")
    def receipt(self, obj):
        return format_html('<a href="{}" target="_blank">🧾 Print</a>', obj.get_absolute_url())

    @admin.action(description="Mark selected sales as RETURNED (stock goes back to the branch)")
    def mark_returned(self, request, queryset):
        n = 0
        for sale in queryset.filter(status="completed"):
            sale.mark_returned(request.user)
            n += 1
        messages.success(request, f"{n} sale(s) returned and stock restored.")


@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = ("created_at", "product", "quantity", "source", "destination", "created_by", "note")
    list_filter = ("from_branch", "to_branch")
    search_fields = ("product__name", "note")
    autocomplete_fields = ["product"]

    def get_readonly_fields(self, request, obj=None):
        # a saved transfer cannot be edited (stock was already moved)
        return ("from_branch", "to_branch", "product", "quantity", "created_by") if obj else ("created_by",)

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="From")
    def source(self, obj):
        return obj.from_branch or "🌐 Online stock"

    @admin.display(description="To")
    def destination(self, obj):
        return obj.to_branch or "🌐 Online stock"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
