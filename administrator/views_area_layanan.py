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
from .forms import AreaLayananForm
from .models import AreaLayanan


@administrator_required
def area_layanan_list(request):
    area_queryset = (
        AreaLayanan.objects
        .all()
        .order_by("nama_area")
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
        area_queryset = area_queryset.filter(
            Q(nama_area__icontains=keyword)
            | Q(kode_pos__icontains=keyword)
        )

    if status == "aktif":
        area_queryset = area_queryset.filter(
            is_active=True
        )

    elif status == "nonaktif":
        area_queryset = area_queryset.filter(
            is_active=False
        )

    jumlah_area = area_queryset.count()

    paginator = Paginator(
        area_queryset,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "page_obj": page_obj,
        "jumlah_area": jumlah_area,
        "keyword": keyword,
        "status_filter": status,
    }

    return render(
        request,
        (
            "administrator/area_layanan/"
            "area_layanan_list.html"
        ),
        context,
    )


@administrator_required
def area_layanan_create(request):
    if request.method == "POST":
        form = AreaLayananForm(
            request.POST
        )

        if form.is_valid():
            area = form.save()

            messages.success(
                request,
                (
                    f"Area layanan {area.nama_area} "
                    "berhasil ditambahkan."
                ),
            )

            return redirect(
                "administrator:area_layanan_detail",
                pk=area.pk,
            )

    else:
        form = AreaLayananForm()

    context = {
        "form": form,
        "judul": "Tambah Area Layanan",
        "deskripsi": (
            "Tambahkan wilayah layanan "
            "antar-jemput laundry."
        ),
        "tombol": "Simpan Area",
    }

    return render(
        request,
        (
            "administrator/area_layanan/"
            "area_layanan_form.html"
        ),
        context,
    )


@administrator_required
def area_layanan_detail(request, pk):
    area = get_object_or_404(
        AreaLayanan,
        pk=pk,
    )

    context = {
        "area": area,
    }

    return render(
        request,
        (
            "administrator/area_layanan/"
            "area_layanan_detail.html"
        ),
        context,
    )


@administrator_required
def area_layanan_update(request, pk):
    area = get_object_or_404(
        AreaLayanan,
        pk=pk,
    )

    if request.method == "POST":
        form = AreaLayananForm(
            request.POST,
            instance=area,
        )

        if form.is_valid():
            area = form.save()

            messages.success(
                request,
                (
                    f"Area layanan {area.nama_area} "
                    "berhasil diperbarui."
                ),
            )

            return redirect(
                "administrator:area_layanan_detail",
                pk=area.pk,
            )

    else:
        form = AreaLayananForm(
            instance=area
        )

    context = {
        "form": form,
        "area": area,
        "judul": "Edit Area Layanan",
        "deskripsi": (
            f"Ubah data area {area.nama_area}."
        ),
        "tombol": "Simpan Perubahan",
    }

    return render(
        request,
        (
            "administrator/area_layanan/"
            "area_layanan_form.html"
        ),
        context,
    )


@require_POST
@administrator_required
def area_layanan_toggle_active(
    request,
    pk,
):
    area = get_object_or_404(
        AreaLayanan,
        pk=pk,
    )

    area.is_active = not area.is_active

    area.save(
        update_fields=[
            "is_active",
            "updated_at",
        ]
    )

    status_pesan = (
        "diaktifkan"
        if area.is_active
        else "dinonaktifkan"
    )

    messages.success(
        request,
        (
            f"Area layanan {area.nama_area} "
            f"berhasil {status_pesan}."
        ),
    )

    return redirect(
        "administrator:area_layanan_detail",
        pk=area.pk,
    )