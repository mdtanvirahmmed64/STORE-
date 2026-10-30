from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

DIVISION_CHOICES = [
    ("Dhaka", _("Dhaka")), ("Chattogram", _("Chattogram")), ("Rajshahi", _("Rajshahi")),
    ("Khulna", _("Khulna")), ("Barishal", _("Barishal")), ("Sylhet", _("Sylhet")),
    ("Rangpur", _("Rangpur")), ("Mymensingh", _("Mymensingh")),
]


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, choices=[("male", _("Male")), ("female", _("Female")), ("other", _("Other"))])

    def __str__(self):
        return f"Profile of {self.user.username}"


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    division = models.CharField(max_length=30, choices=DIVISION_CHOICES, default="Dhaka")
    city = models.CharField("City / District", max_length=60)
    area = models.CharField(max_length=100)
    address_line = models.CharField("House / Road / Details", max_length=255)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ["-is_default", "-id"]

    def __str__(self):
        return f"{self.full_name}, {self.area}, {self.city}"

    @property
    def inside_dhaka(self):
        return self.city.strip().lower() == "dhaka"

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        elif not Address.objects.filter(user=self.user).exclude(pk=self.pk).exists():
            self.is_default = True
        super().save(*args, **kwargs)
