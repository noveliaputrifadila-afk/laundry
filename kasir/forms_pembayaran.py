from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from administrator.models import (
    MetodePembayaran,
    Pembayaran,
    Pesanan,
)


class PembayaranKasirForm(forms.ModelForm):
    class Meta:
        model = Pembayaran
        fields = [
            "pesanan",
            "metode_pembayaran",
            "jumlah",
            "tanggal_pembayaran",
            
            "catatan",
        ]
        widgets = {
            "pesanan": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "metode_pembayaran": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "jumlah": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0.01",
                    "step": "0.01",
                    "placeholder": "Masukkan jumlah pembayaran",
                }
            ),
            "tanggal_pembayaran": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "bukti_pembayaran": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
            "catatan": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Catatan pembayaran",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.pesanan_terpilih = kwargs.pop(
            "pesanan",
            None,
        )

        super().__init__(*args, **kwargs)

        self.fields["pesanan"].queryset = (
            Pesanan.objects
            .select_related("pelanggan")
            .exclude(
                status_pembayaran=Pesanan.StatusPembayaran.LUNAS,
            )
            .exclude(
                status__in=[
                    Pesanan.StatusPesanan.DITOLAK,
                    Pesanan.StatusPesanan.DIBATALKAN,
                ]
            )
            .order_by("-created_at")
        )

        self.fields["metode_pembayaran"].queryset = (
            MetodePembayaran.objects
            .filter(is_active=True)
            .order_by("nama")
        )

        self.fields["tanggal_pembayaran"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]

        if self.pesanan_terpilih:
            self.fields["pesanan"].initial = self.pesanan_terpilih
            self.fields["pesanan"].disabled = True
            self.fields["metode_pembayaran"].initial = (
                self.pesanan_terpilih.metode_pembayaran
            )

            sisa_tagihan = self.hitung_sisa_tagihan(
                self.pesanan_terpilih
            )

            self.fields["jumlah"].initial = sisa_tagihan

    @staticmethod
    def hitung_total_berhasil(pesanan):
        return sum(
            (
                pembayaran.jumlah
                for pembayaran in pesanan.pembayaran.filter(
                    status=Pembayaran.StatusPembayaran.BERHASIL,
                )
            ),
            Decimal("0.00"),
        )

    def hitung_sisa_tagihan(self, pesanan):
        total_berhasil = self.hitung_total_berhasil(pesanan)

        return max(
            pesanan.total_biaya - total_berhasil,
            Decimal("0.00"),
        )

    def clean(self):
        cleaned_data = super().clean()

        pesanan = (
            self.pesanan_terpilih
            or cleaned_data.get("pesanan")
        )
        jumlah = cleaned_data.get("jumlah")

        if not pesanan or jumlah is None:
            return cleaned_data

        if pesanan.status_pembayaran == Pesanan.StatusPembayaran.LUNAS:
            raise ValidationError(
                "Pesanan tersebut sudah lunas."
            )

        if jumlah <= Decimal("0.00"):
            self.add_error(
                "jumlah",
                "Jumlah pembayaran harus lebih dari nol.",
            )

        sisa_tagihan = self.hitung_sisa_tagihan(pesanan)

        if jumlah > sisa_tagihan:
            self.add_error(
                "jumlah",
                (
                    "Jumlah pembayaran melebihi sisa tagihan. "
                    f"Sisa tagihan Rp{sisa_tagihan:,.0f}."
                ),
            )

        cleaned_data["pesanan"] = pesanan

        return cleaned_data

    def save(self, commit=True):
        pembayaran = super().save(commit=False)

        if self.pesanan_terpilih:
            pembayaran.pesanan = self.pesanan_terpilih

        if commit:
            pembayaran.save()

        return pembayaran