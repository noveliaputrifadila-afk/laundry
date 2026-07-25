from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from .decorators import administrator_required
from .models import AreaLayanan, Notifikasi, Pesanan, User


JENIS_ANTAR_JEMPUT = [
    Pesanan.JenisPengantaran.JEMPUT,
    Pesanan.JenisPengantaran.ANTAR,
    Pesanan.JenisPengantaran.ANTAR_JEMPUT,
]


def get_petugas_queryset():
    return User.objects.filter(
        role=User.Role.PETUGAS_LAUNDRY,
        is_active=True,
    ).order_by(
        "first_name",
        "last_name",
        "username",
    )


def hitung_biaya_antar_jemput(jenis_pengantaran, area_layanan):
    """
    Menghitung biaya berdasarkan area dan jenis layanan.
    """
    if not area_layanan:
        return Decimal("0.00")

    if jenis_pengantaran == Pesanan.JenisPengantaran.JEMPUT:
        return area_layanan.biaya_jemput

    if jenis_pengantaran == Pesanan.JenisPengantaran.ANTAR:
        return area_layanan.biaya_antar

    if jenis_pengantaran == Pesanan.JenisPengantaran.ANTAR_JEMPUT:
        return area_layanan.total_biaya_antar_jemput

    return Decimal("0.00")


@administrator_required
def antar_jemput_list(request):
    query = request.GET.get("q", "").strip()
    jenis = request.GET.get("jenis", "").strip()
    status = request.GET.get("status", "").strip()
    area_id = request.GET.get("area", "").strip()
    petugas_id = request.GET.get("petugas", "").strip()
    jadwal = request.GET.get("jadwal", "").strip()

    queryset = (
        Pesanan.objects.filter(
            jenis_pengantaran__in=JENIS_ANTAR_JEMPUT,
        )
        .select_related(
            "pelanggan",
            "petugas_laundry",
            "area_layanan",
        )
        .order_by(
            "tanggal_penjemputan",
            "-created_at",
        )
    )

    if query:
        queryset = queryset.filter(
            Q(kode_pesanan__icontains=query)
            | Q(pelanggan__username__icontains=query)
            | Q(pelanggan__first_name__icontains=query)
            | Q(pelanggan__last_name__icontains=query)
            | Q(pelanggan__nomor_hp__icontains=query)
            | Q(alamat_penjemputan__icontains=query)
            | Q(alamat_pengantaran__icontains=query)
        )

    if jenis:
        queryset = queryset.filter(jenis_pengantaran=jenis)

    if status:
        queryset = queryset.filter(status=status)

    if area_id:
        queryset = queryset.filter(area_layanan_id=area_id)

    if petugas_id:
        queryset = queryset.filter(petugas_laundry_id=petugas_id)

    if jadwal == "belum_diatur":
        queryset = queryset.filter(
            tanggal_penjemputan__isnull=True,
        )
    elif jadwal == "sudah_diatur":
        queryset = queryset.filter(
            tanggal_penjemputan__isnull=False,
        )

    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    seluruh_antar_jemput = Pesanan.objects.filter(
        jenis_pengantaran__in=JENIS_ANTAR_JEMPUT,
    )

    total_biaya = seluruh_antar_jemput.aggregate(
        total=Sum("biaya_antar_jemput")
    )["total"] or Decimal("0.00")

    context = {
        "page_obj": page_obj,
        "pesanan_list": page_obj.object_list,
        "jenis_choices": [
            pilihan
            for pilihan in Pesanan.JenisPengantaran.choices
            if pilihan[0] != Pesanan.JenisPengantaran.DATANG_SENDIRI
        ],
        "status_choices": Pesanan.StatusPesanan.choices,
        "area_list": AreaLayanan.objects.filter(
            is_active=True,
        ).order_by("nama_area"),
        "petugas_list": get_petugas_queryset(),
        "query": query,
        "selected_jenis": jenis,
        "selected_status": status,
        "selected_area": area_id,
        "selected_petugas": petugas_id,
        "selected_jadwal": jadwal,
        "total_antar_jemput": seluruh_antar_jemput.count(),
        "total_jemput": seluruh_antar_jemput.filter(
            jenis_pengantaran=Pesanan.JenisPengantaran.JEMPUT,
        ).count(),
        "total_antar": seluruh_antar_jemput.filter(
            jenis_pengantaran=Pesanan.JenisPengantaran.ANTAR,
        ).count(),
        "total_antar_dan_jemput": seluruh_antar_jemput.filter(
            jenis_pengantaran=Pesanan.JenisPengantaran.ANTAR_JEMPUT,
        ).count(),
        "total_biaya_antar_jemput": total_biaya,
    }

    return render(
        request,
        "administrator/operasional/antar_jemput_list.html",
        context,
    )


@administrator_required
def antar_jemput_detail(request, pk):
    pesanan = get_object_or_404(
        Pesanan.objects.select_related(
            "pelanggan",
            "kasir",
            "petugas_laundry",
            "area_layanan",
        ).prefetch_related(
            "detail",
            "riwayat_status",
        ),
        pk=pk,
        jenis_pengantaran__in=JENIS_ANTAR_JEMPUT,
    )

    context = {
        "pesanan": pesanan,
        "area_list": AreaLayanan.objects.filter(
            is_active=True,
        ).order_by("nama_area"),
        "petugas_list": get_petugas_queryset(),
        "jenis_choices": [
            pilihan
            for pilihan in Pesanan.JenisPengantaran.choices
            if pilihan[0] != Pesanan.JenisPengantaran.DATANG_SENDIRI
        ],
    }

    return render(
        request,
        "administrator/operasional/antar_jemput_detail.html",
        context,
    )


@administrator_required
@require_POST
def antar_jemput_update(request, pk):
    pesanan = get_object_or_404(
        Pesanan,
        pk=pk,
        jenis_pengantaran__in=JENIS_ANTAR_JEMPUT,
    )

    jenis_pengantaran = request.POST.get(
        "jenis_pengantaran",
        "",
    ).strip()

    area_id = request.POST.get("area_layanan", "").strip()
    petugas_id = request.POST.get("petugas_laundry", "").strip()

    alamat_penjemputan = request.POST.get(
        "alamat_penjemputan",
        "",
    ).strip()

    alamat_pengantaran = request.POST.get(
        "alamat_pengantaran",
        "",
    ).strip()

    tanggal_penjemputan_input = request.POST.get(
        "tanggal_penjemputan",
        "",
    ).strip()

    tanggal_pengambilan_input = request.POST.get(
        "tanggal_pengambilan",
        "",
    ).strip()

    catatan_kasir = request.POST.get(
        "catatan_kasir",
        "",
    ).strip()

    jenis_valid = {
        value
        for value, label in Pesanan.JenisPengantaran.choices
        if value != Pesanan.JenisPengantaran.DATANG_SENDIRI
    }

    if jenis_pengantaran not in jenis_valid:
        messages.error(
            request,
            "Jenis layanan antar-jemput tidak valid.",
        )
        return redirect(
            "administrator:antar_jemput_detail",
            pk=pesanan.pk,
        )

    area_layanan = None

    if area_id:
        area_layanan = get_object_or_404(
            AreaLayanan,
            pk=area_id,
            is_active=True,
        )

    petugas = None

    if petugas_id:
        petugas = get_object_or_404(
            User,
            pk=petugas_id,
            role=User.Role.PETUGAS_LAUNDRY,
            is_active=True,
        )

    perlu_jemput = jenis_pengantaran in {
        Pesanan.JenisPengantaran.JEMPUT,
        Pesanan.JenisPengantaran.ANTAR_JEMPUT,
    }

    perlu_antar = jenis_pengantaran in {
        Pesanan.JenisPengantaran.ANTAR,
        Pesanan.JenisPengantaran.ANTAR_JEMPUT,
    }

    if perlu_jemput and not alamat_penjemputan:
        messages.error(
            request,
            "Alamat penjemputan wajib diisi.",
        )
        return redirect(
            "administrator:antar_jemput_detail",
            pk=pesanan.pk,
        )

    if perlu_antar and not alamat_pengantaran:
        messages.error(
            request,
            "Alamat pengantaran wajib diisi.",
        )
        return redirect(
            "administrator:antar_jemput_detail",
            pk=pesanan.pk,
        )

    tanggal_penjemputan = None
    tanggal_pengambilan = None

    if tanggal_penjemputan_input:
        tanggal_penjemputan = parse_datetime(
            tanggal_penjemputan_input
        )

        if tanggal_penjemputan is None:
            messages.error(
                request,
                "Format tanggal penjemputan tidak valid.",
            )
            return redirect(
                "administrator:antar_jemput_detail",
                pk=pesanan.pk,
            )

    if tanggal_pengambilan_input:
        tanggal_pengambilan = parse_datetime(
            tanggal_pengambilan_input
        )

        if tanggal_pengambilan is None:
            messages.error(
                request,
                "Format tanggal pengantaran tidak valid.",
            )
            return redirect(
                "administrator:antar_jemput_detail",
                pk=pesanan.pk,
            )

    biaya = hitung_biaya_antar_jemput(
        jenis_pengantaran,
        area_layanan,
    )

    petugas_lama = pesanan.petugas_laundry

    with transaction.atomic():
        pesanan.jenis_pengantaran = jenis_pengantaran
        pesanan.area_layanan = area_layanan
        pesanan.petugas_laundry = petugas
        pesanan.alamat_penjemputan = (
            alamat_penjemputan if perlu_jemput else ""
        )
        pesanan.alamat_pengantaran = (
            alamat_pengantaran if perlu_antar else ""
        )
        pesanan.tanggal_penjemputan = (
            tanggal_penjemputan if perlu_jemput else None
        )
        pesanan.tanggal_pengambilan = (
            tanggal_pengambilan if perlu_antar else None
        )
        pesanan.biaya_antar_jemput = biaya
        pesanan.catatan_kasir = catatan_kasir

        pesanan.save(
            update_fields=[
                "jenis_pengantaran",
                "area_layanan",
                "petugas_laundry",
                "alamat_penjemputan",
                "alamat_pengantaran",
                "tanggal_penjemputan",
                "tanggal_pengambilan",
                "biaya_antar_jemput",
                "catatan_kasir",
                "total_biaya",
                "updated_at",
            ]
        )

        if petugas and (
            not petugas_lama or petugas_lama.pk != petugas.pk
        ):
            Notifikasi.objects.create(
                penerima=petugas,
                pesanan=pesanan,
                jenis=Notifikasi.JenisNotifikasi.PESANAN,
                judul="Tugas antar-jemput",
                pesan=(
                    f"Anda ditugaskan menangani layanan "
                    f"{pesanan.get_jenis_pengantaran_display()} "
                    f"untuk pesanan {pesanan.kode_pesanan}."
                ),
                url=(
                    f"/administrator/operasional/"
                    f"antar-jemput/{pesanan.pk}/"
                ),
            )

        Notifikasi.objects.create(
            penerima=pesanan.pelanggan,
            pesanan=pesanan,
            jenis=Notifikasi.JenisNotifikasi.PESANAN,
            judul="Jadwal antar-jemput diperbarui",
            pesan=(
                f"Informasi antar-jemput pesanan "
                f"{pesanan.kode_pesanan} telah diperbarui."
            ),
        )

    messages.success(
        request,
        "Informasi antar-jemput berhasil diperbarui.",
    )

    return redirect(
        "administrator:antar_jemput_detail",
        pk=pesanan.pk,
    )