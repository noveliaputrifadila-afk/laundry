from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from .decorators import (
    administrator_or_kasir_required,
)
from .notifications import buat_notifikasi
from .forms import (
    KonfirmasiPesananForm,
    PenugasanPetugasForm,
    TolakPesananForm,
    UbahStatusPembayaranForm,
    UbahStatusPesananForm,
)
from .models import (
    Notifikasi,
    Pesanan,
    RiwayatStatus,
    User,
)



@administrator_or_kasir_required
def pesanan_list(request):
    pesanan_queryset = (
        Pesanan.objects
        .select_related(
            "pelanggan",
            "kasir",
            "petugas_laundry",
            "promo",
            "metode_pembayaran",
            "area_layanan",
        )
        .all()
    )

    keyword = request.GET.get(
        "q",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    status_pembayaran = request.GET.get(
        "status_pembayaran",
        "",
    ).strip()

    petugas = request.GET.get(
        "petugas",
        "",
    ).strip()

    if keyword:
        pesanan_queryset = pesanan_queryset.filter(
            Q(kode_pesanan__icontains=keyword)
            | Q(
                pelanggan__username__icontains=keyword
            )
            | Q(
                pelanggan__first_name__icontains=keyword
            )
            | Q(
                pelanggan__last_name__icontains=keyword
            )
            | Q(
                pelanggan__nomor_hp__icontains=keyword
            )
        )

    status_valid = {
        value
        for value, label
        in Pesanan.StatusPesanan.choices
    }

    if status in status_valid:
        pesanan_queryset = pesanan_queryset.filter(
            status=status
        )

    pembayaran_valid = {
        value
        for value, label
        in Pesanan.StatusPembayaran.choices
    }

    if status_pembayaran in pembayaran_valid:
        pesanan_queryset = pesanan_queryset.filter(
            status_pembayaran=status_pembayaran
        )

    if petugas.isdigit():
        pesanan_queryset = pesanan_queryset.filter(
            petugas_laundry_id=int(petugas)
        )

    jumlah_pesanan = pesanan_queryset.count()

    paginator = Paginator(
        pesanan_queryset,
        15,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    daftar_petugas = (
        User.objects.filter(
            role=User.Role.PETUGAS_LAUNDRY,
            is_active=True,
        )
        .order_by("first_name", "username")
    )

    context = {
        "page_obj": page_obj,
        "jumlah_pesanan": jumlah_pesanan,
        "keyword": keyword,
        "status_filter": status,
        "pembayaran_filter": status_pembayaran,
        "petugas_filter": petugas,
        "status_choices": (
            Pesanan.StatusPesanan.choices
        ),
        "pembayaran_choices": (
            Pesanan.StatusPembayaran.choices
        ),
        "daftar_petugas": daftar_petugas,
    }

    return render(
        request,
        (
            "administrator/pesanan/"
            "pesanan_list.html"
        ),
        context,
    )


@administrator_or_kasir_required
def pesanan_detail(request, pk):
    pesanan = get_object_or_404(
        Pesanan.objects.select_related(
            "pelanggan",
            "kasir",
            "petugas_laundry",
            "promo",
            "metode_pembayaran",
            "area_layanan",
        ).prefetch_related(
            "detail__layanan",
            "riwayat_status__diubah_oleh",
            "pembayaran",
            "kendala",
        ),
        pk=pk,
    )

    form_penugasan = PenugasanPetugasForm(
        instance=pesanan
    )

    form_status = UbahStatusPesananForm(
        pesanan=pesanan
    )

    form_pembayaran = UbahStatusPembayaranForm(
        instance=pesanan
    )

    context = {
        "pesanan": pesanan,
        "form_penugasan": form_penugasan,
        "form_status": form_status,
        "form_pembayaran": form_pembayaran,
        "ada_status_berikutnya": bool(
            form_status.fields["status"].choices
        ),
    }

    return render(
        request,
        (
            "administrator/pesanan/"
            "pesanan_detail.html"
        ),
        context,
    )


@administrator_or_kasir_required
def pesanan_konfirmasi(request, pk):
    pesanan = get_object_or_404(
        Pesanan,
        pk=pk,
    )

    if (
        pesanan.status
        != Pesanan.StatusPesanan.MENUNGGU_PEMERIKSAAN
    ):
        messages.warning(
            request,
            "Pesanan tersebut sudah diproses.",
        )

        return redirect(
            "administrator:pesanan_detail",
            pk=pesanan.pk,
        )

    if request.method == "POST":
        form = KonfirmasiPesananForm(
            request.POST,
            instance=pesanan,
            user=request.user,
        )

        if form.is_valid():
            with transaction.atomic():
                pesanan = form.save(
                    commit=False
                )

                status_lama = pesanan.status

                if (
                    request.user.role
                    == User.Role.KASIR
                ):
                    pesanan.kasir = request.user

                pesanan.status = (
                    Pesanan.StatusPesanan.DITERIMA
                )

                pesanan.alasan_penolakan = ""

                pesanan.save()

                RiwayatStatus.objects.create(
                    pesanan=pesanan,
                    status_sebelumnya=status_lama,
                    status_baru=pesanan.status,
                    diubah_oleh=request.user,
                    catatan=(
                        "Pesanan dikonfirmasi dan diterima."
                    ),
                )

            buat_notifikasi(
                penerima=pesanan.pelanggan,
                judul="Pesanan Diterima",
                pesan=(
                    f"Pesanan {pesanan.kode_pesanan} "
                    "telah diterima dan akan segera diproses."
                ),
                jenis=Notifikasi.JenisNotifikasi.PESANAN,
            )

            messages.success(
                request,
                (
                    f"Pesanan {pesanan.kode_pesanan} "
                    "berhasil dikonfirmasi."
                ),
            )

            return redirect(
                "administrator:pesanan_detail",
                pk=pesanan.pk,
            )

    else:
        form = KonfirmasiPesananForm(
            instance=pesanan,
            user=request.user,
        )

    return render(
        request,
        (
            "administrator/pesanan/"
            "pesanan_konfirmasi.html"
        ),
        {
            "form": form,
            "pesanan": pesanan,
        },
    )


@administrator_or_kasir_required
def pesanan_tolak(request, pk):
    pesanan = get_object_or_404(
        Pesanan,
        pk=pk,
    )

    if (
        pesanan.status
        != Pesanan.StatusPesanan.MENUNGGU_PEMERIKSAAN
    ):
        messages.warning(
            request,
            "Pesanan tersebut sudah diproses.",
        )

        return redirect(
            "administrator:pesanan_detail",
            pk=pesanan.pk,
        )

    if request.method == "POST":
        form = TolakPesananForm(
            request.POST,
            instance=pesanan,
        )

        if form.is_valid():
            with transaction.atomic():
                pesanan = form.save(
                    commit=False
                )

                status_lama = pesanan.status

                if (
                    request.user.role
                    == User.Role.KASIR
                ):
                    pesanan.kasir = request.user

                pesanan.status = (
                    Pesanan.StatusPesanan.DITOLAK
                )

                pesanan.save()

                RiwayatStatus.objects.create(
                    pesanan=pesanan,
                    status_sebelumnya=status_lama,
                    status_baru=pesanan.status,
                    diubah_oleh=request.user,
                    catatan=pesanan.alasan_penolakan,
                )

                buat_notifikasi(
                    penerima=pesanan.pelanggan,
                    judul="Pesanan Ditolak",
                    pesan=(
                        f"Pesanan {pesanan.kode_pesanan} ditolak. "
                        f"Alasan: {pesanan.alasan_penolakan}"
                    ),
                    jenis=Notifikasi.JenisNotifikasi.PESANAN,
                )

            messages.success(
                request,
                (
                    f"Pesanan {pesanan.kode_pesanan} "
                    "berhasil ditolak."
                ),
            )

            return redirect(
                "administrator:pesanan_detail",
                pk=pesanan.pk,
            )

    else:
        form = TolakPesananForm(
            instance=pesanan
        )

    return render(
        request,
        (
            "administrator/pesanan/"
            "pesanan_tolak.html"
        ),
        {
            "form": form,
            "pesanan": pesanan,
        },
    )


@require_POST
@administrator_or_kasir_required
def pesanan_assign_petugas(request, pk):
    pesanan = get_object_or_404(
        Pesanan,
        pk=pk,
    )

    form = PenugasanPetugasForm(
        request.POST,
        instance=pesanan,
    )

    if form.is_valid():
        pesanan = form.save()

        messages.success(
            request,
            (
                f"Petugas untuk pesanan "
                f"{pesanan.kode_pesanan} "
                "berhasil ditentukan."
            ),
        )
    else:
        messages.error(
            request,
            "Petugas laundry gagal ditentukan.",
        )

    return redirect(
        "administrator:pesanan_detail",
        pk=pesanan.pk,
    )


@require_POST
@administrator_or_kasir_required
def pesanan_ubah_status(request, pk):
    pesanan = get_object_or_404(
        Pesanan,
        pk=pk,
    )

    form = UbahStatusPesananForm(
        request.POST,
        pesanan=pesanan,
    )

    if form.is_valid():
        status_lama = pesanan.status
        status_baru = form.cleaned_data[
            "status"
        ]
        catatan = form.cleaned_data[
            "catatan"
        ]

        with transaction.atomic():
            pesanan.status = status_baru

            if (
                status_baru
                == Pesanan.StatusPesanan.SELESAI
                and not pesanan.dapat_diselesaikan
            ):
                messages.error(
                    request,
                    (
                        "Pesanan hanya dapat diselesaikan "
                        "jika pembayaran lunas dan barang "
                        "sudah diterima pelanggan."
                    ),
                )

                return redirect(
                    "administrator:pesanan_detail",
                    pk=pesanan.pk,
                )

            pesanan.save()

            RiwayatStatus.objects.create(
                pesanan=pesanan,
                status_sebelumnya=status_lama,
                status_baru=status_baru,
                diubah_oleh=request.user,
                catatan=catatan,
            )

            buat_notifikasi(
                penerima=pesanan.pelanggan,
                judul="Status Pesanan Diperbarui",
                pesan=(
                    f"Status pesanan {pesanan.kode_pesanan} "
                    f"berubah menjadi "
                    f"{pesanan.get_status_display()}."
                ),
                jenis=Notifikasi.JenisNotifikasi.PESANAN,
            )

        messages.success(
            request,
            (
                f"Status pesanan "
                f"{pesanan.kode_pesanan} "
                "berhasil diperbarui."
            ),
        )

    else:
        pesan_error = " ".join(
            error
            for daftar_error
            in form.errors.values()
            for error in daftar_error
        )

        messages.error(
            request,
            pesan_error
            or "Status pesanan gagal diperbarui.",
        )

    return redirect(
        "administrator:pesanan_detail",
        pk=pesanan.pk,
    )


@require_POST
@administrator_or_kasir_required
def pesanan_ubah_pembayaran(request, pk):
    pesanan = get_object_or_404(
        Pesanan,
        pk=pk,
    )

    form = UbahStatusPembayaranForm(
        request.POST,
        instance=pesanan,
    )

    if form.is_valid():
        pesanan = form.save()

        buat_notifikasi(
            penerima=pesanan.pelanggan,
            judul="Status Pembayaran Diperbarui",
            pesan=(
                f"Status pembayaran pesanan "
                f"{pesanan.kode_pesanan} "
                f"berubah menjadi "
                f"{pesanan.get_status_pembayaran_display()}."
            ),
            jenis=Notifikasi.JenisNotifikasi.PEMBAYARAN,
        )
    else:
        messages.error(
            request,
            (
                "Status pembayaran gagal "
                "diperbarui."
            ),
        )

    return redirect(
        "administrator:pesanan_detail",
        pk=pesanan.pk,
    )