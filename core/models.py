from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, RegexValidator
from django.db import models

from .translation import TRANSLATION_LANGUAGES, TranslatableMixin

hex_color = RegexValidator(r"^#[0-9a-fA-F]{6}$", "Use a color like #f85606")


class SiteSetting(TranslatableMixin, models.Model):
    """Single row that controls the whole site (edit from Admin)."""
    site_name = models.CharField(max_length=100, default="ShopBD")
    tagline = models.CharField(max_length=200, blank=True, default="Online Shopping in Bangladesh")
    logo = models.ImageField(upload_to="site/", blank=True)
    favicon = models.ImageField(upload_to="site/", blank=True)
    phone = models.CharField(max_length=30, blank=True, default="+880 1700-000000")
    email = models.EmailField(blank=True, default="support@shopbd.com")
    address = models.CharField(max_length=255, blank=True, default="Dhaka, Bangladesh")
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    top_notice = models.CharField(max_length=255, blank=True, default="Free delivery on orders over ৳2000!")
    default_language = models.CharField(
        max_length=10, choices=settings.LANGUAGES, default="en",
        help_text="নতুন ভিজিটর প্রথমে এই ভাষায় সাইট দেখবে (পরে নিজে বদলাতে পারবে)",
    )

    shipping_inside_dhaka = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("60"))
    shipping_outside_dhaka = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("120"))
    free_shipping_over = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("2000"),
        help_text="0 দিলে ফ্রি ডেলিভারি বন্ধ থাকবে",
    )

    bkash_number = models.CharField(max_length=20, blank=True, default="01700000000")
    nagad_number = models.CharField(max_length=20, blank=True, default="01700000000")
    enable_cod = models.BooleanField("Enable Cash on Delivery", default=True)
    enable_bkash = models.BooleanField(default=True)
    enable_nagad = models.BooleanField(default=True)

    footer_text = models.TextField(blank=True, default="Your trusted online shop.")

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1  # always one row
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SiteSettingTranslation(models.Model):
    site = models.ForeignKey(SiteSetting, on_delete=models.CASCADE, related_name="translations")
    language = models.CharField(max_length=10, choices=TRANSLATION_LANGUAGES)
    tagline = models.CharField(max_length=200, blank=True)
    top_notice = models.CharField(max_length=255, blank=True)
    footer_text = models.TextField(blank=True)

    class Meta:
        unique_together = ("site", "language")


class ThemeSetting(models.Model):
    """Website colors — edit from Admin → Theme & Colors."""
    PRESET_CHOICES = [
        ("orange", "Daraz Orange (default)"),
        ("amazon", "Amazon Dark"),
        ("green", "Fresh Green"),
        ("blue", "Ocean Blue"),
        ("purple", "Royal Purple"),
        ("red", "Ruby Red"),
        ("pink", "Rose Pink"),
        ("teal", "Teal"),
        ("black", "Classic Black"),
        ("custom", "Custom"),
    ]
    FONT_CHOICES = [
        ("Inter", "Inter (modern)"),
        ("Poppins", "Poppins (rounded)"),
        ("Roboto", "Roboto (Android style)"),
        ("Hind Siliguri", "Hind Siliguri (Bangla friendly)"),
        ("system", "System default"),
    ]

    preset = models.CharField("Ready-made theme", max_length=20, choices=PRESET_CHOICES, default="orange",
                              help_text="একটি থিম বেছে নিলে নিচের রংগুলো নিজে থেকে বসে যাবে, তারপর ইচ্ছামতো বদলাতে পারবেন")
    primary_color = models.CharField("Main color", max_length=7, default="#f85606", validators=[hex_color],
                                     help_text="বাটন, দাম, লিংক, হাইলাইট")
    header_bg = models.CharField("Header background", max_length=7, default="#f85606", validators=[hex_color])
    header_text = models.CharField("Header text & icons", max_length=7, default="#ffffff", validators=[hex_color])
    secondary_color = models.CharField("Top bar / dark sections", max_length=7, default="#1a2b49",
                                       validators=[hex_color], help_text="উপরের নোটিশ বার, নিউজলেটার, কালো বাটন")
    accent_color = models.CharField("Accent color", max_length=7, default="#ffb400", validators=[hex_color],
                                    help_text="সার্চ বাটন, Buy Now, স্টার রেটিং, কাউন্ট ব্যাজ")
    discount_color = models.CharField("Discount badge", max_length=7, default="#e5383b", validators=[hex_color])
    page_bg = models.CharField("Page background", max_length=7, default="#f4f5f7", validators=[hex_color])
    text_color = models.CharField("Text color", max_length=7, default="#1f2430", validators=[hex_color])
    footer_bg = models.CharField("Footer background", max_length=7, default="#111a2e", validators=[hex_color])
    corner_radius = models.PositiveSmallIntegerField("Corner roundness (px)", default=10,
                                                     validators=[MaxValueValidator(24)],
                                                     help_text="0 = চারকোনা, 24 = অনেক গোল")
    font = models.CharField(max_length=30, choices=FONT_CHOICES, default="Inter")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Theme & Colors"
        verbose_name_plural = "Theme & Colors"

    def __str__(self):
        return "Website theme & colors"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def css_variables(self):
        from .theme import build_css_variables
        return build_css_variables(self)


class Banner(TranslatableMixin, models.Model):
    POSITION_CHOICES = [("slider", "Home Slider"), ("side", "Side Banner"), ("middle", "Middle Banner")]
    title = models.CharField(max_length=150)
    subtitle = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="banners/")
    link = models.CharField(max_length=255, blank=True, help_text="যেমন: /products/?category=electronics")
    button_text = models.CharField(max_length=40, blank=True, default="Shop Now")
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default="slider")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "-id"]

    def __str__(self):
        return self.title


class BannerTranslation(models.Model):
    banner = models.ForeignKey(Banner, on_delete=models.CASCADE, related_name="translations")
    language = models.CharField(max_length=10, choices=TRANSLATION_LANGUAGES)
    title = models.CharField(max_length=150, blank=True)
    subtitle = models.CharField(max_length=255, blank=True)
    button_text = models.CharField(max_length=40, blank=True)

    class Meta:
        unique_together = ("banner", "language")


class Page(TranslatableMixin, models.Model):
    """Static pages: About, Privacy Policy, Terms, Return Policy ..."""
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    content = models.TextField(help_text="HTML লেখা যাবে")
    show_in_footer = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class PageTranslation(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="translations")
    language = models.CharField(max_length=10, choices=TRANSLATION_LANGUAGES)
    title = models.CharField(max_length=150, blank=True)
    content = models.TextField(blank=True)

    class Meta:
        unique_together = ("page", "language")


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.subject}"


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
