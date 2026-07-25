from django.urls import path

from .views import (
    dashboard,
    tugas_detail,
    tugas_list,
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

]