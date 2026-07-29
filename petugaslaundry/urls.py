from django.urls import path

from .views import (
    dashboard,
    kendala_detail,
    kendala_list,
    kendala_tambah,
    tugas_detail,
    tugas_list,
    update_status,
)
from .views_notifikasi import (
    notifikasi_baca,
    notifikasi_baca_semua,
    notifikasi_list,
)


app_name = "petugas"


urlpatterns = [
    path(
        "",
        dashboard,
        name="dashboard",
    ),
    path(
            "tugas/",
            tugas_list,
            name="tugas_list",
        ),

    path(
        "tugas/<int:pk>/",
        tugas_detail,
        name="tugas_detail",
    ),
    path(
        "tugas/<int:pk>/update-status/",
        update_status,
        name="update_status",
    ),
    path(
        "kendala/",
        kendala_list,
        name="kendala_list",
    ),

    path(
        "kendala/tambah/<int:pesanan_pk>/",
        kendala_tambah,
        name="kendala_tambah",
    ),

    path(
        "kendala/<int:pk>/",
        kendala_detail,
        name="kendala_detail",
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