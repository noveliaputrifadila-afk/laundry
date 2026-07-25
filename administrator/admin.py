from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    AreaLayanan,
    DetailPesanan,
    Invoice,
    KategoriLayanan,
    KendalaLaundry,
    Layanan,
    MetodePembayaran,
    Notifikasi,
    Pembayaran,
    PengaturanSistem,
    Pesanan,
    Promo,
    RiwayatStatus,
    Tarif,
    User,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "nomor_hp",
        "role",
        "is_verified",
        "is_active",
        "is_staff",
    )
    list_filter = (
        "role",
        "is_verified",
        "is_active",
        "is_staff",
    )
    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "nomor_hp",
    )
    ordering = ("username",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "Informasi Laundry",
            {
                "fields": (
                    "role",
                    "nomor_hp",
                    "alamat",
                    "foto",
                    "is_verified",
                    "verified_at",
                    "verified_by",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Informasi Laundry",
            {
                "fields": (
                    "email",
                    "nomor_hp",
                    "role",
                    "alamat",
                    "is_verified",
                )
            },
        ),
    )


class DetailPesananInline(admin.TabularInline):
    model = DetailPesanan
    extra = 1


class RiwayatStatusInline(admin.TabularInline):
    model = RiwayatStatus
    extra = 0
    readonly_fields = (
        "status_sebelumnya",
        "status_baru",
        "diubah_oleh",
        "catatan",
        "created_at",
    )


@admin.register(Pesanan)
class PesananAdmin(admin.ModelAdmin):
    list_display = (
        "kode_pesanan",
        "pelanggan",
        "kasir",
        "petugas_laundry",
        "status",
        "status_pembayaran",
        "total_biaya",
        "created_at",
    )
    list_filter = (
        "status",
        "status_pembayaran",
        "jenis_pengantaran",
        "created_at",
    )
    search_fields = (
        "kode_pesanan",
        "pelanggan__username",
        "pelanggan__email",
        "pelanggan__nomor_hp",
    )
    readonly_fields = (
        "kode_pesanan",
        "subtotal",
        "diskon",
        "total_biaya",
        "created_at",
        "updated_at",
    )
    inlines = [
        DetailPesananInline,
        RiwayatStatusInline,
    ]


admin.site.register(KategoriLayanan)
admin.site.register(Layanan)
admin.site.register(Tarif)
admin.site.register(Promo)
admin.site.register(MetodePembayaran)
admin.site.register(AreaLayanan)
admin.site.register(Invoice)
admin.site.register(Pembayaran)
admin.site.register(KendalaLaundry)
admin.site.register(Notifikasi)
admin.site.register(PengaturanSistem)