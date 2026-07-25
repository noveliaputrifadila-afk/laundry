from django import forms

from .models import Invoice


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "pesanan",
            "tanggal_jatuh_tempo",
            "status",
            "catatan",
        ]
        widgets = {
            "pesanan": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "tanggal_jatuh_tempo": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "catatan": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Masukkan catatan invoice jika diperlukan",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["tanggal_jatuh_tempo"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]

        pesanan_queryset = self.fields["pesanan"].queryset

        if self.instance and self.instance.pk:
            self.fields["pesanan"].queryset = pesanan_queryset.filter(
                pk=self.instance.pesanan_id
            )
            self.fields["pesanan"].disabled = True
        else:
            self.fields["pesanan"].queryset = (
                pesanan_queryset
                .filter(invoice__isnull=True)
                .select_related("pelanggan")
                .order_by("-created_at")
            )

    def clean(self):
        cleaned_data = super().clean()

        tanggal_jatuh_tempo = cleaned_data.get(
            "tanggal_jatuh_tempo"
        )

        tanggal_terbit = (
            self.instance.tanggal_terbit
            if self.instance and self.instance.pk
            else None
        )

        if (
            tanggal_jatuh_tempo
            and tanggal_terbit
            and tanggal_jatuh_tempo < tanggal_terbit
        ):
            self.add_error(
                "tanggal_jatuh_tempo",
                "Tanggal jatuh tempo tidak boleh sebelum tanggal terbit.",
            )

        return cleaned_data