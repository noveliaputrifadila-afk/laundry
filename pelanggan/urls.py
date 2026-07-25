from django.urls import path

from . import views


app_name = "pelanggan"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path(
            "pesanan/tambah/",
            views.pesanan_tambah,
            name="pesanan_tambah",
        ),
]