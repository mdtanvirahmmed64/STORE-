from django.contrib import admin

from .models import Coupon, Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "variation", "price", "quantity")
    can_delete = False


class HistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("status", "note", "created_at")
    can_delete = False


def set_status(new_status):
    def action(modeladmin, request, queryset):
        for order in queryset:
            modeladmin.change_status(order, new_status, "Updated from admin list")
    action.short_description = f"Mark as {new_status}"
    action.__name__ = f"mark_{new_status}"
    return action


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "full_name", "phone", "total", "payment_method",
                    "payment_status", "status", "created_at")
    list_filter = ("status", "payment_method", "payment_status", "delivery_area", "created_at")
    list_editable = ("payment_status",)
    search_fields = ("order_number", "full_name", "phone", "email", "transaction_id")
    readonly_fields = ("order_number", "user", "subtotal", "discount", "shipping_cost", "total",
                       "coupon", "created_at", "updated_at")
    inlines = [OrderItemInline, HistoryInline]
    date_hierarchy = "created_at"
    actions = [set_status("confirmed"), set_status("processing"), set_status("shipped"),
               set_status("delivered"), set_status("cancelled")]
    fieldsets = (
        ("Order", {"fields": ("order_number", "user", "status", "created_at", "updated_at")}),
        ("Customer & delivery", {"fields": ("full_name", "phone", "email", "division", "city", "area",
                                            "address_line", "delivery_area", "note")}),
        ("Payment", {"fields": ("payment_method", "payment_status", "transaction_id", "sender_number")}),
        ("Amount", {"fields": ("subtotal", "discount", "coupon", "shipping_cost", "total")}),
    )

    @staticmethod
    def change_status(order, new_status, note=""):
        if order.status == new_status:
            return
        old = order.status
        if new_status in ("cancelled", "returned") and old not in ("cancelled", "returned"):
            order.restock()
        order.status = new_status
        if new_status == "delivered" and order.payment_method == "cod":
            order.payment_status = "paid"
        order.save()
        OrderStatusHistory.objects.create(order=order, status=new_status, note=note)

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            new_status = obj.status
            obj.status = Order.objects.get(pk=obj.pk).status
            self.change_status(obj, new_status, f"Changed by {request.user.username}")
        else:
            super().save_model(request, obj, form, change)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "value", "min_order_amount", "valid_to",
                    "used_count", "usage_limit", "is_active")
    list_editable = ("is_active",)
    search_fields = ("code",)
