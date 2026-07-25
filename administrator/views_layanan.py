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
from .forms import LayananForm
from .models import KategoriLayanan, Layanan


@administrator_required
def layanan_list(request):
    """
    Menampilkan daftar layanan laundry.
    """

    layanan = (
        Layanan.objects
        .select_related("kategori")
        .all()
        .order_by("nama")
    )

    keyword = request.GET.get(
        "q",
        "",
    ).strip()

    kategori_id = request.GET.get(
        "kategori",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    if keyword:
        layanan = layanan.filter(
            Q(nama__icontains=keyword)
            | Q(deskripsi__icontains=keyword)
            | Q(kategori__nama__icontains=keyword)
        )

    if kategori_id.isdigit():
        layanan = layanan.filter(
            kategori_id=kategori_id
        )

    if status == "aktif":
        layanan = layanan.filter(
            is_active=True
        )

    elif status == "nonaktif":
        layanan = layanan.filter(
            is_active=False
        )

    jumlah_layanan = layanan.count()

    paginator = Paginator(
        layanan,
        10,
    )

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(
        page_number
    )

    kategori_choices = (
        KategoriLayanan.objects
        .all()
        .order_by("nama")
    )

    context = {
        "page_obj": page_obj,
        "jumlah_layanan": jumlah_layanan,
        "keyword": keyword,
        "kategori_filter": kategori_id,
        "status_filter": status,
        "kategori_choices": kategori_choices,
    }

    return render(
        request,
        "administrator/layanan/layanan_list.html",
        context,
    )


@administrator_required
def layanan_create(request):
    """
    Menambahkan layanan laundry.
    """

    if request.method == "POST":
        form = LayananForm(
            request.POST
        )

        if form.is_valid():
            layanan = form.save()

            messages.success(
                request,
                (
                    f"Layanan {layanan.nama} "
                    "berhasil ditambahkan."
                ),
            )

            return redirect(
                "administrator:layanan_detail",
                pk=layanan.pk,
            )

    else:
        form = LayananForm()

    context = {
        "form": form,
        "judul": "Tambah Layanan",
        "deskripsi": (
            "Tambahkan layanan laundry yang "
            "tersedia untuk pelanggan."
        ),
        "tombol": "Simpan Layanan",
    }

    return render(
        request,
        "administrator/layanan/layanan_form.html",
        context,
    )


@administrator_required
def layanan_detail(request, pk):
    """
    Menampilkan detail layanan.
    """

    layanan = get_object_or_404(
        Layanan.objects.select_related(
            "kategori"
        ),
        pk=pk,
    )

    context = {
        "layanan": layanan,
    }

    return render(
        request,
        "administrator/layanan/layanan_detail.html",
        context,
    )


@administrator_required
def layanan_update(request, pk):
    """
    Mengubah data layanan.
    """

    layanan = get_object_or_404(
        Layanan,
        pk=pk,
    )

    if request.method == "POST":
        form = LayananForm(
            request.POST,
            instance=layanan,
        )

        if form.is_valid():
            layanan = form.save()

            messages.success(
                request,
                (
                    f"Layanan {layanan.nama} "
                    "berhasil diperbarui."
                ),
            )

            return redirect(
                "administrator:layanan_detail",
                pk=layanan.pk,
            )

    else:
        form = LayananForm(
            instance=layanan
        )

    context = {
        "form": form,
        "judul": "Edit Layanan",
        "deskripsi": (
            f"Ubah data layanan {layanan.nama}."
        ),
        "tombol": "Simpan Perubahan",
        "layanan": layanan,
    }

    return render(
        request,
        "administrator/layanan/layanan_form.html",
        context,
    )


@require_POST
@administrator_required
def layanan_toggle_active(request, pk):
    """
    Mengaktifkan atau menonaktifkan layanan.
    """

    layanan = get_object_or_404(
        Layanan,
        pk=pk,
    )

    layanan.is_active = not layanan.is_active

    layanan.save(
        update_fields=[
            "is_active",
        ]
    )

    status = (
        "diaktifkan"
        if layanan.is_active
        else "dinonaktifkan"
    )

    messages.success(
        request,
        (
            f"Layanan {layanan.nama} "
            f"berhasil {status}."
        ),
    )

    return redirect(
        "administrator:layanan_detail",
        pk=layanan.pk,
    )