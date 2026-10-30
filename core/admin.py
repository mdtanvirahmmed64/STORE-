import json

from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse

from .models import (Banner, BannerTranslation, ContactMessage, Page, PageTranslation, SiteSetting,
                     SiteSettingTranslation, Subscriber, ThemeSetting)
from .theme import PRESET_FIELDS, PRESETS


class SingletonAdmin(admin.ModelAdmin):
    """Opens the edit page directly (there is only one row)."""

    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = self.model.load()
        return redirect(reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.pk]))


class SiteSettingTranslationInline(admin.StackedInline):
    model = SiteSettingTranslation
    extra = 0
    verbose_name_plural = "Translations (Bangla / Hindi / Urdu / Arabic) — leave empty to show English"


@admin.register(SiteSetting)
class SiteSettingAdmin(SingletonAdmin):
    inlines = [SiteSettingTranslationInline]
    fieldsets = (
        ("General", {"fields": ("site_name", "tagline", "logo", "favicon", "top_notice", "footer_text",
                                "default_language")}),
        ("Contact", {"fields": ("phone", "email", "address", "facebook", "instagram", "youtube")}),
        ("Delivery charge", {"fields": ("shipping_inside_dhaka", "shipping_outside_dhaka", "free_shipping_over")}),
        ("Payment", {"fields": ("enable_cod", "enable_bkash", "bkash_number", "enable_nagad", "nagad_number")}),
    )


class ColorInput(forms.TextInput):
    input_type = "color"


class ThemeForm(forms.ModelForm):
    class Meta:
        model = ThemeSetting
        fields = "__all__"
        widgets = {f: ColorInput(attrs={"class": "theme-color"}) for f in PRESET_FIELDS}


@admin.register(ThemeSetting)
class ThemeSettingAdmin(SingletonAdmin):
    form = ThemeForm
    change_form_template = "admin/core/themesetting/change_form.html"
    fieldsets = (
        ("1. Pick a ready-made theme", {"fields": ("preset",)}),
        ("2. Change any color you like", {"fields": (
            "primary_color", "header_bg", "header_text", "secondary_color", "accent_color",
            "discount_color", "page_bg", "text_color", "footer_bg")}),
        ("3. Shape & font", {"fields": ("corner_radius", "font")}),
    )

    def render_change_form(self, request, context, *args, **kwargs):
        context["presets_json"] = json.dumps({k: dict(zip(PRESET_FIELDS, v)) for k, v in PRESETS.items()})
        context["preset_fields_json"] = json.dumps(PRESET_FIELDS)
        return super().render_change_form(request, context, *args, **kwargs)

    def response_change(self, request, obj):
        if "_reset" in request.POST:
            for field, value in zip(PRESET_FIELDS, PRESETS["orange"]):
                setattr(obj, field, value)
            obj.preset, obj.corner_radius, obj.font = "orange", 10, "Inter"
            obj.save()
            messages.success(request, "Theme reset to the default orange colors.")
            return redirect(request.path)
        messages.success(request, "Theme saved! Open the website (or refresh it) to see the new colors.")
        return redirect(request.path)


class BannerTranslationInline(admin.TabularInline):
    model = BannerTranslation
    extra = 0


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "position", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("position", "is_active")
    inlines = [BannerTranslationInline]


class PageTranslationInline(admin.StackedInline):
    model = PageTranslation
    extra = 0


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "show_in_footer", "is_active")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PageTranslationInline]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "is_read", "created_at")
    list_filter = ("is_read",)
    list_editable = ("is_read",)
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "phone", "subject", "message", "created_at")


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at")
    search_fields = ("email",)
