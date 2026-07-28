from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from administrator.decorators import role_required
from administrator.models import (
    Invoice,
    Notifikasi,
    Pembayaran,
    Pesanan,
    RatingUlasan,
    User,
)

from .forms import (
    DetailPesananFormSet,
    PembayaranPelangganForm,
    PesananPelangganForm,
)
from .forms_rating import RatingUlasanForm


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
        Pesanan.StatusPesanan.MENUNGGU_BARANG_DIANTAR,
        Pesanan.StatusPesanan.MENUNGGU_PENJEMPUTAN,
        Pesanan.StatusPesanan.MENUNGGU_PEMERIKSAAN,
        Pesanan.StatusPesanan.MENUNGGU_PETUGAS,
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

                # Menentukan status awal.
                if (
                    pesanan.cara_barang_masuk
                    == Pesanan.CaraBarangMasuk.DIJEMPUT
                ):
                    pesanan.status = (
                        Pesanan.StatusPesanan
                        .MENUNGGU_PENJEMPUTAN
                    )
                else:
                    pesanan.status = (
                        Pesanan.StatusPesanan
                        .MENUNGGU_BARANG_DIANTAR
                    )

                # Sinkronisasi sementara dengan field lama
                # agar template atau view lama tidak langsung rusak.
                perlu_jemput = (
                    pesanan.cara_barang_masuk
                    == Pesanan.CaraBarangMasuk.DIJEMPUT
                )
                perlu_antar = (
                    pesanan.cara_barang_keluar
                    == Pesanan.CaraBarangKeluar
                    .DIANTAR_KE_PELANGGAN
                )

                if perlu_jemput and perlu_antar:
                    pesanan.jenis_pengantaran = (
                        Pesanan.JenisPengantaran.ANTAR_JEMPUT
                    )
                elif perlu_jemput:
                    pesanan.jenis_pengantaran = (
                        Pesanan.JenisPengantaran.JEMPUT
                    )
                elif perlu_antar:
                    pesanan.jenis_pengantaran = (
                        Pesanan.JenisPengantaran.ANTAR
                    )
                else:
                    pesanan.jenis_pengantaran = (
                        Pesanan.JenisPengantaran.DATANG_SENDIRI
                    )

                # Biaya belum dihitung sebelum pemeriksaan kasir.
                pesanan.subtotal = Decimal("0.00")
                pesanan.diskon = Decimal("0.00")
                pesanan.biaya_tambahan = Decimal("0.00")
                pesanan.total_biaya = Decimal("0.00")

                pesanan.save()

                details = formset.save(commit=False)

                for detail in details:
                    detail.pesanan = pesanan

                    # Mengisi field lama sementara agar database
                    # dan kode lama tetap kompatibel.
                    detail.nama_barang = (
                        detail.jenis_barang.nama
                    )
                    detail.jumlah = Decimal(
                        detail.jumlah_barang
                    )
                    detail.satuan = detail.layanan.satuan

                    # Harga ditentukan kasir setelah pemeriksaan.
                    detail.harga_satuan = Decimal("0.00")
                    detail.harga_final = None
                    detail.berat_aktual = None
                    detail.subtotal = Decimal("0.00")

                    detail.save()

                for detail in formset.deleted_objects:
                    detail.delete()

                if (
                    pesanan.status
                    == Pesanan.StatusPesanan
                    .MENUNGGU_PENJEMPUTAN
                ):
                    pesan_notifikasi = (
                        f"Pesanan {pesanan.kode_pesanan} "
                        "berhasil dibuat dan sedang menunggu "
                        "penjemputan barang."
                    )
                else:
                    pesan_notifikasi = (
                        f"Pesanan {pesanan.kode_pesanan} "
                        "berhasil dibuat. Silakan antarkan "
                        "barang ke outlet untuk diperiksa "
                        "dan ditimbang."
                    )

                Notifikasi.objects.create(
                    penerima=request.user,
                    jenis=Notifikasi.JenisNotifikasi.PESANAN,
                    judul="Pesanan berhasil dibuat",
                    pesan=pesan_notifikasi,
                    link=(
                        "/pelanggan/pesanan/lacak/"
                        f"?q={pesanan.kode_pesanan}"
                    ),
                )

            messages.success(
                request,
                (
                    "Pesanan laundry berhasil dibuat. "
                    "Harga final akan ditentukan setelah "
                    "barang diperiksa dan ditimbang."
                ),
            )

            return redirect("pelanggan:dashboard")

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
        Pesanan.StatusPesanan.MENUNGGU_BARANG_DIANTAR: 5,
        Pesanan.StatusPesanan.MENUNGGU_PENJEMPUTAN: 10,
        Pesanan.StatusPesanan.MENUNGGU_PEMERIKSAAN: 20,
        Pesanan.StatusPesanan.MENUNGGU_PETUGAS: 30,
        Pesanan.StatusPesanan.MENUNGGU_ANTRIAN: 35,
        Pesanan.StatusPesanan.DICUCI: 50,
        Pesanan.StatusPesanan.DIKERINGKAN: 65,
        Pesanan.StatusPesanan.DISETRIKA: 75,
        Pesanan.StatusPesanan.DILIPAT: 82,
        Pesanan.StatusPesanan.DIKEMAS: 88,
        Pesanan.StatusPesanan.SIAP_DIAMBIL: 95,
        Pesanan.StatusPesanan.SIAP_DIANTAR: 95,
        Pesanan.StatusPesanan.DALAM_PENGANTARAN: 98,
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
    notifikasi_queryset = (
        Notifikasi.objects
        .filter(penerima=request.user)
        .order_by("-created_at")
    )

    jumlah_belum_dibaca = notifikasi_queryset.filter(
        is_read=False,
    ).count()

    paginator = Paginator(
        notifikasi_queryset,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "page_obj": page_obj,
        "notifikasi_list": page_obj.object_list,
        "jumlah_belum_dibaca": jumlah_belum_dibaca,
    }

    return render(
        request,
        "pelanggan/notifikasi/list.html",
        context,
    )
@login_required
def notifikasi_baca(request, pk):
    notifikasi = get_object_or_404(
        Notifikasi,
        pk=pk,
        penerima=request.user,
    )

    if not notifikasi.is_read:
        notifikasi.is_read = True
        notifikasi.save(
            update_fields=["is_read"]
        )

    if notifikasi.link:
        return redirect(notifikasi.link)

    return redirect(
        "pelanggan:notifikasi_list"
    )
@role_required([User.Role.PELANGGAN])
def notifikasi_baca_semua(request):
    if request.method == "POST":
        Notifikasi.objects.filter(
            penerima=request.user,
            is_read=False,
        ).update(
            is_read=True,
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


@role_required([User.Role.PELANGGAN])
def beri_rating(request, pk):
    pesanan = get_object_or_404(
        Pesanan,
        pk=pk,
        pelanggan=request.user,
        status=Pesanan.StatusPesanan.SELESAI,
    )

    rating = RatingUlasan.objects.filter(
        pesanan=pesanan
    ).first()

    if rating:
        messages.info(
            request,
            "Anda sudah memberikan rating untuk pesanan ini."
        )
        return redirect(
            "pelanggan:pesanan_saya"
        )

    if request.method == "POST":
        form = RatingUlasanForm(
            request.POST
        )

        if form.is_valid():
            rating = form.save(
                commit=False
            )
            rating.pesanan = pesanan
            rating.pelanggan = request.user
            rating.save()

            messages.success(
                request,
                "Terima kasih atas rating Anda."
            )

            return redirect(
                "pelanggan:pesanan_saya"
            )
    else:
        form = RatingUlasanForm()

    context = {
        "pesanan": pesanan,
        "form": form,
    }

    return render(
        request,
        "pelanggan/rating_form.html",
        context,
    )