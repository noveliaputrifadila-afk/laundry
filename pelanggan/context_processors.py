from administrator.models import Notifikasi


def notifikasi_pelanggan(request):
    jumlah_belum_dibaca = 0

    if request.user.is_authenticated:
        jumlah_belum_dibaca = Notifikasi.objects.filter(
            penerima=request.user,
            is_read=False,
        ).count()

    return {
    "jumlah_notifikasi_belum_dibaca": jumlah_belum_dibaca,
    "jumlah_notifikasi_pelanggan": jumlah_belum_dibaca,
}