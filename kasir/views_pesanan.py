from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from administrator.models import Pesanan, User

from .decorators import kasir_required
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from .forms_pesanan import (
    DetailPesananFormSet,
    PesananKasirForm,
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
                        Pesanan.StatusPesanan.DITERIMA
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
    Menampilkan daftar pesanan pada modul Kasir.

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
        )
        .order_by("-created_at")
    )

    if user.role == User.Role.KASIR:
        pesanan_queryset = pesanan_queryset.filter(
            Q(kasir=user) |
            Q(kasir__isnull=True)
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
        )

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
    # FILTER JENIS PENGANTARAN
    # ==========================================
    jenis_pengantaran = request.GET.get(
        "jenis_pengantaran",
        "",
    ).strip()

    if jenis_pengantaran:
        pesanan_queryset = pesanan_queryset.filter(
            jenis_pengantaran=jenis_pengantaran,
        )

    # ==========================================
    # RINGKASAN
    # ==========================================
    total_pesanan = pesanan_queryset.count()

    menunggu_konfirmasi = pesanan_queryset.filter(
        status=Pesanan.StatusPesanan.MENUNGGU_KONFIRMASI,
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
        "status_pembayaran_terpilih": status_pembayaran,
        "jenis_pengantaran_terpilih": jenis_pengantaran,

        "status_choices": Pesanan.StatusPesanan.choices,
        "status_pembayaran_choices": (
            Pesanan.StatusPembayaran.choices
        ),
        "jenis_pengantaran_choices": (
            Pesanan.JenisPengantaran.choices
        ),

        "total_pesanan": total_pesanan,
        "menunggu_konfirmasi": menunggu_konfirmasi,
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

    context = {
        "pesanan": pesanan,
    }

    return render(
        request,
        "kasir/pesanan/detail.html",
        context,
    )
