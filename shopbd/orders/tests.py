"""Run with:  python manage.py test"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import SiteSetting
from store.models import Category, Product, Variation

from .models import Coupon, Order


class ShopFlowTests(TestCase):
    def setUp(self):
        SiteSetting.load()
        self.cat = Category.objects.create(name="Electronics")
        self.p = Product.objects.create(name="Test Phone", category=self.cat, price=Decimal("1000"),
                                        discount_price=Decimal("900"), stock=5, image="products/x.jpg")
        self.shirt = Product.objects.create(name="Shirt", category=self.cat, price=Decimal("500"),
                                            stock=10, image="products/y.jpg")
        self.size_l = Variation.objects.create(product=self.shirt, kind="size", value="L", extra_price=Decimal("50"))
        self.color = Variation.objects.create(product=self.shirt, kind="color", value="Red")
        self.user = User.objects.create_user("u1", "u1@example.com", "pass12345")

    def test_pages_load(self):
        for url in [reverse("core:home"), reverse("store:product_list"), reverse("store:category", args=[self.cat.slug]),
                    self.p.get_absolute_url(), reverse("cart:detail"), reverse("accounts:login"),
                    reverse("accounts:register"), reverse("orders:track"), reverse("core:contact"),
                    reverse("store:product_list") + "?q=phone&sort=price_low&min_price=100&max_price=2000"]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_add_to_cart_and_checkout_cod(self):
        self.client.post(reverse("cart:add", args=[self.p.id]), {"quantity": 2})
        r = self.client.post(reverse("orders:checkout"), {
            "full_name": "Karim", "phone": "01711111111", "email": "", "division": "Dhaka", "city": "Dhaka",
            "area": "Mirpur", "address_line": "Road 1", "delivery_area": "inside", "payment_method": "cod"})
        order = Order.objects.get()
        self.assertRedirects(r, reverse("orders:success", args=[order.order_number]))
        self.assertEqual(order.subtotal, Decimal("1800"))
        self.assertEqual(order.shipping_cost, Decimal("60"))
        self.assertEqual(order.total, Decimal("1860"))
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 3)
        # guest can view own order
        self.assertEqual(self.client.get(order.get_absolute_url()).status_code, 200)
        # cancel restores stock
        self.client.post(reverse("orders:cancel", args=[order.order_number]))
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 5)

    def test_variation_required_and_price(self):
        r = self.client.post(reverse("cart:add", args=[self.shirt.id]), {"quantity": 1})
        self.assertEqual(len(self.client.session.get("cart", {})), 0)
        self.client.post(reverse("cart:add", args=[self.shirt.id]),
                         {"quantity": 1, "variation_size": self.size_l.id, "variation_color": self.color.id})
        r = self.client.get(reverse("cart:detail"))
        self.assertContains(r, "৳550")

    def test_coupon_and_mobile_payment(self):
        Coupon.objects.create(code="SAVE10", value=Decimal("10"), valid_to=timezone.now() + timedelta(days=1))
        self.client.post(reverse("cart:add", args=[self.p.id]), {"quantity": 1})
        self.client.post(reverse("cart:apply_coupon"), {"code": "save10"})
        data = {"full_name": "Karim", "phone": "01711111111", "division": "Khulna", "city": "Khulna",
                "area": "Sonadanga", "address_line": "Road 2", "delivery_area": "outside", "payment_method": "bkash"}
        r = self.client.post(reverse("orders:checkout"), data)
        self.assertEqual(r.status_code, 200)  # missing transaction id
        data.update(transaction_id="ABC123", sender_number="01811111111")
        self.client.post(reverse("orders:checkout"), data)
        order = Order.objects.get()
        self.assertEqual(order.discount, Decimal("90"))
        self.assertEqual(order.total, Decimal("900") - Decimal("90") + Decimal("120"))
        self.assertEqual(order.payment_status, "pending")
        self.assertEqual(Coupon.objects.get().used_count, 1)

    def test_cannot_oversell(self):
        self.client.post(reverse("cart:add", args=[self.p.id]), {"quantity": 50})
        cart = self.client.session["cart"]
        self.assertEqual(list(cart.values())[0]["quantity"], 5)

    def test_order_privacy(self):
        self.client.post(reverse("cart:add", args=[self.p.id]), {"quantity": 1})
        self.client.post(reverse("orders:checkout"), {
            "full_name": "Karim", "phone": "01711111111", "division": "Dhaka", "city": "Dhaka",
            "area": "Mirpur", "address_line": "Road 1", "delivery_area": "inside", "payment_method": "cod"})
        order = Order.objects.get()
        other = self.client_class()
        self.assertEqual(other.get(order.get_absolute_url()).status_code, 404)
        r = other.get(reverse("orders:track"), {"order_number": order.order_number, "phone": "01711111111"})
        self.assertContains(r, order.order_number)

    def test_register_login_wishlist(self):
        r = self.client.post(reverse("accounts:register"), {
            "first_name": "New User", "username": "newuser", "email": "new@example.com", "phone": "01999999999",
            "password1": "StrongPass!234", "password2": "StrongPass!234"})
        self.assertRedirects(r, reverse("accounts:dashboard"))
        self.client.logout()
        self.assertTrue(self.client.login(username="new@example.com", password="StrongPass!234"))
        r = self.client.post(reverse("store:wishlist_toggle", args=[self.p.id]), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertTrue(r.json()["added"])
        self.assertContains(self.client.get(reverse("store:wishlist")), "Test Phone")

    def test_staff_dashboard(self):
        admin = User.objects.create_superuser("boss", "b@example.com", "pass12345")
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse("core:staff_dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:orders_order_changelist")).status_code, 200)


class LanguageAndThemeTests(TestCase):
    def setUp(self):
        from core.models import ThemeSetting
        SiteSetting.load()
        ThemeSetting.load()
        self.cat = Category.objects.create(name="Electronics")
        self.cat.translations.create(language="bn", name="ইলেকট্রনিক্স")
        self.p = Product.objects.create(name="Test Phone", category=self.cat, price=Decimal("1000"),
                                        stock=5, image="products/x.jpg")
        self.p.translations.create(language="bn", name="টেস্ট ফোন")

    def test_switch_language(self):
        r = self.client.post(reverse("set_language"), {"language": "bn", "next": "/"})
        self.assertEqual(r.status_code, 302)
        r = self.client.get("/")
        self.assertContains(r, 'lang="bn"')
        self.assertContains(r, "কার্টে যোগ করুন")      # fixed text
        self.assertContains(r, "টেস্ট ফোন")          # product name from Admin translation
        self.assertContains(r, "ইলেকট্রনিক্স")        # category translation
        self.assertContains(r, "৳১,০০০")              # Bangla digits

    def test_rtl_and_fallback(self):
        self.client.post(reverse("set_language"), {"language": "ar", "next": "/"})
        r = self.client.get(self.p.get_absolute_url())
        self.assertContains(r, 'dir="rtl"')
        self.assertContains(r, "Test Phone")          # no Arabic translation → English shown
        self.assertContains(r, "أضف إلى السلة")

    def test_all_languages_render(self):
        self.client.post(reverse("cart:add", args=[self.p.id]), {"quantity": 1})
        for code in ("en", "bn", "hi", "ur", "ar"):
            self.client.post(reverse("set_language"), {"language": code, "next": "/"})
            for url in ["/", "/products/", self.p.get_absolute_url(), "/cart/", "/orders/checkout/",
                        "/accounts/login/", "/accounts/register/", "/orders/track/", "/contact/"]:
                self.assertEqual(self.client.get(url).status_code, 200, (code, url))

    def test_theme_colors_applied(self):
        from core.models import ThemeSetting
        t = ThemeSetting.load()
        t.primary_color = "#12a150"
        t.save()
        r = self.client.get("/")
        self.assertContains(r, "--primary:#12a150")
        self.assertContains(r, "--on-primary:")

    def test_theme_admin_page(self):
        admin = User.objects.create_superuser("boss", "b@example.com", "pass12345")
        self.client.force_login(admin)
        r = self.client.get(reverse("admin:core_themesetting_changelist"), follow=True)
        self.assertContains(r, "Live preview")
        self.assertContains(r, "preset-swatches")


class AppSupportTests(TestCase):
    def test_pwa_endpoints(self):
        r = self.client.get("/manifest.json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["display"], "standalone")
        r = self.client.get("/sw.js")
        self.assertEqual(r["Service-Worker-Allowed"], "/")
        self.assertEqual(self.client.get("/offline/").status_code, 200)
        self.assertEqual(self.client.get("/.well-known/assetlinks.json").json(), [])

    def test_assetlinks_configured(self):
        with self.settings(ANDROID_PACKAGE_NAME="com.shop.app", ANDROID_SHA256_FINGERPRINTS=["AA:BB"]):
            data = self.client.get("/.well-known/assetlinks.json").json()
            self.assertEqual(data[0]["target"]["package_name"], "com.shop.app")

    def test_category_dropdown_markup(self):
        SiteSetting.load()
        parent = Category.objects.create(name="Fashion")
        Category.objects.create(name="Shoes", parent=parent)
        r = self.client.get("/")
        self.assertContains(r, 'class="sub-toggle"')
        self.assertContains(r, "Shoes")
