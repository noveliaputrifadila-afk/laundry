from django.urls import path

from .views import dashboard
from .views_pesanan import (
    pesanan_create,
    pesanan_detail,
    pesanan_list,
    pesanan_terima,
    pesanan_tolak,
    pesanan_pemeriksaan,
    pesanan_selesai,
)
from .views_invoice import (
    invoice_batalkan,
    invoice_create,
    invoice_detail,
    invoice_list,
    invoice_print,
    invoice_terbitkan,
)
from .views_pembayaran import (
    pembayaran_create,
    pembayaran_detail,
    pembayaran_list,
    pembayaran_tolak,
    pembayaran_verifikasi,
)
from .views_pelanggan import (
    pelanggan_detail,
    pelanggan_list,
    pelanggan_register,
)
from .views_notifikasi import (
    notifikasi_baca,
    notifikasi_baca_semua,
    notifikasi_list,
)
from .views_riwayat import riwayat_transaksi


app_name = "kasir"


urlpatterns = [
    path(
        "",
        dashboard,
        name="dashboard",
    ),
        path(
        "pesanan/<int:pk>/terima/",
        pesanan_terima,
        name="pesanan_terima",
    ),

    path(
        "pesanan/<int:pk>/tolak/",
        pesanan_tolak,
        name="pesanan_tolak",
    ),
    path(
        "pesanan/",
        pesanan_list,
        name="pesanan_list",
    ),
    path(
        "pesanan/buat/",
        pesanan_create,
        name="pesanan_create",
    ),

    path(
        "pesanan/<int:pk>/",
        pesanan_detail,
        name="pesanan_detail",
    ),
    path(
        "pesanan/<int:pk>/pemeriksaan/",
        pesanan_pemeriksaan,
        name="pesanan_pemeriksaan",
    ),
    path(
        "pesanan/<int:pk>/selesai/",
        pesanan_selesai,
        name="pesanan_selesai",
    ),
    path(
        "invoice/",
        invoice_list,
        name="invoice_list",
    ),

    path(
        "invoice/buat/<int:pesanan_pk>/",
        invoice_create,
        name="invoice_create",
    ),

    path(
        "invoice/<int:pk>/",
        invoice_detail,
        name="invoice_detail",
    ),

    path(
        "invoice/<int:pk>/terbitkan/",
        invoice_terbitkan,
        name="invoice_terbitkan",
    ),

    path(
        "invoice/<int:pk>/batalkan/",
        invoice_batalkan,
        name="invoice_batalkan",
    ),

    path(
        "invoice/<int:pk>/cetak/",
        invoice_print,
        name="invoice_print",
    ),
# Pembayaran
    path(
        "pembayaran/",
        pembayaran_list,
        name="pembayaran_list",
    ),

    path(
        "pembayaran/catat/",
        pembayaran_create,
        name="pembayaran_create",
    ),

    path(
        "pembayaran/catat/<int:pesanan_pk>/",
        pembayaran_create,
        name="pembayaran_create_pesanan",
    ),

    path(
        "pembayaran/<int:pk>/",
        pembayaran_detail,
        name="pembayaran_detail",
    ),

    path(
        "pembayaran/<int:pk>/verifikasi/",
        pembayaran_verifikasi,
        name="pembayaran_verifikasi",
    ),

    path(
        "pembayaran/<int:pk>/tolak/",
        pembayaran_tolak,
        name="pembayaran_tolak",
    ),
# Pelanggan
    path(
        "pelanggan/",
        pelanggan_list,
        name="pelanggan_list",
    ),

    path(
        "pelanggan/<int:pk>/",
        pelanggan_detail,
        name="pelanggan_detail",
    ),
    path(
        "pelanggan/register/",
        pelanggan_register,
        name="pelanggan_register",
    ),
# Riwayat Transaksi
    path(
        "riwayat-transaksi/",
        riwayat_transaksi,
        name="riwayat_transaksi",
    ),
    path(
        "notifikasi/",
        notifikasi_list,
        name="notifikasi_list",
    ),
    path(
        "notifikasi/<int:pk>/baca/",
        notifikasi_baca,
        name="notifikasi_baca",
    ),
    path(
        "notifikasi/baca-semua/",
        notifikasi_baca_semua,
        name="notifikasi_baca_semua",
    ),


]