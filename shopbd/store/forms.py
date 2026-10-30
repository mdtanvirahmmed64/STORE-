from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Review


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(choices=[(i, i) for i in range(5, 0, -1)], coerce=int,
                                    widget=forms.RadioSelect)

    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {"comment": forms.Textarea(attrs={"rows": 4, "placeholder": _("Share your experience...")})}
