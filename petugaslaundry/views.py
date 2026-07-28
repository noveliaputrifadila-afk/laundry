from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from administrator.models import Pesanan, RiwayatStatus, KendalaLaundry

from .decorators import petugas_required
from .forms import KendalaLaundryForm

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

STATUS_BERIKUTNYA = {
    "diterima": "menunggu_antrian",
    "menunggu_antrian": "dicuci",
    "dicuci": "dikeringkan",
    "dikeringkan": "disetrika",
    "disetrika": "dilipat",
    "dilipat": "dikemas",
}


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
        .values("status")
        .annotate(jumlah=Count("id"))
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
    mode = request.GET.get("mode", "").strip()

    if keyword:
        tugas_queryset = tugas_queryset.filter(
            Q(kode_pesanan__icontains=keyword)
            | Q(pelanggan__username__icontains=keyword)
            | Q(pelanggan__first_name__icontains=keyword)
            | Q(pelanggan__last_name__icontains=keyword)
            | Q(pelanggan__nomor_hp__icontains=keyword)
        )

    if mode == "proses":
        tugas_queryset = tugas_queryset.filter(
            status__in=(
                STATUS_BELUM_DIPROSES
                + STATUS_SEDANG_DIPROSES
            )
        )

        judul_halaman = "Proses Laundry"
        deskripsi_halaman = (
            "Daftar tugas yang masih dalam proses laundry."
        )

    elif mode == "riwayat":
        tugas_queryset = tugas_queryset.filter(
            status="selesai",
        )

        judul_halaman = "Riwayat Pekerjaan"
        deskripsi_halaman = (
            "Daftar pekerjaan laundry yang telah selesai dikerjakan."
        )

    elif status:
        tugas_queryset = tugas_queryset.filter(
            status=status,
        )

        judul_halaman = "Daftar Tugas Laundry"
        deskripsi_halaman = (
            "Kelola seluruh pesanan yang ditugaskan kepada Anda."
        )

    else:
        judul_halaman = "Daftar Tugas Laundry"
        deskripsi_halaman = (
            "Kelola seluruh pesanan yang ditugaskan kepada Anda."
        )

    total_tugas = tugas_queryset.count()

    total_belum_diproses = tugas_queryset.filter(
        status__in=STATUS_BELUM_DIPROSES,
    ).count()

    total_diproses = tugas_queryset.filter(
        status__in=STATUS_SEDANG_DIPROSES,
    ).count()

    total_selesai = tugas_queryset.filter(
        status__in=STATUS_SELESAI_PETUGAS,
    ).count()

    paginator = Paginator(
        tugas_queryset,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "tugas_list": page_obj.object_list,
        "mode": mode,
        "judul_halaman": judul_halaman,
        "deskripsi_halaman": deskripsi_halaman,
        "page_obj": page_obj,
        "keyword": keyword,
        "status_terpilih": status,
        "status_choices": Pesanan._meta.get_field(
            "status"
        ).choices,
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
        .prefetch_related("detail"),
        pk=pk,
    )

    riwayat_status = (
        pesanan.riwayat_status
        .select_related("diubah_oleh")
        .order_by("-created_at")
    )

    context = {
        "pesanan": pesanan,
        "riwayat_status": riwayat_status,
    }

    return render(
        request,
        "petugaslaundry/tugas/detail.html",
        context,
    )


@petugas_required
@transaction.atomic
def update_status(request, pk):
    pesanan = get_object_or_404(
        Pesanan,
        pk=pk,
        petugas_laundry=request.user,
    )

    if request.method != "POST":
        messages.warning(
            request,
            "Perubahan status harus dilakukan melalui tombol proses.",
        )

        return redirect(
            "petugas:tugas_detail",
            pk=pesanan.pk,
        )

    status_lama = pesanan.status

    if status_lama == "dikemas":
        if pesanan.area_layanan:
            status_baru = "siap_diantar"
        else:
            status_baru = "siap_diambil"
    else:
        status_baru = STATUS_BERIKUTNYA.get(
            status_lama
        )

    if not status_baru:
        messages.warning(
            request,
            "Status pesanan ini tidak dapat dilanjutkan lagi.",
        )

        return redirect(
            "petugas:tugas_detail",
            pk=pesanan.pk,
        )

    pesanan.status = status_baru
    pesanan.save(
        update_fields=["status"]
    )

    RiwayatStatus.objects.create(
        pesanan=pesanan,
        status_sebelumnya=status_lama,
        status_baru=status_baru,
        diubah_oleh=request.user,
    )

    messages.success(
        request,
        (
            f"Status pesanan {pesanan.kode_pesanan} "
            f"berhasil diubah menjadi "
            f"{pesanan.get_status_display()}."
        ),
    )

    return redirect(
        "petugas:tugas_detail",
        pk=pesanan.pk,
    )
@petugas_required
def kendala_list(request):
    kendala_queryset = (
        KendalaLaundry.objects
        .filter(dilaporkan_oleh=request.user)
        .select_related(
            "pesanan",
            "pesanan__pelanggan",
            "ditangani_oleh",
        )
        .order_by("-created_at")
    )

    keyword = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    mode = request.GET.get("mode", "").strip()

    if keyword:
        kendala_queryset = kendala_queryset.filter(
            Q(judul__icontains=keyword)
            | Q(deskripsi__icontains=keyword)
            | Q(pesanan__kode_pesanan__icontains=keyword)
            | Q(pesanan__pelanggan__username__icontains=keyword)
            | Q(pesanan__pelanggan__first_name__icontains=keyword)
            | Q(pesanan__pelanggan__last_name__icontains=keyword)
        )

    if mode == "riwayat":
        kendala_queryset = kendala_queryset.filter(
            status=KendalaLaundry.StatusKendala.SELESAI,
        )

        judul_halaman = "Riwayat Kendala"
        deskripsi_halaman = (
            "Daftar kendala yang sudah selesai ditangani."
        )

    elif status:
        kendala_queryset = kendala_queryset.filter(
            status=status,
        )

        judul_halaman = "Kendala Laundry"
        deskripsi_halaman = (
            "Daftar kendala yang pernah Anda laporkan."
        )

    else:
        judul_halaman = "Kendala Laundry"
        deskripsi_halaman = (
            "Daftar kendala yang pernah Anda laporkan."
        )

    total_kendala = kendala_queryset.count()

    total_dilaporkan = kendala_queryset.filter(
        status=KendalaLaundry.StatusKendala.DILAPORKAN,
    ).count()

    total_ditindaklanjuti = kendala_queryset.filter(
        status=KendalaLaundry.StatusKendala.DITINDAKLANJUTI,
    ).count()

    total_selesai = kendala_queryset.filter(
        status=KendalaLaundry.StatusKendala.SELESAI,
    ).count()

    paginator = Paginator(
        kendala_queryset,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "kendala_list": page_obj.object_list,
        "mode": mode,
        "judul_halaman": judul_halaman,
        "deskripsi_halaman": deskripsi_halaman,
        "page_obj": page_obj,
        "keyword": keyword,
        "status_terpilih": status,
        "status_choices": KendalaLaundry.StatusKendala.choices,
        "total_kendala": total_kendala,
        "total_dilaporkan": total_dilaporkan,
        "total_ditindaklanjuti": total_ditindaklanjuti,
        "total_selesai": total_selesai,
    }

    return render(
        request,
        "petugaslaundry/kendala/list.html",
        context,
    )


@petugas_required
def kendala_tambah(request, pesanan_pk):
    pesanan = get_object_or_404(
        Pesanan.objects.select_related(
            "pelanggan",
            "petugas_laundry",
        ),
        pk=pesanan_pk,
        petugas_laundry=request.user,
    )

    if request.method == "POST":
        form = KendalaLaundryForm(
            request.POST,
        )

        if form.is_valid():
            kendala = form.save(
                commit=False,
            )

            kendala.pesanan = pesanan
            kendala.dilaporkan_oleh = request.user
            kendala.status = (
                KendalaLaundry.StatusKendala.DILAPORKAN
            )

            kendala.save()

            messages.success(
                request,
                (
                    f"Kendala untuk pesanan "
                    f"{pesanan.kode_pesanan} "
                    f"berhasil dilaporkan."
                ),
            )

            return redirect(
                "petugas:kendala_detail",
                pk=kendala.pk,
            )
    else:
        form = KendalaLaundryForm()

    context = {
        "form": form,
        "pesanan": pesanan,
    }

    return render(
        request,
        "petugaslaundry/kendala/form.html",
        context,
    )


@petugas_required
def kendala_detail(request, pk):
    kendala = get_object_or_404(
        KendalaLaundry.objects
        .filter(dilaporkan_oleh=request.user)
        .select_related(
            "pesanan",
            "pesanan__pelanggan",
            "pesanan__petugas_laundry",
            "ditangani_oleh",
        ),
        pk=pk,
    )

    context = {
        "kendala": kendala,
    }

    return render(
        request,
        "petugaslaundry/kendala/detail.html",
        context,
    )