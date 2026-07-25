from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from administrator.models import User

from .decorators import kasir_required
from .forms_pelanggan import PelangganKasirRegistrationForm

@kasir_required
def pelanggan_list(request):
    pelanggan_queryset = (
        User.objects
        .filter(role="pelanggan")
        .order_by("-date_joined")
    )

    keyword = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    if keyword:
        pelanggan_queryset = pelanggan_queryset.filter(
            Q(username__icontains=keyword)
            | Q(first_name__icontains=keyword)
            | Q(last_name__icontains=keyword)
            | Q(email__icontains=keyword)
            | Q(nomor_hp__icontains=keyword)
        )

    if status == "aktif":
        pelanggan_queryset = pelanggan_queryset.filter(
            is_active=True,
            is_verified=True,
        )

    elif status == "menunggu":
        pelanggan_queryset = pelanggan_queryset.filter(
            is_verified=False,
        )

    elif status == "nonaktif":
        pelanggan_queryset = pelanggan_queryset.filter(
            is_active=False,
        )

    total_pelanggan = pelanggan_queryset.count()

    paginator = Paginator(pelanggan_queryset, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "pelanggan_list": page_obj.object_list,
        "page_obj": page_obj,
        "keyword": keyword,
        "status_terpilih": status,
        "total_pelanggan": total_pelanggan,
    }

    return render(
        request,
        "kasir/pelanggan/list.html",
        context,
    )

@kasir_required
def pelanggan_register(request):
    if request.method == "POST":
        form = PelangganKasirRegistrationForm(
            request.POST
        )

        if form.is_valid():
            pelanggan = form.save()

            messages.success(
                request,
                (
                    f"Pelanggan {pelanggan.get_full_name() or pelanggan.username} "
                    "berhasil didaftarkan dan langsung terverifikasi."
                ),
            )

            return redirect(
                "kasir:pelanggan_detail",
                pk=pelanggan.pk,
            )

    else:
        form = PelangganKasirRegistrationForm()

    context = {
        "form": form,
    }

    return render(
        request,
        "kasir/pelanggan/register.html",
        context,
    )

@kasir_required
def pelanggan_detail(request, pk):
    pelanggan = get_object_or_404(
        User.objects.prefetch_related(
            "pesanan_pelanggan",
        ),
        pk=pk,
        role="pelanggan",
    )

    pesanan_terbaru = (
        pelanggan.pesanan_pelanggan
        .select_related(
            "metode_pembayaran",
            "kasir",
            "petugas_laundry",
        )
        .order_by("-created_at")[:10]
    )

    context = {
        "pelanggan": pelanggan,
        "pesanan_terbaru": pesanan_terbaru,
    }

    return render(
        request,
        "kasir/pelanggan/detail.html",
        context,
    )