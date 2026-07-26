from django.shortcuts import render
from django.db import transaction
from administrator.decorators import role_required
from administrator.models import (
    Pembayaran,
    Pesanan,
    User,
    Invoice,
    Notifikasi,
)
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect
from django.core.paginator import Paginator
from django.db.models import Q

from .forms import (
    DetailPesananFormSet,
    PembayaranPelangganForm,
    PesananPelangganForm,
)


@role_required([User.Role.PELANGGAN])
def dashboard(request):
    pesanan_saya = (
        Pesanan.objects
        .filter(pelanggan=request.user)
        .select_related(
            "metode_pembayaran",
            "petugas_laundry",
        )
        .prefetch_related(
            "detail__layanan",
        )
        .order_by("-created_at")
    )

    status_aktif = [
        Pesanan.StatusPesanan.MENUNGGU_KONFIRMASI,
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
    ]

    pesanan_terbaru = pesanan_saya[:5]

    context = {
        "pesanan_terbaru": pesanan_terbaru,
        "total_pesanan": pesanan_saya.count(),
        "pesanan_aktif": pesanan_saya.filter(
            status__in=status_aktif,
        ).count(),
        "pesanan_selesai": pesanan_saya.filter(
            status=Pesanan.StatusPesanan.SELESAI,
        ).count(),
        "belum_lunas": pesanan_saya.exclude(
            status_pembayaran=Pesanan.StatusPembayaran.LUNAS,
        ).exclude(
            status__in=[
                Pesanan.StatusPesanan.DITOLAK,
                Pesanan.StatusPesanan.DIBATALKAN,
            ]
        ).count(),
    }

    return render(
        request,
        "pelanggan/dashboard.html",
        context,
    )


@role_required([User.Role.PELANGGAN])
def pesanan_tambah(request):
    pesanan = Pesanan(
        pelanggan=request.user,
    )

    if request.method == "POST":
        form = PesananPelangganForm(
            request.POST,
            instance=pesanan,
        )

        formset = DetailPesananFormSet(
            request.POST,
            instance=pesanan,
            prefix="detail",
        )

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                pesanan = form.save(commit=False)
                pesanan.pelanggan = request.user
                pesanan.save()

                details = formset.save(commit=False)

                for detail in details:
                    detail.pesanan = pesanan

                    tarif = detail.layanan.tarif_aktif

                    if tarif:
                        detail.harga_satuan = tarif.harga
                    else:
                        detail.harga_satuan = 0

                    detail.satuan = detail.layanan.satuan
                    detail.save()

                for detail in formset.deleted_objects:
                    detail.delete()

                pesanan.hitung_total()

                Notifikasi.objects.create(
                    penerima=request.user,
                    pesanan=pesanan,
                    jenis=Notifikasi.JenisNotifikasi.PESANAN,
                    judul="Pesanan berhasil dibuat",
                    pesan=(
                        f"Pesanan {pesanan.kode_pesanan} berhasil dibuat "
                        "dan sedang menunggu konfirmasi kasir."
                    ),
                    url=(
                        "/pelanggan/pesanan/lacak/"
                        f"?q={pesanan.kode_pesanan}"
                    ),
                )

            messages.success(
                request,
                "Pesanan laundry berhasil dibuat.",
            )

            return redirect(
                "pelanggan:dashboard"
            )

    else:
        form = PesananPelangganForm(
            instance=pesanan,
        )

        formset = DetailPesananFormSet(
            instance=pesanan,
            prefix="detail",
        )

    context = {
        "form": form,
        "formset": formset,
    }

    return render(
        request,
        "pelanggan/pesanan/form.html",
        context,
    )

@role_required([User.Role.PELANGGAN])
def pesanan_saya(request):
    keyword = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    pesanan_list = (
    Pesanan.objects
    .filter(pelanggan=request.user)
    .select_related(
        "metode_pembayaran",
        "promo",
        "area_layanan",
    )
    .prefetch_related(
        "detail__layanan",
    )
    .order_by("-created_at")
)

    if keyword:
        pesanan_list = pesanan_list.filter(
            Q(kode_pesanan__icontains=keyword)
            | Q(detail__nama_barang__icontains=keyword)
            | Q(detail__layanan__nama__icontains=keyword)
        ).distinct()

    if status:
        pesanan_list = pesanan_list.filter(
            status=status
        )

    paginator = Paginator(
        pesanan_list,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "page_obj": page_obj,
        "keyword": keyword,
        "status_dipilih": status,
        "status_choices": Pesanan.StatusPesanan.choices,
    }

    return render(
        request,
        "pelanggan/pesanan/list.html",
        context,
    )

@role_required([User.Role.PELANGGAN])
def lacak_laundry(request):
    keyword = request.GET.get("q", "").strip()

    status_selesai = [
        Pesanan.StatusPesanan.SELESAI,
        Pesanan.StatusPesanan.DITOLAK,
        Pesanan.StatusPesanan.DIBATALKAN,
    ]

    pesanan_list = (
        Pesanan.objects
        .filter(pelanggan=request.user)
        .exclude(status__in=status_selesai)
        .select_related(
            "petugas_laundry",
            "metode_pembayaran",
            "area_layanan",
        )
        .prefetch_related(
            "detail__layanan",
        )
        .order_by("-created_at")
    )

    if keyword:
        pesanan_list = pesanan_list.filter(
            Q(kode_pesanan__icontains=keyword)
            | Q(
                detail__layanan__nama__icontains=keyword
            )
            | Q(
                detail__nama_barang__icontains=keyword
            )
        ).distinct()

    progress_map = {
        Pesanan.StatusPesanan.MENUNGGU_KONFIRMASI: 10,
        Pesanan.StatusPesanan.DITERIMA: 20,
        Pesanan.StatusPesanan.MENUNGGU_ANTRIAN: 30,
        Pesanan.StatusPesanan.DICUCI: 45,
        Pesanan.StatusPesanan.DIKERINGKAN: 60,
        Pesanan.StatusPesanan.DISETRIKA: 70,
        Pesanan.StatusPesanan.DILIPAT: 78,
        Pesanan.StatusPesanan.DIKEMAS: 85,
        Pesanan.StatusPesanan.SIAP_DIAMBIL: 92,
        Pesanan.StatusPesanan.SIAP_DIANTAR: 92,
        Pesanan.StatusPesanan.DALAM_PENGANTARAN: 96,
        Pesanan.StatusPesanan.SELESAI: 100,
    }

    for pesanan in pesanan_list:
        pesanan.progress = progress_map.get(
            pesanan.status,
            5,
        )

    context = {
        "pesanan_list": pesanan_list,
        "keyword": keyword,
    }

    return render(
        request,
        "pelanggan/pesanan/lacak.html",
        context,
    )
@role_required([User.Role.PELANGGAN])
def pembayaran_list(request):
    pembayaran_list = (
        Pembayaran.objects
        .filter(
            pesanan__pelanggan=request.user,
        )
        .select_related(
            "pesanan",
            "metode_pembayaran",
            "diverifikasi_oleh",
        )
        .order_by("-tanggal_pembayaran")
    )

    pesanan_belum_lunas = (
        Pesanan.objects
        .filter(
            pelanggan=request.user,
        )
        .exclude(
            status_pembayaran=(
                Pesanan.StatusPembayaran.LUNAS
            ),
        )
        .exclude(
            status__in=[
                Pesanan.StatusPesanan.DITOLAK,
                Pesanan.StatusPesanan.DIBATALKAN,
            ]
        )
        .select_related(
            "metode_pembayaran",
        )
        .order_by("-created_at")
    )

    context = {
        "pembayaran_list": pembayaran_list,
        "pesanan_belum_lunas": pesanan_belum_lunas,
    }

    return render(
        request,
        "pelanggan/pembayaran/list.html",
        context,
    )
@role_required([User.Role.PELANGGAN])
def pembayaran_tambah(request, pesanan_id):
    pesanan = (
        Pesanan.objects
        .select_related(
            "metode_pembayaran",
        )
        .filter(
            id=pesanan_id,
            pelanggan=request.user,
        )
        .first()
    )

    if pesanan is None:
        messages.error(
            request,
            "Pesanan tidak ditemukan.",
        )
        return redirect(
            "pelanggan:pembayaran_list"
        )

    if pesanan.status in [
        Pesanan.StatusPesanan.DITOLAK,
        Pesanan.StatusPesanan.DIBATALKAN,
    ]:
        messages.error(
            request,
            "Pesanan ini tidak dapat dibayar.",
        )
        return redirect(
            "pelanggan:pembayaran_list"
        )

    if (
        pesanan.status_pembayaran
        == Pesanan.StatusPembayaran.LUNAS
    ):
        messages.info(
            request,
            "Pesanan ini sudah lunas.",
        )
        return redirect(
            "pelanggan:pembayaran_list"
        )

    total_berhasil = sum(
        (
            pembayaran.jumlah
            for pembayaran in pesanan.pembayaran.filter(
                status=(
                    Pembayaran.StatusPembayaran.BERHASIL
                ),
            )
        ),
        0,
    )

    sisa_tagihan = max(
        pesanan.total_biaya - total_berhasil,
        0,
    )

    if request.method == "POST":
        form = PembayaranPelangganForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            pembayaran = form.save(
                commit=False,
            )

            if pembayaran.jumlah > sisa_tagihan:
                form.add_error(
                    "jumlah",
                    (
                        "Jumlah pembayaran tidak boleh "
                        "melebihi sisa tagihan."
                    ),
                )
            else:
                pembayaran.pesanan = pesanan
                pembayaran.metode_pembayaran = (
                    pesanan.metode_pembayaran
                )
                pembayaran.status = (
                    Pembayaran.StatusPembayaran.MENUNGGU
                )
                pembayaran.save()

                pesanan.status_pembayaran = (
                    Pesanan.StatusPembayaran
                    .MENUNGGU_VERIFIKASI
                )
                pesanan.save(
                    update_fields=[
                        "status_pembayaran",
                        "updated_at",
                    ]
                )

                messages.success(
                    request,
                    (
                        "Bukti pembayaran berhasil "
                        "dikirim dan menunggu verifikasi."
                    ),
                )

                return redirect(
                    "pelanggan:pembayaran_list"
                )
    else:
        form = PembayaranPelangganForm(
            initial={
                "jumlah": sisa_tagihan,
            }
        )

    context = {
        "form": form,
        "pesanan": pesanan,
        "total_berhasil": total_berhasil,
        "sisa_tagihan": sisa_tagihan,
    }

    return render(
        request,
        "pelanggan/pembayaran/form.html",
        context,
    )
@role_required([User.Role.PELANGGAN])
def invoice_list(request):
    invoice_list = (
        Invoice.objects
        .filter(
            pesanan__pelanggan=request.user,
        )
        .select_related(
            "pesanan",
            "pesanan__metode_pembayaran",
            "dibuat_oleh",
        )
        .order_by("-tanggal_terbit")
    )

    context = {
        "invoice_list": invoice_list,
    }

    return render(
        request,
        "pelanggan/invoice/list.html",
        context,
    )
@role_required([User.Role.PELANGGAN])
def notifikasi_list(request):
    notifikasi_list = (
        Notifikasi.objects
        .filter(penerima=request.user)
        .select_related("pesanan")
        .order_by("-created_at")
    )

    jumlah_belum_dibaca = notifikasi_list.filter(
        sudah_dibaca=False,
    ).count()

    paginator = Paginator(
        notifikasi_list,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "page_obj": page_obj,
        "jumlah_belum_dibaca": jumlah_belum_dibaca,
    }

    return render(
        request,
        "pelanggan/notifikasi/list.html",
        context,
    )
@role_required([User.Role.PELANGGAN])
def notifikasi_baca(request, pk):
    notifikasi = (
        Notifikasi.objects
        .filter(
            pk=pk,
            penerima=request.user,
        )
        .first()
    )

    if notifikasi is None:
        messages.error(
            request,
            "Notifikasi tidak ditemukan.",
        )
        return redirect(
            "pelanggan:notifikasi_list"
        )

    notifikasi.tandai_dibaca()

    if notifikasi.url:
        return redirect(
            notifikasi.url
        )

    return redirect(
        "pelanggan:notifikasi_list"
    )
@role_required([User.Role.PELANGGAN])
def notifikasi_baca_semua(request):
    if request.method == "POST":
        Notifikasi.objects.filter(
            penerima=request.user,
            sudah_dibaca=False,
        ).update(
            sudah_dibaca=True,
            dibaca_pada=timezone.now(),
            updated_at=timezone.now(),
        )

        messages.success(
            request,
            "Semua notifikasi telah ditandai sebagai dibaca.",
        )

    return redirect(
        "pelanggan:notifikasi_list"
    )