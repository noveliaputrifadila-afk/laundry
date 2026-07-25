from django import forms
from django.utils import timezone

from administrator.models import (
    AreaLayanan,
    DetailPesanan,
    Layanan,
    MetodePembayaran,
    Pesanan,
    Promo,
)


class PesananPelangganForm(forms.ModelForm):
    class Meta:
        model = Pesanan
        fields = [
            "jenis_pengantaran",
            "area_layanan",
            "alamat_penjemputan",
            "alamat_pengantaran",
            "tanggal_penjemputan",
            "metode_pembayaran",
            "promo",
            "catatan_pelanggan",
        ]

        widgets = {
            "jenis_pengantaran": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "area_layanan": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "alamat_penjemputan": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Masukkan alamat penjemputan",
                }
            ),
            "alamat_pengantaran": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Masukkan alamat pengantaran",
                }
            ),
            "tanggal_penjemputan": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
            "metode_pembayaran": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "promo": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "catatan_pelanggan": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Tambahkan catatan khusus jika ada",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["area_layanan"].queryset = (
            AreaLayanan.objects.filter(is_active=True)
        )

        self.fields["metode_pembayaran"].queryset = (
            MetodePembayaran.objects.filter(is_active=True)
        )

        self.fields["promo"].queryset = Promo.objects.filter(
            is_active=True,
            tanggal_mulai__lte=timezone.now(),
            tanggal_selesai__gte=timezone.now(),
        )

        self.fields["area_layanan"].required = False
        self.fields["promo"].required = False
        self.fields["tanggal_penjemputan"].required = False

        self.fields["area_layanan"].empty_label = (
            "Pilih area antar-jemput"
        )
        self.fields["metode_pembayaran"].empty_label = (
            "Pilih metode pembayaran"
        )
        self.fields["promo"].empty_label = (
            "Tidak menggunakan promo"
        )

    def clean(self):
        cleaned_data = super().clean()

        jenis_pengantaran = cleaned_data.get(
            "jenis_pengantaran"
        )
        area_layanan = cleaned_data.get("area_layanan")
        alamat_penjemputan = cleaned_data.get(
            "alamat_penjemputan"
        )
        alamat_pengantaran = cleaned_data.get(
            "alamat_pengantaran"
        )
        tanggal_penjemputan = cleaned_data.get(
            "tanggal_penjemputan"
        )

        jenis_memerlukan_jemput = [
            Pesanan.JenisPengantaran.JEMPUT,
            Pesanan.JenisPengantaran.ANTAR_JEMPUT,
        ]

        jenis_memerlukan_antar = [
            Pesanan.JenisPengantaran.ANTAR,
            Pesanan.JenisPengantaran.ANTAR_JEMPUT,
        ]

        jenis_memerlukan_area = [
            Pesanan.JenisPengantaran.JEMPUT,
            Pesanan.JenisPengantaran.ANTAR,
            Pesanan.JenisPengantaran.ANTAR_JEMPUT,
        ]

        if (
            jenis_pengantaran in jenis_memerlukan_area
            and not area_layanan
        ):
            self.add_error(
                "area_layanan",
                "Area layanan wajib dipilih.",
            )

        if (
            jenis_pengantaran in jenis_memerlukan_jemput
            and not alamat_penjemputan
        ):
            self.add_error(
                "alamat_penjemputan",
                "Alamat penjemputan wajib diisi.",
            )

        if (
            jenis_pengantaran in jenis_memerlukan_jemput
            and not tanggal_penjemputan
        ):
            self.add_error(
                "tanggal_penjemputan",
                "Tanggal penjemputan wajib diisi.",
            )

        if (
            tanggal_penjemputan
            and tanggal_penjemputan <= timezone.now()
        ):
            self.add_error(
                "tanggal_penjemputan",
                "Tanggal penjemputan harus setelah waktu sekarang.",
            )

        if (
            jenis_pengantaran in jenis_memerlukan_antar
            and not alamat_pengantaran
        ):
            self.add_error(
                "alamat_pengantaran",
                "Alamat pengantaran wajib diisi.",
            )

        return cleaned_data


class DetailPesananPelangganForm(forms.ModelForm):
    class Meta:
        model = DetailPesanan
        fields = [
            "layanan",
            "nama_barang",
            "jumlah",
            "catatan",
        ]

        widgets = {
            "layanan": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "nama_barang": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Contoh: pakaian harian, sepatu, karpet"
                    ),
                }
            ),
            "jumlah": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0.01",
                    "step": "0.01",
                    "placeholder": "Masukkan berat atau jumlah",
                }
            ),
            "catatan": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Contoh: jangan menggunakan pewangi"
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["layanan"].queryset = (
            Layanan.objects.filter(
                is_active=True,
                tarif_set__is_active=True,
            )
            .select_related("kategori")
            .distinct()
        )

        self.fields["layanan"].empty_label = (
            "Pilih layanan laundry"
        )