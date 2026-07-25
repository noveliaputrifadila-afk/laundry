from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from administrator.views_auth import (
    PelangganRegistrationView,
    RedirectDashboardView,
    RoleBasedLoginView,
    logout_view,
)


urlpatterns = [
    path(
        "django-admin/",
        admin.site.urls,
    ),
    

    # Autentikasi
    path(
        "",
        RedirectDashboardView.as_view(),
        name="home",
    ),
    path(
        "login/",
        RoleBasedLoginView.as_view(),
        name="login",
    ),
    path(
        "register/",
        PelangganRegistrationView.as_view(),
        name="register",
    ),
    path(
        "logout/",
        logout_view,
        name="logout",
    ),

    # Empat aplikasi
    path(
        "administrator/",
        include("administrator.urls"),
    ),
    path(
        "kasir/",
        include("kasir.urls"),
    ),
    path(
        "petugaslaundry/",
        include("petugaslaundry.urls"),
    ),
    path(
        "pelanggan/",
        include("pelanggan.urls"),
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )