from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import render

from .decorators import administrator_required
from .forms import FilterLogAktivitasForm
from .models import (
    AreaLayanan,
    KategoriLayanan,
    Layanan,
    LogAktivitas,
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
    """
    Menampilkan ringkasan data aplikasi pada dashboard administrator.
    """

    # =========================================================
    # STATISTIK PENGGUNA
    # =========================================================
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

    pelanggan_menunggu_verifikasi = (
        User.objects.filter(
            role=User.Role.PELANGGAN,
            is_verified=False,
            is_active=True,
        )
        .order_by("-date_joined")[:5]
    )

    jumlah_menunggu_verifikasi = User.objects.filter(
        role=User.Role.PELANGGAN,
        is_verified=False,
        is_active=True,
    ).count()

    # =========================================================
    # STATISTIK PESANAN
    # =========================================================
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

    # =========================================================
    # STATISTIK PENDAPATAN
    # =========================================================
    total_pendapatan = (
        Pembayaran.objects.filter(
            status=Pembayaran.StatusPembayaran.BERHASIL,
        ).aggregate(
            total=Sum("jumlah")
        )["total"]
        or Decimal("0.00")
    )

    # =========================================================
    # STATISTIK DATA MASTER
    # =========================================================
    jumlah_kategori = KategoriLayanan.objects.count()
    jumlah_layanan = Layanan.objects.count()

    jumlah_tarif = Tarif.objects.filter(
        is_active=True,
    ).count()

    jumlah_promo = Promo.objects.filter(
        is_active=True,
    ).count()

    jumlah_metode_pembayaran = MetodePembayaran.objects.filter(
        is_active=True,
    ).count()

    jumlah_area_layanan = AreaLayanan.objects.filter(
        is_active=True,
    ).count()

    # =========================================================
    # PESANAN TERBARU
    # =========================================================
    pesanan_terbaru = (
        Pesanan.objects.select_related(
            "pelanggan",
            "kasir",
            "petugas_laundry",
            "metode_pembayaran",
        )
        .order_by("-created_at")[:8]
    )

    # =========================================================
    # RIWAYAT STATUS TERBARU
    # =========================================================
    aktivitas_terbaru = (
        RiwayatStatus.objects.select_related(
            "pesanan",
            "diubah_oleh",
        )
        .order_by("-created_at")[:8]
    )

    context = {
        # Pengguna
        "jumlah_administrator": jumlah_administrator,
        "jumlah_kasir": jumlah_kasir,
        "jumlah_petugas": jumlah_petugas,
        "jumlah_pelanggan": jumlah_pelanggan,
        "jumlah_menunggu_verifikasi": (
            jumlah_menunggu_verifikasi
        ),
        "pelanggan_menunggu_verifikasi": (
            pelanggan_menunggu_verifikasi
        ),

        # Pesanan dan pendapatan
        "jumlah_pesanan": jumlah_pesanan,
        "jumlah_pesanan_menunggu": (
            jumlah_pesanan_menunggu
        ),
        "jumlah_pesanan_diproses": (
            jumlah_pesanan_diproses
        ),
        "jumlah_pesanan_selesai": (
            jumlah_pesanan_selesai
        ),
        "total_pendapatan": total_pendapatan,

        # Data master
        "jumlah_kategori": jumlah_kategori,
        "jumlah_layanan": jumlah_layanan,
        "jumlah_tarif": jumlah_tarif,
        "jumlah_promo": jumlah_promo,
        "jumlah_metode_pembayaran": (
            jumlah_metode_pembayaran
        ),
        "jumlah_area_layanan": jumlah_area_layanan,

        # Data terbaru
        "pesanan_terbaru": pesanan_terbaru,
        "aktivitas_terbaru": aktivitas_terbaru,
    }

    return render(
        request,
        "administrator/dashboard.html",
        context,
    )


@administrator_required
def log_aktivitas_list(request):
    """
    Menampilkan daftar log aktivitas yang hanya dapat
    diakses oleh administrator.
    """

    queryset = (
        LogAktivitas.objects
        .select_related("pengguna")
        .order_by("-dibuat_pada")
    )

    form = FilterLogAktivitasForm(
        request.GET or None
    )

    if form.is_valid():
        keyword = form.cleaned_data.get("keyword")
        jenis = form.cleaned_data.get("jenis")
        pengguna = form.cleaned_data.get("pengguna")
        tanggal_mulai = form.cleaned_data.get(
            "tanggal_mulai"
        )
        tanggal_selesai = form.cleaned_data.get(
            "tanggal_selesai"
        )

        if keyword:
            queryset = queryset.filter(
                Q(
                    pengguna__username__icontains=keyword
                )
                | Q(
                    pengguna__first_name__icontains=keyword
                )
                | Q(
                    pengguna__last_name__icontains=keyword
                )
                | Q(
                    aktivitas__icontains=keyword
                )
                | Q(
                    objek__icontains=keyword
                )
                | Q(
                    keterangan__icontains=keyword
                )
                | Q(
                    ip_address__icontains=keyword
                )
            )

        if jenis:
            queryset = queryset.filter(
                jenis=jenis
            )

        if pengguna:
            queryset = queryset.filter(
                pengguna=pengguna
            )

        if tanggal_mulai:
            queryset = queryset.filter(
                dibuat_pada__date__gte=tanggal_mulai
            )

        if tanggal_selesai:
            queryset = queryset.filter(
                dibuat_pada__date__lte=tanggal_selesai
            )

    total_log = queryset.count()

    paginator = Paginator(
        queryset,
        15,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "form": form,
        "page_obj": page_obj,
        "total_log": total_log,
    }

    return render(
        request,
        "administrator/log_aktivitas/list.html",
        context,
    )