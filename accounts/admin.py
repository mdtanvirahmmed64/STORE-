from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from pos.models import BranchStaff

from .models import Address, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


class BranchStaffInline(admin.StackedInline):
    model = BranchStaff
    can_delete = True
    extra = 0
    max_num = 1
    verbose_name_plural = "Shop branch (give POS access: choose a branch and role)"


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0


admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline, BranchStaffInline, AddressInline]
    list_display = ("username", "email", "first_name", "phone", "is_staff", "date_joined")

    @admin.display(description="Phone")
    def phone(self, obj):
        return getattr(getattr(obj, "profile", None), "phone", "")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "city", "area", "user", "is_default")
    search_fields = ("full_name", "phone", "user__username")
