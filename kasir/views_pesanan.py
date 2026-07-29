from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.urls import reverse
from administrator.models import (
    Notifikasi,
    Pesanan,
    RiwayatStatus,
    User,
)

from .decorators import kasir_required
from .forms_pesanan import (
    DetailPesananFormSet,
    PemeriksaanDetailForm,
    PesananKasirForm,
)

from decimal import Decimal



@login_required
def pesanan_selesai(request, pk):
    pesanan = get_object_or_404(
        Pesanan,
        pk=pk,
    )

    if request.method != "POST":
        return redirect(
            "kasir:pesanan_detail",
            pk=pk,
        )

    if (
        pesanan.status_pembayaran
        != Pesanan.StatusPembayaran.LUNAS
    ):
        messages.error(
            request,
            "Pesanan belum dapat diselesaikan karena pembayaran belum lunas.",
        )

        return redirect(
            "kasir:pesanan_detail",
            pk=pk,
        )

    status_lama = pesanan.status

    pesanan.status = Pesanan.StatusPesanan.SELESAI
    pesanan.diterima_pelanggan = True
    pesanan.save()

    RiwayatStatus.objects.create(
        pesanan=pesanan,
        status_sebelumnya=status_lama,
        status_baru=Pesanan.StatusPesanan.SELESAI,
        diubah_oleh=request.user,
        catatan="Barang telah diterima pelanggan.",
    )

    Notifikasi.objects.create(
        penerima=pesanan.pelanggan,
        judul="Laundry Selesai",
        pesan=(
            f"Pesanan {pesanan.kode_pesanan} "
            "telah selesai."
        ),
        jenis=Notifikasi.JenisNotifikasi.STATUS,
    )

    messages.success(
        request,
        "Pesanan berhasil diselesaikan.",
    )

    return redirect(
        "kasir:pesanan_detail",
        pk=pk,
    )

@kasir_required
def pesanan_create(request):
    """
    Membuat pesanan baru melalui kasir.

    Harga satuan tidak diambil dari browser, tetapi selalu
    diambil ulang dari tarif aktif pada server.
    """

    pesanan_baru = Pesanan()

    if request.method == "POST":
        form = PesananKasirForm(
            request.POST,
            instance=pesanan_baru,
        )

        formset = DetailPesananFormSet(
            request.POST,
            instance=pesanan_baru,
            prefix="detail",
        )

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    pesanan = form.save(commit=False)

                    # Administrator masih boleh menguji modul Kasir,
                    # tetapi field kasir hanya diisi jika akun benar-benar Kasir.
                    if request.user.role == User.Role.KASIR:
                        pesanan.kasir = request.user
                    else:
                        pesanan.kasir = None

                    pesanan.status = (
                        Pesanan.StatusPesanan.MENUNGGU_PEMERIKSAAN
                    )

                    pesanan.status_pembayaran = (
                        Pesanan.StatusPembayaran.BELUM_DIBAYAR
                    )

                    area = pesanan.area_layanan
                    jenis = pesanan.jenis_pengantaran

                    biaya_antar_jemput = Decimal("0.00")

                    if area:
                        if jenis == Pesanan.JenisPengantaran.JEMPUT:
                            biaya_antar_jemput = area.biaya_jemput

                        elif jenis == Pesanan.JenisPengantaran.ANTAR:
                            biaya_antar_jemput = area.biaya_antar

                        elif jenis == Pesanan.JenisPengantaran.ANTAR_JEMPUT:
                            biaya_antar_jemput = (
                                area.biaya_antar
                                + area.biaya_jemput
                            )

                    pesanan.biaya_antar_jemput = (
                        biaya_antar_jemput
                    )

                    pesanan.save()

                    detail_instances = formset.save(
                        commit=False
                    )

                    for detail in detail_instances:
                        layanan = detail.layanan
                        tarif = layanan.tarif_aktif

                        if tarif is None:
                            raise ValueError(
                                f"Layanan {layanan.nama} "
                                "tidak memiliki tarif aktif."
                            )

                        detail.pesanan = pesanan
                        detail.satuan = layanan.satuan
                        detail.harga_satuan = tarif.harga
                        detail.subtotal = (
                            detail.jumlah
                            * detail.harga_satuan
                        )

                        detail.save()

                    for detail_dihapus in (
                        formset.deleted_objects
                    ):
                        detail_dihapus.delete()

                    pesanan.hitung_total(simpan=True)

                    messages.success(
                        request,
                        (
                            f"Pesanan {pesanan.kode_pesanan} "
                            "berhasil dibuat."
                        ),
                    )

                    return redirect(
                        "kasir:pesanan_detail",
                        pk=pesanan.pk,
                    )

            except ValueError as error:
                form.add_error(
                    None,
                    str(error),
                )

    else:
        form = PesananKasirForm(
            instance=pesanan_baru,
        )

        formset = DetailPesananFormSet(
            instance=pesanan_baru,
            prefix="detail",
        )

    context = {
        "form": form,
        "formset": formset,
    }

    return render(
        request,
        "kasir/pesanan/form.html",
        context,
    )

@kasir_required
def pesanan_list(request):
    """
    Menampilkan daftar pesanan pada modul kasir.

    Administrator dapat melihat seluruh pesanan.

    Kasir dapat melihat:
    - pesanan yang belum mempunyai kasir;
    - pesanan yang ditangani oleh dirinya sendiri.
    """

    user = request.user

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
        .prefetch_related(
            "detail",
            "detail__layanan",
            "detail__jenis_barang",
        )
        .order_by("-created_at")
    )

    if user.role == User.Role.KASIR:
        pesanan_queryset = pesanan_queryset.filter(
            Q(kasir=user)
            | Q(kasir__isnull=True)
        )

    # ==========================================
    # PENCARIAN
    # ==========================================
    keyword = request.GET.get("q", "").strip()

    if keyword:
        pesanan_queryset = pesanan_queryset.filter(
            Q(kode_pesanan__icontains=keyword)
            | Q(pelanggan__username__icontains=keyword)
            | Q(pelanggan__first_name__icontains=keyword)
            | Q(pelanggan__last_name__icontains=keyword)
            | Q(pelanggan__nomor_hp__icontains=keyword)
            | Q(pelanggan__email__icontains=keyword)
            | Q(detail__jenis_barang__nama__icontains=keyword)
            | Q(detail__layanan__nama__icontains=keyword)
        ).distinct()

    # ==========================================
    # FILTER STATUS PESANAN
    # ==========================================
    status = request.GET.get("status", "").strip()

    if status:
        pesanan_queryset = pesanan_queryset.filter(
            status=status,
        )

    # ==========================================
    # FILTER STATUS PEMBAYARAN
    # ==========================================
    status_pembayaran = request.GET.get(
        "status_pembayaran",
        "",
    ).strip()

    if status_pembayaran:
        pesanan_queryset = pesanan_queryset.filter(
            status_pembayaran=status_pembayaran,
        )

    # ==========================================
    # FILTER CARA BARANG MASUK
    # ==========================================
    cara_barang_masuk = request.GET.get(
        "cara_barang_masuk",
        "",
    ).strip()

    if cara_barang_masuk:
        pesanan_queryset = pesanan_queryset.filter(
            cara_barang_masuk=cara_barang_masuk,
        )

    # ==========================================
    # RINGKASAN
    # ==========================================
    total_pesanan = pesanan_queryset.count()

    menunggu_barang_diantar = pesanan_queryset.filter(
        status=(
            Pesanan.StatusPesanan.MENUNGGU_BARANG_DIANTAR
        ),
    ).count()

    menunggu_penjemputan = pesanan_queryset.filter(
        status=(
            Pesanan.StatusPesanan.MENUNGGU_PENJEMPUTAN
        ),
    ).count()

    menunggu_pemeriksaan = pesanan_queryset.filter(
        status=(
            Pesanan.StatusPesanan.MENUNGGU_PEMERIKSAAN
        ),
    ).count()

    belum_dibayar = pesanan_queryset.filter(
        status_pembayaran=(
            Pesanan.StatusPembayaran.BELUM_DIBAYAR
        ),
    ).count()

    selesai = pesanan_queryset.filter(
        status=Pesanan.StatusPesanan.SELESAI,
    ).count()

    # ==========================================
    # PAGINATION
    # ==========================================
    paginator = Paginator(
        pesanan_queryset,
        10,
    )

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "pesanan_list": page_obj.object_list,

        "keyword": keyword,
        "status_terpilih": status,
        "status_pembayaran_terpilih": (
            status_pembayaran
        ),
        "cara_barang_masuk_terpilih": (
            cara_barang_masuk
        ),

        "status_choices": (
            Pesanan.StatusPesanan.choices
        ),
        "status_pembayaran_choices": (
            Pesanan.StatusPembayaran.choices
        ),
        "cara_barang_masuk_choices": (
            Pesanan.CaraBarangMasuk.choices
        ),

        "total_pesanan": total_pesanan,
        "menunggu_barang_diantar": (
            menunggu_barang_diantar
        ),
        "menunggu_penjemputan": (
            menunggu_penjemputan
        ),
        "menunggu_pemeriksaan": (
            menunggu_pemeriksaan
        ),
        "belum_dibayar": belum_dibayar,
        "selesai": selesai,
    }

    return render(
        request,
        "kasir/pesanan/list.html",
        context,
    )

@kasir_required
def pesanan_detail(request, pk):
    """
    Menampilkan detail lengkap satu pesanan.
    """

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
        .prefetch_related(
            "detail",
            "detail__layanan",
            "riwayat_status",
            "riwayat_status__diubah_oleh",
            "pembayaran",
            "pembayaran__metode_pembayaran",
        )
    )

    pesanan = get_object_or_404(
        pesanan_queryset,
        pk=pk,
    )

    if (
        request.user.role == User.Role.KASIR
        and pesanan.kasir_id not in {
            None,
            request.user.id,
        }
    ):
        return render(
            request,
            "kasir/403.html",
            status=403,
        )

    form_pemeriksaan = []

    for detail in pesanan.detail.all():
        form_pemeriksaan.append(
            (
                detail,
                PemeriksaanDetailForm(
                    instance=detail,
                    prefix=f"detail_{detail.id}",
                ),
            )
        )

    context = {
        "pesanan": pesanan,
        "form_pemeriksaan": form_pemeriksaan,
    }

    return render(
        request,
        "kasir/pesanan/detail.html",
        context,
    )

from django.views.decorators.http import require_POST


@require_POST
@kasir_required
def pesanan_terima(request, pk):
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
            "Pesanan ini sudah diproses sebelumnya.",
        )

        return redirect(
            "kasir:pesanan_detail",
            pk=pesanan.pk,
        )

    petugas = (
        User.objects
        .filter(
            role=User.Role.PETUGAS_LAUNDRY,
            is_active=True,
            is_verified=True,
        )
        .order_by("id")
        .first()
    )

    if petugas is None:
        messages.error(
            request,
            "Belum ada Petugas Laundry yang aktif.",
        )

        return redirect(
            "kasir:pesanan_detail",
            pk=pesanan.pk,
        )

    status_sebelumnya = pesanan.status

    with transaction.atomic():
        pesanan.kasir = request.user
        pesanan.petugas_laundry = petugas
        pesanan.status = (
            Pesanan.StatusPesanan.MENUNGGU_ANTRIAN
        )

        pesanan.save(
            update_fields=[
                "kasir",
                "petugas_laundry",
                "status",
                "updated_at",
            ]
        )

        RiwayatStatus.objects.create(
            pesanan=pesanan,
            status_sebelumnya=status_sebelumnya,
            status_baru=pesanan.status,
            diubah_oleh=request.user,
            catatan=(
                "Pesanan diterima oleh kasir dan "
                "ditugaskan kepada petugas laundry."
            ),
        )

    messages.success(
        request,
        (
            "Pesanan berhasil diterima dan masuk "
            f"ke tugas {petugas.get_full_name() or petugas.username}."
        ),
    )

    return redirect(
        "kasir:pesanan_detail",
        pk=pesanan.pk,
    )


@require_POST
@kasir_required
def pesanan_tolak(request, pk):
    pesanan = get_object_or_404(Pesanan, pk=pk)

    pesanan.kasir = request.user
    pesanan.status = Pesanan.StatusPesanan.DITOLAK
    pesanan.save()

    messages.success(request, "Pesanan berhasil ditolak.")

    return redirect(
        "kasir:pesanan_detail",
        pk=pesanan.pk,
    )

@require_POST
@kasir_required
@transaction.atomic
def pesanan_pemeriksaan(request, pk):
    pesanan = get_object_or_404(
        Pesanan.objects.prefetch_related(
            "detail__layanan",
            "detail__jenis_barang",
        ),
        pk=pk,
    )

    status_diperbolehkan = {
        Pesanan.StatusPesanan.MENUNGGU_BARANG_DIANTAR,
        Pesanan.StatusPesanan.MENUNGGU_PENJEMPUTAN,
        Pesanan.StatusPesanan.MENUNGGU_PEMERIKSAAN,
    }

    if pesanan.status not in status_diperbolehkan:
        messages.error(
            request,
            "Pesanan ini tidak dapat diperiksa pada status sekarang.",
        )

        return redirect(
            "kasir:pesanan_detail",
            pk=pesanan.pk,
        )

    forms_pemeriksaan = []
    semua_valid = True

    for detail in pesanan.detail.all():
        form = PemeriksaanDetailForm(
            request.POST,
            instance=detail,
            prefix=f"detail_{detail.id}",
        )

        forms_pemeriksaan.append(
            (detail, form)
        )

        if not form.is_valid():
            semua_valid = False

    if not semua_valid:
        context = {
            "pesanan": pesanan,
            "form_pemeriksaan": forms_pemeriksaan,
        }

        return render(
            request,
            "kasir/pesanan/detail.html",
            context,
        )

    for detail, form in forms_pemeriksaan:
        form.save()

    pesanan.hitung_total(
        simpan=False
    )

    petugas = (
        User.objects
        .filter(
            role=User.Role.PETUGAS_LAUNDRY,
            is_active=True,
        )
        .annotate(
            jumlah_pekerjaan=Count(
                "pesanan_dikerjakan",
                filter=Q(
                    pesanan_dikerjakan__status__in=[
                        Pesanan.StatusPesanan.MENUNGGU_ANTRIAN,
                        Pesanan.StatusPesanan.DICUCI,
                        Pesanan.StatusPesanan.DIKERINGKAN,
                        Pesanan.StatusPesanan.DISETRIKA,
                        Pesanan.StatusPesanan.DILIPAT,
                        Pesanan.StatusPesanan.DIKEMAS,
                    ]
                ),
            )
        )
        .order_by(
            "jumlah_pekerjaan",
            "id",
        )
        .first()
    )

    status_lama = pesanan.status

    pesanan.kasir = request.user
    pesanan.petugas_laundry = petugas

    if petugas:
        pesanan.status = (
            Pesanan.StatusPesanan.MENUNGGU_ANTRIAN
        )
    else:
        pesanan.status = (
            Pesanan.StatusPesanan.MENUNGGU_PETUGAS
        )

    pesanan.save(
        update_fields=[
            "kasir",
            "petugas_laundry",
            "status",
            "subtotal",
            "diskon",
            "total_biaya",
            "updated_at",
        ]
    )

    RiwayatStatus.objects.create(
        pesanan=pesanan,
        status_sebelumnya=status_lama,
        status_baru=pesanan.status,
        diubah_oleh=request.user,
        catatan=(
            "Pemeriksaan barang diselesaikan oleh kasir."
        ),
    )

    if petugas:
        Notifikasi.objects.create(
            penerima=petugas,
            jenis=Notifikasi.JenisNotifikasi.PESANAN,
            judul="Tugas laundry baru",
            pesan=(
                f"Pesanan {pesanan.kode_pesanan} "
                "telah ditugaskan kepada Anda."
            ),
            link=reverse(
                "petugas:tugas_detail",
                kwargs={
                    "pk": pesanan.pk,
                },
            ),
            is_read=False,
        )

        messages.success(
            request,
            (
                "Pemeriksaan berhasil disimpan. "
                f"Pesanan ditugaskan kepada "
                f"{petugas.get_full_name() or petugas.username}."
            ),
        )

    else:
        messages.warning(
            request,
            (
                "Pemeriksaan berhasil disimpan, tetapi "
                "belum ada Petugas Laundry yang tersedia."
            ),
        )

    return redirect(
        "kasir:pesanan_detail",
        pk=pesanan.pk,
    )