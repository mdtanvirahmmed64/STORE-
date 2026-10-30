from django import forms
from django.utils.translation import gettext_lazy as _


class ContactForm(forms.Form):
    name = forms.CharField(label=_("Name"), max_length=100)
    email = forms.EmailField(label=_("Email"))
    phone = forms.CharField(label=_("Phone"), max_length=20, required=False)
    subject = forms.CharField(label=_("Subject"), max_length=200)
    message = forms.CharField(label=_("Message"), widget=forms.Textarea(attrs={"rows": 5}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs["class"] = "form-control"
