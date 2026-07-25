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

from .decorators import administrator_required
from .forms import TarifForm
from .models import Layanan, Tarif


@administrator_required
def tarif_list(request):
    tarif_queryset = (
        Tarif.objects
        .select_related(
            "layanan",
            "layanan__kategori",
        )
        .all()
    )

    keyword = request.GET.get(
        "q",
        "",
    ).strip()

    layanan_id = request.GET.get(
        "layanan",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    if keyword:
        tarif_queryset = tarif_queryset.filter(
            Q(layanan__nama__icontains=keyword)
            | Q(layanan__kode__icontains=keyword)
            | Q(
                layanan__kategori__nama__icontains=keyword
            )
        )

    if layanan_id.isdigit():
        tarif_queryset = tarif_queryset.filter(
            layanan_id=layanan_id
        )

    if status == "aktif":
        tarif_queryset = tarif_queryset.filter(
            is_active=True
        )

    elif status == "nonaktif":
        tarif_queryset = tarif_queryset.filter(
            is_active=False
        )

    tarif_queryset = tarif_queryset.order_by(
        "layanan__nama",
        "-tanggal_mulai",
    )

    jumlah_tarif = tarif_queryset.count()

    paginator = Paginator(
        tarif_queryset,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    layanan_choices = (
        Layanan.objects
        .select_related("kategori")
        .all()
        .order_by(
            "kategori__nama",
            "nama",
        )
    )

    context = {
        "page_obj": page_obj,
        "jumlah_tarif": jumlah_tarif,
        "keyword": keyword,
        "layanan_filter": layanan_id,
        "status_filter": status,
        "layanan_choices": layanan_choices,
    }

    return render(
        request,
        "administrator/tarif/tarif_list.html",
        context,
    )


@administrator_required
def tarif_create(request):
    if request.method == "POST":
        form = TarifForm(request.POST)

        if form.is_valid():
            tarif = form.save()

            messages.success(
                request,
                (
                    f"Tarif layanan "
                    f"{tarif.layanan.nama} "
                    "berhasil ditambahkan."
                ),
            )

            return redirect(
                "administrator:tarif_detail",
                pk=tarif.pk,
            )

    else:
        form = TarifForm()

    context = {
        "form": form,
        "judul": "Tambah Tarif",
        "deskripsi": (
            "Tambahkan harga layanan laundry."
        ),
        "tombol": "Simpan Tarif",
    }

    return render(
        request,
        "administrator/tarif/tarif_form.html",
        context,
    )


@administrator_required
def tarif_detail(request, pk):
    tarif = get_object_or_404(
        Tarif.objects.select_related(
            "layanan",
            "layanan__kategori",
        ),
        pk=pk,
    )

    return render(
        request,
        "administrator/tarif/tarif_detail.html",
        {
            "tarif": tarif,
        },
    )


@administrator_required
def tarif_update(request, pk):
    tarif = get_object_or_404(
        Tarif,
        pk=pk,
    )

    if request.method == "POST":
        form = TarifForm(
            request.POST,
            instance=tarif,
        )

        if form.is_valid():
            tarif = form.save()

            messages.success(
                request,
                (
                    f"Tarif layanan "
                    f"{tarif.layanan.nama} "
                    "berhasil diperbarui."
                ),
            )

            return redirect(
                "administrator:tarif_detail",
                pk=tarif.pk,
            )

    else:
        form = TarifForm(
            instance=tarif
        )

    context = {
        "form": form,
        "tarif": tarif,
        "judul": "Edit Tarif",
        "deskripsi": (
            f"Ubah tarif layanan "
            f"{tarif.layanan.nama}."
        ),
        "tombol": "Simpan Perubahan",
    }

    return render(
        request,
        "administrator/tarif/tarif_form.html",
        context,
    )


@require_POST
@administrator_required
@transaction.atomic
def tarif_toggle_active(request, pk):
    tarif = get_object_or_404(
        Tarif.objects.select_related(
            "layanan"
        ),
        pk=pk,
    )

    if tarif.is_active:
        tarif.is_active = False
        status_pesan = "dinonaktifkan"

    else:
        Tarif.objects.filter(
            layanan=tarif.layanan,
            is_active=True,
        ).exclude(
            pk=tarif.pk
        ).update(
            is_active=False
        )

        tarif.is_active = True
        status_pesan = "diaktifkan"

    tarif.save(
        update_fields=[
            "is_active",
            "updated_at",
        ]
    )

    messages.success(
        request,
        (
            f"Tarif {tarif.layanan.nama} "
            f"berhasil {status_pesan}."
        ),
    )

    return redirect(
        "administrator:tarif_detail",
        pk=tarif.pk,
    )