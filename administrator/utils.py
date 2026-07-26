from .models import LogAktivitas


def get_client_ip(request):
    forwarded_for = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def catat_log(
    request,
    aktivitas,
    jenis=LogAktivitas.JenisAktivitas.LAINNYA,
    objek="",
    keterangan="",
):
    pengguna = None

    if (
        hasattr(request, "user")
        and request.user.is_authenticated
    ):
        pengguna = request.user

    return LogAktivitas.objects.create(
        pengguna=pengguna,
        jenis=jenis,
        aktivitas=aktivitas,
        objek=objek,
        keterangan=keterangan,
        ip_address=get_client_ip(request),
        user_agent=request.META.get(
            "HTTP_USER_AGENT",
            "",
        ),
    )