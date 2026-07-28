from django import forms
from django.utils import timezone

from administrator.models import (
    AreaLayanan,
    DetailPesanan,
    JenisBarang,
    Layanan,
    MetodePembayaran,
    Pesanan,
    Promo,
    Pembayaran,
    User,
)


class PesananPelangganForm(forms.ModelForm):
    setuju_ketentuan = forms.BooleanField(
        required=True,
        label=(
            "Saya telah membaca ketentuan barang yang dapat "
            "dan tidak dapat diterima oleh laundry."
        ),
        error_messages={
            "required": (
                "Anda wajib menyetujui ketentuan laundry "
                "sebelum membuat pesanan."
            ),
        },
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    class Meta:
        model = Pesanan
        fields = [
            "cara_barang_masuk",
            "cara_barang_keluar",
            "area_layanan",
            "alamat_penjemputan",
            "alamat_pengantaran",
            "tanggal_penjemputan",
            "metode_pembayaran",
            "promo",
            "catatan_pelanggan",
        ]

        widgets = {
            "cara_barang_masuk": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "cara_barang_keluar": forms.Select(
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
                    "placeholder": (
                        "Masukkan alamat tempat barang dijemput"
                    ),
                }
            ),
            "alamat_pengantaran": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Masukkan alamat tujuan pengantaran"
                    ),
                }
            ),
            "tanggal_penjemputan": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
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
                    "placeholder": (
                        "Contoh: terdapat noda pada bagian lengan"
                    ),
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
        self.fields["alamat_penjemputan"].required = False
        self.fields["alamat_pengantaran"].required = False

        self.fields["area_layanan"].empty_label = (
            "Pilih area layanan"
        )
        self.fields["metode_pembayaran"].empty_label = (
            "Pilih metode pembayaran"
        )
        self.fields["promo"].empty_label = (
            "Tidak menggunakan promo"
        )

        self.fields["cara_barang_masuk"].choices = [
            (
                "",
                "Pilih cara barang masuk",
            ),
            *Pesanan.CaraBarangMasuk.choices,
        ]

        self.fields["cara_barang_keluar"].choices = [
            (
                "",
                "Pilih cara barang dikembalikan",
            ),
            *Pesanan.CaraBarangKeluar.choices,
        ]

        if self.instance and self.instance.tanggal_penjemputan:
            self.initial["tanggal_penjemputan"] = (
                self.instance.tanggal_penjemputan.strftime(
                    "%Y-%m-%dT%H:%M"
                )
            )

    def clean(self):
        cleaned_data = super().clean()

        cara_masuk = cleaned_data.get("cara_barang_masuk")
        cara_keluar = cleaned_data.get("cara_barang_keluar")
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

        membutuhkan_penjemputan = (
            cara_masuk
            == Pesanan.CaraBarangMasuk.DIJEMPUT
        )

        membutuhkan_pengantaran = (
            cara_keluar
            == Pesanan.CaraBarangKeluar.DIANTAR_KE_PELANGGAN
        )

        if (
            membutuhkan_penjemputan
            or membutuhkan_pengantaran
        ) and not area_layanan:
            self.add_error(
                "area_layanan",
                "Area layanan wajib dipilih.",
            )

        if membutuhkan_penjemputan:
            if not alamat_penjemputan:
                self.add_error(
                    "alamat_penjemputan",
                    "Alamat penjemputan wajib diisi.",
                )

            if not tanggal_penjemputan:
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
            membutuhkan_pengantaran
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
            "jenis_barang",
            "jumlah_barang",
            "catatan",
        ]

        widgets = {
            "layanan": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "jenis_barang": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "jumlah_barang": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                    "step": "1",
                    "placeholder": "Masukkan jumlah barang",
                }
            ),
            "catatan": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Contoh: terdapat noda berat atau "
                        "jangan menggunakan pewangi"
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

        self.fields["jenis_barang"].queryset = (
            JenisBarang.objects.filter(
                is_active=True,
            ).order_by("nama")
        )

        self.fields["layanan"].empty_label = (
            "Pilih layanan laundry"
        )

        self.fields["jenis_barang"].empty_label = (
            "Pilih jenis barang"
        )

DetailPesananFormSet = forms.inlineformset_factory(
    Pesanan,
    DetailPesanan,
    form=DetailPesananPelangganForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)        

class PembayaranPelangganForm(forms.ModelForm):
    class Meta:
        model = Pembayaran
        fields = [
            "jumlah",
            "bukti_pembayaran",
            "catatan",
        ]

        widgets = {
            "jumlah": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                    "step": "0.01",
                    "placeholder": "Masukkan jumlah pembayaran",
                }
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

    def clean_bukti_pembayaran(self):
        bukti = self.cleaned_data.get(
            "bukti_pembayaran"
        )

        if not bukti:
            raise forms.ValidationError(
                "Bukti pembayaran wajib diunggah."
            )

        if bukti.size > 2 * 1024 * 1024:
            raise forms.ValidationError(
                "Ukuran bukti maksimal 2 MB."
            )

        return bukti
    
class ProfilPelangganForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "email",
            "nomor_hp",
            "alamat",
        ]

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Masukkan nama lengkap",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Masukkan email",
                }
            ),
            "nomor_hp": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Masukkan nomor HP",
                }
            ),
            "alamat": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Masukkan alamat lengkap",
                    "rows": 4,
                }
            ),
        }

    
