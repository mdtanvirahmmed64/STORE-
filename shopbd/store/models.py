from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from core.translation import TRANSLATION_LANGUAGES, TranslatableMixin


def unique_slug(instance, value, model):
    base = slugify(value, allow_unicode=True) or "item"
    slug, n = base, 1
    while model.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        n += 1
        slug = f"{base}-{n}"
    return slug


class Category(TranslatableMixin, models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True, allow_unicode=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    image = models.ImageField(upload_to="categories/", blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome class, যেমন: fa-mobile-screen")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    show_on_home = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.parent.name} › {self.name}" if self.parent_id else self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, Category)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("store:category", args=[self.slug])

    def get_descendant_ids(self):
        ids = [self.pk]
        for child in self.children.all():
            ids += child.get_descendant_ids()
        return ids


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True, allow_unicode=True)
    logo = models.ImageField(upload_to="brands/", blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, Brand)
        super().save(*args, **kwargs)


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True, category__is_active=True)


class Product(TranslatableMixin, models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True, allow_unicode=True)
    sku = models.CharField("SKU", max_length=50, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    brand = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True, help_text="HTML লেখা যাবে")
    specification = models.TextField(blank=True, help_text="প্রতি লাইনে একটি:  Key: Value")
    price = models.DecimalField("Regular price (৳)", max_digits=10, decimal_places=2)
    discount_price = models.DecimalField("Sale price (৳)", max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField("Main image", upload_to="products/")
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_flash_sale = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0"), editable=False)
    review_count = models.PositiveIntegerField(default=0, editable=False)
    sold_count = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["is_active", "-created_at"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, Product)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("store:product_detail", args=[self.slug])

    @property
    def final_price(self):
        if self.discount_price is not None and self.discount_price < self.price:
            return self.discount_price
        return self.price

    @property
    def has_discount(self):
        return self.final_price < self.price

    @property
    def discount_percent(self):
        if not self.has_discount or not self.price:
            return 0
        return int(round((self.price - self.final_price) * 100 / self.price))

    @property
    def in_stock(self):
        return self.stock > 0

    def spec_list(self):
        rows = []
        for line in self.tr("specification").splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                rows.append((k.strip(), v.strip()))
        return rows

    def update_rating(self):
        agg = self.reviews.filter(is_approved=True).aggregate(avg=Avg("rating"), n=Count("id"))
        self.rating = Decimal(str(round(agg["avg"] or 0, 2)))
        self.review_count = agg["n"]
        Product.objects.filter(pk=self.pk).update(rating=self.rating, review_count=self.review_count)


class CategoryTranslation(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="translations")
    language = models.CharField(max_length=10, choices=TRANSLATION_LANGUAGES)
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ("category", "language")

    def __str__(self):
        return f"{self.language}: {self.name}"


class ProductTranslation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="translations")
    language = models.CharField(max_length=10, choices=TRANSLATION_LANGUAGES)
    name = models.CharField(max_length=200, blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True, help_text="HTML লেখা যাবে")
    specification = models.TextField(blank=True, help_text="প্রতি লাইনে একটি:  Key: Value")

    class Meta:
        unique_together = ("product", "language")

    def __str__(self):
        return f"{self.language}: {self.name}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/gallery/")
    alt = models.CharField(max_length=150, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"Image of {self.product.name}"


class Variation(models.Model):
    KIND_CHOICES = [("color", _("Color")), ("size", _("Size")), ("other", _("Option"))]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variations")
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default="size")
    value = models.CharField(max_length=50)
    extra_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["kind", "id"]

    def __str__(self):
        return f"{self.get_kind_display()}: {self.value}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(max_length=1000)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("product", "user")

    def __str__(self):
        return f"{self.product} - {self.rating}★"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_rating()

    def delete(self, *args, **kwargs):
        product = self.product
        super().delete(*args, **kwargs)
        product.update_rating()


class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} ♥ {self.product}"
