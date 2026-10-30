"""
Demo data loader:  python manage.py seed_demo
Creates categories, brands, products (with generated images), banners, pages,
a coupon, an admin user and a demo customer. Safe to run more than once.
"""
import io
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from core.models import (Banner, BannerTranslation, Page, PageTranslation, SiteSetting, SiteSettingTranslation,
                         ThemeSetting)
from orders.models import Coupon
from store.models import Brand, Category, CategoryTranslation, Product, ProductTranslation, Variation

from . import _demo_translations as DT

PALETTE = ["#f85606", "#1c7ed6", "#12a150", "#7048e8", "#e64980", "#f59f00", "#0ca678", "#1a2b49", "#d6336c", "#4263eb"]

CATALOG = {
    ("Electronics", "fa-mobile-screen"): {
        "Mobile Phones": [("Galaxy A55 5G (8/256GB)", 45999, 42999, "Samsung"), ("Redmi Note 13 Pro", 32999, 29499, "Xiaomi"),
                          ("iPhone 15 (128GB)", 124999, None, "Apple"), ("Realme 12 Pro+", 39999, 36999, "Realme")],
        "Laptops": [("IdeaPad Slim 3 Ryzen 5", 64999, 59999, "Lenovo"), ("MacBook Air M2 13\"", 139999, 131999, "Apple"),
                    ("VivoBook 15 Core i5", 69999, None, "Asus")],
        "Accessories": [("Wireless Earbuds Pro", 3499, 2299, "Xiaomi"), ("20000mAh Power Bank", 2800, 2199, "Xiaomi"),
                        ("Smart Watch Series 8", 5500, 3999, "Samsung"), ("USB-C Fast Charger 65W", 1990, 1490, "Realme")],
    },
    ("Men's Fashion", "fa-shirt"): {
        "T-Shirts": [("Premium Cotton T-Shirt", 650, 450, "Yellow"), ("Graphic Print Tee", 750, 550, "Yellow")],
        "Panjabi": [("Eid Special Cotton Panjabi", 2450, 1890, "Aarong"), ("Embroidered Silk Panjabi", 3950, None, "Aarong")],
        "Shoes": [("Casual Leather Loafer", 3200, 2690, "Bata"), ("Running Sneakers", 2800, 2290, "Apex")],
    },
    ("Women's Fashion", "fa-person-dress"): {
        "Saree": [("Jamdani Saree", 6500, 5800, "Aarong"), ("Printed Georgette Saree", 2900, 2190, "Aarong")],
        "Three Piece": [("Lawn Three Piece", 2400, 1750, "Yellow"), ("Embroidered Cotton Kameez", 2800, None, "Yellow")],
        "Bags": [("Ladies Hand Bag", 1850, 1390, "Apex")],
    },
    ("Home & Living", "fa-couch"): {
        "Kitchen": [("Non-stick Fry Pan 26cm", 1650, 1290, "Miyako"), ("Electric Kettle 1.8L", 1450, 1090, "Miyako"),
                    ("Rice Cooker 2.8L", 3200, 2850, "Walton")],
        "Home Decor": [("Wall Clock Wooden", 1200, 890, "Hatil"), ("LED Table Lamp", 950, None, "Walton")],
    },
    ("Health & Beauty", "fa-spa"): {
        "Skin Care": [("Vitamin C Face Serum 30ml", 1200, 850, "Garnier"), ("Sunscreen SPF 50", 950, 790, "Garnier")],
        "Hair Care": [("Herbal Hair Oil 200ml", 450, 380, "Parachute")],
    },
    ("Groceries", "fa-basket-shopping"): {
        "Rice & Oil": [("Miniket Rice 5kg", 450, 425, "ACI"), ("Soybean Oil 5L", 890, 860, "Teer")],
        "Snacks": [("Chanachur 350g", 120, None, "Pran"), ("Chocolate Cookies Pack", 180, 150, "Olympic")],
    },
    ("Sports & Outdoor", "fa-futbol"): {
        "Fitness": [("Yoga Mat 6mm", 1200, 890, "Decathlon"), ("Adjustable Dumbbell Set", 4500, 3990, "Decathlon")],
        "Cricket": [("English Willow Cricket Bat", 6500, 5600, "SG")],
    },
    ("Kids & Toys", "fa-puzzle-piece"): {
        "Toys": [("Remote Control Car", 2200, 1650, "Toyzone"), ("Building Blocks 300pcs", 1500, 1190, "Toyzone")],
    },
}


def font(size):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_image(text, color, size=(800, 800), sub=""):
    """Create a simple gradient image with text (placeholder product photo)."""
    w, h = size
    img = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(img)
    base = Image.new("RGB", size, "#ffffff")
    mask = Image.linear_gradient("L").resize(size)
    img = Image.composite(img, base, mask.point(lambda p: int(p * 0.85)))
    draw = ImageDraw.Draw(img)
    draw.ellipse((w * 0.55, -h * 0.15, w * 1.2, h * 0.5), fill=(255, 255, 255))
    words, lines, line = text.split(), [], ""
    f = font(int(min(w, h) / 11))
    for word in words:
        test = (line + " " + word).strip()
        if draw.textlength(test, font=f) > w * 0.8 and line:
            lines.append(line)
            line = word
        else:
            line = test
    lines.append(line)
    y = h / 2 - len(lines) * f.size * 0.65
    for ln in lines:
        tw = draw.textlength(ln, font=f)
        draw.text(((w - tw) / 2, y), ln, font=f, fill="#1f2430")
        y += f.size * 1.25
    if sub:
        fs = font(int(min(w, h) / 22))
        tw = draw.textlength(sub, font=fs)
        draw.text(((w - tw) / 2, y + 10), sub, font=fs, fill="#555")
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return ContentFile(buf.getvalue())


class Command(BaseCommand):
    help = "Load demo data for ShopBD"

    def add_arguments(self, parser):
        parser.add_argument("--no-users", action="store_true", help="Do not create demo users")

    def handle(self, *args, **opts):
        site = SiteSetting.load()
        site.facebook = site.facebook or "https://facebook.com/"
        site.save()

        if not opts["no_users"]:
            if not User.objects.filter(username="admin").exists():
                User.objects.create_superuser("admin", "admin@example.com", "admin12345", first_name="Admin")
                self.stdout.write(self.style.SUCCESS("Admin user → admin / admin12345"))
            if not User.objects.filter(username="customer").exists():
                u = User.objects.create_user("customer", "customer@example.com", "customer12345", first_name="Rahim Uddin")
                u.profile.phone = "01712345678"
                u.profile.save()
                u.addresses.create(full_name="Rahim Uddin", phone="01712345678", division="Dhaka", city="Dhaka",
                                   area="Dhanmondi", address_line="House 12, Road 5", is_default=True)
                self.stdout.write(self.style.SUCCESS("Demo customer → customer / customer12345"))

        pages = {
            "about-us": ("About Us", "<p>We are a Bangladeshi online marketplace delivering authentic products all over the country.</p>"),
            "privacy-policy": ("Privacy Policy", "<p>We respect your privacy. Your personal data is only used to process your orders.</p>"),
            "terms-and-conditions": ("Terms & Conditions", "<p>By using this website you agree to our terms.</p>"),
            "return-policy": ("Return & Refund Policy", "<p>You can return a product within 7 days of delivery if it is damaged or wrong.</p>"),
        }
        for slug, (title, content) in pages.items():
            Page.objects.get_or_create(slug=slug, defaults={"title": title, "content": content})

        brands = {}
        n_products = 0
        for ci, ((cat_name, icon), subs) in enumerate(CATALOG.items()):
            cat, _ = Category.objects.get_or_create(name=cat_name, parent=None, defaults={"icon": icon, "order": ci})
            for si, (sub_name, items) in enumerate(subs.items()):
                sub, _ = Category.objects.get_or_create(name=sub_name, parent=cat, defaults={"order": si})
                for name, price, sale, brand_name in items:
                    if brand_name not in brands:
                        brands[brand_name], _ = Brand.objects.get_or_create(name=brand_name)
                    if Product.objects.filter(name=name).exists():
                        continue
                    color = random.choice(PALETTE)
                    p = Product(
                        name=name, category=sub, brand=brands[brand_name],
                        sku=f"SB-{random.randint(10000, 99999)}",
                        short_description=f"Original {brand_name} {name} with warranty and fast delivery.",
                        description=(f"<p><strong>{name}</strong> from {brand_name}. 100% authentic product "
                                     "sourced directly from the brand.</p><ul><li>Fast delivery all over Bangladesh</li>"
                                     "<li>Cash on delivery available</li><li>7 days easy return</li></ul>"),
                        specification=f"Brand: {brand_name}\nCategory: {sub_name}\nWarranty: 6 months\nOrigin: Bangladesh",
                        price=Decimal(price), discount_price=Decimal(sale) if sale else None,
                        stock=random.choice([0, 3, 8, 15, 25, 40, 60]) if n_products % 9 == 8 else random.randint(6, 60),
                        is_featured=random.random() < 0.4, is_flash_sale=bool(sale) and random.random() < 0.45,
                        sold_count=random.randint(0, 250),
                    )
                    p.image.save(f"{sub.slug}-{n_products}.jpg", make_image(name, color, sub=brand_name), save=False)
                    p.save()
                    for k in range(2):
                        p.images.create(image=ContentFile(make_image(name, random.choice(PALETTE)).read(),
                                                          name=f"{sub.slug}-{n_products}-{k}.jpg"))
                    if sub_name in ("T-Shirts", "Panjabi", "Shoes", "Three Piece"):
                        sizes = ["39", "40", "41", "42"] if sub_name == "Shoes" else ["M", "L", "XL", "XXL"]
                        for s in sizes:
                            Variation.objects.create(product=p, kind="size", value=s,
                                                     extra_price=Decimal("50") if s in ("XXL", "42") else Decimal("0"))
                        for c in ("Black", "White", "Blue"):
                            Variation.objects.create(product=p, kind="color", value=c)
                    if sub_name == "Mobile Phones":
                        for c in ("Black", "Blue"):
                            Variation.objects.create(product=p, kind="color", value=c)
                    n_products += 1

        if not Banner.objects.exists():
            banners = [
                ("Mega Shopping Fest", "Up to 60% OFF on electronics", "#f85606", "slider", "/category/electronics/"),
                ("Eid Collection 2026", "New Panjabi & Saree arrivals", "#7048e8", "slider", "/category/mens-fashion/"),
                ("Free Delivery", "On all orders over ৳2000", "#12a150", "slider", "/products/"),
                ("Flash Sale", "Limited time deals", "#e64980", "side", "/products/?filter=flash"),
                ("New Arrivals", "Fresh every week", "#1c7ed6", "side", "/products/?filter=new"),
                ("Groceries", "Daily needs delivered", "#0ca678", "middle", "/category/groceries/"),
                ("Home & Living", "Make your home beautiful", "#f59f00", "middle", "/category/home-living/"),
                ("Beauty Week", "Top brands, best price", "#d6336c", "middle", "/category/health-beauty/"),
            ]
            for i, (title, sub, color, pos, link) in enumerate(banners):
                size = (1400, 560) if pos == "slider" else (700, 400) if pos == "side" else (800, 300)
                b = Banner(title=title, subtitle=sub, position=pos, link=link, order=i)
                # no text inside the picture — the title is shown on top in the visitor's language
                b.image.save(f"banner-{i}.jpg", make_image(" ", color, size=size), save=True)

        Coupon.objects.get_or_create(code="WELCOME10", defaults={
            "discount_type": "percent", "value": Decimal("10"), "max_discount": Decimal("500"),
            "min_order_amount": Decimal("500"), "valid_to": timezone.now() + timedelta(days=365)})
        Coupon.objects.get_or_create(code="FLAT200", defaults={
            "discount_type": "fixed", "value": Decimal("200"), "min_order_amount": Decimal("2000"),
            "valid_to": timezone.now() + timedelta(days=365)})

        ThemeSetting.load()
        self.add_branches(create_users=not opts["no_users"])
        self.add_translations()

        self.stdout.write(self.style.SUCCESS(f"Demo data ready: {Product.objects.count()} products, "
                                             f"{Category.objects.count()} categories. Coupons: WELCOME10, FLAT200"))

    def add_translations(self):
        """Bangla / Hindi / Urdu / Arabic text for the demo content (safe to run again)."""
        site = SiteSetting.load()
        for lang, (tagline, notice, footer) in zip(DT.LANGS, DT.SITE):
            SiteSettingTranslation.objects.update_or_create(
                site=site, language=lang, defaults={"tagline": tagline, "top_notice": notice, "footer_text": footer})

        for cat in Category.objects.all():
            names = DT.CATEGORIES.get(cat.name)
            if names:
                for lang, name in zip(DT.LANGS, names):
                    CategoryTranslation.objects.update_or_create(category=cat, language=lang, defaults={"name": name})

        for banner in Banner.objects.all():
            data = DT.BANNERS.get(banner.title)
            if not data:
                continue
            for lang, (title, sub, button) in zip(DT.LANGS, data):
                BannerTranslation.objects.update_or_create(
                    banner=banner, language=lang, defaults={"title": title, "subtitle": sub, "button_text": button})
            # older demo banners had English text drawn inside the picture; redraw them plain
            if banner.position != "slider" and not banner.image.name.endswith("-plain.jpg"):
                color = random.choice(PALETTE)
                size = (700, 400) if banner.position == "side" else (800, 300)
                banner.image.save(f"banner-{banner.pk}-plain.jpg", make_image(" ", color, size=size), save=True)

        for page in Page.objects.all():
            data = DT.PAGES.get(page.slug)
            if data:
                for lang, (title, content) in zip(DT.LANGS, data):
                    PageTranslation.objects.update_or_create(page=page, language=lang,
                                                             defaults={"title": title, "content": content})

        for product in Product.objects.all():
            names = DT.PRODUCTS.get(product.name)
            if not names:
                continue
            brand = product.brand.name if product.brand else ""
            for i, (lang, name) in enumerate(zip(("bn", "hi"), names)):
                category = DT.CATEGORIES.get(product.category.name, (product.category.name,) * 4)[i]
                ProductTranslation.objects.update_or_create(
                    product=product, language=lang,
                    defaults={"name": name,
                              "short_description": DT.PRODUCT_SHORT[i].format(brand=brand, name=name),
                              "description": DT.PRODUCT_DESC[i].format(name=name),
                              "specification": DT.PRODUCT_SPEC[i].format(brand=brand, category=category)})
        self.stdout.write(self.style.SUCCESS("Translations added for categories, banners, pages and products."))

    def add_branches(self, create_users=True):
        """Two demo shops with stock, staff and two weeks of counter sales."""
        from pos.models import Branch, BranchStaff, BranchStock, Sale, SaleItem

        dhn, _c = Branch.objects.get_or_create(code="DHN", defaults={
            "name": "Dhanmondi Branch", "address": "House 12, Road 7, Dhanmondi, Dhaka", "phone": "+880 1700-000001"})
        utt, _c = Branch.objects.get_or_create(code="UTT", defaults={
            "name": "Uttara Branch", "address": "Sector 7, Uttara, Dhaka", "phone": "+880 1700-000002"})
        products = list(Product.objects.all())
        for branch in (dhn, utt):
            for p in products:
                BranchStock.objects.get_or_create(branch=branch, product=p,
                                                  defaults={"quantity": random.choice([0, 2, 4, 8, 12, 20, 30])})

        if create_users:
            for username, pwd, branch, role, name in (("manager1", "manager12345", dhn, "manager", "Karim (Manager)"),
                                                       ("cashier1", "cashier12345", utt, "cashier", "Sumi (Cashier)")):
                if not User.objects.filter(username=username).exists():
                    u = User.objects.create_user(username, f"{username}@example.com", pwd, first_name=name)
                    BranchStaff.objects.create(user=u, branch=branch, role=role)
                    self.stdout.write(self.style.SUCCESS(f"Branch {role} → {username} / {pwd} ({branch.name})"))

        if Sale.objects.exists() or not products:
            return
        cashier = User.objects.filter(username="manager1").first()
        rng = random.Random(7)
        for days_ago in range(13, -1, -1):
            for branch in (dhn, utt):
                for _n in range(rng.randint(2, 6)):
                    when = timezone.now() - timedelta(days=days_ago, hours=rng.randint(0, 8), minutes=rng.randint(0, 59))
                    picked = rng.sample(products, rng.randint(1, 3))
                    lines = [(p, rng.randint(1, 2)) for p in picked]
                    subtotal = sum(p.final_price * q for p, q in lines)
                    discount = (subtotal * Decimal("0.05")).quantize(Decimal("1")) if rng.random() < .25 else Decimal("0")
                    total = subtotal - discount
                    method = rng.choice(["cash", "cash", "cash", "bkash", "card", "nagad"])
                    paid = (total / 100).to_integral_value(rounding="ROUND_CEILING") * 100 if method == "cash" else total
                    sale = Sale(branch=branch, cashier=cashier, subtotal=subtotal, discount=discount, total=total,
                                paid_amount=paid, change_amount=paid - total, payment_method=method)
                    sale.number = f"{branch.code}-{timezone.localtime(when):%y%m%d}-{Sale.objects.filter(branch=branch).count() + 1:04d}"
                    sale.created_at = when
                    sale.save()
                    SaleItem.objects.bulk_create([SaleItem(sale=sale, product=p, product_name=p.name, sku=p.sku,
                                                           unit_price=p.final_price, quantity=q) for p, q in lines])
        self.stdout.write(self.style.SUCCESS("Demo branches ready: Dhanmondi (DHN), Uttara (UTT) with 2 weeks of sales."))
