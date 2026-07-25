from django.shortcuts import render

from administrator.decorators import role_required
from administrator.models import Pesanan, User


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