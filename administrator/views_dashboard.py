from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.utils import timezone

from .decorators import administrator_required
from .models import (
    DetailPesanan,
    Invoice,
    KendalaLaundry,
    Pembayaran,
    Pesanan,
    User,
)


@administrator_required
def dashboard(request):
    sekarang = timezone.now()
    hari_ini = timezone.localdate()
    awal_bulan = hari_ini.replace(day=1)

    pesanan_queryset = Pesanan.objects.all()
    pembayaran_berhasil = Pembayaran.objects.filter(
        status=Pembayaran.StatusPembayaran.BERHASIL,
    )

    # =========================================================
    # STATISTIK UTAMA
    # =========================================================
    pesanan_hari_ini = pesanan_queryset.filter(
        created_at__date=hari_ini,
    ).count()

    pendapatan_hari_ini = (
        pembayaran_berhasil.filter(
            tanggal_pembayaran__date=hari_ini,
        ).aggregate(
            total=Coalesce(
                Sum("jumlah"),
                Decimal("0.00"),
            )
        )["total"]
    )

    pendapatan_bulan_ini = (
        pembayaran_berhasil.filter(
            tanggal_pembayaran__date__gte=awal_bulan,
            tanggal_pembayaran__date__lte=hari_ini,
        ).aggregate(
            total=Coalesce(
                Sum("jumlah"),
                Decimal("0.00"),
            )
        )["total"]
    )

    pelanggan_aktif = User.objects.filter(
        role=User.Role.PELANGGAN,
        is_active=True,
        is_verified=True,
    ).count()

    invoice_belum_dibayar = Invoice.objects.exclude(
        status__in=[
            Invoice.StatusInvoice.LUNAS,
            Invoice.StatusInvoice.DIBATALKAN,
        ]
    ).count()

    status_proses = [
        Pesanan.StatusPesanan.MENUNGGU_PETUGAS,
        Pesanan.StatusPesanan.MENUNGGU_ANTRIAN,
        Pesanan.StatusPesanan.DICUCI,
        Pesanan.StatusPesanan.DIKERINGKAN,
        Pesanan.StatusPesanan.DISETRIKA,
        Pesanan.StatusPesanan.DILIPAT,
        Pesanan.StatusPesanan.DIKEMAS,
        Pesanan.StatusPesanan.SIAP_DIAMBIL,
        Pesanan.StatusPesanan.SIAP_DIANTAR,
        Pesanan.StatusPesanan.DALAM_PENGANTARAN,
    ]

    laundry_diproses = pesanan_queryset.filter(
        status__in=status_proses,
    ).count()

    laundry_selesai = pesanan_queryset.filter(
        status=Pesanan.StatusPesanan.SELESAI,
    ).count()

    kendala_aktif = KendalaLaundry.objects.exclude(
        status=KendalaLaundry.StatusKendala.SELESAI,
    ).count()

    pembayaran_menunggu = Pembayaran.objects.filter(
        status=Pembayaran.StatusPembayaran.MENUNGGU,
    ).count()

    pesanan_belum_ditugaskan = pesanan_queryset.filter(
        petugas_laundry__isnull=True,
    ).exclude(
        status__in=[
            Pesanan.StatusPesanan.MENUNGGU_PEMERIKSAAN,
            Pesanan.StatusPesanan.DITOLAK,
            Pesanan.StatusPesanan.DIBATALKAN,
            Pesanan.StatusPesanan.SELESAI,
        ]
    ).count()

    # =========================================================
    # GRAFIK PENDAPATAN 7 HARI
    # =========================================================
    label_pendapatan = []
    data_pendapatan = []
    data_pesanan_harian = []

    for jumlah_hari in range(6, -1, -1):
        tanggal = hari_ini - timedelta(days=jumlah_hari)

        pendapatan = (
            pembayaran_berhasil.filter(
                tanggal_pembayaran__date=tanggal,
            ).aggregate(
                total=Coalesce(
                    Sum("jumlah"),
                    Decimal("0.00"),
                )
            )["total"]
        )

        jumlah_pesanan = pesanan_queryset.filter(
            created_at__date=tanggal,
        ).count()

        label_pendapatan.append(
            tanggal.strftime("%d %b")
        )
        data_pendapatan.append(float(pendapatan))
        data_pesanan_harian.append(jumlah_pesanan)

    # =========================================================
    # GRAFIK STATUS PESANAN
    # =========================================================
    agregasi_status = {
        item["status"]: item["total"]
        for item in pesanan_queryset.values("status").annotate(
            total=Count("id")
        )
    }

    label_status = []
    data_status = []

    for value, label in Pesanan.StatusPesanan.choices:
        jumlah = agregasi_status.get(value, 0)

        if jumlah > 0:
            label_status.append(label)
            data_status.append(jumlah)

    # =========================================================
    # PESANAN TERBARU
    # =========================================================
    pesanan_terbaru = (
        pesanan_queryset.select_related(
            "pelanggan",
            "petugas_laundry",
            "metode_pembayaran",
        )
        .prefetch_related("detail__layanan")
        .order_by("-created_at")[:8]
    )

    # =========================================================
    # TOP LAYANAN
    # =========================================================
    top_layanan = (
        DetailPesanan.objects.values(
            "layanan__nama",
            "layanan__satuan",
        )
        .annotate(
            jumlah_transaksi=Count(
                "pesanan",
                distinct=True,
            ),
            total_item=Coalesce(
                Sum("jumlah"),
                Decimal("0.00"),
            ),
            total_pendapatan=Coalesce(
                Sum("subtotal"),
                Decimal("0.00"),
            ),
        )
        .order_by("-jumlah_transaksi", "-total_item")[:5]
    )

    # =========================================================
    # TOP PETUGAS
    # =========================================================
    top_petugas = (
        User.objects.filter(
            role=User.Role.PETUGAS_LAUNDRY,
            is_active=True,
        )
        .annotate(
            total_tugas=Count(
                "pesanan_dikerjakan",
                distinct=True,
            ),
            tugas_aktif=Count(
                "pesanan_dikerjakan",
                filter=Q(
                    pesanan_dikerjakan__status__in=status_proses,
                ),
                distinct=True,
            ),
            tugas_selesai=Count(
                "pesanan_dikerjakan",
                filter=Q(
                    pesanan_dikerjakan__status=(
                        Pesanan.StatusPesanan.SELESAI
                    ),
                ),
                distinct=True,
            ),
        )
        .order_by("-tugas_selesai", "-total_tugas")[:5]
    )

    # =========================================================
    # INVOICE BELUM LUNAS
    # =========================================================
    invoice_terbaru = (
        Invoice.objects.exclude(
            status__in=[
                Invoice.StatusInvoice.LUNAS,
                Invoice.StatusInvoice.DIBATALKAN,
            ]
        )
        .select_related(
            "pesanan",
            "pesanan__pelanggan",
        )
        .order_by("tanggal_jatuh_tempo", "-tanggal_terbit")[:6]
    )

    # =========================================================
    # KENDALA TERBARU
    # =========================================================
    kendala_terbaru = (
        KendalaLaundry.objects.exclude(
            status=KendalaLaundry.StatusKendala.SELESAI,
        )
        .select_related(
            "pesanan",
            "dilaporkan_oleh",
            "ditangani_oleh",
        )
        .order_by("-created_at")[:5]
    )

    # =========================================================
    # PESANAN TERLAMBAT
    # =========================================================
    pesanan_terlambat = (
        pesanan_queryset.filter(
            estimasi_selesai__lt=sekarang,
        )
        .exclude(
            status__in=[
                Pesanan.StatusPesanan.SELESAI,
                Pesanan.StatusPesanan.DIBATALKAN,
                Pesanan.StatusPesanan.DITOLAK,
            ]
        )
        .select_related(
            "pelanggan",
            "petugas_laundry",
        )
        .order_by("estimasi_selesai")[:5]
    )

    context = {
        "hari_ini": hari_ini,
        "now": sekarang,


        # KPI
        "pesanan_hari_ini": pesanan_hari_ini,
        "pendapatan_hari_ini": pendapatan_hari_ini,
        "pendapatan_bulan_ini": pendapatan_bulan_ini,
        "pelanggan_aktif": pelanggan_aktif,
        "invoice_belum_dibayar": invoice_belum_dibayar,
        "laundry_diproses": laundry_diproses,
        "laundry_selesai": laundry_selesai,
        "kendala_aktif": kendala_aktif,
        "pembayaran_menunggu": pembayaran_menunggu,
        "pesanan_belum_ditugaskan": pesanan_belum_ditugaskan,

        # Tabel
        "pesanan_terbaru": pesanan_terbaru,
        "top_layanan": top_layanan,
        "top_petugas": top_petugas,
        "invoice_terbaru": invoice_terbaru,
        "kendala_terbaru": kendala_terbaru,
        "pesanan_terlambat": pesanan_terlambat,

        # Chart
        "label_pendapatan": label_pendapatan,
        "data_pendapatan": data_pendapatan,
        "data_pesanan_harian": data_pesanan_harian,
        "label_status": label_status,
        "data_status": data_status,
    }

    return render(
        request,
        "administrator/dashboard.html",
        context,
    )