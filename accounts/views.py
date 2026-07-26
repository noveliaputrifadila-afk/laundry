from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import (
    CustomPasswordChangeForm,
    ProfileUpdateForm,
)


@login_required
def profile_view(request):
    return render(
        request,
        "accounts/profile.html",
        {
            "profile_user": request.user,
        },
    )


@login_required
def profile_edit(request):
    if request.method == "POST":
        form = ProfileUpdateForm(
            request.POST,
            instance=request.user,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Profil berhasil diperbarui.",
            )

            return redirect("accounts:profile")
    else:
        form = ProfileUpdateForm(
            instance=request.user,
        )

    return render(
        request,
        "accounts/profile_edit.html",
        {
            "form": form,
        },
    )


@login_required
def password_change(request):
    if request.method == "POST":
        form = CustomPasswordChangeForm(
            request.user,
            request.POST,
        )

        if form.is_valid():
            user = form.save()

            update_session_auth_hash(
                request,
                user,
            )

            messages.success(
                request,
                "Password berhasil diubah.",
            )

            return redirect("accounts:profile")
    else:
        form = CustomPasswordChangeForm(
            request.user,
        )

    return render(
        request,
        "accounts/password_change.html",
        {
            "form": form,
        },
    )