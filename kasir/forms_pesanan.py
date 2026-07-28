from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from administrator.models import (
    AreaLayanan,
    DetailPesanan,
    
    Layanan,
    MetodePembayaran,
    
    Pesanan,
    Promo,
    User,
)


class PesananKasirForm(forms.ModelForm):
    class Meta:
        model = Pesanan

        fields = [
            "pelanggan",
            "metode_pembayaran",
            "promo",
            "jenis_pengantaran",
            "area_layanan",
            "alamat_penjemputan",
            "alamat_pengantaran",
            "tanggal_penjemputan",
            "tanggal_pengambilan",
            "catatan_pelanggan",
            "catatan_kasir",
        ]

        widgets = {
            "pelanggan": forms.Select(
                attrs={
                    "class": "form-select",
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
            "jenis_pengantaran": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_jenis_pengantaran",
                }
            ),
            "area_layanan": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_area_layanan",
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
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "tanggal_pengambilan": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "catatan_pelanggan": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Catatan dari pelanggan, bila ada",
                }
            ),
            "catatan_kasir": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Catatan internal kasir",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["pelanggan"].queryset = (
            User.objects.filter(
                role=User.Role.PELANGGAN,
                is_active=True,
                is_verified=True,
            )
            .order_by("first_name", "username")
        )

        self.fields["metode_pembayaran"].queryset = (
            MetodePembayaran.objects.filter(
                is_active=True,
            ).order_by("nama")
        )

        self.fields["promo"].queryset = (
            Promo.objects.filter(
                is_active=True,
            ).order_by("nama")
        )

        self.fields["area_layanan"].queryset = (
            AreaLayanan.objects.filter(
                is_active=True,
            ).order_by("nama_area")
        )

        self.fields["promo"].required = False
        self.fields["area_layanan"].required = False
        self.fields["alamat_penjemputan"].required = False
        self.fields["alamat_pengantaran"].required = False
        self.fields["tanggal_penjemputan"].required = False
        self.fields["tanggal_pengambilan"].required = False
        self.fields["catatan_pelanggan"].required = False
        self.fields["catatan_kasir"].required = False

    def clean(self):
        cleaned_data = super().clean()

        jenis_pengantaran = cleaned_data.get(
            "jenis_pengantaran"
        )
        area_layanan = cleaned_data.get(
            "area_layanan"
        )
        alamat_penjemputan = cleaned_data.get(
            "alamat_penjemputan"
        )
        alamat_pengantaran = cleaned_data.get(
            "alamat_pengantaran"
        )

        membutuhkan_jemput = jenis_pengantaran in {
            Pesanan.JenisPengantaran.JEMPUT,
            Pesanan.JenisPengantaran.ANTAR_JEMPUT,
        }

        membutuhkan_antar = jenis_pengantaran in {
            Pesanan.JenisPengantaran.ANTAR,
            Pesanan.JenisPengantaran.ANTAR_JEMPUT,
        }

        if jenis_pengantaran != Pesanan.JenisPengantaran.DATANG_SENDIRI:
            if not area_layanan:
                self.add_error(
                    "area_layanan",
                    "Area layanan wajib dipilih untuk layanan antar-jemput.",
                )

        if membutuhkan_jemput and not alamat_penjemputan:
            self.add_error(
                "alamat_penjemputan",
                "Alamat penjemputan wajib diisi.",
            )

        if membutuhkan_antar and not alamat_pengantaran:
            self.add_error(
                "alamat_pengantaran",
                "Alamat pengantaran wajib diisi.",
            )

        return cleaned_data


class DetailPesananForm(forms.ModelForm):
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
                    "class": "form-select layanan-select",
                }
            ),
            "nama_barang": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Contoh: Pakaian campur",
                }
            ),
            "jumlah": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0.01",
                    "step": "0.01",
                    "placeholder": "0",
                }
            ),
            "catatan": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Catatan khusus",
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
            .order_by("kategori__nama", "nama")
        )

        self.fields["catatan"].required = False

    def clean_layanan(self):
        layanan = self.cleaned_data.get("layanan")

        if layanan and not layanan.tarif_aktif:
            raise forms.ValidationError(
                "Layanan ini belum mempunyai tarif aktif."
            )

        return layanan


class BaseDetailPesananFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        if any(self.errors):
            return

        jumlah_detail = 0

        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue

            if form.cleaned_data.get("DELETE"):
                continue

            layanan = form.cleaned_data.get("layanan")
            nama_barang = form.cleaned_data.get("nama_barang")
            jumlah = form.cleaned_data.get("jumlah")

            if layanan and nama_barang and jumlah:
                jumlah_detail += 1

        if jumlah_detail < 1:
            raise forms.ValidationError(
                "Minimal satu detail layanan harus diisi."
            )


DetailPesananFormSet = inlineformset_factory(
    parent_model=Pesanan,
    model=DetailPesanan,
    form=DetailPesananForm,
    formset=BaseDetailPesananFormSet,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)

class PemeriksaanDetailForm(forms.ModelForm):
    class Meta:
        model = DetailPesanan

        fields = [
            "berat_aktual",
            "harga_final",
            "catatan",
        ]

        widgets = {
            "berat_aktual": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0.01",
                    "step": "0.01",
                    "placeholder": "Contoh: 3.50",
                }
            ),
            "harga_final": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "100",
                    "placeholder": "Contoh: 8000",
                }
            ),
            "catatan": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Catatan hasil pemeriksaan, bila ada",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["catatan"].required = False

        # Berat hanya wajib untuk layanan berbasis kilogram.
        if (
            self.instance
            and self.instance.pk
            and self.instance.layanan_id
        ):
            if (
                self.instance.layanan.satuan
                == Layanan.Satuan.KILOGRAM
            ):
                self.fields["berat_aktual"].required = True
            else:
                self.fields["berat_aktual"].required = False

    def clean(self):
        cleaned_data = super().clean()

        berat_aktual = cleaned_data.get("berat_aktual")
        harga_final = cleaned_data.get("harga_final")

        if harga_final is None:
            self.add_error(
                "harga_final",
                "Harga final wajib diisi.",
            )

        if (
            self.instance
            and self.instance.layanan_id
            and self.instance.layanan.satuan
            == Layanan.Satuan.KILOGRAM
            and berat_aktual is None
        ):
            self.add_error(
                "berat_aktual",
                "Berat aktual wajib diisi untuk layanan kilogram.",
            )

        return cleaned_data