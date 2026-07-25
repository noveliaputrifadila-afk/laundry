from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .decorators import administrator_required
from .models import KendalaLaundry, Notifikasi


@administrator_required
def kendala_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    kendala_queryset = (
        KendalaLaundry.objects
        .select_related(
            "pesanan",
            "pesanan__pelanggan",
            "dilaporkan_oleh",
            "ditangani_oleh",
        )
        .order_by("-created_at")
    )

    if query:
        kendala_queryset = kendala_queryset.filter(
            Q(judul__icontains=query)
            | Q(deskripsi__icontains=query)
            | Q(pesanan__kode_pesanan__icontains=query)
            | Q(pesanan__pelanggan__username__icontains=query)
            | Q(pesanan__pelanggan__first_name__icontains=query)
            | Q(pesanan__pelanggan__last_name__icontains=query)
            | Q(dilaporkan_oleh__username__icontains=query)
        )

    if status:
        kendala_queryset = kendala_queryset.filter(status=status)

    context = {
        "kendala_list": kendala_queryset,
        "query": query,
        "selected_status": status,
        "status_choices": KendalaLaundry.StatusKendala.choices,
        "total_data": kendala_queryset.count(),
        "total_dilaporkan": KendalaLaundry.objects.filter(
            status=KendalaLaundry.StatusKendala.DILAPORKAN
        ).count(),
        "total_ditindaklanjuti": KendalaLaundry.objects.filter(
            status=KendalaLaundry.StatusKendala.DITINDAKLANJUTI
        ).count(),
        "total_selesai": KendalaLaundry.objects.filter(
            status=KendalaLaundry.StatusKendala.SELESAI
        ).count(),
    }

    return render(
        request,
        "administrator/kendala/kendala_list.html",
        context,
    )


@administrator_required
def kendala_detail(request, pk):
    kendala = get_object_or_404(
        KendalaLaundry.objects.select_related(
            "pesanan",
            "pesanan__pelanggan",
            "pesanan__kasir",
            "pesanan__petugas_laundry",
            "dilaporkan_oleh",
            "ditangani_oleh",
        ),
        pk=pk,
    )

    return render(
        request,
        "administrator/kendala/kendala_detail.html",
        {
            "kendala": kendala,
        },
    )


@administrator_required
@require_POST
def kendala_tindak_lanjut(request, pk):
    kendala = get_object_or_404(
        KendalaLaundry.objects.select_related(
            "pesanan",
            "dilaporkan_oleh",
        ),
        pk=pk,
    )

    tanggapan = request.POST.get("tanggapan", "").strip()

    if not tanggapan:
        messages.error(
            request,
            "Tanggapan wajib diisi.",
        )
        return redirect(
            "administrator:kendala_detail",
            pk=kendala.pk,
        )

    if kendala.status == KendalaLaundry.StatusKendala.SELESAI:
        messages.error(
            request,
            "Kendala yang sudah selesai tidak dapat ditindaklanjuti kembali.",
        )
        return redirect(
            "administrator:kendala_detail",
            pk=kendala.pk,
        )

    with transaction.atomic():
        kendala.status = (
            KendalaLaundry.StatusKendala.DITINDAKLANJUTI
        )
        kendala.tanggapan_kasir = tanggapan
        kendala.ditangani_oleh = request.user

        kendala.save(
            update_fields=[
                "status",
                "tanggapan_kasir",
                "ditangani_oleh",
                "updated_at",
            ]
        )

        Notifikasi.objects.create(
            penerima=kendala.dilaporkan_oleh,
            pesanan=kendala.pesanan,
            jenis=Notifikasi.JenisNotifikasi.KENDALA,
            judul="Kendala sedang ditindaklanjuti",
            pesan=(
                f"Kendala '{kendala.judul}' pada pesanan "
                f"{kendala.pesanan.kode_pesanan} sedang ditindaklanjuti."
            ),
        )

    messages.success(
        request,
        "Kendala berhasil ditindaklanjuti.",
    )

    return redirect(
        "administrator:kendala_detail",
        pk=kendala.pk,
    )


@administrator_required
@require_POST
def kendala_selesaikan(request, pk):
    kendala = get_object_or_404(
        KendalaLaundry.objects.select_related(
            "pesanan",
            "dilaporkan_oleh",
        ),
        pk=pk,
    )

    tanggapan = request.POST.get("tanggapan", "").strip()

    if not tanggapan:
        messages.error(
            request,
            "Penyelesaian atau tanggapan akhir wajib diisi.",
        )
        return redirect(
            "administrator:kendala_detail",
            pk=kendala.pk,
        )

    if kendala.status == KendalaLaundry.StatusKendala.SELESAI:
        messages.info(
            request,
            "Kendala tersebut sudah diselesaikan sebelumnya.",
        )
        return redirect(
            "administrator:kendala_detail",
            pk=kendala.pk,
        )

    with transaction.atomic():
        kendala.status = KendalaLaundry.StatusKendala.SELESAI
        kendala.tanggapan_kasir = tanggapan
        kendala.ditangani_oleh = request.user

        kendala.save(
            update_fields=[
                "status",
                "tanggapan_kasir",
                "ditangani_oleh",
                "updated_at",
            ]
        )

        Notifikasi.objects.create(
            penerima=kendala.dilaporkan_oleh,
            pesanan=kendala.pesanan,
            jenis=Notifikasi.JenisNotifikasi.KENDALA,
            judul="Kendala telah diselesaikan",
            pesan=(
                f"Kendala '{kendala.judul}' pada pesanan "
                f"{kendala.pesanan.kode_pesanan} telah diselesaikan."
            ),
        )

        if kendala.pesanan.pelanggan_id:
            Notifikasi.objects.create(
                penerima=kendala.pesanan.pelanggan,
                pesanan=kendala.pesanan,
                jenis=Notifikasi.JenisNotifikasi.KENDALA,
                judul="Kendala pesanan telah diselesaikan",
                pesan=(
                    f"Kendala pada pesanan "
                    f"{kendala.pesanan.kode_pesanan} telah diselesaikan."
                ),
            )

    messages.success(
        request,
        "Kendala berhasil diselesaikan.",
    )

    return redirect(
        "administrator:kendala_detail",
        pk=kendala.pk,
    )


@administrator_required
@require_POST
def kendala_buka_kembali(request, pk):
    kendala = get_object_or_404(
        KendalaLaundry,
        pk=pk,
    )

    alasan = request.POST.get("alasan", "").strip()

    if kendala.status != KendalaLaundry.StatusKendala.SELESAI:
        messages.error(
            request,
            "Hanya kendala selesai yang dapat dibuka kembali.",
        )
        return redirect(
            "administrator:kendala_detail",
            pk=kendala.pk,
        )

    if not alasan:
        messages.error(
            request,
            "Alasan membuka kembali kendala wajib diisi.",
        )
        return redirect(
            "administrator:kendala_detail",
            pk=kendala.pk,
        )

    kendala.status = KendalaLaundry.StatusKendala.DITINDAKLANJUTI
    kendala.tanggapan_kasir = (
        f"{kendala.tanggapan_kasir}\n\n"
        f"Dibuka kembali: {alasan}"
    ).strip()
    kendala.ditangani_oleh = request.user

    kendala.save(
        update_fields=[
            "status",
            "tanggapan_kasir",
            "ditangani_oleh",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "Kendala berhasil dibuka kembali.",
    )

    return redirect(
        "administrator:kendala_detail",
        pk=kendala.pk,
    )