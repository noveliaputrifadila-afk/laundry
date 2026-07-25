from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import render
from django.utils.dateparse import parse_date

from administrator.models import Pesanan

from .decorators import kasir_required


@kasir_required
def riwayat_transaksi(request):
    transaksi_queryset = (
        Pesanan.objects
        .filter(kasir=request.user)
        .select_related(
            "pelanggan",
            "kasir",
            "petugas_laundry",
            "metode_pembayaran",
            "promo",
        )
        .order_by("-created_at")
    )

    keyword = request.GET.get("q", "").strip()
    status_pesanan = request.GET.get(
        "status_pesanan",
        "",
    ).strip()
    status_pembayaran = request.GET.get(
        "status_pembayaran",
        "",
    ).strip()

    tanggal_mulai_string = request.GET.get(
        "tanggal_mulai",
        "",
    ).strip()
    tanggal_selesai_string = request.GET.get(
        "tanggal_selesai",
        "",
    ).strip()

    tanggal_mulai = parse_date(tanggal_mulai_string)
    tanggal_selesai = parse_date(tanggal_selesai_string)

    if keyword:
        transaksi_queryset = transaksi_queryset.filter(
            Q(kode_pesanan__icontains=keyword)
            | Q(pelanggan__username__icontains=keyword)
            | Q(pelanggan__first_name__icontains=keyword)
            | Q(pelanggan__last_name__icontains=keyword)
            | Q(pelanggan__email__icontains=keyword)
            | Q(pelanggan__nomor_hp__icontains=keyword)
        )

    if status_pesanan:
        transaksi_queryset = transaksi_queryset.filter(
            status=status_pesanan,
        )

    if status_pembayaran:
        transaksi_queryset = transaksi_queryset.filter(
            status_pembayaran=status_pembayaran,
        )

    if tanggal_mulai:
        transaksi_queryset = transaksi_queryset.filter(
            created_at__date__gte=tanggal_mulai,
        )

    if tanggal_selesai:
        transaksi_queryset = transaksi_queryset.filter(
            created_at__date__lte=tanggal_selesai,
        )

    total_transaksi = transaksi_queryset.count()

    total_nominal = (
        transaksi_queryset.aggregate(
            total=Sum("total_biaya")
        ).get("total")
        or Decimal("0.00")
    )

    total_lunas = transaksi_queryset.filter(
        status_pembayaran=(
            Pesanan.StatusPembayaran.LUNAS
        )
    ).count()

    nominal_lunas = (
        transaksi_queryset.filter(
            status_pembayaran=(
                Pesanan.StatusPembayaran.LUNAS
            )
        )
        .aggregate(total=Sum("total_biaya"))
        .get("total")
        or Decimal("0.00")
    )

    total_belum_lunas = transaksi_queryset.exclude(
        status_pembayaran=(
            Pesanan.StatusPembayaran.LUNAS
        )
    ).count()

    paginator = Paginator(
        transaksi_queryset,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "transaksi_list": page_obj.object_list,
        "page_obj": page_obj,

        "keyword": keyword,
        "status_pesanan_terpilih": status_pesanan,
        "status_pembayaran_terpilih": status_pembayaran,
        "tanggal_mulai": tanggal_mulai_string,
        "tanggal_selesai": tanggal_selesai_string,

        "status_pesanan_choices": (
            Pesanan.StatusPesanan.choices
        ),
        "status_pembayaran_choices": (
            Pesanan.StatusPembayaran.choices
        ),

        "total_transaksi": total_transaksi,
        "total_nominal": total_nominal,
        "total_lunas": total_lunas,
        "nominal_lunas": nominal_lunas,
        "total_belum_lunas": total_belum_lunas,
    }

    return render(
        request,
        "kasir/riwayat/list.html",
        context,
    )