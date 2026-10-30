from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import Address, Profile


class StyledMixin:
    def _style(self):
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                field.widget.attrs.setdefault("class", "form-control")


class RegisterForm(StyledMixin, UserCreationForm):
    first_name = forms.CharField(label=_("Full name"), max_length=100)
    email = forms.EmailField(label=_("Email"))
    phone = forms.CharField(label=_("Phone"), max_length=20, help_text=_("e.g. 01712345678"))

    class Meta:
        model = User
        fields = ["first_name", "username", "email", "phone", "password1", "password2"]
        labels = {"username": _("Username")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
        self.fields["password1"].label = _("Password")
        self.fields["password2"].label = _("Confirm password")
        for f in ("password1", "password2", "username"):
            self.fields[f].help_text = ""

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("An account with this email already exists."))
        return email

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip().replace(" ", "").replace("-", "")
        if not phone.lstrip("+").isdigit() or len(phone) < 11:
            raise forms.ValidationError(_("Enter a valid phone number."))
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        if commit:
            user.save()
            profile, _created = Profile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data["phone"]
            profile.save()
        return user


class LoginForm(StyledMixin, AuthenticationForm):
    username = forms.CharField(label=_("Username or Email"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].label = _("Password")
        self._style()


class UserForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {"first_name": _("First name"), "last_name": _("Last name"), "email": _("Email")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class ProfileForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["phone", "gender", "date_of_birth", "avatar"]
        labels = {"phone": _("Phone"), "gender": _("Gender"), "date_of_birth": _("Date of birth"),
                  "avatar": _("Profile picture")}
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class AddressForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Address
        fields = ["full_name", "phone", "division", "city", "area", "address_line", "is_default"]
        labels = {"full_name": _("Full name"), "phone": _("Phone"), "division": _("Division"),
                  "city": _("City / District"), "area": _("Area"),
                  "address_line": _("House / Road / Details"), "is_default": _("Make this my default address")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
