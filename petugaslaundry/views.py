from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404
from administrator.models import Pesanan

from .decorators import petugas_required


STATUS_SEDANG_DIPROSES = [
    "dicuci",
    "dikeringkan",
    "disetrika",
    "dilipat",
    "dikemas",
]

STATUS_BELUM_DIPROSES = [
    "diterima",
    "menunggu_antrian",
]

STATUS_SELESAI_PETUGAS = [
    "siap_diambil",
    "siap_diantar",
    "dalam_pengantaran",
    "selesai",
]


@petugas_required
def dashboard(request):
    hari_ini = timezone.localdate()

    semua_tugas = (
        Pesanan.objects
        .filter(petugas_laundry=request.user)
        .select_related(
            "pelanggan",
            "kasir",
            "metode_pembayaran",
            "area_layanan",
        )
        .prefetch_related("detail")
    )

    total_tugas = semua_tugas.count()

    tugas_belum_diproses = semua_tugas.filter(
        status__in=STATUS_BELUM_DIPROSES,
    ).count()

    tugas_sedang_diproses = semua_tugas.filter(
        status__in=STATUS_SEDANG_DIPROSES,
    ).count()

    tugas_selesai = semua_tugas.filter(
        status__in=STATUS_SELESAI_PETUGAS,
    ).count()

    tugas_selesai_hari_ini = semua_tugas.filter(
        status="selesai",
        tanggal_selesai__date=hari_ini,
    ).count()

    tugas_aktif = (
        semua_tugas
        .exclude(
            status__in=[
                "selesai",
                "dibatalkan",
                "ditolak",
            ]
        )
        .order_by(
            "estimasi_selesai",
            "-created_at",
        )[:5]
    )

    tugas_terbaru = (
        semua_tugas
        .order_by("-created_at")[:5]
    )

    status_statistik = (
        semua_tugas
        .values(
            "status",
        )
        .annotate(
            jumlah=Count("id"),
        )
        .order_by("status")
    )

    status_labels = dict(
        Pesanan._meta.get_field("status").choices
    )

    statistik_status = [
        {
            "status": item["status"],
            "label": status_labels.get(
                item["status"],
                item["status"],
            ),
            "jumlah": item["jumlah"],
        }
        for item in status_statistik
    ]

    context = {
        "hari_ini": hari_ini,
        "total_tugas": total_tugas,
        "tugas_belum_diproses": tugas_belum_diproses,
        "tugas_sedang_diproses": tugas_sedang_diproses,
        "tugas_selesai": tugas_selesai,
        "tugas_selesai_hari_ini": tugas_selesai_hari_ini,
        "tugas_aktif": tugas_aktif,
        "tugas_terbaru": tugas_terbaru,
        "statistik_status": statistik_status,
    }

    return render(
        request,
        "petugaslaundry/dashboard.html",
        context,
    )
@petugas_required
def tugas_list(request):
    tugas_queryset = (
        Pesanan.objects
        .filter(petugas_laundry=request.user)
        .select_related(
            "pelanggan",
            "kasir",
            "metode_pembayaran",
            "area_layanan",
            "promo",
        )
        .prefetch_related("detail")
        .order_by("-created_at")
    )

    keyword = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    if keyword:
        tugas_queryset = tugas_queryset.filter(
            Q(kode_pesanan__icontains=keyword)
            | Q(pelanggan__username__icontains=keyword)
            | Q(pelanggan__first_name__icontains=keyword)
            | Q(pelanggan__last_name__icontains=keyword)
            | Q(pelanggan__nomor_hp__icontains=keyword)
        )

    if status:
        tugas_queryset = tugas_queryset.filter(status=status)

    total_tugas = tugas_queryset.count()

    total_belum_diproses = tugas_queryset.filter(
        status__in=[
            "diterima",
            "menunggu_antrian",
        ]
    ).count()

    total_diproses = tugas_queryset.filter(
        status__in=[
            "dicuci",
            "dikeringkan",
            "disetrika",
            "dilipat",
            "dikemas",
        ]
    ).count()

    total_selesai = tugas_queryset.filter(
        status__in=[
            "siap_diambil",
            "siap_diantar",
            "dalam_pengantaran",
            "selesai",
        ]
    ).count()

    paginator = Paginator(tugas_queryset, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "tugas_list": page_obj.object_list,
        "page_obj": page_obj,
        "keyword": keyword,
        "status_terpilih": status,
        "status_choices": Pesanan._meta.get_field("status").choices,
        "total_tugas": total_tugas,
        "total_belum_diproses": total_belum_diproses,
        "total_diproses": total_diproses,
        "total_selesai": total_selesai,
    }

    return render(
        request,
        "petugaslaundry/tugas/list.html",
        context,
    )
@petugas_required
def tugas_detail(request, pk):
    pesanan = get_object_or_404(
        Pesanan.objects
        .filter(petugas_laundry=request.user)
        .select_related(
            "pelanggan",
            "kasir",
            "petugas_laundry",
            "metode_pembayaran",
            "area_layanan",
            "promo",
        )
        .prefetch_related(
            "detail",
            "riwayat_status",
        ),
        pk=pk,
    )

    context = {
        "pesanan": pesanan,
    }

    return render(
        request,
        "petugaslaundry/tugas/detail.html",
        context,
    )