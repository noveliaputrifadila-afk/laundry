from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST

from .decorators import administrator_required
from .forms import (
    PelangganRegistrationForm,
    RoleAuthenticationForm,
)
from .models import User


class RoleBasedLoginView(LoginView):
    """
    Login utama seluruh pengguna.

    Setelah berhasil login, pengguna diarahkan menuju
    dashboard berdasarkan role.
    """

    template_name = "registration/login.html"
    authentication_form = RoleAuthenticationForm
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_role_url(request.user))

        return super().dispatch(
            request,
            *args,
            **kwargs,
        )

    def form_valid(self, form):
        response = super().form_valid(form)

        remember_me = form.cleaned_data.get("remember_me")

        if remember_me:
            self.request.session.set_expiry(
                self.request.session.get_expiry_age()
            )
        else:
            self.request.session.set_expiry(0)

        nama = (
            self.request.user.get_full_name()
            or self.request.user.username
        )

        messages.success(
            self.request,
            f"Selamat datang, {nama}.",
        )

        return response

    def get_success_url(self):
        next_url = self.get_redirect_url()

        if next_url:
            return next_url

        return self.get_role_url(self.request.user)

    @staticmethod
    def get_role_url(user):
        role_urls = {
            User.Role.ADMINISTRATOR: (
                "administrator:dashboard"
            ),
            User.Role.KASIR: "kasir:dashboard",
            User.Role.PETUGAS_LAUNDRY: (
                "petugas:dashboard"
            ),
            User.Role.PELANGGAN: "pelanggan:dashboard",
        }

        return reverse_lazy(
            role_urls.get(
                user.role,
                "login",
            )
        )


class PelangganRegistrationView(View):
    """
    Registrasi pelanggan.

    Akun yang baru dibuat belum dapat digunakan sebelum
    diverifikasi administrator.
    """

    template_name = "registration/register.html"
    form_class = PelangganRegistrationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(
                RoleBasedLoginView.get_role_url(
                    request.user
                )
            )

        return super().dispatch(
            request,
            *args,
            **kwargs,
        )

    def get(self, request):
        form = self.form_class()

        return render(
            request,
            self.template_name,
            {
                "form": form,
            },
        )

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                (
                    "Registrasi berhasil. Akun Anda sedang "
                    "menunggu verifikasi administrator."
                ),
            )

            return redirect("login")

        return render(
            request,
            self.template_name,
            {
                "form": form,
            },
        )


class RedirectDashboardView(LoginRequiredMixin, View):
    """
    Mengarahkan pengguna yang sudah login ke dashboard
    sesuai role.
    """

    login_url = reverse_lazy("login")

    def get(self, request):
        return redirect(
            RoleBasedLoginView.get_role_url(
                request.user
            )
        )


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(
            request,
            "Anda berhasil keluar dari aplikasi.",
        )

    return redirect("login")


@administrator_required
def pelanggan_menunggu_verifikasi(request):
    pelanggan = User.objects.filter(
        role=User.Role.PELANGGAN,
        is_verified=False,
    ).order_by("-date_joined")

    context = {
        "pelanggan_list": pelanggan,
        "jumlah_menunggu": pelanggan.count(),
    }

    return render(
        request,
        "administrator/pelanggan/verifikasi_list.html",
        context,
    )


@require_POST
@administrator_required
def verifikasi_pelanggan(request, pk):
    pelanggan = get_object_or_404(
        User,
        pk=pk,
        role=User.Role.PELANGGAN,
    )

    if pelanggan.is_verified:
        messages.info(
            request,
            "Pelanggan tersebut sudah diverifikasi.",
        )
        return redirect(
            "administrator:pelanggan_verifikasi"
        )

    pelanggan.verifikasi(request.user)

    messages.success(
        request,
        (
            f"Akun pelanggan {pelanggan.username} "
            f"berhasil diverifikasi."
        ),
    )

    return redirect(
        "administrator:pelanggan_verifikasi"
    )


@require_POST
@administrator_required
def tolak_pelanggan(request, pk):
    """
    Untuk sementara penolakan membuat akun menjadi nonaktif.

    Data tidak langsung dihapus agar tetap memiliki riwayat.
    """

    pelanggan = get_object_or_404(
        User,
        pk=pk,
        role=User.Role.PELANGGAN,
        is_verified=False,
    )

    alasan = request.POST.get(
        "alasan",
        "",
    ).strip()

    if not alasan:
        messages.error(
            request,
            "Alasan penolakan wajib diisi.",
        )
        return redirect(
            "administrator:pelanggan_verifikasi"
        )

    pelanggan.is_active = False
    pelanggan.save(
        update_fields=[
            "is_active",
        ]
    )

    messages.warning(
        request,
        (
            f"Registrasi {pelanggan.username} ditolak. "
            f"Alasan: {alasan}"
        ),
    )

    return redirect(
        "administrator:pelanggan_verifikasi"
    )