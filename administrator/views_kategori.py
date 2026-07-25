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
from .forms import KategoriLayananForm
from .models import KategoriLayanan


@administrator_required
def kategori_list(request):
    """
    Daftar kategori layanan.
    """

    kategori = KategoriLayanan.objects.all().order_by(
        "nama"
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
        kategori = kategori.filter(
            Q(nama__icontains=keyword)
            | Q(deskripsi__icontains=keyword)
        )

    if status == "aktif":
        kategori = kategori.filter(
            is_active=True
        )

    elif status == "nonaktif":
        kategori = kategori.filter(
            is_active=False
        )

    jumlah_kategori = kategori.count()

    paginator = Paginator(
        kategori,
        10,
    )

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(
        page_number
    )

    context = {
        "page_obj": page_obj,
        "keyword": keyword,
        "status_filter": status,
        "jumlah_kategori": jumlah_kategori,
    }

    return render(
        request,
        "administrator/kategori/kategori_list.html",
        context,
    )


@administrator_required
def kategori_create(request):
    """
    Menambahkan kategori layanan.
    """

    if request.method == "POST":
        form = KategoriLayananForm(
            request.POST
        )

        if form.is_valid():
            kategori = form.save()

            messages.success(
                request,
                (
                    f"Kategori {kategori.nama} "
                    "berhasil ditambahkan."
                ),
            )

            return redirect(
                "administrator:kategori_detail",
                pk=kategori.pk,
            )

    else:
        form = KategoriLayananForm()

    context = {
        "form": form,
        "judul": "Tambah Kategori Layanan",
        "deskripsi": (
            "Tambahkan kategori untuk "
            "mengelompokkan layanan laundry."
        ),
        "tombol": "Simpan Kategori",
    }

    return render(
        request,
        "administrator/kategori/kategori_form.html",
        context,
    )


@administrator_required
def kategori_detail(request, pk):
    """
    Menampilkan detail kategori.
    """

    kategori = get_object_or_404(
        KategoriLayanan,
        pk=pk,
    )

    context = {
        "kategori": kategori,
    }

    return render(
        request,
        "administrator/kategori/kategori_detail.html",
        context,
    )


@administrator_required
def kategori_update(request, pk):
    """
    Mengubah kategori layanan.
    """

    kategori = get_object_or_404(
        KategoriLayanan,
        pk=pk,
    )

    if request.method == "POST":
        form = KategoriLayananForm(
            request.POST,
            instance=kategori,
        )

        if form.is_valid():
            kategori = form.save()

            messages.success(
                request,
                (
                    f"Kategori {kategori.nama} "
                    "berhasil diperbarui."
                ),
            )

            return redirect(
                "administrator:kategori_detail",
                pk=kategori.pk,
            )

    else:
        form = KategoriLayananForm(
            instance=kategori
        )

    context = {
        "form": form,
        "judul": "Edit Kategori Layanan",
        "deskripsi": (
            f"Ubah data kategori {kategori.nama}."
        ),
        "tombol": "Simpan Perubahan",
        "kategori": kategori,
    }

    return render(
        request,
        "administrator/kategori/kategori_form.html",
        context,
    )


@require_POST
@administrator_required
def kategori_toggle_active(request, pk):
    """
    Mengaktifkan atau menonaktifkan kategori.
    """

    kategori = get_object_or_404(
        KategoriLayanan,
        pk=pk,
    )

    kategori.is_active = not kategori.is_active

    kategori.save(
        update_fields=[
            "is_active",
        ]
    )

    status = (
        "diaktifkan"
        if kategori.is_active
        else "dinonaktifkan"
    )

    messages.success(
        request,
        (
            f"Kategori {kategori.nama} "
            f"berhasil {status}."
        ),
    )

    return redirect(
        "administrator:kategori_detail",
        pk=kategori.pk,
    )