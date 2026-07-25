from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .decorators import administrator_required
from .forms_invoice import InvoiceForm
from .models import Invoice


@administrator_required
def invoice_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    invoices = (
        Invoice.objects
        .select_related(
            "pesanan",
            "pesanan__pelanggan",
            "dibuat_oleh",
        )
        .order_by("-tanggal_terbit")
    )

    if query:
        invoices = invoices.filter(
            Q(nomor_invoice__icontains=query)
            | Q(pesanan__kode_pesanan__icontains=query)
            | Q(pesanan__pelanggan__username__icontains=query)
            | Q(pesanan__pelanggan__first_name__icontains=query)
            | Q(pesanan__pelanggan__last_name__icontains=query)
        )

    if status:
        invoices = invoices.filter(status=status)

    context = {
        "invoices": invoices,
        "query": query,
        "selected_status": status,
        "status_choices": Invoice.StatusInvoice.choices,
        "total_invoice": invoices.count(),
    }

    return render(
        request,
        "administrator/invoice/invoice_list.html",
        context,
    )


@administrator_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            "pesanan",
            "pesanan__pelanggan",
            "pesanan__metode_pembayaran",
            "dibuat_oleh",
        ).prefetch_related(
            "pesanan__detail",
            "pesanan__detail__layanan",
        ),
        pk=pk,
    )

    context = {
        "invoice": invoice,
    }

    return render(
        request,
        "administrator/invoice/invoice_detail.html",
        context,
    )


@administrator_required
def invoice_create(request):
    if request.method == "POST":
        form = InvoiceForm(request.POST)

        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.dibuat_oleh = request.user
            invoice.total = invoice.pesanan.total_biaya
            invoice.save()

            messages.success(
                request,
                f"Invoice {invoice.nomor_invoice} berhasil dibuat.",
            )

            return redirect(
                "administrator:invoice_detail",
                pk=invoice.pk,
            )
    else:
        form = InvoiceForm()

    context = {
        "form": form,
        "judul": "Tambah Invoice",
        "tombol": "Simpan Invoice",
    }

    return render(
        request,
        "administrator/invoice/invoice_form.html",
        context,
    )


@administrator_required
def invoice_update(request, pk):
    invoice = get_object_or_404(
        Invoice,
        pk=pk,
    )

    if request.method == "POST":
        form = InvoiceForm(
            request.POST,
            instance=invoice,
        )

        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.total = invoice.pesanan.total_biaya
            invoice.save()

            messages.success(
                request,
                f"Invoice {invoice.nomor_invoice} berhasil diperbarui.",
            )

            return redirect(
                "administrator:invoice_detail",
                pk=invoice.pk,
            )
    else:
        form = InvoiceForm(
            instance=invoice,
        )

    context = {
        "form": form,
        "invoice": invoice,
        "judul": "Edit Invoice",
        "tombol": "Simpan Perubahan",
    }

    return render(
        request,
        "administrator/invoice/invoice_form.html",
        context,
    )


@administrator_required
@require_POST
def invoice_terbitkan(request, pk):
    invoice = get_object_or_404(
        Invoice,
        pk=pk,
    )

    if invoice.status == Invoice.StatusInvoice.DIBATALKAN:
        messages.error(
            request,
            "Invoice yang sudah dibatalkan tidak dapat diterbitkan.",
        )
    else:
        invoice.status = Invoice.StatusInvoice.DITERBITKAN
        invoice.save(
            update_fields=[
                "status",
                "total",
                "updated_at",
            ]
        )

        messages.success(
            request,
            f"Invoice {invoice.nomor_invoice} berhasil diterbitkan.",
        )

    return redirect(
        "administrator:invoice_detail",
        pk=invoice.pk,
    )


@administrator_required
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
    else:
        invoice.status = Invoice.StatusInvoice.DIBATALKAN
        invoice.save(
            update_fields=[
                "status",
                "total",
                "updated_at",
            ]
        )

        messages.success(
            request,
            f"Invoice {invoice.nomor_invoice} berhasil dibatalkan.",
        )

    return redirect(
        "administrator:invoice_detail",
        pk=invoice.pk,
    )