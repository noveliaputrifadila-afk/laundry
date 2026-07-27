from django import forms

from administrator.models import RatingUlasan


class RatingUlasanForm(forms.ModelForm):
    class Meta:
        model = RatingUlasan
        fields = [
            "nilai",
            "ulasan",
        ]

        widgets = {
            "nilai": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "ulasan": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Tulis ulasan Anda tentang layanan laundry...",
                }
            ),
        }

        labels = {
            "nilai": "Rating",
            "ulasan": "Ulasan",
        }