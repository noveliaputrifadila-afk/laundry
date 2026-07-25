from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.views.decorators.http import require_POST

from administrator.models import (
    Invoice,
    Pembayaran,
    Pesanan,
)

from .decorators import kasir_required
from .forms_pembayaran import PembayaranKasirForm


def sinkronkan_status_pembayaran(pesanan):
    """
    Menyesuaikan status pembayaran pada Pesanan dan Invoice
    berdasarkan pembayaran yang berhasil.
    """

    total_berhasil = (
        pesanan.pembayaran
        .filter(
            status=Pembayaran.StatusPembayaran.BERHASIL,
        )
        .aggregate(total=Sum("jumlah"))
        .get("total")
        or Decimal("0.00")
    )

    memiliki_pembayaran_menunggu = (
        pesanan.pembayaran
        .filter(
            status=Pembayaran.StatusPembayaran.MENUNGGU,
        )
        .exists()
    )

    if total_berhasil >= pesanan.total_biaya:
        status_pembayaran = Pesanan.StatusPembayaran.LUNAS

    elif total_berhasil > Decimal("0.00"):
        status_pembayaran = Pesanan.StatusPembayaran.DP

    elif memiliki_pembayaran_menunggu:
        status_pembayaran = (
            Pesanan.StatusPembayaran.MENUNGGU_VERIFIKASI
        )

    else:
        status_pembayaran = (
            Pesanan.StatusPembayaran.BELUM_DIBAYAR
        )

    if pesanan.status_pembayaran != status_pembayaran:
        pesanan.status_pembayaran = status_pembayaran
        pesanan.save(
            update_fields=[
                "status_pembayaran",
                "updated_at",
            ]
        )

    if hasattr(pesanan, "invoice"):
        invoice = pesanan.invoice

        if status_pembayaran == Pesanan.StatusPembayaran.LUNAS:
            invoice.status = Invoice.StatusInvoice.LUNAS

        elif invoice.status == Invoice.StatusInvoice.LUNAS:
            invoice.status = Invoice.StatusInvoice.DITERBITKAN

        invoice.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    return total_berhasil


@kasir_required
def pembayaran_list(request):
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

    keyword = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    if keyword:
        pembayaran_queryset = pembayaran_queryset.filter(
            Q(kode_pembayaran__icontains=keyword)
            | Q(pesanan__kode_pesanan__icontains=keyword)
            | Q(pesanan__pelanggan__username__icontains=keyword)
            | Q(pesanan__pelanggan__first_name__icontains=keyword)
            | Q(pesanan__pelanggan__last_name__icontains=keyword)
            | Q(pesanan__pelanggan__nomor_hp__icontains=keyword)
        )

    if status:
        pembayaran_queryset = pembayaran_queryset.filter(
            status=status,
        )

    total_pembayaran = pembayaran_queryset.count()

    total_menunggu = pembayaran_queryset.filter(
        status=Pembayaran.StatusPembayaran.MENUNGGU,
    ).count()

    total_berhasil = pembayaran_queryset.filter(
        status=Pembayaran.StatusPembayaran.BERHASIL,
    ).count()

    nominal_berhasil = (
        pembayaran_queryset
        .filter(
            status=Pembayaran.StatusPembayaran.BERHASIL,
        )
        .aggregate(total=Sum("jumlah"))
        .get("total")
        or Decimal("0.00")
    )

    paginator = Paginator(
        pembayaran_queryset,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "pembayaran_list": page_obj.object_list,
        "page_obj": page_obj,
        "keyword": keyword,
        "status_terpilih": status,
        "status_choices": Pembayaran.StatusPembayaran.choices,
        "total_pembayaran": total_pembayaran,
        "total_menunggu": total_menunggu,
        "total_berhasil": total_berhasil,
        "nominal_berhasil": nominal_berhasil,
    }

    return render(
        request,
        "kasir/pembayaran/list.html",
        context,
    )


@kasir_required
def pembayaran_create(request, pesanan_pk=None):
    pesanan = None

    if pesanan_pk is not None:
        pesanan = get_object_or_404(
            Pesanan.objects.select_related(
                "pelanggan",
                "metode_pembayaran",
            ),
            pk=pesanan_pk,
        )

    if request.method == "POST":
        form = PembayaranKasirForm(
            request.POST,
            request.FILES,
            pesanan=pesanan,
        )

        if form.is_valid():
            with transaction.atomic():
                pembayaran = form.save(commit=False)

                # Pembayaran yang dicatat langsung oleh kasir
                # dianggap berhasil dan terverifikasi.
                pembayaran.status = (
                    Pembayaran.StatusPembayaran.BERHASIL
                )
                pembayaran.diverifikasi_oleh = request.user
                pembayaran.diverifikasi_pada = timezone.now()
                pembayaran.save()

                sinkronkan_status_pembayaran(
                    pembayaran.pesanan
                )

            messages.success(
                request,
                (
                    f"Pembayaran {pembayaran.kode_pembayaran} "
                    "berhasil dicatat."
                ),
            )

            return redirect(
                "kasir:pembayaran_detail",
                pk=pembayaran.pk,
            )

    else:
        form = PembayaranKasirForm(
            pesanan=pesanan,
        )

    context = {
        "form": form,
        "pesanan": pesanan,
    }

    return render(
        request,
        "kasir/pembayaran/form.html",
        context,
    )


@kasir_required
def pembayaran_detail(request, pk):
    pembayaran = get_object_or_404(
        Pembayaran.objects.select_related(
            "pesanan",
            "pesanan__pelanggan",
            "pesanan__invoice",
            "metode_pembayaran",
            "diverifikasi_oleh",
        ),
        pk=pk,
    )

    total_berhasil = (
        pembayaran.pesanan.pembayaran
        .filter(
            status=Pembayaran.StatusPembayaran.BERHASIL,
        )
        .aggregate(total=Sum("jumlah"))
        .get("total")
        or Decimal("0.00")
    )

    sisa_tagihan = max(
        pembayaran.pesanan.total_biaya - total_berhasil,
        Decimal("0.00"),
    )

    context = {
        "pembayaran": pembayaran,
        "pesanan": pembayaran.pesanan,
        "total_berhasil": total_berhasil,
        "sisa_tagihan": sisa_tagihan,
    }

    return render(
        request,
        "kasir/pembayaran/detail.html",
        context,
    )


@kasir_required
@require_POST
def pembayaran_verifikasi(request, pk):
    pembayaran = get_object_or_404(
        Pembayaran.objects.select_related("pesanan"),
        pk=pk,
    )

    if pembayaran.status != Pembayaran.StatusPembayaran.MENUNGGU:
        messages.warning(
            request,
            "Pembayaran tersebut sudah diproses.",
        )

        return redirect(
            "kasir:pembayaran_detail",
            pk=pembayaran.pk,
        )

    with transaction.atomic():
        pembayaran.status = Pembayaran.StatusPembayaran.BERHASIL
        pembayaran.diverifikasi_oleh = request.user
        pembayaran.diverifikasi_pada = timezone.now()
        pembayaran.catatan = request.POST.get(
            "catatan",
            pembayaran.catatan,
        ).strip()

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
        (
            f"Pembayaran {pembayaran.kode_pembayaran} "
            "berhasil diverifikasi."
        ),
    )

    return redirect(
        "kasir:pembayaran_detail",
        pk=pembayaran.pk,
    )


@kasir_required
@require_POST
def pembayaran_tolak(request, pk):
    pembayaran = get_object_or_404(
        Pembayaran.objects.select_related("pesanan"),
        pk=pk,
    )

    if pembayaran.status != Pembayaran.StatusPembayaran.MENUNGGU:
        messages.warning(
            request,
            "Pembayaran tersebut sudah diproses.",
        )

        return redirect(
            "kasir:pembayaran_detail",
            pk=pembayaran.pk,
        )

    alasan = request.POST.get("alasan", "").strip()

    if not alasan:
        messages.error(
            request,
            "Alasan penolakan wajib diisi.",
        )

        return redirect(
            "kasir:pembayaran_detail",
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
        (
            f"Pembayaran {pembayaran.kode_pembayaran} "
            "telah ditolak."
        ),
    )

    return redirect(
        "kasir:pembayaran_detail",
        pk=pembayaran.pk,
    )