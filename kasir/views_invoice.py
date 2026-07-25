from datetime import timedelta

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.views.decorators.http import require_POST

from administrator.models import Invoice, Pesanan

from .decorators import kasir_required


@kasir_required
def invoice_list(request):
    """
    Menampilkan seluruh invoice pada modul Kasir.
    """

    invoice_queryset = (
        Invoice.objects
        .select_related(
            "pesanan",
            "pesanan__pelanggan",
            "dibuat_oleh",
        )
        .order_by("-tanggal_terbit")
    )

    # ==========================================
    # PENCARIAN
    # ==========================================
    keyword = request.GET.get("q", "").strip()

    if keyword:
        invoice_queryset = invoice_queryset.filter(
            Q(nomor_invoice__icontains=keyword)
            | Q(pesanan__kode_pesanan__icontains=keyword)
            | Q(pesanan__pelanggan__username__icontains=keyword)
            | Q(pesanan__pelanggan__first_name__icontains=keyword)
            | Q(pesanan__pelanggan__last_name__icontains=keyword)
            | Q(pesanan__pelanggan__nomor_hp__icontains=keyword)
        )

    # ==========================================
    # FILTER STATUS
    # ==========================================
    status = request.GET.get("status", "").strip()

    if status:
        invoice_queryset = invoice_queryset.filter(
            status=status,
        )

    # ==========================================
    # RINGKASAN
    # ==========================================
    total_invoice = invoice_queryset.count()

    invoice_draft = invoice_queryset.filter(
        status=Invoice.StatusInvoice.DRAFT,
    ).count()

    invoice_diterbitkan = invoice_queryset.filter(
        status=Invoice.StatusInvoice.DITERBITKAN,
    ).count()

    invoice_lunas = invoice_queryset.filter(
        status=Invoice.StatusInvoice.LUNAS,
    ).count()

    # ==========================================
    # PAGINATION
    # ==========================================
    paginator = Paginator(
        invoice_queryset,
        10,
    )

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "invoice_list": page_obj.object_list,
        "page_obj": page_obj,

        "keyword": keyword,
        "status_terpilih": status,
        "status_choices": Invoice.StatusInvoice.choices,

        "total_invoice": total_invoice,
        "invoice_draft": invoice_draft,
        "invoice_diterbitkan": invoice_diterbitkan,
        "invoice_lunas": invoice_lunas,
    }

    return render(
        request,
        "kasir/invoice/list.html",
        context,
    )


@kasir_required
def invoice_create(request, pesanan_pk):
    """
    Membuat invoice berdasarkan pesanan.

    Karena relasi Invoice ke Pesanan adalah OneToOne,
    satu pesanan hanya boleh mempunyai satu invoice.
    """

    pesanan = get_object_or_404(
        Pesanan.objects.select_related(
            "pelanggan",
            "metode_pembayaran",
        ).prefetch_related(
            "detail__layanan",
        ),
        pk=pesanan_pk,
    )

    # Jika invoice sudah tersedia, langsung arahkan ke detail.
    if hasattr(pesanan, "invoice"):
        messages.info(
            request,
            "Pesanan tersebut sudah mempunyai invoice.",
        )

        return redirect(
            "kasir:invoice_detail",
            pk=pesanan.invoice.pk,
        )

    if request.method == "POST":
        jumlah_hari = request.POST.get(
            "jumlah_hari_jatuh_tempo",
            "3",
        )

        catatan = request.POST.get(
            "catatan",
            "",
        ).strip()

        try:
            jumlah_hari = int(jumlah_hari)
        except (TypeError, ValueError):
            jumlah_hari = 3

        if jumlah_hari < 0:
            jumlah_hari = 0

        invoice = Invoice.objects.create(
            pesanan=pesanan,
            dibuat_oleh=request.user,
            tanggal_terbit=timezone.now(),
            tanggal_jatuh_tempo=(
                timezone.now()
                + timedelta(days=jumlah_hari)
            ),
            total=pesanan.total_biaya,
            status=Invoice.StatusInvoice.DRAFT,
            catatan=catatan,
        )

        messages.success(
            request,
            (
                f"Invoice {invoice.nomor_invoice} "
                "berhasil dibuat."
            ),
        )

        return redirect(
            "kasir:invoice_detail",
            pk=invoice.pk,
        )

    context = {
        "pesanan": pesanan,
    }

    return render(
        request,
        "kasir/invoice/create.html",
        context,
    )


@kasir_required
def invoice_detail(request, pk):
    """
    Menampilkan detail invoice.
    """

    invoice = get_object_or_404(
        Invoice.objects
        .select_related(
            "pesanan",
            "pesanan__pelanggan",
            "pesanan__kasir",
            "pesanan__metode_pembayaran",
            "dibuat_oleh",
        )
        .prefetch_related(
            "pesanan__detail__layanan",
            "pesanan__pembayaran",
            "pesanan__pembayaran__metode_pembayaran",
        ),
        pk=pk,
    )

    context = {
        "invoice": invoice,
        "pesanan": invoice.pesanan,
    }

    return render(
        request,
        "kasir/invoice/detail.html",
        context,
    )


@kasir_required
@require_POST
def invoice_terbitkan(request, pk):
    invoice = get_object_or_404(
        Invoice,
        pk=pk,
    )

    if invoice.status != Invoice.StatusInvoice.DRAFT:
        messages.warning(
            request,
            "Hanya invoice berstatus draft yang dapat diterbitkan.",
        )

        return redirect(
            "kasir:invoice_detail",
            pk=invoice.pk,
        )

    invoice.status = Invoice.StatusInvoice.DITERBITKAN
    invoice.tanggal_terbit = timezone.now()

    if invoice.tanggal_jatuh_tempo is None:
        invoice.tanggal_jatuh_tempo = (
            timezone.now()
            + timedelta(days=3)
        )

    invoice.save(
        update_fields=[
            "status",
            "tanggal_terbit",
            "tanggal_jatuh_tempo",
            "updated_at",
        ]
    )

    messages.success(
        request,
        f"Invoice {invoice.nomor_invoice} berhasil diterbitkan.",
    )

    return redirect(
        "kasir:invoice_detail",
        pk=invoice.pk,
    )


@kasir_required
@require_POST
def invoice_batalkan(request, pk):
    invoice = get_object_or_404(
        Invoice,
        pk=pk,
    )

    if invoice.status == Invoice.StatusInvoice.LUNAS:
        messages.error(
            request,
            "Invoice yang sudah lunas tidak dapat dibatalkan.",
        )

        return redirect(
            "kasir:invoice_detail",
            pk=invoice.pk,
        )

    invoice.status = Invoice.StatusInvoice.DIBATALKAN
    invoice.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        f"Invoice {invoice.nomor_invoice} berhasil dibatalkan.",
    )

    return redirect(
        "kasir:invoice_detail",
        pk=invoice.pk,
    )


@kasir_required
def invoice_print(request, pk):
    """
    Halaman khusus cetak invoice.
    """

    invoice = get_object_or_404(
        Invoice.objects
        .select_related(
            "pesanan",
            "pesanan__pelanggan",
            "pesanan__kasir",
            "pesanan__metode_pembayaran",
            "dibuat_oleh",
        )
        .prefetch_related(
            "pesanan__detail__layanan",
        ),
        pk=pk,
    )

    context = {
        "invoice": invoice,
        "pesanan": invoice.pesanan,
    }

    return render(
        request,
        "kasir/invoice/print.html",
        context,
    )