from decimal import Decimal
from io import BytesIO

import qrcode

from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .decorators import administrator_required
from .forms_invoice import InvoiceForm
from .models import Invoice

def format_rupiah(nilai):
    try:
        nilai = Decimal(nilai or 0)
    except (TypeError, ValueError):
        nilai = Decimal("0.00")

    hasil = f"{nilai:,.0f}".replace(",", ".")

    return f"Rp{hasil}"

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

@administrator_required
def invoice_pdf(request, pk):
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

    pesanan = invoice.pesanan
    detail_pesanan = pesanan.detail.all()

    response = HttpResponse(
        content_type="application/pdf",
    )

    response["Content-Disposition"] = (
        f'inline; filename="Invoice-{invoice.nomor_invoice}.pdf"'
    )

    buffer = BytesIO()

    dokumen = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=invoice.nomor_invoice,
        author="NSIA Laundry",
    )

    styles = getSampleStyleSheet()

    style_judul = ParagraphStyle(
        name="JudulLaundry",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0d6efd"),
    )

    style_normal = ParagraphStyle(
        name="NormalInvoice",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
    )

    style_kecil = ParagraphStyle(
        name="KecilInvoice",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#6c757d"),
    )

    style_kanan = ParagraphStyle(
        name="KananInvoice",
        parent=style_normal,
        alignment=TA_RIGHT,
    )

    elemen = []

    elemen.append(
        Paragraph(
            "NSIA LAUNDRY",
            style_judul,
        )
    )

    elemen.append(
        Paragraph(
            "Layanan Laundry Bersih, Cepat, dan Terpercaya",
            ParagraphStyle(
                name="Subjudul",
                parent=style_kecil,
                alignment=TA_CENTER,
            ),
        )
    )

    elemen.append(Spacer(1, 6 * mm))

    elemen.append(
        Table(
            [[""]],
            colWidths=[158 * mm],
            rowHeights=[1.5],
            style=TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor("#0d6efd"),
                    ),
                ]
            ),
        )
    )

    elemen.append(Spacer(1, 6 * mm))

    nama_pelanggan = (
        pesanan.pelanggan.get_full_name()
        or pesanan.pelanggan.username
    )

    informasi = Table(
        [
            [
                Paragraph("<b>Data Pelanggan</b>", style_normal),
                Paragraph("<b>Informasi Invoice</b>", style_normal),
            ],
            [
                Paragraph(
                    f"Nama: {nama_pelanggan}<br/>"
                    f"No. HP: {pesanan.pelanggan.nomor_hp or '-'}<br/>"
                    f"Email: {pesanan.pelanggan.email or '-'}",
                    style_normal,
                ),
                Paragraph(
                    f"Nomor Invoice: {invoice.nomor_invoice}<br/>"
                    f"Kode Pesanan: {pesanan.kode_pesanan}<br/>"
                    f"Tanggal: "
                    f"{invoice.tanggal_terbit.strftime('%d-%m-%Y %H:%M')}",
                    style_normal,
                ),
            ],
        ],
        colWidths=[79 * mm, 79 * mm],
    )

    informasi.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#f8f9fa"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#dee2e6"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#dee2e6"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    elemen.append(informasi)
    elemen.append(Spacer(1, 7 * mm))

    data_detail = [
        [
            "No",
            "Layanan",
            "Jumlah",
            "Harga",
            "Subtotal",
        ]
    ]

    for nomor, detail in enumerate(detail_pesanan, start=1):
        jumlah = getattr(detail, "jumlah", None)
        berat = getattr(detail, "berat", None)

        if berat:
            jumlah_tampil = f"{berat} kg"
        elif jumlah:
            jumlah_tampil = f"{jumlah} item"
        else:
            jumlah_tampil = "-"

        data_detail.append(
            [
                nomor,
                detail.layanan.nama,
                jumlah_tampil,
                format_rupiah(detail.harga_satuan),
                format_rupiah(detail.subtotal),
            ]
        )

    tabel_detail = Table(
        data_detail,
        colWidths=[
            12 * mm,
            65 * mm,
            26 * mm,
            27 * mm,
            28 * mm,
        ],
        repeatRows=1,
    )

    tabel_detail.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#0d6efd"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#dee2e6"),
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (0, -1),
                    "CENTER",
                ),
                (
                    "ALIGN",
                    (2, 1),
                    (-1, -1),
                    "RIGHT",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    elemen.append(tabel_detail)
    elemen.append(Spacer(1, 7 * mm))

    ringkasan = Table(
        [
            [
                "Subtotal",
                format_rupiah(pesanan.subtotal),
            ],
            [
                "Diskon",
                f"- {format_rupiah(pesanan.diskon)}",
            ],
            [
                "Biaya tambahan",
                format_rupiah(pesanan.biaya_tambahan),
            ],
            [
                Paragraph("<b>TOTAL</b>", style_normal),
                Paragraph(
                    f"<b>{format_rupiah(invoice.total)}</b>",
                    style_kanan,
                ),
            ],
        ],
        colWidths=[48 * mm, 42 * mm],
        hAlign="RIGHT",
    )

    ringkasan.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT",
                ),
                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, 2),
                    0.4,
                    colors.HexColor("#dee2e6"),
                ),
                (
                    "BACKGROUND",
                    (0, 3),
                    (-1, 3),
                    colors.HexColor("#d1e7dd"),
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    elemen.append(ringkasan)
    elemen.append(Spacer(1, 8 * mm))

    tracking_path = reverse(
        "administrator:tracking_pesanan",
        kwargs={
            "kode_pesanan": pesanan.kode_pesanan,
        },
    )

    tracking_url = request.build_absolute_uri(tracking_path)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )

    qr.add_data(tracking_url)
    qr.make(fit=True)

    gambar_qr = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    buffer_qr = BytesIO()
    gambar_qr.save(buffer_qr, format="PNG")
    buffer_qr.seek(0)

    qr_pdf = Image(
        buffer_qr,
        width=36 * mm,
        height=36 * mm,
    )

    tabel_qr = Table(
        [
            [
                qr_pdf,
                Paragraph(
                    "<b>Lacak Pesanan</b><br/>"
                    "Pindai QR Code untuk melihat status "
                    "dan progres laundry.",
                    style_normal,
                ),
            ]
        ],
        colWidths=[45 * mm, 113 * mm],
    )

    tabel_qr.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#f8f9fa"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#dee2e6"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    elemen.append(tabel_qr)
    elemen.append(Spacer(1, 7 * mm))

    elemen.append(
        Paragraph(
            "Terima kasih telah menggunakan layanan NSIA Laundry.",
            ParagraphStyle(
                name="Footer",
                parent=style_normal,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            ),
        )
    )

    dokumen.build(elemen)

    pdf = buffer.getvalue()
    buffer.close()

    response.write(pdf)

    return response