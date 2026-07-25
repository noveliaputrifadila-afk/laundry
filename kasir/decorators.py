from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def kasir_required(view_function):
    @login_required
    @wraps(view_function)
    def wrapper(request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            return redirect("login")

        role = getattr(user, "role", None)

        if role not in {
            user.Role.KASIR,
            user.Role.ADMINISTRATOR,
        }:
            messages.error(
                request,
                "Anda tidak memiliki hak akses ke halaman kasir.",
            )

            return redirect("login")

        return view_function(request, *args, **kwargs)

    return wrapper