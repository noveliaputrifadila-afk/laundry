import csv
from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .decorators import administrator_required
from .forms_laporan import FilterLaporanPesananForm
from .models import Pesanan


def get_queryset_laporan(request):
    hari_ini = timezone.localdate()

    tanggal_awal_default = (
        hari_ini.replace(day=1).isoformat()
    )
    tanggal_akhir_default = (
        hari_ini.isoformat()
    )

    data_filter = request.GET.copy()

    if not data_filter.get("tanggal_mulai"):
        data_filter["tanggal_mulai"] = (
            tanggal_awal_default
        )

    if not data_filter.get("tanggal_selesai"):
        data_filter["tanggal_selesai"] = (
            tanggal_akhir_default
        )

    form = FilterLaporanPesananForm(data_filter)

    queryset = (
        Pesanan.objects
        .select_related(
            "pelanggan",
            "kasir",
            "petugas_laundry",
            "metode_pembayaran",
            "promo",
        )
        .all()
    )

    if not form.is_valid():
        return form, queryset.none()

    cleaned_data = form.cleaned_data

    tanggal_mulai = cleaned_data.get("tanggal_mulai")
    tanggal_selesai = cleaned_data.get("tanggal_selesai")
    status = cleaned_data.get("status")
    status_pembayaran = cleaned_data.get("status_pembayaran")
    kasir = cleaned_data.get("kasir")
    petugas_laundry = cleaned_data.get("petugas_laundry")

    if tanggal_mulai:
        queryset = queryset.filter(
            created_at__date__gte=tanggal_mulai
        )

    if tanggal_selesai:
        queryset = queryset.filter(
            created_at__date__lte=tanggal_selesai
        )

    if status:
        queryset = queryset.filter(status=status)

    if status_pembayaran:
        queryset = queryset.filter(
            status_pembayaran=status_pembayaran
        )

    if kasir:
        queryset = queryset.filter(kasir=kasir)

    if petugas_laundry:
        queryset = queryset.filter(
            petugas_laundry=petugas_laundry
        )

    return form, queryset


@administrator_required
def laporan_pesanan(request):
    form, queryset = get_queryset_laporan(
        request
    )

    ringkasan = queryset.aggregate(
        jumlah_pesanan=Count("id"),
        total_subtotal=Sum("subtotal"),
        total_diskon=Sum("diskon"),
        total_antar_jemput=Sum(
            "biaya_antar_jemput"
        ),
        total_biaya_tambahan=Sum(
            "biaya_tambahan"
        ),
        total_nilai_transaksi=Sum(
            "total_biaya"
        ),
    )

    queryset_lunas = queryset.filter(
        status_pembayaran=(
            Pesanan.StatusPembayaran.LUNAS
        )
    )

    pendapatan = queryset_lunas.aggregate(
        jumlah_transaksi_lunas=Count("id"),
        total_pendapatan=Sum("total_biaya"),
    )

    nilai_default = Decimal("0.00")

    context_ringkasan = {
        "jumlah_pesanan": (
            ringkasan["jumlah_pesanan"] or 0
        ),
        "total_subtotal": (
            ringkasan["total_subtotal"]
            or nilai_default
        ),
        "total_diskon": (
            ringkasan["total_diskon"]
            or nilai_default
        ),
        "total_antar_jemput": (
            ringkasan["total_antar_jemput"]
            or nilai_default
        ),
        "total_biaya_tambahan": (
            ringkasan["total_biaya_tambahan"]
            or nilai_default
        ),
        "total_nilai_transaksi": (
            ringkasan["total_nilai_transaksi"]
            or nilai_default
        ),
        "jumlah_transaksi_lunas": (
            pendapatan["jumlah_transaksi_lunas"]
            or 0
        ),
        "total_pendapatan": (
            pendapatan["total_pendapatan"]
            or nilai_default
        ),
    }

    jumlah_per_status = (
        queryset.values(
            "status"
        )
        .annotate(
            jumlah=Count("id")
        )
        .order_by("-jumlah")
    )

    label_status = dict(
        Pesanan.StatusPesanan.choices
    )

    data_status = [
        {
            "status": item["status"],
            "label": label_status.get(
                item["status"],
                item["status"],
            ),
            "jumlah": item["jumlah"],
        }
        for item in jumlah_per_status
    ]

    paginator = Paginator(
        queryset,
        20,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    parameter_filter = request.GET.copy()
    parameter_filter.pop("page", None)

    context = {
        "form": form,
        "page_obj": page_obj,
        "ringkasan": context_ringkasan,
        "data_status": data_status,
        "parameter_filter": (
            parameter_filter.urlencode()
        ),
    }

    return render(
        request,
        (
            "administrator/laporan/"
            "laporan_pesanan.html"
        ),
        context,
    )


def aman_untuk_csv(value):
    """
    Menghindari formula injection ketika file CSV
    dibuka melalui aplikasi spreadsheet.
    """
    if value is None:
        return ""

    value = str(value)

    if value.startswith(
        ("=", "+", "-", "@")
    ):
        return "'" + value

    return value


@administrator_required
def laporan_pesanan_csv(request):
    form, queryset = get_queryset_laporan(
        request
    )

    if not form.is_valid():
        queryset = Pesanan.objects.none()

    response = HttpResponse(
        content_type=(
            "text/csv; charset=utf-8"
        )
    )

    nama_file = (
        "laporan-pesanan-"
        f"{timezone.localdate():%Y-%m-%d}.csv"
    )

    response[
        "Content-Disposition"
    ] = f'attachment; filename="{nama_file}"'

    # Agar karakter UTF-8 terbaca baik oleh Excel.
    response.write("\ufeff")

    writer = csv.writer(response)

    writer.writerow(
        [
            "No",
            "Kode Pesanan",
            "Tanggal",
            "Pelanggan",
            "Nomor HP",
            "Kasir",
            "Petugas Laundry",
            "Metode Pembayaran",
            "Status Pesanan",
            "Status Pembayaran",
            "Subtotal",
            "Diskon",
            "Biaya Antar-Jemput",
            "Biaya Tambahan",
            "Total",
        ]
    )

    for nomor, pesanan in enumerate(
        queryset.iterator(),
        start=1,
    ):
        nama_pelanggan = (
            pesanan.pelanggan.get_full_name()
            or pesanan.pelanggan.username
        )

        nama_kasir = ""

        if pesanan.kasir:
            nama_kasir = (
                pesanan.kasir.get_full_name()
                or pesanan.kasir.username
            )

        nama_petugas = ""

        if pesanan.petugas_laundry:
            nama_petugas = (
                pesanan.petugas_laundry
                .get_full_name()
                or pesanan.petugas_laundry.username
            )

        writer.writerow(
            [
                nomor,
                aman_untuk_csv(
                    pesanan.kode_pesanan
                ),
                timezone.localtime(
                    pesanan.created_at
                ).strftime("%d-%m-%Y %H:%M"),
                aman_untuk_csv(
                    nama_pelanggan
                ),
                aman_untuk_csv(
                    pesanan.pelanggan.nomor_hp
                ),
                aman_untuk_csv(
                    nama_kasir
                ),
                aman_untuk_csv(
                    nama_petugas
                ),
                aman_untuk_csv(
                    pesanan.metode_pembayaran.nama
                ),
                pesanan.get_status_display(),
                (
                    pesanan
                    .get_status_pembayaran_display()
                ),
                pesanan.subtotal,
                pesanan.diskon,
                pesanan.biaya_antar_jemput,
                pesanan.biaya_tambahan,
                pesanan.total_biaya,
            ]
        )

    return response