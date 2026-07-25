from django import forms

from administrator.models import KendalaLaundry


class KendalaLaundryForm(forms.ModelForm):
    class Meta:
        model = KendalaLaundry
        fields = [
            "judul",
            "deskripsi",
        ]

        widgets = {
            "judul": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Contoh: Mesin cuci bermasalah",
                }
            ),
            "deskripsi": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Jelaskan kendala yang terjadi "
                        "secara lengkap..."
                    ),
                }
            ),
        }

        labels = {
            "judul": "Judul Kendala",
            "deskripsi": "Deskripsi Kendala",
        }