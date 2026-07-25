from django import forms
from django.utils import timezone

from .forms import BootstrapFormMixin
from .models import Pesanan, User


class FilterLaporanPesananForm(
    BootstrapFormMixin,
    forms.Form,
):
    tanggal_mulai = forms.DateField(
        label="Tanggal Mulai",
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        ),
    )

    tanggal_selesai = forms.DateField(
        label="Tanggal Selesai",
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        ),
    )

    status = forms.ChoiceField(
        label="Status Pesanan",
        required=False,
        choices=[
            ("", "Semua status"),
            *Pesanan.StatusPesanan.choices,
        ],
    )

    status_pembayaran = forms.ChoiceField(
        label="Status Pembayaran",
        required=False,
        choices=[
            ("", "Semua pembayaran"),
            *Pesanan.StatusPembayaran.choices,
        ],
    )

    kasir = forms.ModelChoiceField(
        label="Kasir",
        required=False,
        queryset=User.objects.none(),
        empty_label="Semua kasir",
    )

    petugas_laundry = forms.ModelChoiceField(
        label="Petugas Laundry",
        required=False,
        queryset=User.objects.none(),
        empty_label="Semua petugas",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.apply_bootstrap_classes()

        self.fields["kasir"].queryset = (
            User.objects.filter(
                role=User.Role.KASIR,
                is_active=True,
            )
            .order_by(
                "first_name",
                "last_name",
                "username",
            )
        )

        self.fields[
            "petugas_laundry"
        ].queryset = (
            User.objects.filter(
                role=User.Role.PETUGAS_LAUNDRY,
                is_active=True,
            )
            .order_by(
                "first_name",
                "last_name",
                "username",
            )
        )

        hari_ini = timezone.localdate()

        if not self.is_bound:
            self.initial["tanggal_mulai"] = (
                hari_ini.replace(day=1)
            )
            self.initial["tanggal_selesai"] = (
                hari_ini
            )

    def clean(self):
        cleaned_data = super().clean()

        tanggal_mulai = cleaned_data.get(
            "tanggal_mulai"
        )
        tanggal_selesai = cleaned_data.get(
            "tanggal_selesai"
        )

        if (
            tanggal_mulai
            and tanggal_selesai
            and tanggal_mulai > tanggal_selesai
        ):
            self.add_error(
                "tanggal_selesai",
                (
                    "Tanggal selesai tidak boleh lebih "
                    "kecil dari tanggal mulai."
                ),
            )

        return cleaned_data