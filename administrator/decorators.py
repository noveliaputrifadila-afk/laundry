from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from .models import User


def administrator_or_kasir_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        role_diizinkan = {
            User.Role.ADMINISTRATOR,
            User.Role.KASIR,
        }

        if request.user.role not in role_diizinkan:
            messages.error(
                request,
                (
                    "Halaman ini hanya dapat diakses "
                    "administrator atau kasir."
                ),
            )

            return redirect("dashboard")

        return view_func(
            request,
            *args,
            **kwargs,
        )

    return wrapper

def role_required(allowed_roles):
    """
    Membatasi view berdasarkan role pengguna.

    Contoh:
        @role_required([User.Role.ADMINISTRATOR])
        def dashboard(request):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(
                    request.get_full_path()
                )

            if not request.user.is_active:
                messages.error(
                    request,
                    "Akun Anda sedang tidak aktif.",
                )
                return redirect("logout")

            if request.user.role not in allowed_roles:
                raise PermissionDenied(
                    "Anda tidak memiliki hak akses "
                    "ke halaman tersebut."
                )

            if (
                request.user.role == User.Role.PELANGGAN
                and not request.user.is_verified
            ):
                messages.warning(
                    request,
                    "Akun Anda belum diverifikasi.",
                )
                return redirect("logout")

            return view_func(
                request,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator


def administrator_required(view_func):
    return role_required(
        [User.Role.ADMINISTRATOR]
    )(view_func)


def kasir_required(view_func):
    return role_required(
        [User.Role.KASIR]
    )(view_func)


def petugas_laundry_required(view_func):
    return role_required(
        [User.Role.PETUGAS_LAUNDRY]
    )(view_func)


def pelanggan_required(view_func):
    return role_required(
        [User.Role.PELANGGAN]
    )(view_func)