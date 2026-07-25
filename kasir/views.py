from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.utils import timezone

from administrator.models import (
    Invoice,
    Pembayaran,
    Pesanan,
    User,
)

from .decorators import kasir_required


@kasir_required
def dashboard(request):
    sekarang = timezone.now()
    hari_ini = timezone.localdate()
    awal_bulan = hari_ini.replace(day=1)

    user = request.user

    # Administrator dapat melihat seluruh transaksi.
    # Kasir hanya melihat transaksi yang ditangani sendiri.
    if user.role == User.Role.ADMINISTRATOR:
        pesanan_queryset = Pesanan.objects.all()
        invoice_queryset = Invoice.objects.all()
        pembayaran_queryset = Pembayaran.objects.all()
    else:
        pesanan_queryset = Pesanan.objects.filter(
            Q(kasir=user) | Q(kasir__isnull=True),
        )

        invoice_queryset = Invoice.objects.filter(
            dibuat_oleh=user,
        )

        pembayaran_queryset = Pembayaran.objects.filter(
            Q(diverifikasi_oleh=user)
            | Q(
                diverifikasi_oleh__isnull=True,
                status=Pembayaran.StatusPembayaran.MENUNGGU,
            )
        )

    # =====================================================
    # KPI
    # =====================================================
    pesanan_hari_ini = pesanan_queryset.filter(
        created_at__date=hari_ini,
    ).count()

    invoice_hari_ini = invoice_queryset.filter(
        tanggal_terbit__date=hari_ini,
    ).count()

    pembayaran_hari_ini = pembayaran_queryset.filter(
        tanggal_pembayaran__date=hari_ini,
        status=Pembayaran.StatusPembayaran.BERHASIL,
    ).count()

    pendapatan_hari_ini = pembayaran_queryset.filter(
        tanggal_pembayaran__date=hari_ini,
        status=Pembayaran.StatusPembayaran.BERHASIL,
    ).aggregate(
        total=Coalesce(
            Sum("jumlah"),
            Decimal("0.00"),
        )
    )["total"]

    pendapatan_bulan_ini = pembayaran_queryset.filter(
        tanggal_pembayaran__date__gte=awal_bulan,
        tanggal_pembayaran__date__lte=hari_ini,
        status=Pembayaran.StatusPembayaran.BERHASIL,
    ).aggregate(
        total=Coalesce(
            Sum("jumlah"),
            Decimal("0.00"),
        )
    )["total"]

    belum_dibayar = pesanan_queryset.filter(
        status_pembayaran=Pesanan.StatusPembayaran.BELUM_DIBAYAR,
    ).count()

    pembayaran_menunggu = pembayaran_queryset.filter(
        status=Pembayaran.StatusPembayaran.MENUNGGU,
    ).count()

    pesanan_menunggu_konfirmasi = pesanan_queryset.filter(
        status=Pesanan.StatusPesanan.MENUNGGU_KONFIRMASI,
    ).count()

    pesanan_selesai_hari_ini = pesanan_queryset.filter(
        status=Pesanan.StatusPesanan.SELESAI,
        tanggal_selesai__date=hari_ini,
    ).count()

    # =====================================================
    # GRAFIK TRANSAKSI TUJUH HARI
    # =====================================================
    label_grafik = []
    data_pesanan = []
    data_pendapatan = []

    for selisih_hari in range(6, -1, -1):
        tanggal = hari_ini - timedelta(days=selisih_hari)

        jumlah_pesanan = pesanan_queryset.filter(
            created_at__date=tanggal,
        ).count()

        jumlah_pendapatan = pembayaran_queryset.filter(
            tanggal_pembayaran__date=tanggal,
            status=Pembayaran.StatusPembayaran.BERHASIL,
        ).aggregate(
            total=Coalesce(
                Sum("jumlah"),
                Decimal("0.00"),
            )
        )["total"]

        label_grafik.append(tanggal.strftime("%d %b"))
        data_pesanan.append(jumlah_pesanan)
        data_pendapatan.append(float(jumlah_pendapatan))

    # =====================================================
    # DATA TABEL
    # =====================================================
    pesanan_terbaru = (
        pesanan_queryset
        .select_related(
            "pelanggan",
            "kasir",
            "petugas_laundry",
            "metode_pembayaran",
        )
        .prefetch_related(
            "detail__layanan",
        )
        .order_by("-created_at")[:8]
    )

    pembayaran_terbaru = (
        pembayaran_queryset
        .select_related(
            "pesanan",
            "pesanan__pelanggan",
            "metode_pembayaran",
            "diverifikasi_oleh",
        )
        .order_by("-tanggal_pembayaran")[:7]
    )

    invoice_belum_lunas = (
        invoice_queryset
        .exclude(
            status__in=[
                Invoice.StatusInvoice.LUNAS,
                Invoice.StatusInvoice.DIBATALKAN,
            ]
        )
        .select_related(
            "pesanan",
            "pesanan__pelanggan",
        )
        .order_by(
            "tanggal_jatuh_tempo",
            "-tanggal_terbit",
        )[:7]
    )

    pesanan_per_status = {
        item["status"]: item["total"]
        for item in pesanan_queryset.values("status").annotate(
            total=Count("id"),
        )
    }

    label_status = []
    data_status = []

    for value, label in Pesanan.StatusPesanan.choices:
        total = pesanan_per_status.get(value, 0)

        if total:
            label_status.append(label)
            data_status.append(total)

    context = {
        "hari_ini": hari_ini,
        "sekarang": sekarang,

        "pesanan_hari_ini": pesanan_hari_ini,
        "invoice_hari_ini": invoice_hari_ini,
        "pembayaran_hari_ini": pembayaran_hari_ini,
        "pendapatan_hari_ini": pendapatan_hari_ini,
        "pendapatan_bulan_ini": pendapatan_bulan_ini,
        "belum_dibayar": belum_dibayar,
        "pembayaran_menunggu": pembayaran_menunggu,
        "pesanan_menunggu_konfirmasi": (
            pesanan_menunggu_konfirmasi
        ),
        "pesanan_selesai_hari_ini": (
            pesanan_selesai_hari_ini
        ),

        "pesanan_terbaru": pesanan_terbaru,
        "pembayaran_terbaru": pembayaran_terbaru,
        "invoice_belum_lunas": invoice_belum_lunas,

        "label_grafik": label_grafik,
        "data_pesanan": data_pesanan,
        "data_pendapatan": data_pendapatan,
        "label_status": label_status,
        "data_status": data_status,
    }

    return render(
        request,
        "kasir/dashboard.html",
        context,
    )