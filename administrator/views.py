from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import administrator_required
from .forms import FilterLogAktivitasForm
from .models import (
    AreaLayanan,
    KategoriLayanan,
    Layanan,
    LogAktivitas,
    MetodePembayaran,
    Pembayaran,
    Pesanan,
    Promo,
    RiwayatStatus,
    Tarif,
    User,
    Notifikasi,
)
from io import BytesIO

import qrcode

from django.http import HttpResponse
from django.urls import reverse

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

def format_rupiah(nilai):
    """
    Mengubah angka menjadi format Rupiah.
    Contoh: 25000 menjadi Rp25.000
    """
    try:
        nilai = Decimal(nilai or 0)
    except (TypeError, ValueError):
        nilai = Decimal("0.00")

    hasil = f"{nilai:,.0f}"
    hasil = hasil.replace(",", ".")

    return f"Rp{hasil}"

@administrator_required
def dashboard(request):
    """
    Menampilkan ringkasan data aplikasi pada dashboard administrator.
    """

    # =========================================================
    # STATISTIK PENGGUNA
    # =========================================================
    jumlah_administrator = User.objects.filter(
        role=User.Role.ADMINISTRATOR,
        is_active=True,
    ).count()

    jumlah_kasir = User.objects.filter(
        role=User.Role.KASIR,
        is_active=True,
    ).count()

    jumlah_petugas = User.objects.filter(
        role=User.Role.PETUGAS_LAUNDRY,
        is_active=True,
    ).count()

    jumlah_pelanggan = User.objects.filter(
        role=User.Role.PELANGGAN,
    ).count()

    pelanggan_menunggu_verifikasi = (
        User.objects.filter(
            role=User.Role.PELANGGAN,
            is_verified=False,
            is_active=True,
        )
        .order_by("-date_joined")[:5]
    )

    jumlah_menunggu_verifikasi = User.objects.filter(
        role=User.Role.PELANGGAN,
        is_verified=False,
        is_active=True,
    ).count()

    # =========================================================
    # STATISTIK PESANAN
    # =========================================================
    jumlah_pesanan = Pesanan.objects.count()

    jumlah_pesanan_menunggu = Pesanan.objects.filter(
        status=Pesanan.StatusPesanan.MENUNGGU_PEMERIKSAAN,
    ).count()

    jumlah_pesanan_diproses = Pesanan.objects.exclude(
        status__in=[
            Pesanan.StatusPesanan.MENUNGGU_PEMERIKSAAN,
            Pesanan.StatusPesanan.DITOLAK,
            Pesanan.StatusPesanan.DIBATALKAN,
            Pesanan.StatusPesanan.SELESAI,
        ]
    ).count()

    jumlah_pesanan_selesai = Pesanan.objects.filter(
        status=Pesanan.StatusPesanan.SELESAI,
    ).count()

    # =========================================================
    # STATISTIK PENDAPATAN
    # =========================================================
    total_pendapatan = (
        Pembayaran.objects.filter(
            status=Pembayaran.StatusPembayaran.BERHASIL,
        ).aggregate(
            total=Sum("jumlah")
        )["total"]
        or Decimal("0.00")
    )

    # =========================================================
    # STATISTIK DATA MASTER
    # =========================================================
    jumlah_kategori = KategoriLayanan.objects.count()
    jumlah_layanan = Layanan.objects.count()

    jumlah_tarif = Tarif.objects.filter(
        is_active=True,
    ).count()

    jumlah_promo = Promo.objects.filter(
        is_active=True,
    ).count()

    jumlah_metode_pembayaran = MetodePembayaran.objects.filter(
        is_active=True,
    ).count()

    jumlah_area_layanan = AreaLayanan.objects.filter(
        is_active=True,
    ).count()

    # =========================================================
    # PESANAN TERBARU
    # =========================================================
    pesanan_terbaru = (
        Pesanan.objects.select_related(
            "pelanggan",
            "kasir",
            "petugas_laundry",
            "metode_pembayaran",
        )
        .order_by("-created_at")[:8]
    )

    # =========================================================
    # RIWAYAT STATUS TERBARU
    # =========================================================
    aktivitas_terbaru = (
        RiwayatStatus.objects.select_related(
            "pesanan",
            "diubah_oleh",
        )
        .order_by("-created_at")[:8]
    )

    context = {
        # Pengguna
        "jumlah_administrator": jumlah_administrator,
        "jumlah_kasir": jumlah_kasir,
        "jumlah_petugas": jumlah_petugas,
        "jumlah_pelanggan": jumlah_pelanggan,
        "jumlah_menunggu_verifikasi": (
            jumlah_menunggu_verifikasi
        ),
        "pelanggan_menunggu_verifikasi": (
            pelanggan_menunggu_verifikasi
        ),

        # Pesanan dan pendapatan
        "jumlah_pesanan": jumlah_pesanan,
        "jumlah_pesanan_menunggu": (
            jumlah_pesanan_menunggu
        ),
        "jumlah_pesanan_diproses": (
            jumlah_pesanan_diproses
        ),
        "jumlah_pesanan_selesai": (
            jumlah_pesanan_selesai
        ),
        "total_pendapatan": total_pendapatan,

        # Data master
        "jumlah_kategori": jumlah_kategori,
        "jumlah_layanan": jumlah_layanan,
        "jumlah_tarif": jumlah_tarif,
        "jumlah_promo": jumlah_promo,
        "jumlah_metode_pembayaran": (
            jumlah_metode_pembayaran
        ),
        "jumlah_area_layanan": jumlah_area_layanan,

        # Data terbaru
        "pesanan_terbaru": pesanan_terbaru,
        "aktivitas_terbaru": aktivitas_terbaru,
    }

    return render(
        request,
        "administrator/dashboard.html",
        context,
    )


@administrator_required
def log_aktivitas_list(request):
    """
    Menampilkan daftar log aktivitas yang hanya dapat
    diakses oleh administrator.
    """

    queryset = (
        LogAktivitas.objects
        .select_related("pengguna")
        .order_by("-dibuat_pada")
    )

    form = FilterLogAktivitasForm(
        request.GET or None
    )

    if form.is_valid():
        keyword = form.cleaned_data.get("keyword")
        jenis = form.cleaned_data.get("jenis")
        pengguna = form.cleaned_data.get("pengguna")
        tanggal_mulai = form.cleaned_data.get(
            "tanggal_mulai"
        )
        tanggal_selesai = form.cleaned_data.get(
            "tanggal_selesai"
        )

        if keyword:
            queryset = queryset.filter(
                Q(
                    pengguna__username__icontains=keyword
                )
                | Q(
                    pengguna__first_name__icontains=keyword
                )
                | Q(
                    pengguna__last_name__icontains=keyword
                )
                | Q(
                    aktivitas__icontains=keyword
                )
                | Q(
                    objek__icontains=keyword
                )
                | Q(
                    keterangan__icontains=keyword
                )
                | Q(
                    ip_address__icontains=keyword
                )
            )

        if jenis:
            queryset = queryset.filter(
                jenis=jenis
            )

        if pengguna:
            queryset = queryset.filter(
                pengguna=pengguna
            )

        if tanggal_mulai:
            queryset = queryset.filter(
                dibuat_pada__date__gte=tanggal_mulai
            )

        if tanggal_selesai:
            queryset = queryset.filter(
                dibuat_pada__date__lte=tanggal_selesai
            )

    total_log = queryset.count()

    paginator = Paginator(
        queryset,
        15,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "form": form,
        "page_obj": page_obj,
        "total_log": total_log,
    }

    return render(
        request,
        "administrator/log_aktivitas/list.html",
        context,
    )

@administrator_required
def notifikasi_list(request):
    """
    Menampilkan seluruh notifikasi milik administrator
    yang sedang login.
    """

    queryset = (
        Notifikasi.objects
        .filter(penerima=request.user)
        .order_by("-created_at")
    )

    status = request.GET.get("status", "")
    jenis = request.GET.get("jenis", "")
    keyword = request.GET.get("keyword", "").strip()

    if status == "belum_dibaca":
        queryset = queryset.filter(is_read=False)

    elif status == "sudah_dibaca":
        queryset = queryset.filter(is_read=True)

    if jenis:
        queryset = queryset.filter(jenis=jenis)

    if keyword:
        queryset = queryset.filter(
            Q(judul__icontains=keyword)
            | Q(pesan__icontains=keyword)
        )

    jumlah_belum_dibaca = Notifikasi.objects.filter(
        penerima=request.user,
        is_read=False,
    ).count()

    paginator = Paginator(
        queryset,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "page_obj": page_obj,
        "jumlah_belum_dibaca": jumlah_belum_dibaca,
        "pilihan_jenis": Notifikasi.JenisNotifikasi.choices,
        "status_filter": status,
        "jenis_filter": jenis,
        "keyword": keyword,
    }

    return render(
        request,
        "administrator/notifikasi/list.html",
        context,
    )


@administrator_required
def notifikasi_tandai_dibaca(request, pk):
    """
    Menandai satu notifikasi sebagai sudah dibaca.
    """

    notifikasi = get_object_or_404(
        Notifikasi,
        pk=pk,
        penerima=request.user,
    )

    if request.method == "POST":
        notifikasi.is_read = True
        notifikasi.save(
            update_fields=["is_read"]
        )

        if notifikasi.link:
            return redirect(notifikasi.link)

    return redirect(
        "administrator:notifikasi_list"
    )


@administrator_required
def notifikasi_tandai_semua_dibaca(request):
    """
    Menandai seluruh notifikasi administrator
    sebagai sudah dibaca.
    """

    if request.method == "POST":
        Notifikasi.objects.filter(
            penerima=request.user,
            is_read=False,
        ).update(
            is_read=True
        )

    return redirect(
        "administrator:notifikasi_list"
    )

@administrator_required
def monitoring_detail(request, pk):
    pesanan = get_object_or_404(
        Pesanan.objects.select_related(
            "pelanggan",
            "petugas_laundry",
        ),
        pk=pk,
    )

    riwayat = (
        RiwayatStatus.objects.filter(
            pesanan=pesanan,
        )
        .select_related("diubah_oleh")
        .order_by("created_at")
    )

    return render(
        request,
        "administrator/monitoring/detail.html",
        {
            "pesanan": pesanan,
            "riwayat": riwayat,
        },
    )


def tracking_pesanan(request, kode_pesanan):
    """
    Halaman tracking yang dapat dibuka melalui QR Code.

    Halaman ini sengaja tidak memakai administrator_required,
    karena pelanggan perlu dapat membukanya setelah memindai QR.
    """
    pesanan = get_object_or_404(
        Pesanan.objects.select_related(
            "pelanggan",
            "kasir",
            "petugas_laundry",
        ),
        kode_pesanan=kode_pesanan,
    )

    riwayat = (
        RiwayatStatus.objects.filter(pesanan=pesanan)
        .select_related("diubah_oleh")
        .order_by("created_at")
    )

    urutan_status = [
        Pesanan.StatusPesanan.MENUNGGU_PEMERIKSAAN,
        Pesanan.StatusPesanan.DITERIMA,
        Pesanan.StatusPesanan.MENUNGGU_ANTRIAN,
        Pesanan.StatusPesanan.DICUCI,
        Pesanan.StatusPesanan.DIKERINGKAN,
        Pesanan.StatusPesanan.DISETRIKA,
        Pesanan.StatusPesanan.DILIPAT,
        Pesanan.StatusPesanan.DIKEMAS,
        Pesanan.StatusPesanan.SIAP_DIAMBIL,
        Pesanan.StatusPesanan.SIAP_DIANTAR,
        Pesanan.StatusPesanan.DALAM_PENGANTARAN,
        Pesanan.StatusPesanan.SELESAI,
    ]

    status_labels = dict(Pesanan.StatusPesanan.choices)

    try:
        posisi_status = urutan_status.index(pesanan.status)
    except ValueError:
        posisi_status = -1

    tahapan = []

    for index, status in enumerate(urutan_status):
        tahapan.append(
            {
                "kode": status,
                "nama": status_labels.get(status, status),
                "selesai": index <= posisi_status,
                "aktif": index == posisi_status,
            }
        )

    return render(
        request,
        "tracking/detail.html",
        {
            "pesanan": pesanan,
            "riwayat": riwayat,
            "tahapan": tahapan,
        },
    )


def qr_code_pesanan(request, kode_pesanan):
    """
    Menghasilkan QR Code dalam format PNG.
    """
    pesanan = get_object_or_404(
        Pesanan,
        kode_pesanan=kode_pesanan,
    )

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
        box_size=10,
        border=4,
    )

    qr.add_data(tracking_url)
    qr.make(fit=True)

    gambar = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    buffer = BytesIO()
    gambar.save(buffer, format="PNG")
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="image/png",
    )

    response["Content-Disposition"] = (
        f'inline; filename="QR-{pesanan.kode_pesanan}.png"'
    )

    return response


@administrator_required
def invoice_pdf(request, kode_pesanan):
    """
    Membuat invoice pesanan dalam format PDF.
    Invoice memuat detail layanan, total pembayaran,
    serta QR Code untuk membuka halaman tracking.
    """

    pesanan = get_object_or_404(
        Pesanan.objects.select_related(
            "pelanggan",
            "kasir",
            "petugas_laundry",
            "metode_pembayaran",
            "promo",
            "area_layanan",
        ),
        kode_pesanan=kode_pesanan,
    )

    detail_pesanan = (
        pesanan.detail
        .select_related("layanan")
        .all()
        .order_by("id")
    )

    nomor_invoice = f"INV-{pesanan.kode_pesanan}"

    nama_file = f"Invoice-{pesanan.kode_pesanan}.pdf"

    response = HttpResponse(
        content_type="application/pdf",
    )

    response["Content-Disposition"] = (
        f'inline; filename="{nama_file}"'
    )

    buffer = BytesIO()

    dokumen = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=nomor_invoice,
        author="NSIA Laundry",
    )

    styles = getSampleStyleSheet()

    style_judul_laundry = ParagraphStyle(
        name="JudulLaundry",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0d6efd"),
        spaceAfter=3,
    )

    style_subjudul = ParagraphStyle(
        name="SubjudulLaundry",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#6c757d"),
    )

    style_judul_invoice = ParagraphStyle(
        name="JudulInvoice",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#212529"),
    )

    style_normal = ParagraphStyle(
        name="NormalInvoice",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#212529"),
    )

    style_kecil = ParagraphStyle(
        name="KecilInvoice",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#6c757d"),
    )

    style_total = ParagraphStyle(
        name="TotalInvoice",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.white,
    )

    elemen = []

    # =========================================================
    # HEADER INVOICE
    # =========================================================
    informasi_laundry = [
        Paragraph(
            "NSIA LAUNDRY",
            style_judul_laundry,
        ),
        Paragraph(
            "Layanan Laundry Bersih, Cepat, dan Terpercaya",
            style_subjudul,
        ),
    ]

    informasi_invoice = [
        Paragraph(
            "INVOICE",
            style_judul_invoice,
        ),
        Paragraph(
            f"<b>{nomor_invoice}</b>",
            ParagraphStyle(
                name="NomorInvoice",
                parent=style_normal,
                alignment=TA_RIGHT,
            ),
        ),
    ]

    tabel_header = Table(
        [
            [
                informasi_laundry,
                informasi_invoice,
            ]
        ],
        colWidths=[
            105 * mm,
            53 * mm,
        ],
    )

    tabel_header.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (0, 0),
                    "LEFT",
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, 0),
                    "RIGHT",
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
            ]
        )
    )

    elemen.append(tabel_header)

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

    elemen.append(Spacer(1, 8 * mm))

    # =========================================================
    # INFORMASI PELANGGAN DAN PESANAN
    # =========================================================
    nama_pelanggan = (
        pesanan.pelanggan.get_full_name()
        or pesanan.pelanggan.username
    )

    tanggal_invoice = pesanan.created_at.strftime(
        "%d-%m-%Y %H:%M"
    )

    estimasi_selesai = (
        pesanan.estimasi_selesai.strftime(
            "%d-%m-%Y %H:%M"
        )
        if pesanan.estimasi_selesai
        else "-"
    )

    informasi_pelanggan = [
        Paragraph(
            "<b>DITAGIHKAN KEPADA</b>",
            style_normal,
        ),
        Spacer(1, 3),
        Paragraph(
            nama_pelanggan,
            style_normal,
        ),
        Paragraph(
            f"No. HP: {pesanan.pelanggan.nomor_hp or '-'}",
            style_kecil,
        ),
        Paragraph(
            f"Email: {pesanan.pelanggan.email or '-'}",
            style_kecil,
        ),
        Paragraph(
            f"Alamat: {pesanan.pelanggan.alamat or '-'}",
            style_kecil,
        ),
    ]

    informasi_pesanan = [
        Paragraph(
            "<b>INFORMASI PESANAN</b>",
            style_normal,
        ),
        Spacer(1, 3),
        Paragraph(
            f"Kode Pesanan: "
            f"<b>{pesanan.kode_pesanan}</b>",
            style_normal,
        ),
        Paragraph(
            f"Tanggal: {tanggal_invoice}",
            style_kecil,
        ),
        Paragraph(
            f"Estimasi selesai: {estimasi_selesai}",
            style_kecil,
        ),
        Paragraph(
            f"Metode penerimaan: "
            f"{pesanan.get_jenis_pengantaran_display()}",
            style_kecil,
        ),
    ]

    tabel_informasi = Table(
        [
            [
                informasi_pelanggan,
                informasi_pesanan,
            ]
        ],
        colWidths=[
            79 * mm,
            79 * mm,
        ],
    )

    tabel_informasi.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
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
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#dee2e6"),
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
            ]
        )
    )

    elemen.append(tabel_informasi)
    elemen.append(Spacer(1, 8 * mm))

    # =========================================================
    # TABEL DETAIL PESANAN
    # =========================================================
    data_detail = [
        [
            Paragraph("<b>No.</b>", style_normal),
            Paragraph("<b>Layanan/Barang</b>", style_normal),
            Paragraph("<b>Jumlah</b>", style_normal),
            Paragraph("<b>Harga</b>", style_normal),
            Paragraph("<b>Subtotal</b>", style_normal),
        ]
    ]

    for nomor, detail in enumerate(
        detail_pesanan,
        start=1,
    ):
        nama_layanan = detail.layanan.nama

        if detail.nama_barang:
            nama_layanan += (
                f"<br/><font size='8' color='#6c757d'>"
                f"{detail.nama_barang}</font>"
            )

        jumlah = (
            f"{detail.jumlah:,.2f} "
            f"{detail.get_satuan_display()}"
        )

        jumlah = jumlah.replace(",", "X")
        jumlah = jumlah.replace(".", ",")
        jumlah = jumlah.replace("X", ".")

        data_detail.append(
            [
                Paragraph(
                    str(nomor),
                    style_normal,
                ),
                Paragraph(
                    nama_layanan,
                    style_normal,
                ),
                Paragraph(
                    jumlah,
                    style_normal,
                ),
                Paragraph(
                    format_rupiah(detail.harga_satuan),
                    style_normal,
                ),
                Paragraph(
                    format_rupiah(detail.subtotal),
                    style_normal,
                ),
            ]
        )

    if not detail_pesanan.exists():
        data_detail.append(
            [
                "",
                Paragraph(
                    "Belum ada detail layanan.",
                    style_kecil,
                ),
                "",
                "",
                "",
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
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#dee2e6"),
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#f8f9fa"),
                    ],
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    elemen.append(tabel_detail)
    elemen.append(Spacer(1, 7 * mm))

    # =========================================================
    # RINGKASAN BIAYA
    # =========================================================
    data_ringkasan = [
        [
            Paragraph(
                "Subtotal",
                style_normal,
            ),
            Paragraph(
                format_rupiah(pesanan.subtotal),
                ParagraphStyle(
                    name="SubtotalNilai",
                    parent=style_normal,
                    alignment=TA_RIGHT,
                ),
            ),
        ],
        [
            Paragraph(
                "Diskon",
                style_normal,
            ),
            Paragraph(
                f"- {format_rupiah(pesanan.diskon)}",
                ParagraphStyle(
                    name="DiskonNilai",
                    parent=style_normal,
                    alignment=TA_RIGHT,
                ),
            ),
        ],
        [
            Paragraph(
                "Biaya antar-jemput",
                style_normal,
            ),
            Paragraph(
                format_rupiah(
                    pesanan.biaya_antar_jemput
                ),
                ParagraphStyle(
                    name="AntarJemputNilai",
                    parent=style_normal,
                    alignment=TA_RIGHT,
                ),
            ),
        ],
        [
            Paragraph(
                "Biaya tambahan",
                style_normal,
            ),
            Paragraph(
                format_rupiah(
                    pesanan.biaya_tambahan
                ),
                ParagraphStyle(
                    name="TambahanNilai",
                    parent=style_normal,
                    alignment=TA_RIGHT,
                ),
            ),
        ],
        [
            Paragraph(
                "TOTAL",
                style_total,
            ),
            Paragraph(
                format_rupiah(pesanan.total_biaya),
                ParagraphStyle(
                    name="TotalNilai",
                    parent=style_total,
                    alignment=TA_RIGHT,
                ),
            ),
        ],
    ]

    tabel_ringkasan = Table(
        data_ringkasan,
        colWidths=[
            48 * mm,
            42 * mm,
        ],
        hAlign="RIGHT",
    )

    tabel_ringkasan.setStyle(
        TableStyle(
            [
                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, 3),
                    0.4,
                    colors.HexColor("#dee2e6"),
                ),
                (
                    "BACKGROUND",
                    (0, 4),
                    (-1, 4),
                    colors.HexColor("#198754"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    elemen.append(tabel_ringkasan)
    elemen.append(Spacer(1, 8 * mm))

    # =========================================================
    # STATUS PEMBAYARAN
    # =========================================================
    status_pembayaran = (
        pesanan.get_status_pembayaran_display()
    )

    if (
        pesanan.status_pembayaran
        == Pesanan.StatusPembayaran.LUNAS
    ):
        warna_status = colors.HexColor("#198754")
    elif (
        pesanan.status_pembayaran
        == Pesanan.StatusPembayaran.GAGAL
    ):
        warna_status = colors.HexColor("#dc3545")
    else:
        warna_status = colors.HexColor("#ffc107")

    tabel_status = Table(
        [
            [
                Paragraph(
                    "<b>Status Pembayaran</b>",
                    style_normal,
                ),
                Paragraph(
                    f"<b>{status_pembayaran.upper()}</b>",
                    ParagraphStyle(
                        name="StatusPembayaran",
                        parent=style_normal,
                        alignment=TA_RIGHT,
                        textColor=warna_status,
                    ),
                ),
            ],
            [
                Paragraph(
                    "Metode Pembayaran",
                    style_normal,
                ),
                Paragraph(
                    pesanan.metode_pembayaran.nama,
                    ParagraphStyle(
                        name="MetodePembayaran",
                        parent=style_normal,
                        alignment=TA_RIGHT,
                    ),
                ),
            ],
        ],
        colWidths=[
            79 * mm,
            79 * mm,
        ],
    )

    tabel_status.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#dee2e6"),
                ),
                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, 0),
                    0.5,
                    colors.HexColor("#dee2e6"),
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    elemen.append(tabel_status)
    elemen.append(Spacer(1, 10 * mm))

    # =========================================================
    # QR CODE TRACKING
    # =========================================================
    tracking_path = reverse(
        "administrator:tracking_pesanan",
        kwargs={
            "kode_pesanan": pesanan.kode_pesanan,
        },
    )

    tracking_url = request.build_absolute_uri(
        tracking_path
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=(
            qrcode.constants.ERROR_CORRECT_M
        ),
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
    gambar_qr.save(
        buffer_qr,
        format="PNG",
    )
    buffer_qr.seek(0)

    qr_pdf = Image(
        buffer_qr,
        width=36 * mm,
        height=36 * mm,
    )

    informasi_tracking = [
        Paragraph(
            "<b>Lacak Pesanan Anda</b>",
            style_normal,
        ),
        Spacer(1, 4),
        Paragraph(
            "Pindai QR Code untuk melihat status dan "
            "progres laundry secara langsung.",
            style_kecil,
        ),
        Spacer(1, 4),
        Paragraph(
            pesanan.kode_pesanan,
            style_kecil,
        ),
    ]

    tabel_qr = Table(
        [
            [
                qr_pdf,
                informasi_tracking,
            ]
        ],
        colWidths=[
            45 * mm,
            113 * mm,
        ],
    )

    tabel_qr.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
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
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    elemen.append(tabel_qr)
    elemen.append(Spacer(1, 8 * mm))

    # =========================================================
    # CATATAN DAN FOOTER
    # =========================================================
    if pesanan.catatan_pelanggan:
        elemen.append(
            Paragraph(
                "<b>Catatan pelanggan:</b>",
                style_normal,
            )
        )
        elemen.append(
            Paragraph(
                pesanan.catatan_pelanggan,
                style_kecil,
            )
        )
        elemen.append(Spacer(1, 5 * mm))

    elemen.append(
        Paragraph(
            "Terima kasih telah menggunakan layanan "
            "NSIA Laundry.",
            ParagraphStyle(
                name="UcapanTerimaKasih",
                parent=style_normal,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            ),
        )
    )

    elemen.append(
        Paragraph(
            "Invoice ini dibuat secara otomatis oleh sistem.",
            ParagraphStyle(
                name="FooterInvoice",
                parent=style_kecil,
                alignment=TA_CENTER,
            ),
        )
    )

    dokumen.build(elemen)

    pdf = buffer.getvalue()
    buffer.close()

    response.write(pdf)

    return response