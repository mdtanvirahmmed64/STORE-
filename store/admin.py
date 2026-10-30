from django.contrib import admin
from django.utils.html import format_html

from pos.models import BranchStock

from .models import (Brand, Category, CategoryTranslation, Product, ProductImage, ProductTranslation, Review,
                     Variation, Wishlist)


def thumb(img, size=50):
    if img:
        return format_html('<img src="{}" style="width:{}px;height:{}px;object-fit:cover;border-radius:6px">',
                           img.url, size, size)
    return "-"


class CategoryTranslationInline(admin.TabularInline):
    model = CategoryTranslation
    extra = 0
    verbose_name_plural = "Translations (leave empty to show English)"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = [CategoryTranslationInline]
    list_display = ("name", "parent", "order", "is_active", "show_on_home", "product_count")
    list_editable = ("order", "is_active", "show_on_home")
    list_filter = ("is_active", "parent")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Products")
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_editable = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductTranslationInline(admin.StackedInline):
    model = ProductTranslation
    extra = 0
    classes = ("collapse",)
    verbose_name_plural = "Translations (Bangla / Hindi / Urdu / Arabic) — leave empty to show English"


class BranchStockInline(admin.TabularInline):
    model = BranchStock
    extra = 0
    fields = ("branch", "quantity", "low_stock_alert")
    verbose_name_plural = "Shop / branch stock (online stock is the 'Stock' field above)"


class VariationInline(admin.TabularInline):
    model = Variation
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("image_tag", "name", "category", "price", "discount_price", "stock", "shop_stock",
                    "is_active", "is_featured", "is_flash_sale", "sold_count")
    list_display_links = ("image_tag", "name")
    list_editable = ("price", "discount_price", "stock", "is_active", "is_featured", "is_flash_sale")
    list_filter = ("is_active", "is_featured", "is_flash_sale", "category", "brand")
    search_fields = ("name", "sku", "short_description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("rating", "review_count", "views", "created_at", "updated_at")
    inlines = [ProductImageInline, VariationInline, BranchStockInline, ProductTranslationInline]
    list_per_page = 30
    actions = ["make_active", "make_inactive"]
    fieldsets = (
        ("Basic info", {"fields": ("name", "slug", "sku", "category", "brand", "image")}),
        ("Price & stock", {"fields": ("price", "discount_price", "stock"),
                           "description": "Stock = online stock. Shop/branch stock is further below."}),
        ("Description", {"fields": ("short_description", "description", "specification")}),
        ("Visibility", {"fields": ("is_active", "is_featured", "is_flash_sale", "is_new_arrival")}),
        ("Stats", {"fields": ("rating", "review_count", "sold_count", "views", "created_at", "updated_at"),
                   "classes": ("collapse",)}),
    )

    @admin.display(description="Shop stock")
    def shop_stock(self, obj):
        return sum(b.quantity for b in obj.branch_stocks.all())

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("branch_stocks")

    @admin.display(description="Image")
    def image_tag(self, obj):
        return thumb(obj.image)

    @admin.action(description="Mark selected as active")
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Mark selected as inactive")
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "is_approved", "created_at")
    list_filter = ("is_approved", "rating")
    list_editable = ("is_approved",)
    search_fields = ("product__name", "user__username", "comment")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.product.update_rating()


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
