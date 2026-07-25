from django.shortcuts import render

from administrator.decorators import role_required
from administrator.models import Pesanan, User
from django.contrib import messages
from django.shortcuts import redirect

from .forms import (
    PesananPelangganForm,
    DetailPesananPelangganForm,
)


@role_required([User.Role.PELANGGAN])
def dashboard(request):
    context = {
        "pesanan_saya": Pesanan.objects.filter(
            pelanggan=request.user
        ).order_by("-created_at"),
    }

    return render(
        request,
        "pelanggan/dashboard.html",
        context,
    )

@role_required([User.Role.PELANGGAN])
def pesanan_tambah(request):

    if request.method == "POST":

        form = PesananPelangganForm(request.POST)
        detail_form = DetailPesananPelangganForm(request.POST)

        if form.is_valid() and detail_form.is_valid():

            pesanan = form.save(commit=False)
            pesanan.pelanggan = request.user
            pesanan.save()

            detail = detail_form.save(commit=False)
            detail.pesanan = pesanan

            tarif = detail.layanan.tarif_aktif

            if tarif:
                detail.harga_satuan = tarif.harga
            else:
                detail.harga_satuan = 0

            detail.satuan = detail.layanan.satuan
            detail.save()

            pesanan.hitung_total()

            messages.success(
                request,
                "Pesanan laundry berhasil dibuat.",
            )

            return redirect(
                "pelanggan:dashboard"
            )

    else:

        form = PesananPelangganForm()
        detail_form = DetailPesananPelangganForm()

    context = {
        "form": form,
        "detail_form": detail_form,
    }

    return render(
        request,
        "pelanggan/pesanan/form.html",
        context,
    )