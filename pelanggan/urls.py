from django.urls import path

from . import views


app_name = "pelanggan"


urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "pesanan/tambah/",
        views.pesanan_tambah,
        name="pesanan_tambah",
    ),

    path(
    "pesanan/",
    views.pesanan_saya,
    name="pesanan_saya",
    ),

    path(
    "pesanan/lacak/",
    views.lacak_laundry,
    name="lacak_laundry",
),

path(
    "pembayaran/",
    views.pembayaran_list,
    name="pembayaran_list",
),
path(
    "pembayaran/<int:pesanan_id>/tambah/",
    views.pembayaran_tambah,
    name="pembayaran_tambah",
),
path(
    "invoice/",
    views.invoice_list,
    name="invoice_list",
),
path(
    "notifikasi/",
    views.notifikasi_list,
    name="notifikasi_list",
),
path(
    "notifikasi/<int:pk>/baca/",
    views.notifikasi_baca,
    name="notifikasi_baca",
),
path(
    "notifikasi/baca-semua/",
    views.notifikasi_baca_semua,
    name="notifikasi_baca_semua",
),
]