from django import forms
from django.utils.translation import gettext_lazy as _

from accounts.models import DIVISION_CHOICES

from .models import Order


class CheckoutForm(forms.Form):
    full_name = forms.CharField(label=_("Full name"), max_length=100)
    phone = forms.CharField(label=_("Phone"), max_length=20)
    email = forms.EmailField(label=_("Email"), required=False)
    division = forms.ChoiceField(label=_("Division"), choices=DIVISION_CHOICES)
    city = forms.CharField(label=_("City / District"), max_length=60)
    area = forms.CharField(label=_("Area"), max_length=100)
    address_line = forms.CharField(label=_("Full address (House, Road)"), max_length=255)
    delivery_area = forms.ChoiceField(choices=Order.AREA_CHOICES, widget=forms.RadioSelect, initial="inside")
    payment_method = forms.ChoiceField(choices=Order.PAYMENT_METHOD_CHOICES, widget=forms.RadioSelect,
                                       initial="cod")
    sender_number = forms.CharField(label=_("Your bKash/Nagad number"), max_length=20, required=False)
    transaction_id = forms.CharField(label=_("Transaction ID"), max_length=60, required=False)
    note = forms.CharField(label=_("Order note (optional)"), required=False,
                           widget=forms.Textarea(attrs={"rows": 2}))
    save_address = forms.BooleanField(label=_("Save this address to my account"), required=False, initial=True)

    def __init__(self, *args, settings_obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        if settings_obj is not None:
            allowed = []
            if settings_obj.enable_cod:
                allowed.append(("cod", _("Cash on Delivery")))
            if settings_obj.enable_bkash:
                allowed.append(("bkash", _("bKash")))
            if settings_obj.enable_nagad:
                allowed.append(("nagad", _("Nagad")))
            self.fields["payment_method"].choices = allowed or [("cod", _("Cash on Delivery"))]
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.RadioSelect, forms.CheckboxInput)):
                field.widget.attrs.setdefault("class", "form-control")

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip().replace(" ", "").replace("-", "")
        if not phone.lstrip("+").isdigit() or len(phone) < 11:
            raise forms.ValidationError(_("Enter a valid phone number (e.g. 01712345678)."))
        return phone

    def clean(self):
        data = super().clean()
        if data.get("payment_method") in ("bkash", "nagad"):
            if not data.get("transaction_id"):
                self.add_error("transaction_id", _("Transaction ID is required for mobile payment."))
            if not data.get("sender_number"):
                self.add_error("sender_number", _("Please enter the number you paid from."))
        return data


class TrackOrderForm(forms.Form):
    order_number = forms.CharField(max_length=20, widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": _("Order number, e.g. SB2610291234")}))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": _("Phone used in the order")}))
