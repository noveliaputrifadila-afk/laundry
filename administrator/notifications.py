from .models import Notifikasi


def buat_notifikasi(
    penerima,
    judul,
    pesan,
    jenis=Notifikasi.JenisNotifikasi.INFO,
    link="",
):
    if penerima is None:
        return None

    return Notifikasi.objects.create(
        penerima=penerima,
        judul=judul,
        pesan=pesan,
        jenis=jenis,
        link=link,
    )
