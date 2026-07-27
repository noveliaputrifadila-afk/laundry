from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .decorators import administrator_required
from .models import Notifikasi, Pesanan, User, RiwayatStatus


def get_petugas_laundry_queryset():
    """
    Mengambil seluruh akun petugas laundry yang aktif.
    """
    return (
        User.objects.filter(
            role=User.Role.PETUGAS_LAUNDRY,
            is_active=True,
        )
        .annotate(
            jumlah_tugas=Count(
                "pesanan_dikerjakan",
                distinct=True,
            )
        )
        .order_by("first_name", "last_name", "username")
    )


@administrator_required
def penugasan_list(request):
    query = request.GET.get("q", "").strip()
    status_penugasan = request.GET.get("penugasan", "").strip()
    petugas_id = request.GET.get("petugas", "").strip()

    pesanan_queryset = (
        Pesanan.objects.select_related(
            "pelanggan",
            "petugas_laundry",
            "kasir",
        )
        .prefetch_related(
            "detail",
        )
        .order_by("-created_at")
    )

    if query:
        pesanan_queryset = pesanan_queryset.filter(
            Q(kode_pesanan__icontains=query)
            | Q(pelanggan__username__icontains=query)
            | Q(pelanggan__first_name__icontains=query)
            | Q(pelanggan__last_name__icontains=query)
            | Q(pelanggan__nomor_hp__icontains=query)
        )

    if status_penugasan == "belum_ditugaskan":
        pesanan_queryset = pesanan_queryset.filter(
            petugas_laundry__isnull=True,
        )
    elif status_penugasan == "sudah_ditugaskan":
        pesanan_queryset = pesanan_queryset.filter(
            petugas_laundry__isnull=False,
        )

    if petugas_id:
        pesanan_queryset = pesanan_queryset.filter(
            petugas_laundry_id=petugas_id,
        )

    paginator = Paginator(pesanan_queryset, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    seluruh_pesanan = Pesanan.objects.all()

    context = {
        "page_obj": page_obj,
        "pesanan_list": page_obj.object_list,
        "petugas_list": get_petugas_laundry_queryset(),
        "query": query,
        "selected_penugasan": status_penugasan,
        "selected_petugas": petugas_id,
        "total_pesanan": seluruh_pesanan.count(),
        "total_belum_ditugaskan": seluruh_pesanan.filter(
            petugas_laundry__isnull=True,
        ).count(),
        "total_sudah_ditugaskan": seluruh_pesanan.filter(
            petugas_laundry__isnull=False,
        ).count(),
    }

    return render(
        request,
        "administrator/operasional/penugasan_list.html",
        context,
    )


@administrator_required
def penugasan_detail(request, pk):
    pesanan = get_object_or_404(
        Pesanan.objects.select_related(
            "pelanggan",
            "petugas_laundry",
            "kasir",
        ).prefetch_related(
            "detail",
            "riwayat_status",
        ),
        pk=pk,
    )

    context = {
        "pesanan": pesanan,
        "petugas_list": get_petugas_laundry_queryset(),
    }

    return render(
        request,
        "administrator/operasional/penugasan_detail.html",
        context,
    )


@administrator_required
@require_POST
def penugasan_assign(request, pk):
    pesanan = get_object_or_404(
        Pesanan.objects.select_related(
            "pelanggan",
            "petugas_laundry",
        ),
        pk=pk,
    )

    petugas_id = request.POST.get("petugas_id", "").strip()

    if not petugas_id:
        messages.error(
            request,
            "Petugas laundry wajib dipilih.",
        )
        return redirect(
            "administrator:penugasan_detail",
            pk=pesanan.pk,
        )

    petugas = get_object_or_404(
        User,
        pk=petugas_id,
        role=User.Role.PETUGAS_LAUNDRY,
        is_active=True,
    )

    petugas_lama = pesanan.petugas_laundry

    if petugas_lama and petugas_lama.pk == petugas.pk:
        messages.info(
            request,
            "Petugas tersebut sudah ditugaskan pada pesanan ini.",
        )
        return redirect(
            "administrator:penugasan_detail",
            pk=pesanan.pk,
        )

    with transaction.atomic():
        pesanan.petugas_laundry = petugas

        pesanan.save(
            update_fields=[
                "petugas_laundry",
                "updated_at",
            ]
        )

        Notifikasi.objects.create(
            penerima=petugas,
            jenis=Notifikasi.JenisNotifikasi.PENUGASAN,
            judul="Tugas laundry baru",
            pesan=(
                f"Anda mendapatkan tugas untuk pesanan "
                f"{pesanan.kode_pesanan}."
            ),
            link=f"/petugas/tugas/{pesanan.pk}/",
        )

        if petugas_lama and petugas_lama.pk != petugas.pk:
            Notifikasi.objects.create(
                penerima=petugas_lama,
                jenis=Notifikasi.JenisNotifikasi.PENUGASAN,
                judul="Penugasan dialihkan",
                pesan=(
                    f"Pesanan {pesanan.kode_pesanan} telah "
                    f"dialihkan kepada petugas lain."
                ),
                link="/petugas/tugas/",
            )

    if petugas_lama:
        messages.success(
            request,
            f"Petugas pesanan berhasil diganti menjadi {petugas.username}.",
        )
    else:
        messages.success(
            request,
            f"Pesanan berhasil ditugaskan kepada {petugas.username}.",
        )

    return redirect(
        "administrator:penugasan_detail",
        pk=pesanan.pk,
    )


@administrator_required
@require_POST
def penugasan_hapus(request, pk):
    pesanan = get_object_or_404(
        Pesanan.objects.select_related(
            "petugas_laundry",
        ),
        pk=pk,
    )

    if not pesanan.petugas_laundry:
        messages.info(
            request,
            "Pesanan tersebut belum memiliki petugas.",
        )
        return redirect(
            "administrator:penugasan_detail",
            pk=pesanan.pk,
        )

    petugas_lama = pesanan.petugas_laundry

    with transaction.atomic():
        pesanan.petugas_laundry = None

        pesanan.save(
            update_fields=[
                "petugas_laundry",
                "updated_at",
            ]
        )

        Notifikasi.objects.create(
            penerima=petugas_lama,
            pesanan=pesanan,
            jenis=Notifikasi.JenisNotifikasi.PESANAN,
            judul="Penugasan dibatalkan",
            pesan=(
                f"Penugasan Anda pada pesanan "
                f"{pesanan.kode_pesanan} telah dibatalkan."
            ),
        )

    messages.success(
        request,
        "Penugasan petugas berhasil dihapus.",
    )

    return redirect(
        "administrator:penugasan_detail",
        pk=pesanan.pk,
    )