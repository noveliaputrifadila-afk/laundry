from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .decorators import administrator_required
from .models import Notifikasi


@administrator_required
def notifikasi_list(request):
    query = request.GET.get("q", "").strip()
    jenis = request.GET.get("jenis", "").strip()
    status = request.GET.get("status", "").strip()

    semua_notifikasi = Notifikasi.objects.filter(
        penerima=request.user,
    )

    notifikasi_queryset = (
        semua_notifikasi
        .select_related(
            "penerima",
            
        )
        .order_by("-created_at")
    )

    if query:
        notifikasi_queryset = notifikasi_queryset.filter(
            Q(judul__icontains=query)
            | Q(pesan__icontains=query)
            
        )

    if jenis:
        notifikasi_queryset = notifikasi_queryset.filter(
            jenis=jenis,
        )

    if status == "belum_dibaca":
        notifikasi_queryset = notifikasi_queryset.filter(
            is_read=False,
        )
    elif status == "is_read":
        notifikasi_queryset = notifikasi_queryset.filter(
            is_read=True,
        )

    paginator = Paginator(notifikasi_queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "notifikasi_list": page_obj.object_list,
        "query": query,
        "selected_jenis": jenis,
        "selected_status": status,
        "jenis_choices": Notifikasi.JenisNotifikasi.choices,
        "total_notifikasi": semua_notifikasi.count(),
        "total_belum_dibaca": semua_notifikasi.filter(
            is_read=False,
        ).count(),
        "total_is_read": semua_notifikasi.filter(
            is_read=True,
        ).count(),
    }

    return render(
        request,
        "administrator/notifikasi/notifikasi_list.html",
        context,
    )


@administrator_required
def notifikasi_detail(request, pk):
    notifikasi = get_object_or_404(
        Notifikasi.objects.select_related(
            "penerima",
            
        ),
        pk=pk,
        penerima=request.user,
    )

    if not notifikasi.is_read:
        notifikasi.tandai_dibaca()

    return render(
        request,
        "administrator/notifikasi/notifikasi_detail.html",
        {
            "notifikasi": notifikasi,
        },
    )


@administrator_required
@require_POST
def notifikasi_tandai_dibaca(request, pk):
    notifikasi = get_object_or_404(
        Notifikasi,
        pk=pk,
        penerima=request.user,
    )

    notifikasi.tandai_dibaca()

    messages.success(
        request,
        "Notifikasi berhasil ditandai sebagai sudah dibaca.",
    )

    next_url = request.POST.get("next")

    if next_url:
        return redirect(next_url)

    return redirect("administrator:notifikasi_list")


@administrator_required
@require_POST
def notifikasi_tandai_belum_dibaca(request, pk):
    notifikasi = get_object_or_404(
        Notifikasi,
        pk=pk,
        penerima=request.user,
    )

    notifikasi.is_read = False
    notifikasi.dibaca_pada = None

    notifikasi.save(
        update_fields=[
            "is_read",
            "dibaca_pada",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "Notifikasi berhasil ditandai sebagai belum dibaca.",
    )

    return redirect("administrator:notifikasi_list")


@administrator_required
@require_POST
def notifikasi_tandai_semua_dibaca(request):
    jumlah_diubah = Notifikasi.objects.filter(
        penerima=request.user,
        is_read=False,
    ).update(
        is_read=True,
        dibaca_pada=timezone.now(),
        updated_at=timezone.now(),
    )

    if jumlah_diubah:
        messages.success(
            request,
            f"{jumlah_diubah} notifikasi berhasil ditandai sebagai sudah dibaca.",
        )
    else:
        messages.info(
            request,
            "Tidak ada notifikasi baru yang perlu ditandai.",
        )

    return redirect("administrator:notifikasi_list")


@administrator_required
@require_POST
def notifikasi_hapus(request, pk):
    notifikasi = get_object_or_404(
        Notifikasi,
        pk=pk,
        penerima=request.user,
    )

    notifikasi.delete()

    messages.success(
        request,
        "Notifikasi berhasil dihapus.",
    )

    return redirect("administrator:notifikasi_list")


@administrator_required
@require_POST
def notifikasi_hapus_semua_dibaca(request):
    jumlah_dihapus, _ = Notifikasi.objects.filter(
        penerima=request.user,
        is_read=True,
    ).delete()

    if jumlah_dihapus:
        messages.success(
            request,
            f"{jumlah_dihapus} notifikasi yang sudah dibaca berhasil dihapus.",
        )
    else:
        messages.info(
            request,
            "Tidak ada notifikasi yang sudah dibaca untuk dihapus.",
        )

    return redirect("administrator:notifikasi_list")