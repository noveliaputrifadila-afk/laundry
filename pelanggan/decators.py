from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def pelanggan_required(view_function):
    @wraps(view_function)
    def wrapper(request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            return redirect("login")

        if user.role != user.Role.PELANGGAN:
            messages.error(
                request,
                "Anda tidak memiliki akses ke halaman pelanggan.",
            )

            if user.role == user.Role.ADMINISTRATOR:
                return redirect("administrator:dashboard")

            if user.role == user.Role.KASIR:
                return redirect("kasir:dashboard")

            if user.role == user.Role.PETUGAS_LAUNDRY:
                return redirect("petugas:dashboard")

            return redirect("login")

        return view_function(request, *args, **kwargs)

    return wrapper