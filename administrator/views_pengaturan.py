from django.contrib import messages
from django.shortcuts import (
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from .decorators import administrator_required
from .forms import PengaturanSistemForm
from .models import PengaturanSistem


def ambil_pengaturan_sistem():
    """
    Mengambil satu pengaturan utama.

    Jika data belum ada, sistem otomatis membuat
    pengaturan dengan nilai default dari model.
    """
    pengaturan = (
        PengaturanSistem.objects
        .order_by("pk")
        .first()
    )

    if pengaturan is None:
        pengaturan = PengaturanSistem.objects.create()

    return pengaturan


@administrator_required
def pengaturan_sistem(request):
    pengaturan = ambil_pengaturan_sistem()

    if request.method == "POST":
        form = PengaturanSistemForm(
            request.POST,
            instance=pengaturan,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Pengaturan sistem berhasil diperbarui.",
            )

            return redirect(
                "administrator:pengaturan_sistem"
            )

    else:
        form = PengaturanSistemForm(
            instance=pengaturan
        )

    context = {
        "form": form,
        "pengaturan": pengaturan,
    }

    return render(
        request,
        (
            "administrator/pengaturan/"
            "pengaturan_sistem.html"
        ),
        context,
    )


@require_POST
@administrator_required
def pengaturan_toggle_pesanan(request):
    pengaturan = ambil_pengaturan_sistem()

    pengaturan.menerima_pesanan = (
        not pengaturan.menerima_pesanan
    )

    pengaturan.save(
        update_fields=[
            "menerima_pesanan",
            "updated_at",
        ]
    )

    if pengaturan.menerima_pesanan:
        pesan = (
            "Penerimaan pesanan berhasil dibuka."
        )
    else:
        pesan = (
            "Penerimaan pesanan berhasil ditutup."
        )

    messages.success(
        request,
        pesan,
    )

    return redirect(
        "administrator:pengaturan_sistem"
    )