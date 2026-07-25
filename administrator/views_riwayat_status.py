from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .decorators import administrator_required
from .models import Pesanan, RiwayatStatus, User


def get_status_choices():
    return Pesanan._meta.get_field("status").choices


@administrator_required
def riwayat_status_list(request):
    query = request.GET.get("q", "").strip()
    status_lama = request.GET.get("status_lama", "").strip()
    status_baru = request.GET.get("status_baru", "").strip()
    pengubah_id = request.GET.get("pengubah", "").strip()

    queryset = (
        RiwayatStatus.objects
        .select_related(
            "pesanan",
            "pesanan__pelanggan",
            "pesanan__petugas_laundry",
            "diubah_oleh",
        )
        .order_by("-created_at")
    )

    if query:
        queryset = queryset.filter(
            Q(pesanan__kode_pesanan__icontains=query)
            | Q(pesanan__pelanggan__username__icontains=query)
            | Q(pesanan__pelanggan__first_name__icontains=query)
            | Q(pesanan__pelanggan__last_name__icontains=query)
            | Q(diubah_oleh__username__icontains=query)
            | Q(diubah_oleh__first_name__icontains=query)
            | Q(diubah_oleh__last_name__icontains=query)
            | Q(catatan__icontains=query)
        )

    if status_lama:
        queryset = queryset.filter(status_lama=status_lama)

    if status_baru:
        queryset = queryset.filter(status_baru=status_baru)

    if pengubah_id:
        queryset = queryset.filter(diubah_oleh_id=pengubah_id)

    paginator = Paginator(queryset, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    pengubah_list = (
        User.objects
        .filter(perubahan_status_pesanan__isnull=False)
        .distinct()
        .order_by(
            "first_name",
            "last_name",
            "username",
        )
    )

    seluruh_riwayat = RiwayatStatus.objects.all()
    hari_ini = timezone.localdate()

    context = {
        "page_obj": page_obj,
        "riwayat_list": page_obj.object_list,
        "status_choices": get_status_choices(),
        "pengubah_list": pengubah_list,
        "query": query,
        "selected_status_lama": status_lama,
        "selected_status_baru": status_baru,
        "selected_pengubah": pengubah_id,
        "total_riwayat": seluruh_riwayat.count(),
        "total_hari_ini": seluruh_riwayat.filter(
            created_at__date=hari_ini,
        ).count(),
        "total_diperbarui_petugas": seluruh_riwayat.filter(
            diubah_oleh__role=User.Role.PETUGAS_LAUNDRY,
        ).count(),
        "total_diperbarui_kasir": seluruh_riwayat.filter(
            diubah_oleh__role=User.Role.KASIR,
        ).count(),
    }

    return render(
        request,
        "administrator/operasional/riwayat_status_list.html",
        context,
    )


@administrator_required
def riwayat_status_detail(request, pk):
    riwayat = get_object_or_404(
        RiwayatStatus.objects.select_related(
            "pesanan",
            "pesanan__pelanggan",
            "pesanan__kasir",
            "pesanan__petugas_laundry",
            "diubah_oleh",
        ),
        pk=pk,
    )

    riwayat_pesanan = (
        RiwayatStatus.objects
        .filter(pesanan=riwayat.pesanan)
        .select_related("diubah_oleh")
        .order_by("-created_at")
    )

    context = {
        "riwayat": riwayat,
        "pesanan": riwayat.pesanan,
        "riwayat_pesanan": riwayat_pesanan,
    }

    return render(
        request,
        "administrator/operasional/riwayat_status_detail.html",
        context,
    )