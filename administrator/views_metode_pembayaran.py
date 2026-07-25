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
from .forms import MetodePembayaranForm
from .models import MetodePembayaran


@administrator_required
def metode_pembayaran_list(request):
    metode_queryset = (
        MetodePembayaran.objects
        .all()
        .order_by("nama")
    )

    keyword = request.GET.get(
        "q",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    if keyword:
        metode_queryset = metode_queryset.filter(
            Q(nama__icontains=keyword)
            | Q(nomor_rekening__icontains=keyword)
            | Q(atas_nama__icontains=keyword)
        )

    if status == "aktif":
        metode_queryset = metode_queryset.filter(
            is_active=True
        )

    elif status == "nonaktif":
        metode_queryset = metode_queryset.filter(
            is_active=False
        )

    jumlah_metode = metode_queryset.count()

    paginator = Paginator(
        metode_queryset,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "page_obj": page_obj,
        "jumlah_metode": jumlah_metode,
        "keyword": keyword,
        "status_filter": status,
    }

    return render(
        request,
        (
            "administrator/metode_pembayaran/"
            "metode_pembayaran_list.html"
        ),
        context,
    )


@administrator_required
def metode_pembayaran_create(request):
    if request.method == "POST":
        form = MetodePembayaranForm(
            request.POST
        )

        if form.is_valid():
            metode = form.save()

            messages.success(
                request,
                (
                    f"Metode pembayaran {metode.nama} "
                    "berhasil ditambahkan."
                ),
            )

            return redirect(
                "administrator:metode_pembayaran_detail",
                pk=metode.pk,
            )

    else:
        form = MetodePembayaranForm()

    context = {
        "form": form,
        "judul": "Tambah Metode Pembayaran",
        "deskripsi": (
            "Tambahkan metode pembayaran yang dapat "
            "dipilih pelanggan."
        ),
        "tombol": "Simpan Metode",
    }

    return render(
        request,
        (
            "administrator/metode_pembayaran/"
            "metode_pembayaran_form.html"
        ),
        context,
    )


@administrator_required
def metode_pembayaran_detail(request, pk):
    metode = get_object_or_404(
        MetodePembayaran,
        pk=pk,
    )

    context = {
        "metode": metode,
    }

    return render(
        request,
        (
            "administrator/metode_pembayaran/"
            "metode_pembayaran_detail.html"
        ),
        context,
    )


@administrator_required
def metode_pembayaran_update(request, pk):
    metode = get_object_or_404(
        MetodePembayaran,
        pk=pk,
    )

    if request.method == "POST":
        form = MetodePembayaranForm(
            request.POST,
            instance=metode,
        )

        if form.is_valid():
            metode = form.save()

            messages.success(
                request,
                (
                    f"Metode pembayaran {metode.nama} "
                    "berhasil diperbarui."
                ),
            )

            return redirect(
                "administrator:metode_pembayaran_detail",
                pk=metode.pk,
            )

    else:
        form = MetodePembayaranForm(
            instance=metode
        )

    context = {
        "form": form,
        "metode": metode,
        "judul": "Edit Metode Pembayaran",
        "deskripsi": (
            f"Ubah metode pembayaran {metode.nama}."
        ),
        "tombol": "Simpan Perubahan",
    }

    return render(
        request,
        (
            "administrator/metode_pembayaran/"
            "metode_pembayaran_form.html"
        ),
        context,
    )


@require_POST
@administrator_required
def metode_pembayaran_toggle_active(
    request,
    pk,
):
    metode = get_object_or_404(
        MetodePembayaran,
        pk=pk,
    )

    metode.is_active = not metode.is_active

    metode.save(
        update_fields=[
            "is_active",
            "updated_at",
        ]
    )

    status_pesan = (
        "diaktifkan"
        if metode.is_active
        else "dinonaktifkan"
    )

    messages.success(
        request,
        (
            f"Metode pembayaran {metode.nama} "
            f"berhasil {status_pesan}."
        ),
    )

    return redirect(
        "administrator:metode_pembayaran_detail",
        pk=metode.pk,
    )