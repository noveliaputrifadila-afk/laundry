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
from .forms import UserCreateForm, UserUpdateForm
from .models import User


@administrator_required
def user_list(request):
    """
    Menampilkan seluruh pengguna dengan fitur:
    - pencarian
    - filter role
    - filter status akun
    - filter verifikasi
    - pagination
    """

    users = User.objects.all().order_by("-date_joined")

    keyword = request.GET.get("q", "").strip()
    role = request.GET.get("role", "").strip()
    status = request.GET.get("status", "").strip()
    verifikasi = request.GET.get("verifikasi", "").strip()

    if keyword:
        users = users.filter(
            Q(username__icontains=keyword)
            | Q(first_name__icontains=keyword)
            | Q(last_name__icontains=keyword)
            | Q(email__icontains=keyword)
            | Q(nomor_hp__icontains=keyword)
        )

    valid_roles = {
        choice[0]
        for choice in User.Role.choices
    }

    if role in valid_roles:
        users = users.filter(role=role)

    if status == "aktif":
        users = users.filter(is_active=True)

    elif status == "nonaktif":
        users = users.filter(is_active=False)

    if verifikasi == "terverifikasi":
        users = users.filter(is_verified=True)

    elif verifikasi == "belum":
        users = users.filter(is_verified=False)

    jumlah_user = users.count()

    paginator = Paginator(users, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "jumlah_user": jumlah_user,
        "keyword": keyword,
        "role_filter": role,
        "status_filter": status,
        "verifikasi_filter": verifikasi,
        "role_choices": User.Role.choices,
    }

    return render(
        request,
        "administrator/users/user_list.html",
        context,
    )


@administrator_required
def user_create(request):
    """
    Administrator membuat akun internal:
    - Administrator
    - Kasir
    - Petugas Laundry
    """

    if request.method == "POST":
        form = UserCreateForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            user_obj = form.save()

            messages.success(
                request,
                (
                    f"Pengguna {user_obj.username} "
                    "berhasil ditambahkan."
                ),
            )

            return redirect(
                "administrator:user_detail",
                pk=user_obj.pk,
            )

    else:
        form = UserCreateForm()

    context = {
        "form": form,
        "judul": "Tambah Pengguna",
        "deskripsi": (
            "Tambahkan akun Administrator, Kasir, "
            "atau Petugas Laundry."
        ),
        "tombol": "Simpan Pengguna",
    }

    return render(
        request,
        "administrator/users/user_form.html",
        context,
    )


@administrator_required
def user_detail(request, pk):
    """
    Menampilkan detail pengguna.
    """

    user_obj = get_object_or_404(
        User,
        pk=pk,
    )

    context = {
        "user_obj": user_obj,
    }

    return render(
        request,
        "administrator/users/user_detail.html",
        context,
    )


@administrator_required
def user_update(request, pk):
    """
    Mengubah data pengguna.
    """

    user_obj = get_object_or_404(
        User,
        pk=pk,
    )

    if request.method == "POST":
        form = UserUpdateForm(
            request.POST,
            request.FILES,
            instance=user_obj,
            request_user=request.user,
        )

        if form.is_valid():
            user_obj = form.save()

            messages.success(
                request,
                (
                    f"Data pengguna {user_obj.username} "
                    "berhasil diperbarui."
                ),
            )

            return redirect(
                "administrator:user_detail",
                pk=user_obj.pk,
            )

    else:
        form = UserUpdateForm(
            instance=user_obj,
            request_user=request.user,
        )

    context = {
        "form": form,
        "judul": "Edit Pengguna",
        "deskripsi": (
            f"Ubah data akun {user_obj.username}."
        ),
        "tombol": "Simpan Perubahan",
        "user_obj": user_obj,
    }

    return render(
        request,
        "administrator/users/user_form.html",
        context,
    )


@require_POST
@administrator_required
def user_toggle_active(request, pk):
    """
    Mengaktifkan atau menonaktifkan akun pengguna.
    """

    user_obj = get_object_or_404(
        User,
        pk=pk,
    )

    if user_obj.pk == request.user.pk:
        messages.error(
            request,
            "Anda tidak dapat menonaktifkan akun sendiri.",
        )

        return redirect(
            "administrator:user_detail",
            pk=user_obj.pk,
        )

    if user_obj.is_superuser:
        messages.error(
            request,
            "Akun superuser tidak dapat dinonaktifkan.",
        )

        return redirect(
            "administrator:user_detail",
            pk=user_obj.pk,
        )

    user_obj.is_active = not user_obj.is_active

    user_obj.save(
        update_fields=[
            "is_active",
        ]
    )

    if user_obj.is_active:
        status = "diaktifkan"
    else:
        status = "dinonaktifkan"

    messages.success(
        request,
        (
            f"Akun {user_obj.username} "
            f"berhasil {status}."
        ),
    )

    return redirect(
        "administrator:user_detail",
        pk=user_obj.pk,
    )


@require_POST
@administrator_required
def user_verify(request, pk):
    """
    Memverifikasi akun pelanggan.
    """

    user_obj = get_object_or_404(
        User,
        pk=pk,
        role=User.Role.PELANGGAN,
    )

    if user_obj.is_verified:
        messages.info(
            request,
            "Akun pelanggan tersebut sudah diverifikasi.",
        )

        return redirect(
            "administrator:user_detail",
            pk=user_obj.pk,
        )

    user_obj.is_verified = True
    user_obj.is_active = True

    user_obj.save(
        update_fields=[
            "is_verified",
            "is_active",
        ]
    )

    messages.success(
        request,
        (
            f"Akun pelanggan {user_obj.username} "
            "berhasil diverifikasi."
        ),
    )

    return redirect(
        "administrator:user_detail",
        pk=user_obj.pk,
    )