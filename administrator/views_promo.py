from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from .decorators import administrator_required
from .forms import PromoForm
from .models import Promo


@administrator_required
def promo_list(request):
    promo_queryset = (
        Promo.objects
        .prefetch_related("layanan")
        .all()
    )

    keyword = request.GET.get(
        "q",
        "",
    ).strip()

    jenis = request.GET.get(
        "jenis",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    if keyword:
        promo_queryset = promo_queryset.filter(
            Q(kode__icontains=keyword)
            | Q(nama__icontains=keyword)
        )

    if jenis in {
        Promo.JenisDiskon.PERSENTASE,
        Promo.JenisDiskon.NOMINAL,
    }:
        promo_queryset = promo_queryset.filter(
            jenis_diskon=jenis
        )

    if status == "aktif":
        promo_queryset = promo_queryset.filter(
            is_active=True
        )

    elif status == "nonaktif":
        promo_queryset = promo_queryset.filter(
            is_active=False
        )

    promo_queryset = promo_queryset.order_by(
        "-tanggal_mulai"
    ).distinct()

    jumlah_promo = promo_queryset.count()

    paginator = Paginator(
        promo_queryset,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "page_obj": page_obj,
        "jumlah_promo": jumlah_promo,
        "keyword": keyword,
        "jenis_filter": jenis,
        "status_filter": status,
        "jenis_choices": Promo.JenisDiskon.choices,
    }

    return render(
        request,
        "administrator/promo/promo_list.html",
        context,
    )


@administrator_required
def promo_create(request):
    if request.method == "POST":
        form = PromoForm(request.POST)

        if form.is_valid():
            promo = form.save()

            messages.success(
                request,
                (
                    f"Promo {promo.kode} berhasil "
                    "ditambahkan."
                ),
            )

            return redirect(
                "administrator:promo_detail",
                pk=promo.pk,
            )

    else:
        form = PromoForm()

    context = {
        "form": form,
        "judul": "Tambah Promo",
        "deskripsi": (
            "Tambahkan promo atau potongan harga baru."
        ),
        "tombol": "Simpan Promo",
    }

    return render(
        request,
        "administrator/promo/promo_form.html",
        context,
    )


@administrator_required
def promo_detail(request, pk):
    promo = get_object_or_404(
        Promo.objects.prefetch_related(
            "layanan"
        ),
        pk=pk,
    )

    context = {
        "promo": promo,
        "masih_berlaku": promo.masih_berlaku(),
    }

    return render(
        request,
        "administrator/promo/promo_detail.html",
        context,
    )


@administrator_required
def promo_update(request, pk):
    promo = get_object_or_404(
        Promo,
        pk=pk,
    )

    if request.method == "POST":
        form = PromoForm(
            request.POST,
            instance=promo,
        )

        if form.is_valid():
            promo = form.save()

            messages.success(
                request,
                (
                    f"Promo {promo.kode} berhasil "
                    "diperbarui."
                ),
            )

            return redirect(
                "administrator:promo_detail",
                pk=promo.pk,
            )

    else:
        form = PromoForm(
            instance=promo
        )

    context = {
        "form": form,
        "promo": promo,
        "judul": "Edit Promo",
        "deskripsi": (
            f"Ubah data promo {promo.kode}."
        ),
        "tombol": "Simpan Perubahan",
    }

    return render(
        request,
        "administrator/promo/promo_form.html",
        context,
    )


@require_POST
@administrator_required
def promo_toggle_active(request, pk):
    promo = get_object_or_404(
        Promo,
        pk=pk,
    )

    promo.is_active = not promo.is_active

    promo.save(
        update_fields=[
            "is_active",
            "updated_at",
        ]
    )

    status_pesan = (
        "diaktifkan"
        if promo.is_active
        else "dinonaktifkan"
    )

    messages.success(
        request,
        (
            f"Promo {promo.kode} berhasil "
            f"{status_pesan}."
        ),
    )

    return redirect(
        "administrator:promo_detail",
        pk=promo.pk,
    )