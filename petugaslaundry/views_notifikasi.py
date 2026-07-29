from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from administrator.models import Notifikasi

from .decorators import petugas_required


@petugas_required
def notifikasi_list(request):
    queryset = (
        Notifikasi.objects
        .filter(penerima=request.user)
        .order_by("-created_at")
    )

    jumlah_belum_dibaca = queryset.filter(
        is_read=False,
    ).count()

    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "page_obj": page_obj,
        "jumlah_belum_dibaca": jumlah_belum_dibaca,
        "judul_halaman": "Notifikasi Petugas Laundry",
        "url_baca": "petugas:notifikasi_baca",
        "url_baca_semua": "petugas:notifikasi_baca_semua",
    }

    return render(
        request,
        "notifikasi/list_umum.html",
        context,
    )


@petugas_required
def notifikasi_baca(request, pk):
    notifikasi = get_object_or_404(
        Notifikasi,
        pk=pk,
        penerima=request.user,
    )

    if not notifikasi.is_read:
        notifikasi.is_read = True
        notifikasi.save(
            update_fields=["is_read"]
        )

    if notifikasi.link:
        return redirect(notifikasi.link)

    return redirect("petugas:notifikasi_list")


@require_POST
@petugas_required
def notifikasi_baca_semua(request):
    Notifikasi.objects.filter(
        penerima=request.user,
        is_read=False,
    ).update(is_read=True)

    messages.success(
        request,
        "Semua notifikasi berhasil ditandai sudah dibaca.",
    )

    return redirect("petugas:notifikasi_list")