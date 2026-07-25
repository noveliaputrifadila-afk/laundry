from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render

from .decorators import administrator_required
from .models import Pesanan, RiwayatStatus, User


def get_status_choices():
    """
    Mengambil pilihan status langsung dari field Pesanan.status.

    Cara ini lebih aman karena tidak bergantung pada nama
    class enum status yang digunakan dalam model.
    """
    return Pesanan._meta.get_field("status").choices


@administrator_required
def monitoring_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    petugas_id = request.GET.get("petugas", "").strip()

    pesanan_queryset = (
        Pesanan.objects
        .select_related(
            "pelanggan",
            "kasir",
            "petugas_laundry",
        )
        .prefetch_related(
            "detail",
            "riwayat_status",
        )
        .order_by("-updated_at")
    )

    if query:
        pesanan_queryset = pesanan_queryset.filter(
            Q(kode_pesanan__icontains=query)
            | Q(pelanggan__username__icontains=query)
            | Q(pelanggan__first_name__icontains=query)
            | Q(pelanggan__last_name__icontains=query)
            | Q(petugas_laundry__username__icontains=query)
            | Q(petugas_laundry__first_name__icontains=query)
            | Q(petugas_laundry__last_name__icontains=query)
        )

    if status:
        pesanan_queryset = pesanan_queryset.filter(
            status=status,
        )

    if petugas_id:
        pesanan_queryset = pesanan_queryset.filter(
            petugas_laundry_id=petugas_id,
        )

    paginator = Paginator(pesanan_queryset, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    petugas_list = (
        User.objects
        .filter(
            role=User.Role.PETUGAS_LAUNDRY,
            is_active=True,
        )
        .order_by(
            "first_name",
            "last_name",
            "username",
        )
    )

    statistik_status = (
        Pesanan.objects
        .values("status")
        .annotate(jumlah=Count("id"))
        .order_by()
    )

    jumlah_per_status = {
        item["status"]: item["jumlah"]
        for item in statistik_status
    }

    status_cards = []

    for value, label in get_status_choices():
        status_cards.append(
            {
                "value": value,
                "label": label,
                "jumlah": jumlah_per_status.get(value, 0),
            }
        )

    context = {
        "page_obj": page_obj,
        "pesanan_list": page_obj.object_list,
        "petugas_list": petugas_list,
        "status_choices": get_status_choices(),
        "status_cards": status_cards,
        "query": query,
        "selected_status": status,
        "selected_petugas": petugas_id,
        "total_pesanan": Pesanan.objects.count(),
        "total_belum_petugas": Pesanan.objects.filter(
            petugas_laundry__isnull=True,
        ).count(),
        "total_dengan_petugas": Pesanan.objects.filter(
            petugas_laundry__isnull=False,
        ).count(),
    }

    return render(
        request,
        "administrator/operasional/monitoring_list.html",
        context,
    )


@administrator_required
def monitoring_detail(request, pk):
    pesanan = get_object_or_404(
        Pesanan.objects
        .select_related(
            "pelanggan",
            "kasir",
            "petugas_laundry",
        )
        .prefetch_related(
            "detail_pesanan",
            "riwayat_status",
        ),
        pk=pk,
    )

    riwayat_list = (
        RiwayatStatus.objects
        .filter(pesanan=pesanan)
        .select_related("diubah_oleh")
        .order_by("-created_at")
    )

    context = {
        "pesanan": pesanan,
        "riwayat_list": riwayat_list,
    }

    return render(
        request,
        "administrator/operasional/monitoring_detail.html",
        context,
    )