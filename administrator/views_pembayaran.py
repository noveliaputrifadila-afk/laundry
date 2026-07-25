from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .decorators import administrator_required
from .models import Invoice, Pembayaran, Pesanan


def hitung_total_pembayaran_berhasil(pesanan):
    """
    Menghitung seluruh pembayaran berhasil pada sebuah pesanan.
    """
    return (
        pesanan.pembayaran
        .filter(status=Pembayaran.StatusPembayaran.BERHASIL)
        .aggregate(total=Sum("jumlah"))
        .get("total")
        or Decimal("0.00")
    )


def sinkronkan_status_pembayaran(pesanan):
    """
    Menyesuaikan status pembayaran Pesanan dan Invoice berdasarkan
    akumulasi pembayaran yang berhasil.
    """
    total_berhasil = hitung_total_pembayaran_berhasil(pesanan)

    if total_berhasil <= Decimal("0.00"):
        status_pesanan = Pesanan.StatusPembayaran.BELUM_DIBAYAR

    elif total_berhasil < pesanan.total_biaya:
        status_pesanan = Pesanan.StatusPembayaran.DP

    else:
        status_pesanan = Pesanan.StatusPembayaran.LUNAS

    if pesanan.status_pembayaran != status_pesanan:
        pesanan.status_pembayaran = status_pesanan
        pesanan.save(
            update_fields=[
                "status_pembayaran",
                "total_biaya",
                "updated_at",
            ]
        )

    try:
        invoice = pesanan.invoice
    except Invoice.DoesNotExist:
        invoice = None

    if invoice:
        status_invoice_baru = invoice.status

        if status_pesanan == Pesanan.StatusPembayaran.LUNAS:
            status_invoice_baru = Invoice.StatusInvoice.LUNAS

        elif (
            invoice.status == Invoice.StatusInvoice.LUNAS
            and status_pesanan != Pesanan.StatusPembayaran.LUNAS
        ):
            status_invoice_baru = Invoice.StatusInvoice.DITERBITKAN

        if invoice.status != status_invoice_baru:
            invoice.status = status_invoice_baru
            invoice.save(
                update_fields=[
                    "status",
                    "total",
                    "updated_at",
                ]
            )

    return total_berhasil


@administrator_required
def pembayaran_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    metode = request.GET.get("metode", "").strip()

    pembayaran_queryset = (
        Pembayaran.objects
        .select_related(
            "pesanan",
            "pesanan__pelanggan",
            "metode_pembayaran",
            "diverifikasi_oleh",
        )
        .order_by("-tanggal_pembayaran")
    )

    if query:
        pembayaran_queryset = pembayaran_queryset.filter(
            Q(kode_pembayaran__icontains=query)
            | Q(pesanan__kode_pesanan__icontains=query)
            | Q(pesanan__pelanggan__username__icontains=query)
            | Q(pesanan__pelanggan__first_name__icontains=query)
            | Q(pesanan__pelanggan__last_name__icontains=query)
            | Q(pesanan__pelanggan__nomor_hp__icontains=query)
        )

    if status:
        pembayaran_queryset = pembayaran_queryset.filter(
            status=status
        )

    if metode:
        pembayaran_queryset = pembayaran_queryset.filter(
            metode_pembayaran_id=metode
        )

    from .models import MetodePembayaran

    context = {
        "pembayaran_list": pembayaran_queryset,
        "query": query,
        "selected_status": status,
        "selected_metode": metode,
        "status_choices": Pembayaran.StatusPembayaran.choices,
        "metode_pembayaran_list": MetodePembayaran.objects.filter(
            is_active=True
        ).order_by("nama"),
        "total_data": pembayaran_queryset.count(),
        "total_menunggu": Pembayaran.objects.filter(
            status=Pembayaran.StatusPembayaran.MENUNGGU
        ).count(),
        "total_berhasil": Pembayaran.objects.filter(
            status=Pembayaran.StatusPembayaran.BERHASIL
        ).count(),
        "nominal_berhasil": (
            Pembayaran.objects
            .filter(status=Pembayaran.StatusPembayaran.BERHASIL)
            .aggregate(total=Sum("jumlah"))
            .get("total")
            or Decimal("0.00")
        ),
    }

    return render(
        request,
        "administrator/pembayaran/pembayaran_list.html",
        context,
    )


@administrator_required
def pembayaran_detail(request, pk):
    pembayaran = get_object_or_404(
        Pembayaran.objects.select_related(
            "pesanan",
            "pesanan__pelanggan",
            "pesanan__metode_pembayaran",
            "metode_pembayaran",
            "diverifikasi_oleh",
        ),
        pk=pk,
    )

    total_berhasil = hitung_total_pembayaran_berhasil(
        pembayaran.pesanan
    )

    sisa_pembayaran = max(
        pembayaran.pesanan.total_biaya - total_berhasil,
        Decimal("0.00"),
    )

    context = {
        "pembayaran": pembayaran,
        "total_berhasil": total_berhasil,
        "sisa_pembayaran": sisa_pembayaran,
    }

    return render(
        request,
        "administrator/pembayaran/pembayaran_detail.html",
        context,
    )


@administrator_required
@require_POST
def pembayaran_verifikasi(request, pk):
    pembayaran = get_object_or_404(
        Pembayaran.objects.select_related("pesanan"),
        pk=pk,
    )

    if pembayaran.status == Pembayaran.StatusPembayaran.BERHASIL:
        messages.info(
            request,
            "Pembayaran tersebut sudah diverifikasi sebelumnya.",
        )
        return redirect(
            "administrator:pembayaran_detail",
            pk=pembayaran.pk,
        )

    if pembayaran.status == Pembayaran.StatusPembayaran.DIKEMBALIKAN:
        messages.error(
            request,
            "Pembayaran yang telah dikembalikan tidak dapat diverifikasi.",
        )
        return redirect(
            "administrator:pembayaran_detail",
            pk=pembayaran.pk,
        )

    catatan = request.POST.get("catatan", "").strip()

    with transaction.atomic():
        pembayaran.status = Pembayaran.StatusPembayaran.BERHASIL
        pembayaran.diverifikasi_oleh = request.user
        pembayaran.diverifikasi_pada = timezone.now()

        if catatan:
            pembayaran.catatan = catatan

        pembayaran.save(
            update_fields=[
                "status",
                "diverifikasi_oleh",
                "diverifikasi_pada",
                "catatan",
                "updated_at",
            ]
        )

        sinkronkan_status_pembayaran(
            pembayaran.pesanan
        )

    messages.success(
        request,
        f"Pembayaran {pembayaran.kode_pembayaran} berhasil diverifikasi.",
    )

    return redirect(
        "administrator:pembayaran_detail",
        pk=pembayaran.pk,
    )


@administrator_required
@require_POST
def pembayaran_tolak(request, pk):
    pembayaran = get_object_or_404(
        Pembayaran.objects.select_related("pesanan"),
        pk=pk,
    )

    alasan = request.POST.get("alasan", "").strip()

    if not alasan:
        messages.error(
            request,
            "Alasan penolakan wajib diisi.",
        )
        return redirect(
            "administrator:pembayaran_detail",
            pk=pembayaran.pk,
        )

    if pembayaran.status == Pembayaran.StatusPembayaran.BERHASIL:
        messages.error(
            request,
            "Pembayaran yang sudah berhasil tidak dapat ditolak.",
        )
        return redirect(
            "administrator:pembayaran_detail",
            pk=pembayaran.pk,
        )

    if pembayaran.status == Pembayaran.StatusPembayaran.DIKEMBALIKAN:
        messages.error(
            request,
            "Pembayaran yang sudah dikembalikan tidak dapat ditolak.",
        )
        return redirect(
            "administrator:pembayaran_detail",
            pk=pembayaran.pk,
        )

    with transaction.atomic():
        pembayaran.status = Pembayaran.StatusPembayaran.DITOLAK
        pembayaran.diverifikasi_oleh = request.user
        pembayaran.diverifikasi_pada = timezone.now()
        pembayaran.catatan = alasan

        pembayaran.save(
            update_fields=[
                "status",
                "diverifikasi_oleh",
                "diverifikasi_pada",
                "catatan",
                "updated_at",
            ]
        )

        sinkronkan_status_pembayaran(
            pembayaran.pesanan
        )

    messages.success(
        request,
        f"Pembayaran {pembayaran.kode_pembayaran} berhasil ditolak.",
    )

    return redirect(
        "administrator:pembayaran_detail",
        pk=pembayaran.pk,
    )


@administrator_required
@require_POST
def pembayaran_kembalikan(request, pk):
    pembayaran = get_object_or_404(
        Pembayaran.objects.select_related("pesanan"),
        pk=pk,
    )

    alasan = request.POST.get("alasan", "").strip()

    if pembayaran.status != Pembayaran.StatusPembayaran.BERHASIL:
        messages.error(
            request,
            "Hanya pembayaran berhasil yang dapat dikembalikan.",
        )
        return redirect(
            "administrator:pembayaran_detail",
            pk=pembayaran.pk,
        )

    if not alasan:
        messages.error(
            request,
            "Alasan pengembalian wajib diisi.",
        )
        return redirect(
            "administrator:pembayaran_detail",
            pk=pembayaran.pk,
        )

    with transaction.atomic():
        pembayaran.status = Pembayaran.StatusPembayaran.DIKEMBALIKAN
        pembayaran.diverifikasi_oleh = request.user
        pembayaran.diverifikasi_pada = timezone.now()
        pembayaran.catatan = alasan

        pembayaran.save(
            update_fields=[
                "status",
                "diverifikasi_oleh",
                "diverifikasi_pada",
                "catatan",
                "updated_at",
            ]
        )

        sinkronkan_status_pembayaran(
            pembayaran.pesanan
        )

    messages.success(
        request,
        f"Pembayaran {pembayaran.kode_pembayaran} ditandai dikembalikan.",
    )

    return redirect(
        "administrator:pembayaran_detail",
        pk=pembayaran.pk,
    )