from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import render

from .decorators import administrator_required
from .models import (
    AreaLayanan,
    KategoriLayanan,
    Layanan,
    MetodePembayaran,
    Pembayaran,
    Pesanan,
    Promo,
    RiwayatStatus,
    Tarif,
    User,
)


@administrator_required
def dashboard(request):
    # Statistik pengguna
    jumlah_administrator = User.objects.filter(
        role=User.Role.ADMINISTRATOR,
        is_active=True,
    ).count()

    jumlah_kasir = User.objects.filter(
        role=User.Role.KASIR,
        is_active=True,
    ).count()

    jumlah_petugas = User.objects.filter(
        role=User.Role.PETUGAS_LAUNDRY,
        is_active=True,
    ).count()

    jumlah_pelanggan = User.objects.filter(
        role=User.Role.PELANGGAN,
    ).count()

    pelanggan_menunggu_verifikasi = User.objects.filter(
        role=User.Role.PELANGGAN,
        is_verified=False,
        is_active=True,
    ).order_by("-date_joined")[:5]

    jumlah_menunggu_verifikasi = User.objects.filter(
        role=User.Role.PELANGGAN,
        is_verified=False,
        is_active=True,
    ).count()

    # Statistik pesanan
    jumlah_pesanan = Pesanan.objects.count()

    jumlah_pesanan_menunggu = Pesanan.objects.filter(
        status=Pesanan.StatusPesanan.MENUNGGU_KONFIRMASI,
    ).count()

    jumlah_pesanan_diproses = Pesanan.objects.exclude(
        status__in=[
            Pesanan.StatusPesanan.MENUNGGU_KONFIRMASI,
            Pesanan.StatusPesanan.DITOLAK,
            Pesanan.StatusPesanan.DIBATALKAN,
            Pesanan.StatusPesanan.SELESAI,
        ]
    ).count()

    jumlah_pesanan_selesai = Pesanan.objects.filter(
        status=Pesanan.StatusPesanan.SELESAI,
    ).count()

    # Pendapatan hanya dari pembayaran berhasil.
    total_pendapatan = Pembayaran.objects.filter(
        status=Pembayaran.StatusPembayaran.BERHASIL,
    ).aggregate(
        total=Sum("jumlah")
    )["total"] or Decimal("0.00")

    # Data master
    jumlah_kategori = KategoriLayanan.objects.count()
    jumlah_layanan = Layanan.objects.count()
    jumlah_tarif = Tarif.objects.filter(is_active=True).count()
    jumlah_promo = Promo.objects.filter(is_active=True).count()
    jumlah_metode_pembayaran = MetodePembayaran.objects.filter(
        is_active=True
    ).count()
    jumlah_area_layanan = AreaLayanan.objects.filter(
        is_active=True
    ).count()

    # Pesanan terbaru
    pesanan_terbaru = (
        Pesanan.objects
        .select_related(
            "pelanggan",
            "kasir",
            "petugas_laundry",
            "metode_pembayaran",
        )
        .order_by("-created_at")[:8]
    )

    # Aktivitas status terakhir
    aktivitas_terbaru = (
        RiwayatStatus.objects
        .select_related(
            "pesanan",
            "diubah_oleh",
        )
        .order_by("-created_at")[:8]
    )

    context = {
        "jumlah_administrator": jumlah_administrator,
        "jumlah_kasir": jumlah_kasir,
        "jumlah_petugas": jumlah_petugas,
        "jumlah_pelanggan": jumlah_pelanggan,
        "jumlah_menunggu_verifikasi": jumlah_menunggu_verifikasi,
        "pelanggan_menunggu_verifikasi": pelanggan_menunggu_verifikasi,

        "jumlah_pesanan": jumlah_pesanan,
        "jumlah_pesanan_menunggu": jumlah_pesanan_menunggu,
        "jumlah_pesanan_diproses": jumlah_pesanan_diproses,
        "jumlah_pesanan_selesai": jumlah_pesanan_selesai,
        "total_pendapatan": total_pendapatan,

        "jumlah_kategori": jumlah_kategori,
        "jumlah_layanan": jumlah_layanan,
        "jumlah_tarif": jumlah_tarif,
        "jumlah_promo": jumlah_promo,
        "jumlah_metode_pembayaran": jumlah_metode_pembayaran,
        "jumlah_area_layanan": jumlah_area_layanan,

        "pesanan_terbaru": pesanan_terbaru,
        "aktivitas_terbaru": aktivitas_terbaru,
    }

    return render(
        request,
        "administrator/dashboard.html",
        context,
    )